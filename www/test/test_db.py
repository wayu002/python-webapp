# coding:utf-8
# !/usr/bin/python

import unittest
import time
from .. import db

class TestDB(unittest.TestCase):
    '''
    Test db module
    '''

    def setUp(self):
        db.create_engine('wangyu', 'taotao', 'python_blog')
        db.update('drop table if exists user')
        db.update('create table user (id int primary key, name text,' +
                  'email text, password text, last_modified real)')
        db.update('delete from user')

    def tearDown(self):
        db.update('delete from user')
        db.update('drop table if exists user')
        db.engine = None

    # test insert
    def test_insert(self):
        u1 = dict(id=2000, name='Bob', email='bob@test.org', password='bob',
                  last_modified=time.time())
        # row count should be 1
        self.assertEquals(db.insert('user',**u1), 1)
        # select from table
        u2 = db.select_one('select * from user where id=?', 2000)
        self.assertEquals(u2.name, u'Bob')
        # delete insert data
        # db.update('delete from user')

    # test select one
    def test_select_one(self):
        u1 = dict(id = 100, name = 'Alice', email = 'Alice@test.org',
                  password = 'test', last_modified = time.time())
        u2 = dict(id = 101, name = 'sarah', email = 'sarah@test.org',
                  password = 'test', last_modified = time.time())
        db.insert('user', **u1)
        db.insert('user', **u2)
        r1 = db.select_one('select * from user where id=?', 100)
        self.assertEquals(r1.name, u'Alice')
        r2 = db.select_one('select * from user where password=?', 'test')
        self.assertEquals(r2.name, u'Alice')

        # delete two insert data
        # db.update('delete from user')

    # test select int
    def test_select_int(self):
        u1 = dict(id=200, name='abc', email = 'abc@test.com', password = 'test',
                  last_modified = time.time())

        u2 = dict(id=201, name='def', email = 'abc@test.com', password = 'test',
                  last_modified = time.time())
        db.insert('user', **u1)
        db.insert('user', **u2)
        r1 = db.select_int('select count(*) from user where email = ?',
                           'abc@test.com')
        self.assertEquals(r1, 2)
        with self.assertRaises(db.MultiColumnsError):
            db.select_int('select id,name from user where email = ?',
                               'abc@test.com')

        # delete insert data
        # db.update('delete from user')

    # test select
    def test_select(self):
        u1 = dict(id=200, name='abc', email = 'abc@test.com', password = 'test',
                  last_modified = time.time())

        u2 = dict(id=201, name='def', email = 'abc@test.com', password = 'test',
                  last_modified = time.time())
        db.insert('user', **u1)
        db.insert('user', **u2)
        L = db.select('select * from user where id = ?', 200)
        self.assertEquals(L[0].email, u'abc@test.com')
        # delete inser data
        # db.update('delete from user')

if __name__ == '__main__':
    unittest.main()
