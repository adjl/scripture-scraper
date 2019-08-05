#!/usr/bin/env python3

import json
import os
import re
import sys
import time

from functools import reduce

import requests

from bs4 import BeautifulSoup


site_url = 'https://www.biblegateway.com/passage/?search={}+{}-{}&version={}'
api_url = 'https://agile-scrubland-2714.herokuapp.com/passage/{}/{}/{}'

re = {
    'quote_gap': re.compile(r'([“‘’”])\s([“‘’”])\s?([“‘’”])?'),
    'note_mark': re.compile(r'\[[a-z]+\]'),
    'sentence_end': re.compile(r'[.?!][’”]*$'),
    'quote_start': re.compile(r'^“'),
    'em_dash': re.compile(r'—\s+'),
    'extra_space': re.compile(r'\s{2,}')
}


def extract_headings(book, version, start, end):
    time.sleep(1.0)
    html = BeautifulSoup(
        requests.get(site_url.format(book, start, end, version)).text, 'html.parser')
    return (heading.get_text(strip=True) for heading in html.find_all('h3'))


def extract(book, version, chapters):
    def extract_text(book, version, chapter):
        time.sleep(1.0)
        response = json.loads(requests.get(api_url.format(version, book, chapter)).text)
        lines = (line for verse in response['verses'] for line in verse['lines'])
        return [line['text'] for line in lines if line['text'] not in headings]

    headings = set(json.loads(file_io('headings', version, book, 'r')))
    return (extract_text(book, version, chapter + 1) for chapter in range(chapters))


def transform(text):
    def clean_string(line):
        return re['quote_gap'].sub(r'\1\2\3', re['note_mark'].sub('', line))

    def is_sentence_end(line):
        return re['sentence_end'].search(line)

    def is_quote_start(line):
        return re['quote_start'].search(line)

    def to_lower(line):
        return ''.join((tuple(line)[0].lower(), *tuple(line)[1:]))

    def fix_spacing(line):
        return re['extra_space'].sub(' ', re['em_dash'].sub('—', line))

    text[0] = clean_string(text[0]).strip()
    for i in range(1, len(text)):
        text[i] = clean_string(text[i]).strip()
        if not is_sentence_end(text[i - 1]) and not is_quote_start(text[i]):
            text[i] = to_lower(text[i])
    return fix_spacing(' '.join(text))


def file_io(path, version, book, mode, output=None):
    path = ''.join((path, '/', version, '/'))
    if not os.path.isdir(path):
        os.mkdir(path, mode=0o775)
    path = ''.join((path, book, '.json' if path.startswith('headings') else '.txt'))
    with open(path, mode) as file:
        if mode == 'w':
            return file.write(output)
        return file.read()


def group(n):
    for i in range(1, n + 1, n // 3 + 1):
        yield (i, min(i + n // 3, n))


def main(book, version, chapters):
    headings = (
        extract_headings(book, version, start, end) for start, end in group(chapters))
    headings = reduce(lambda x, y: x + list(y), headings, [])
    file_io('headings', version, book, 'w',
            json.dumps(headings, ensure_ascii=False, indent=4))
    text = ' '.join(transform(text) for text in extract(book, version, chapters))
    file_io('output', version, book, 'w', text)


if __name__ == '__main__':
    book = input('Book to obtain (ensure correct spelling and capitalisation): ')
    version = input('Translation abbreviation (e.g., NKJV): ').upper()
    chapters = int(input('No. of chapters in {} (e.g., 21 in John): '.format(book)))
    try:
        main(book, version, chapters)
    except (KeyboardInterrupt, EOFError):
        sys.exit()
