# coding:utf-8
# !/usr/bin/python

from datetime import datetime
from logging.handlers import RotatingFileHandler
import os

def time_rotate_handler(filename, mode='a', maxBytes=0,backupCount=0, encoding=None, delay=0):
    dt = datetime.today()
    root_path = os.path.join(os.getcwd(), 'log')
    filename =  os.path.join(root_path, dt.strftime('%Y-%m-%d') + '-' + filename)
    return RotatingFileHandler(filename, mode, maxBytes, backupCount, encoding, delay)
