#!/usr/bin/env python3

import json
import sys
import time

from functools import reduce

import requests

from bs4 import BeautifulSoup


url = 'https://www.biblegateway.com/passage/?search={}+{}-{}&version=NKJV'


def extract_headings(book, start, end):
    time.sleep(1.0)
    html = BeautifulSoup(requests.get(url.format(book, start, end)).text, 'html.parser')
    return (heading.get_text(strip=True) for heading in html.find_all('h3'))


def pairwise(lst):
    for i in range(0, len(lst), 2):
        yield tuple(lst[i: i + 2])


def main():
    book, chapter_groups = sys.argv[1], sys.argv[2:]
    headings = (extract_headings(book, start, end)
                for start, end in pairwise(chapter_groups))
    headings = reduce(lambda x, y: tuple(list(x) + list(y)), headings)
    headings_filepath = ''.join(('headings/', book, '.json'))
    with open(headings_filepath, 'w') as headings_file:
        headings_file.write(json.dumps(headings, ensure_ascii=False, indent=4))


if __name__ == '__main__':
    main()
