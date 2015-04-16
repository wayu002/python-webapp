# coding:utf-8
# !/usr/bin/python

from www.log import Log

if __name__ == '__main__':
    l = Log(__name__)
    l.warning('test')
    l.error('test')
    l.info('test')
    l.debug('test')
