# coding:utf-8
# !/usr/bin/python

import unittest
import time
from .. import orm
from .. import db

class TestORM(unittest.TestCase):
    '''
    unit test  for orm module
    '''

    def setUp(self):
        db.create_engine('wangyu', 'taotao', 'python_blog')
        db.update('drop table if exists user')
        db.update('create table user (id int primary key, name text,' +
                  'email text, password text, last_modified real)')

    def tearDown(self):
        db.update('drop table if exists user')
        db.engine = None

    def test_user(self):
        u = orm.User(id=111, name='test', email='test@test.com')
        u.insert()
        r = db.select_one('select * from user where id=?', 111)
        self.assertEquals(r.email, u.email)
        self.assertEquals(r.password, u.password)

if __name__ == '__main__':
    unittest.main()

