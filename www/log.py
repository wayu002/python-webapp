# coding:utf-8
# !/usr/bin/python

import logging
import logging.config
import json
import pdb

class Log(object):

    def __init__(self, name):
        try:
            pdb.set_trace()
            with open('/work/python-webapp/conf/logging.conf','rt') as f:
                conf_setting = json.load(f)
                logging.config.dictConfig(conf_setting)
                self._logger = logging.getLogger(name)
        except BaseException, e:
            print 'init logging failed, err: %s' % e

    def info(self, message):
        self._logger.info(message)

    def debug(self, message):
        self._logger.debug(message)

    def error(self, message):
        self._logger.error(message)


    def warning(self, message):
        self._logger.warning(message)

    def critical(self, message):
        self._logger.critical(message)
