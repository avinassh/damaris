import time
import shutil
import tempfile
import random

import requests
from pytg import Telegram
import praw
from peewee import SqliteDatabase, Model, CharField

from settings import (REDDIT_APP_KEY, REDDIT_APP_SECRET, REDDIT_USER_AGENT,
                      RECEPIENT, TG_CLI, TG_PUBKEY, CAPTIONS)


tg = Telegram(telegram=TG_CLI, pubkey_file=TG_PUBKEY)
reddit_client = praw.Reddit(user_agent=REDDIT_USER_AGENT,
                            client_id=REDDIT_APP_KEY,
                            client_secret=REDDIT_APP_SECRET)
db = SqliteDatabase('damaris.db')


class FetchedThreads(Model):
    thread_id = CharField(unique=True)
    url = CharField()

    class Meta:
        database = db


def initialize_db():
    db.connect()
    # Create table only if it doesn't exist
    db.create_tables([FetchedThreads, ], safe=True)


def deinit():
    db.close()


def mark_thread_posted(thread_id, url):
    thread = {
        'thread_id': thread_id,
        'url': url
    }
    FetchedThreads.create(**thread)


def get_random_caption():
    return random.choice(CAPTIONS)


def is_thread_posted(thread_id):
    return FetchedThreads.select().where(FetchedThreads.thread_id == thread_id)


def post_image_to_tg(recepient, image_url, caption):
    # telegram restricts max characters of `caption` to be 200
    sender = tg.sender
    with tempfile.NamedTemporaryFile(suffix='.jpg') as fp:
        response = requests.get(image_url, stream=True)
        shutil.copyfileobj(response.raw, fp)
        sender.send_photo(recepient, fp.name, caption[:200])


def post_stuff_from_reddit(subreddit_name='cats'):
    for submission in reddit_client.subreddit('cats').hot():
        if submission.is_self:
            continue
        try:
            thread_id = submission.id
            image_url = submission.preview['images'][0]['source']['url']
        except (KeyError, IndexError):
            continue
        if is_thread_posted(thread_id=thread_id):
            continue
        post_image_to_tg(recepient=RECEPIENT,
                         image_url=image_url, caption=get_random_caption())
        mark_thread_posted(thread_id=thread_id, url=image_url)
        break


def main():
    initialize_db()
    time.sleep(60 * random.randint(1, 120))
    post_stuff_from_reddit()
    deinit()


if __name__ == '__main__':
    main()
