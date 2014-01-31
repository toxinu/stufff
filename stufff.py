#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import pickle
import requests
import requests.utils
from docopt import docopt
from urlparse import urljoin

doc = """Stufff

Usage:
  stufff --box-list
  stufff --thing-list <box-id>
"""

password = "admin"
cookie_path = "./cookie"
stufff_url = "http://localhost:5000"


def load_cookies():
    try:
        with open(cookie_path, 'rb') as f:
            return pickle.load(f)
    except IndexError:
        return None


def save_cookies(requests_cookiejar):
    with open(cookie_path, 'wb') as f:
        pickle.dump(requests_cookiejar, f)

if __name__ == "__main__":
    args = docopt(doc, version="0.1")
    cookies = None
    if os.path.exists(cookie_path):
        cookies = load_cookies()

    # Check if logged in
    if cookies:
        r = requests.get(urljoin(stufff_url, '/box/list.json'), cookies=cookies)
        if r.status_code == 401:
            cookies = None
    if cookies is None:
        r = requests.post(urljoin(stufff_url, '/login'), data={'password': password})
        if r.status_code == 200:
            print(':: Authenticated successfully')
            save_cookies(r.cookies)
            cookies = r.cookies
        else:
            print('!! Failed to authenticate')
            sys.exit(1)

    if args.get('--box-list'):
        r = requests.get(urljoin(stufff_url, '/box/list.json'), cookies=cookies)
        boxes = r.json().get('boxes')
        for box in boxes:
            print('%s %s' % (box['id'], box['name']))
        sys.exit(0)

    if args.get('--thing-list'):
        r = requests.get(
            urljoin(stufff_url, '/box/%s.json' % args.get('<box-id>')), cookies=cookies)
        things = r.json().get('things')
        for thing in things:
            print('%s (done:%s) %s (%s)' % (
                thing['id'], thing['done'], thing['name'], thing['added_date']))
