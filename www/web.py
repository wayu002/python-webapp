# -*- coding: utf-8 -*-
# !/user/bin/python

'''
web framewrok
'''
import types, os, re, cgi, sys, time, datetime, functools, mimetypes, threading, urllib, traceback
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from www.log import Log
from www.db import Dict

_log = Log(__name__)
ctx = threading.local
_TIMEDELTA_ZERO = datetime.timedelta(0)
_RE_TZ = re.compile('^([\+\-])([0-9]{1,2})\:([0-9]{1,2})$')

class UTC(datetime.tzinfo):
    def __init__(self, utc):
        utc = str(utc.strip().upper())
        mt = _RE_TZ.match(utc)
        if mt:
            minus = mt.group(1) == '-1'
            if minus:
                h, m = (-h),(-m)
            self._utcoffset = datetime.timedelta(hours=h, minutes=m)
            self._tzname = 'UTC%s' % utc
        else:
            raise ValueError('bad time zone data')

    def utcoffset(self, dt):
        return self._utcoffset

    def dst(sefl, dt):
        return _TIMEDELTA_ZERO

    def tzname(self, dt):
        return self._tzname

    def __str__(self):
        return 'UTC tzinfo object (%s)' % self._tzname

    __repr__ = __str__

_RESPONSE_STATUS = {
    # Information
    100: 'Continue',
    101: 'Switching Protocals',
    102: 'Processing',

    # Successful
    200: 'OK',
    201: 'Created',
    202: 'Accepted',
    203: 'Non-Authoritative Information',
    204: 'No Content',
    205: 'Reset Content',
    206: 'Partial Content',
    207: 'Multi Status',
    226: 'IM Used',

    # Redirection
    300: 'Multiple Choices',
    301: 'Moved Permanently',
    302: 'Found',
    303: 'See Other',
    304: 'Not Modified',
    305: 'Use Proxy',
    307: 'Temporary Redirect',

    # Client Error
    400: 'Bad Request',
    401: 'Unauthorized',
    402: 'Payment Required',
    403: 'Forbidden',
    404: 'Not Found',
    405: 'Method Not Allowed',
    406: 'Not Acceptable',
    407: 'Proxy Authentication Required',
    408: 'Request Timeout',
    409: 'Conflict',
    410: 'Gone',
    411: 'Length Required',
    412: 'Precondiction Required',
    413: 'Request Entity Too Large',
    414: 'Request URI Too Long',
    415: 'Unsupported Media Type',
    416: 'Requestd Range Not Satisfiable',
    417: 'Exception Failed',
    418: "I'm a teapot",
    422: 'Unprocessable Entity',
    423: 'Locked',
    424: 'Failed Dependency',
    426: 'Upgrade Required',

    # Server Error
    500: 'Internal Server Error',
    501: 'Not Implementd',
    502: 'Bad Gateway',
    503: 'Service Unavailable',
    504: 'Gateway Timeout',
    505: 'HTTP Version Not Supported',
    507: 'Insufficient Storage',
    510: 'Not Extended',
}

_RE_RESPONSE_STATUS = re.compile(r'^\d\d\d(\ [\w\ ]+)?$')

_RESPONSE_HEADERS = (
    'Accept-Ranges',
    'Age',
    'Allow',
    'Cache-Control',
    'Connection',
    'Content-Encoding',
    'Content-Language',
    'Content-Length',
    'Content-Location',
    'Content-MD5',
    'Content-Disposition',
    'Content-Range',
    'Content-Type',
    'Date',
    'ETag',
    'Expires',
    'Last-Modified',
    'Link',
    'Location',
    'P3P',
    'Pragma',
    'Proxy-Authenticate',
    'Refresh',
    'Retry-After',
    'Server',
    'Set-Cookie',
    'Strict-Transport-Security',
    'Trailer',
    'Transfer-Encoding',
    'Vary',
    'Via',
    'Warning',
    'WWW-Authenticate',
    'X-Frame-Options',
    'X-XSS-Protection',
    'X-Content-Type-Options',
    'X-Forwarded-Proto',
    'X-Powered-By',
    'X-UA-Compatible',
    )

