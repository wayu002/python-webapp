# coding:utf-8
# !/usr/bin/python

import time
import uuid
import functools
import threading
from www.log import Log

_log = Log(__name__)

class Dict(dict):
    '''
    >>> d1 = Dict()
    >>> d1['x'] = 100
    >>> d1.x
    100
    >>> d1.y = 200
    >>> d1['y']
    200
    >>> d2 = Dict(a=1,b=2,c='3')
    >>> d2.c
    '3'
    >>> d2['empty']
    Traceback (most recent call last):
        ...
    KeyError: 'empty'
    >>> d2.empty
    Traceback (most recent call last):
    ...
    AttributeError: 'Dict' has no attribute 'empty'
    >>> d3 = Dict(('a','b','c'),(1,2,3))
    >>> d3.a
    1
    >>> d3.b
    2
    >>> d3.c
    3
    '''
    def __init__(self, names=(), values=(), **kw):
        super(Dict, self).__init__(**kw)
        for k, v in zip(names, values):
            self[k] = v

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Dict' has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value


def next_id(t=None):
    '''
    Return next id as 50-char string.
    '''
    if t is None:
        t = time.time()
    return '%015d%s000' % (int(t*1000), uuid.uuid4().hex)


def _profiling(start, sql=''):
    t = time.time() - start
    if t > 0.1:
        _log.warning('[PROFILING] [DB] %s: %s' % (t, sql))
    else:
        _log.info('[PROFILING] [DB] %s: %s' % (t, sql))


class DBError(Exception):
    pass


class MultiColumnsError(DBError):
    pass


class _LasyConnection(object):
    def __init__(self):
        self.connection = None

    def cursor(self):
        if self.connection is None:
            connection = engine.connect()
            _log.info('open connection <%s>...' % hex(id(connection)))
            self.connection = connection
        return self.connection.cursor()

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def cleanup(self):
        if self.connection:
            connection = self.connection
            self.connection = None
            _log.info('close connection <%s> ...' % hex(id(connection)))
            connection.close()


class _DbCtx(threading.local):
    '''
    Thread local object that holds connection info.
    '''

    def __init__(self):
        self.connection = None
        self.transactions = 0

    def is_init(self):
        return self.connection is not None

    def init(self):
        _log.info('open lazy connection...')
        self.connection = _LasyConnection()
        self.transactions = 0

    def cleanup(self):
        self.connection.cleanup()
        self.connection = None

    def cursor(self):
        return self.connection.cursor()

# thread-local db context:
_db_ctx = _DbCtx()

# global engine object:
engine = None


class _Engine(object):
    def __init__(self, connect):
        self._connect = connect

    def connect(self):
        return self._connect()


def create_engine(user, password, database, host='127.0.0.1', port=3306, **kw):
    import mysql.connector
    global engine
    if engine is not None:
        raise DBError('Engine is already initialized.')
    params = dict(user=user, password=password, database=database, host=host,
                  port=port)
    defaults = dict(use_unicode=True, charset='utf8', collation=
                    'utf8_general_ci', autocommit=False)
    for k, v in defaults.iteritems():
        params[k] = kw.pop(k, v)
    params.update(kw)
    params['buffered'] = True
    engine = _Engine(lambda: mysql.connector.connect(**params))
    _log.info('Init mysql engine <%s> ok.' % hex(id(engine)))


class _ConnectionCtx(object):
    '''
    _ConnectionCtx object that can open and close connection context.
    '''


    def __enter__(self):
        global _db_ctx
        self.should_cleanup = False
        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_cleanup = True
        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_ctx
        if self.should_cleanup:
            _db_ctx.cleanup()

def connection():
    '''
    Return _ConnectionCtx object that can be used by 'with' statement
    '''
    return _ConnectionCtx()

def with_connection(func):
    '''
    Decorator for reuse connection
    '''
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        with _ConnectionCtx():
            return func(*args, **kw)
    return _wrapper

class _TransacationCtx(object):
    '''
    _TransacationCtx object that can handle transactions.
    '''
    def __enter__(self):
        global _db_ctx
        self.should_close_conn = False
        if not _db_ctx.is_init():
            _db_ctx.init()
            self.should_close_conn = True
        _db_ctx.transactions = _db_ctx.transactions + 1
        _log.info('begin transaction...' if _db_ctx.transactions == 1 else
                     'join current transaction...')
        return self

    def __exit__(self, exctype, excvalue, traceback):
        global _db_ctx
        _db_ctx.transactions = _db_ctx.transactions - 1
        try:
            if _db_ctx.transactions == 0:
                if exctype is None:
                    self.commit()
                else:
                    self.rollback()
        finally:
            if self.should_close_conn:
                _db_ctx.cleanup()

    def commit(self):
        global _db_ctx
        _log.info('commit transactions...')
        try:
            _db_ctx.connection.commit()
            _log.info('commit ok.')
        except:
            _log.warning('commit failed try rollback...')
            _db_ctx.connection.rollback()
            _log.info('rollback ok.')
            raise

    def rollback(self):
        global _db_ctx
        _log.warning('rollback transaction...')
        _db_ctx.connection.rollback()
        _log.info('rollback ok')

def transaction():
    '''
    Create a transaction object so can use with statement.
    '''
    return _TransacationCtx()

def with_transactions(func):
    @functools.wraps(func)
    def _wrapper(*args, **kw):
        _start = time.time()
        with _TransacationCtx():
            return func(*args, **kw)
        _profiling(_start)
    return _wrapper

def _select(sql, first, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    _log.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, args)
        if cursor.description:
            name = [x[0] for x in cursor.description]
        if first:
            values = cursor.fetchone()
            if not values:
                return None
            return Dict(name, values)
        return [Dict(name, x) for x in cursor.fetchall()]
    finally:
        if cursor:
            cursor.close()

@with_connection
def select_one(sql, *args):
    return _select(sql, True, *args)

@with_connection
def select_int(sql, *args):
    d = _select(sql, True, *args)
    if len(d) != 1:
        raise MultiColumnsError('Expect only one column.')
    return d.values()[0]

@with_connection
def select(sql, *args):
    return _select(sql, False, *args)

@with_connection
def _update(sql, *args):
    global _db_ctx
    cursor = None
    sql = sql.replace('?', '%s')
    _log.info('SQL: %s, ARGS: %s' % (sql, args))
    try:
        cursor = _db_ctx.connection.cursor()
        cursor.execute(sql, args)
        r = cursor.rowcount
        if _db_ctx.transactions == 0:
            _log.info('auto commit')
            _db_ctx.connection.commit()
        return r
    finally:
        if cursor:
            cursor.close()

def insert(table, **kw):
    cols, args = zip(*kw.iteritems())
    sql = 'insert into `%s` (%s) values (%s)' % (table, ','.join(['`%s`' % col for col in cols]),','.join(['?' for i in range(len(cols))]))
    return _update(sql, *args)

def update(sql, *args):
    return _update(sql, *args)

if __name__ == '__main__':
    _log.basicConfig(level=logging.DEBUG)
    create_engine('wangyu', 'taotao', 'python_blog')
    update('drop table if exists user')
    update('create table user (id int primary key, name text, email text, passwd text, last_modified real)')
    import doctest
    doctest.testmod()
    print next_id()
