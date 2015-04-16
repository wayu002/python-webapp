# coding:utf-8
# !/usr/bin/python

from datetime import datetime
from logging.handlers import RotatingFileHandler

def time_rotate_handler(filename, mode='a', maxBytes=0,backupCount=0,
                        encoding=None, delay=0):
    dt = today()
    filename = dt.strftime(%Y-%m-%d)
    return RotatingFileHandler(filename, mode, maxBytes, backupCount,
                               encoding, delay)