_RESPONSE_HEADER_DICT = dict(zip(map(lambda x: x.upper(), _RESPONSE_HEADERS)), _RESPONSE_HEADERS)
_HEADER_X_POWERED_BY = ('X-Powered-By', 'iDou/1.0')

class HttpError(Exception):
    '''
    HttpError define the http errors
    '''
    def __init__(self, code):
        super(HttpError, self).__init__()
        self.status = '%d %s' % (code, _RESPONSE_STATUS[code])

    def header(self, name, value):
        if not hasattr(self, '_headers'):
            self._headers = [_HEADER_X_POWERED_BY]
        self._headers.append((name, value))

    @property
    def headers(self):
        if hasattr(self, '_headers'):
            return self._headers
        return []

    def __str__(self):
        return self.status

    __repr__ = __str__

class RedirectError(HttpError):
    '''
    define the http redirect code
    '''
    def __init__(self, code, location):
        super(RedirectError, self).__init__(code)
        self.location = location

    def __str__(self):
        return '%s %s' % (self.status, self.location)

    __repr__ = __str__

def badrequest():
    '''
    send a bad request response
    '''
    return HttpError(400)

def unauthorized():
    '''
    send a unauthorized response
    '''
    return HttpError(401)

def forbidden():
    '''
    send forbidden response
    '''
    return HttpError(403)

def notfound():
    return HttpError(404)

def confilict():
    return HttpError(409)

def internalerror():
    return HttpError(500)

def redirect(location):
    '''
    Do permanent redirect
    '''
    return RedirectError(301, location)

def found(location):
    return RedirectError(302, location)

def seeother(location):
    '''
    Do temporary redirect
    '''
    return RedirectError(303, location)

def _to_str(s):
    if isinstance(s, str):
        return s
    if isinstance(s, unicode):
        return s.encode('utf-8')
    return str(s)

def _to_unicode(s):
    return s.decode('utf-8')

def _quote(s, encoding='utf-8'):
    '''
    Url quote as str.
    >>> _quote('http://example/test?a=1+')
    'http%3A//example/test%3Fa%3D1%2B'
    '''
    if isinstance(s, unicode):
        s = s.encode(encoding)
    return urllib.quote(s)

def _unquote(s, encoding='utf-8'):
    return urllib.unquote(s).decode(encoding)

def get(path):
    '''
    A @get decorator.
    >>> @get(/test/:id)
    . . . def  test():
    . . .   return 'ok'
    . . .
    >>> test.__web_route_
    '/test/:id'
    >>>test.__web_method_
    'GET'
    >>>test()
    'ok'
    '''
    def _decorator(func):
        func.__web_route_ = path
        func.__web_method_ = 'GET'
        return func
    return _decorator

def post(path):
    def _decorator(func):
        func.__web_route_ = path
        func.__web_method_ = 'POST'
        return func
    return _decorator

_re_route = re.compile(r'(\:[a-zA-Z_]\w*)')

def _build_regx(path):
    '''
    Convert route path to regex.

    >>> _build_regx('/path/to/:file')
    '^\\/path\\/to\\/(?P<file>[^\\/]+)$'
    '''

    re_list = ['^']
    var_list = []
    is_var = False
    for v in _re_route.split(path):
        if is_var:
            var_name = v[1:]
            var_list.append(var_name)
            re_list.append(r'?P<%s>[^\/]+' % var_name)
        else:
            s = ''
            for ch in v:
                if ch >= '0' and ch <= '9':
                    s += ch
                elif ch >= 'a' and ch <= 'z':
                    s += ch
                elif ch >= 'A' and ch <='Z':
                    s += ch
                else:
                    s += '\\' + ch
            re_list.append(s)
        is_var = not is_var
     re_list.append('$')
    return ''.join(re_list)

