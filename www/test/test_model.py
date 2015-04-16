# coding:utf-8
# !/usr/bin/python

from .. import db
from ..model import User, Blog, Comment
import unittest

class TestModel(unittest.TestCase):
    '''
    unit test for model
    '''

    def setUp(self):
        db.create_engine('wangyu', 'taotao', 'python_blog')
        self._drop_table()

    def tearDown(self):
        self._drop_table()
        db.engine = None

    def _drop_table(self):
        db.update('drop table if exists users')
        db.update('drop table if exists blogs')
        db.update('drop table if exists comments')

    def test_user(self):
        # create user table
        db.update('create table users (id varchar(50) not null,' +
                  'email varchar(50) not null,'+
                  'password varchar(50) not null,'+
                  'admin bool not null,'+
                  'name varchar(50) not null,'+
                  'image varchar(500) not null,'+
                  'created_at real not null,'+
                  'key index_created_at (created_at),'+
                  'primary key (id))'+
                  'engine=innodb default charset=utf8')
        u = User(name='test', email='test@test.com', password='test',
                 image='about:blank')
        u.insert()
        r = db.select_one('select * from users where name=?', 'test')
        self.assertEquals(u.id, r.id)
        self.assertEquals(u.name, r.name)
        u1 = User.find_first('where name=?', 'test')
        self.assertEquals(u.id, u1.id)
        self.assertEquals(u.name, u1.name)
        self.assertEquals(u.image, u1.image)
        u1.delete()
        self.assertEquals(User.count_all(), 0)


    def test_blog(self):
        # create blogs table
        db.update('create table blogs (id varchar(50) not null, '+
                  'user_id varchar(50) not null, '+
                  'user_name varchar(50) not null, '+
                  'user_image varchar(500) not null, '+
                  'name varchar(50) not null, '+
                  'summary varchar(200) not null, '+
                  'content mediumtext not null, '+
                  'created_at real not null, '+
                  'key idx_created_at (created_at), '+
                  'primary key (id)) engine=innodb default charset=utf8')
        b = Blog(user_id=db.next_id(), user_name='test', name='title',
                 summary='some summary text', content='blablabla')
        b.insert()
        r = db.select_one('select * from blogs where user_name=?', 'test')
        self.assertEquals(b.id, r.id)
        self.assertEquals(b.user_id, r.user_id)
        self.assertEquals(b.content, r.content)
        b1 = Blog.find_first('where name=?', 'title')
        self.assertEquals(b.user_id, b1.user_id)
        self.assertEquals(b.id, b1.id)
        b1.delete()
        self.assertEquals(Blog.count_all(), 0)

    def test_comment(self):
        # create comments table
        db.update('create table comments (id varchar(50) not null, '+
                  'blog_id varchar(50) not null, '+
                  'user_id varchar(50) not null, '+
                  'user_name varchar(50) not null, '+
                  'user_image varchar(500) not null, '+
                  'content mediumtext not null, '+
                  'created_at real not null, '+
                  'key idx_created_at (created_at), '+
                  'primary key (id)) engine=innodb default charset=utf8')
        c = Comment(blog_id=db.next_id(), user_id=db.next_id(), user_name='test',
                    content='blablabla')
        c.insert()
        r = db.select_one('select * from comments where user_name=?', 'test')
        self.assertEquals(c.id, r.id)
        self.assertEquals(c.blog_id, r.blog_id)
        self.assertEquals(c.user_id, r.user_id)
        self.assertEquals(c.content, r.content)
        c1 = Comment.find_first('where user_name=?', 'test')
        self.assertEquals(c1.id, c.id)
        self.assertEquals(c1.blog_id, c.blog_id)
        self.assertEquals(c1.user_id, c.user_id)
        c1.delete()
        self.assertEquals(Comment.count_all(), 0)

if __name__ == '__main__':
    unittest.main()
