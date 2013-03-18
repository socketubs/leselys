# -*- coding: utf-8 -*-
from sofart import Database


class Storage(object):
    def __init__(self, **kwargs):
        self.path = kwargs['path']
        self.mode = kwargs['mode']
        self.db = Database(self.path, self.mode)

    def get_users(self):
        res = []
        for user in self.db.users.find():
            res.append(user['username'])
        return res

    def add_user(self, username, password):
        return str(self.db.users.save({'username': username,
                                       'password': password}))

    def remove_user(self, username):
        user = self.db.users.find_one({'username': username})
        if user:
            self.db.users.remove(user['_id'])

    def get_password(self, username):
        user = self.db.users.find_one({'username': username})
        if user:
            return user['password']
        return None

    def set_password(self, username, password):
        return self.db.users.save({'username': username, 'password': password})

    def set_setting(self, key, value):
        self.db.settings.save({key: value})

    def get_setting(self, key):
        if not self.db.settings.find_one():
            return False
        if not self.db.settings.find_one().get(key, False):
            return False
        else:
            return self.db.settings.find_one()[key]

    def get_settings(self):
        settings = {}
        for setting in self.db.settings.find():
            settings.update(setting)
        del settings['_id']
        return settings

    def add_feed(self, content):
        return self.db.feeds.save(content)

    def remove_feed(self, _id):
        self.db.feeds.remove(_id)
        for entry in self.db.stories.find({'feed_id': _id}):
            self.db.stories.remove(entry['_id'])

    def get_feed_by_id(self, _id):
        return self.db.feeds.find_one({'_id': _id})

    def get_feed_by_title(self, title):
        return self.db.feeds.find_one({'title': title})

    def update_feed(self, _id, content):
        self.db.feeds.remove(_id)
        return self.db.feeds.save(content)

    def get_feeds(self):
        res = []
        for feed in self.db.feeds.find():
            res.append(feed)
        return res

    def add_story(self, content):
        return self.db.stories.save(content)

    def remove_story(self, _id):
        self.db.stories.remove(_id)

    def update_story(self, _id, content):
        self.db.stories.remove(_id)
        return self.db.stories.save(content)

    def get_story_by_id(self, _id):
        return self.db.stories.find_one({'_id': _id})

    def get_story_by_title(self, title):
        return self.db.stories.find_one({'title': title})

    def get_feed_unread(self, feed_id):
        res = []
        for feed in self.db.stories.find({'feed_id': feed_id, 'read': False}):
            res.append(feed)
        return res

    def get_stories(self, feed_id):
        res = []
        for story in self.db.stories.find({'feed_id': feed_id}):
            res.append(story)
        return res