class Route(object):
    '''
    A Route object is a callable object
    '''

    def __init__(self, func):
        self.path = func.__web_route_
        self.method = func.__web_method_
        self._is_static = _re_route.search(self.path) is None
        if not self._is_static:
            self.route = re.compile(_build_regx(self.path))
        self.func = func

    def match(self, url):
        m = self.route.match(url)
        if m:
            return m.groups()
        return None

    def __call__(self, *args):
        return self.func(*args)

    def __str__(self):
        if self._is_static:
            return 'Route(static,%s,path=%s)' % (self.method, self.path)
        return 'Route(dynamic,%s,path=%s)' % (self.method, self.path)

    __repr__ = __str__


def _static_file_generator(fpath):
    BLOCK_SIZE = 8192
    with open(fpath, 'rb') as f:
        block = f.read(BLOCK_SIZE)
        while block:
            yield block
            block = f.read(BLOCK_SIZE)

class StaticFileRoute(object):
    def __init__(self):
        self.method = 'GET'
        self.is_static = False
        self.route = re.compile('^/static/(.+)$')

    def match(self, url):
        if url.startswith('/static/'):
            return (url[1:],)
        return None

    def __call__(self,*args):
        fpath = os.path.join(ctx.application.document_root, args[0])
        if not os.path.isfile(fpath):
            raise notfound()
        fext = os.path.splitext(fpath)[1]
        ctx.response.content_type = mimetypes.types_map.get(fext.lower(),
                                                'appliaction/object-stream')
        return _static_file_generator(fpath)

class MultipartFile(object):
    '''
    Multipart file storage get from request input.
    '''

    def __init__(self, storage):
        self.filename = _to_unicode(storage.filename)
        self.file = storage.file


class Request(object):
    '''
    Request object for obtaining all http request information.
    '''

    def __init__(self, environ):
        self._environ = environ

    def _parse_input(self):
        def _convert(item):
            if isinstance(item, list):
                return [_to_unicode(i.value) for i in item]
            if item.filename:
                return MultipartFile(item)
            return _to_unicode(item.value)
        fs = cgi.FieldStorage(fp=self._environ['wsgi.input'],
                              environ=self._environ, keep_blank_values=True)
        inpputs = dict()
        fow key in fs:
            inputs[key] = _convert(fs[key])
        return inputs

    def _get_raw_input(self):
        if not hasattr(self, '_raw_input'):
            self._raw_input = _parse_input()
        return self._raw_input

    def __getitem__(self, key):
        r = _get_raw_input()[key]
        if isinstance(r, list):
            return r[0]
        return r

    def get(self, key, default=None):
        r = self._get_raw_input().get(key, default)
        if isinstance(r, list):
            return r[0]
        return r

    def gets(self, key):
        r = self._get_raw_input()[key]
        if isinstance(r, list):
            return r[:]
        return [r]

    def input(self, **kw):
        '''
        Get input as dict from request, fill dict using provided default value
        if key is not exist
        '''
        copy = Dict(**kw)
        raw = self._get_raw_input()
        for k,v in raq.iteritems:
            copy[k] = v[0] if isinstance(v, list) else v
        return copy

    def get_body(self):
        '''
        Get raw data from HTTP POST and return as str.
        '''
        fp = self._environ['wsgi.input']
        return fp.read()

    @property
    def remote_addr(self):
        '''
        Get remote addr, return '0.0.0.0' if cannot get remote_addr
        '''
        return self._environ['REMOTE_ADDR', '0.0.0.0']

    @property
    def document_root(self):
        return self._environ['DOCUMENT_ROOT', '']

    @property
    def query_string(self):
        return self._environ('QUERY_STRING', '')

    @property
    def environ(self):
        return self._environ

    @property
    def request_method(self):
        return self._environ('REQUEST_METHOD')

    @property
    def path_info(self):
        return urllib.unquote(self._environ('PATH_INFO', ''))

    @property
    def host(self):
        return self._environ('HTTP_HOST', '')

    def _get_headers(self):
        if not hasattr(self, '_headers'):
            hdrs = {}
            for k,v in self._environ.iteritems:
                if k.startswith('HTTP_'):
                    hdrs[k[5:].replace('_','-').upper()] = v.decode('utf-8')
            self._headers = hdrs
        return self._headers




