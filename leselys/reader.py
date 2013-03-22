# coding: utf-8
import datetime
import feedparser
import threading
import leselys
import copy

import requests
from urlparse import urlparse
from urlparse import urljoin

from leselys.helpers import u
from leselys.helpers import get_datetime
from leselys.helpers import get_dicttime
from leselys.feed_finder import FeedFinder

storage = leselys.core.storage

#########################################################################
# Set defaults settings
#########################################################################
if not storage.get_setting('acceptable_elements'):
    storage.set_setting('acceptable_elements', ["object", "embed", "iframe"])

# Acceptable elements are special tag that you can disable in entries rendering
acceptable_elements = storage.get_setting('acceptable_elements')

for element in acceptable_elements:
    feedparser._HTMLSanitizer.acceptable_elements.add(element)

#########################################################################
# Retriever object
#########################################################################


class Retriever(threading.Thread):
    """The Retriever object has to retrieve all feeds asynchronously and
    return it to the Reader when a new subscription arrives
    """

    def __init__(self, feed):
        threading.Thread.__init__(self)
        # self.feed is raw parsed feed
        self.feed = feed
        self.title = feed.feed['title']
        self.data = feed['entries']

    def run(self):
        # This feed comes from database
        feed = storage.get_feed_by_title(self.title)

        for entry in self.data:
            title = entry['title']
            link = entry['link']
            try:
                description = entry['content'][0]['value']
            except KeyError:
                description = entry['summary']

            if entry.get('updated_parsed'):
                last_update = get_dicttime(entry.updated_parsed)
            else:
                last_update = get_dicttime(datetime.datetime.now().timetuple())

            if entry.get('published_parsed', False):
                published = get_dicttime(entry.published_parsed)
            else:
                published = get_dicttime(datetime.datetime.now().timetuple())

            storage.add_story({
                'title': title,
                'link': link,
                'description': description,
                'published': published,
                'last_update': last_update,
                'feed_id': feed['_id'],
                'read': False})


class Refresher(threading.Thread):
    """The Refresher object have to retrieve all new entries asynchronously
    """

    def __init__(self, feed):
        threading.Thread.__init__(self)
        self.feed = feed
        self.feed_id = u(feed['_id'])

    def run(self):
        self.data = feedparser.parse(self.feed['url'])

        local_update = get_datetime(self.feed['last_update'])
        if self.data.feed.get('updated_parsed'):
            remote_update = get_datetime(self.data.feed.updated_parsed)
            remote_update_raw = get_dicttime(self.data.feed.updated_parsed)
        elif self.data.get('updated_parsed'):
            remote_update = get_datetime(self.data.updated_parsed)
            remote_update_raw = get_dicttime(self.data.updated_parsed)
        elif self.data.feed.get('published_parsed'):
            remote_update = get_datetime(self.data.feed.published_parsed)
            remote_update_raw = get_dicttime(self.data.feed.published_parsed)
        elif self.data.get('published_parsed'):
            remote_update = get_datetime(self.data.published_parsed)
            remote_update_raw = get_dicttime(self.data.published_parsed)
        else:
            remote_update = datetime.datetime.now()
            remote_update_raw = get_dicttime(remote_update.timetuple())

        if remote_update > local_update:
            print(':: %s is outdated' % self.feed['title'])
            readed = []
            for entry in storage.get_stories(self.feed['_id']):
                if entry['read']:
                    readed.append(entry['title'])
                storage.remove_story(entry['_id'])

            retriever = Retriever(self.data)
            retriever.start()
            retriever.join()

            for entry in readed:
                if storage.get_story_by_title(entry):
                    entry = storage.get_story_by_title(entry)
                    entry['read'] = True
                    storage.update_story(entry['_id'], copy.copy(entry))

            self.feed['last_update'] = remote_update_raw
            storage.update_feed(self.feed_id, self.feed)

#########################################################################
# Reader object
#########################################################################


