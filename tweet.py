#!/usr/local/bin/python2.7

import meetup.api
import pytz
from pytz import timezone
from datetime import datetime, timedelta
from twython import Twython
from config import consumer_key, consumer_secret, access_token, access_token_secret, meetup_key

twitter = Twython(consumer_key, consumer_secret, access_token, access_token_secret)

def get_latest_event():
    client = meetup.api.Client(meetup_key)
    group = client.GetGroup({"urlname": "VTCode"})

    event_info = group.next_event
    event_utc = clean_time(event_info["time"])

    return event_info["name"], event_utc


def clean_time(event_utc):
    string_utc = str(event_utc)
    stripped_utc = string_utc[0:10]

    utc = pytz.utc
    fmt = '%m-%d-%Y'
    utc_dt = utc.localize(datetime.utcfromtimestamp(float(stripped_utc)))

    return utc_dt.strftime(fmt)


def check_for_dupes(proposed_tweet):
    return proposed_tweet in [tweet["text"] for tweet in twitter.get_user_timeline()]


def compose_tweet(event_info, event_utc):
    return "Next up: " + event_info + ": " + event_utc


def main():
    event_name, event_utc = get_latest_event()
    proposed_tweet = compose_tweet(event_name, event_utc)

    if not check_for_dupes(proposed_tweet):
        twitter.update_status(status=proposed_tweet)

if __name__ == "__main__":
    main()
