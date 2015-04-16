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