class Reader(object):
    """The Reader object is the feeds manager, it handles all
    new feed, read/unread state and refresh feeds
    """

    def get_feed(self, url):
        """Given url might be point to http document or to actual feed. In case
        of http document, we try to find first feed auto discovery url.
        """
        stripped = url.strip()
        resp = requests.get(stripped)
        feed = feedparser.parse(resp.text)
        if feed.version != '':
            return feed

        urls = FeedFinder.parse(resp.text)
        feed_url = ''
        if len(urls) > 0:
            # Each url is tuple where href is first element.
            # NOTE : Sites might have several feeds available and we are just
            # naively picking first one found.
            feed_url = urls[0][0]
            if urlparse(feed_url)[1] == '':
                # We have empty 'netloc', meaning we have relative url
                feed_url = urljoin(stripped, feed_url)
        return feedparser.parse(feed_url)

    def add(self, url):
        feed = self.get_feed(url)

        # Bad feed
        if feed.version == '' or not feed.feed.get('title'):
            return {'success': False, 'output': 'Bad feed'}

        title = feed.feed['title']
        feed_id = storage.get_feed_by_title(title)
        if not feed_id:
            if feed.feed.get('updated_parsed'):
                feed_update = get_dicttime(feed.feed.updated_parsed)
            elif feed.get('updated_parsed'):
                feed_update = get_dicttime(feed.updated_parsed)
            elif feed.feed.get('published_parsed'):
                feed_update = get_dicttime(feed.feed.published_parsed)
            elif feed.get('published_parsed'):
                feed_update = get_dicttime(feed.published_parsed)
            else:
                feed_update = get_dicttime(datetime.datetime.now().timetuple())

            feed_id = storage.add_feed({'url': url,
                                        'title': title,
                                        'last_update': feed_update})
        else:
            return {'success': False, 'output': 'Feed already exists'}

        retriever = Retriever(feed)
        retriever.start()

        return {
            'success': True,
            'title': title,
            'url': url,
            'feed_id': feed_id,
            'output': 'Feed added',
            'counter': len(feed['entries'])}

    def delete(self, feed_id):
        if not storage.get_feed_by_id(feed_id):
            return {'success': False, "output": "Feed not found"}
        storage.remove_feed(feed_id)
        return {"success": True, "output": "Feed removed"}

    def get(self, feed_id, order_type='normal'):
        res = []
        for entry in storage.get_stories(feed_id):
            res.append({
                "title": entry['title'],
                "_id": entry['_id'],
                "read": entry['read'],
                'last_update': entry['last_update']})

        # Must implement different order_type

        # Readed
        readed = []
        for entry in res:
            if entry['read']:
                readed.append(entry)
        readed.sort(key=lambda r: get_datetime(r['last_update']), reverse=True)
        # Unread
        unreaded = []
        for entry in res:
            if not entry['read']:
                unreaded.append(entry)
        unreaded.sort(key=lambda r: get_datetime(r['last_update']),
                      reverse=True)
        return unreaded + readed

    def get_feeds(self):
        feeds = []
        for feed in storage.get_feeds():
            feeds.append({'title': feed['title'],
                          'id': feed['_id'],
                          'url': feed['url'],
                          'counter': self.get_unread(feed['_id'])
                          })
        return feeds

    def refresh(self, feed_id):
        feed = storage.get_feed_by_id(feed_id)
        refresher = Refresher(feed)
        refresher.start()
        refresher.join()
        feed['counter'] = self.get_unread(feed_id)
        return {'success': True, 'content': feed}

    def get_unread(self, feed_id):
        return len(storage.get_feed_unread(feed_id))

    def read(self, story_id):
        """
        Return story content, set it at readed state and give
        previous read state for counter
        """
        story = storage.get_story_by_id(story_id)
        if story['read']:
            return {'success': False,
                    'output': 'Story already readed',
                    'content': story}

        # Save read state before update it for javascript counter in UI
        story['read'] = True
        storage.update_story(story['_id'], copy.copy(story))
        return {'success': True, 'content': story}

    def unread(self, story_id):
        story = storage.get_story_by_id(story_id)
        if not story['read']:
            return {'success': False, 'output': 'Story already unreaded'}
        story['read'] = False
        storage.update_story(story['_id'], copy.copy(story))
        return {'success': True, 'content': story}
