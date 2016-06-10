#!/usr/bin/env python2.7

from collections import namedtuple
from datetime import datetime
import sys

import meetup.api
from requests.exceptions import ReadTimeout
from pyshorteners import Shortener
import pytz
from twython import Twython

from _config import twitter_key, twitter_secret, twitter_token, \
        twitter_token_secret, meetup_key, meetup_groups


twitter = Twython(twitter_key, twitter_secret,
                  twitter_token, twitter_token_secret)
meetup_client = meetup.api.Client(meetup_key)
Event = namedtuple('Event', 'group_name event_name date link')


def get_latest_event(group):
    group_info = meetup_client.GetGroup({"urlname": group})
    try:
        event_info = group_info.next_event
    except AttributeError:
        # no upcoming meetups
        return None

    group_name = group_info.name
    link = make_link(group, event_info['id'])
    event_name = event_info['name']
    date = clean_time(event_info['time'])

    return Event(group_name, event_name, date, link)


def make_link(group_name, event_id, shorten=True):
    url = "https://meetup.com/{group_name}/events/{event_id}".format(
        group_name=group_name,
        event_id=event_id)
    if shorten:
        shortener = Shortener('Tinyurl')
        try:
            url =  shortener.short(url)
        except ReadTimeout:
            pass
    return url


def clean_time(event_utc):
    string_utc = str(event_utc)
    stripped_utc = string_utc[0:10]

    utc = pytz.utc
    fmt = '%m/%d at %I:%M%p'
    utc_dt = utc.localize(datetime.utcfromtimestamp(float(stripped_utc)))

    time =  utc_dt.strftime(fmt).lower()
    if time[0] == "0":
        time = time[1:]
    if time[-7] == "0":
        time = time[:-7] + time[-6:]
    if ":00" in time:
        time = time[:-5] + time[-2:]

    return time


def is_dupe(tweet):
    return tweet in [_tweet["text"] for _tweet in twitter.get_user_timeline()]


def compose_tweet(event):
    "compose the tweet using whatever info will fit"
    if tweet_length(event) <= 136:

        tweet = "{group_name}: {event_name} {date} {link}".format(
                        group_name=event.group_name,
                        event_name=event.event_name,
                        date=event.date,
                        link=event.link)

    elif tweet_length(event, start_at[1]) <= 138:

        tweet = "{event_name} {date} {link}".format(
                        event_name=event.event_name[:96],
                        date=event.date,
                        link=event.link)

    else:

        tweet = "{event_name} {date} {link}".format(
                        event_name=event.event_name,
                        date=event.date,
                        link=event.link)

    return tweet


def tweet_length(event, start_at=0):
    return sum(
        [len(attrib) for attrib in event.__dict__.values()[start_at:]]
    )


def main():
    for group in meetup_groups:
        event = get_latest_event(group)
        if not event: continue

        print("Got an event! {event_name}".format(event_name=event.event_name))

        tweet = compose_tweet(event)

        if is_dupe(tweet):
            print("Already tweeted that one!")
            continue
        print("Tweeting: '" + tweet + "'")
        twitter.update_status(status=tweet)


if __name__ == "__main__":
    main()
