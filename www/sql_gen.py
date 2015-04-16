# coding:utf-8
# !/usr/bin/python

from www.model import User, Blog, Comment
import os
import sys
import logging
#import subprocess

class SqlGenerator(object):
    '''
    script for generate sql file according to the model
    '''

    def __init__(self):
        self._file_name = 'python_blog.sql'
        self._full_path = os.path.join(os.getcwd(), self._file_name)

    def generate(self, *args):
        try:
            f = os.open(self._full_path, os.O_RDWR|os.O_CREAT|os.O_TRUNC)
            for m in args:
                if not hasattr(m, '__sql__'):
                    continue
                os.write(f, m.__sql__)
                os.write(f, '\n\n')
            os.close(f)
            f = None
            #execs = ['mysql', '-u wangyu --password=taotao python_blog < ' +
             #        self._full_path]
            #logging.warning(execs)
            #p = subprocess.Popen(execs)
            #subprocess.call(['mysql', '-u wangyu --password=taotao python_blog < ' + self._full_path])
            #std_out, std_err = p.communicate()
            #logging.warning('import mysql from sql file, output: %s, error: %s'
             #               % (std_out, std_err))
        except BaseException, e:
            logging.error(e)
        finally:
            if f is not None:
                os.close(f)

if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN)
    L = [User, Blog, Comment]
    sgen = SqlGenerator()
    sgen.generate(*L)

