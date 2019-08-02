#!/usr/bin/env python3

import json
import re
import sys
import time

import requests


url = 'https://agile-scrubland-2714.herokuapp.com/passage/NKJV/{}/{}'

re = {
    'note_mark': re.compile(r'\[[a-z]+\]'),
    'sentence_end': re.compile(r'[.?!](”)?$'),
    'quote_start': re.compile(r'^“'),
    'em_dash': re.compile(r'—\s+'),
    'extra_space': re.compile(r'\s{2,}')
}


def extract(book, chapters):
    def extract_text(book, chapter):
        time.sleep(1.0)
        response = json.loads(requests.get(url.format(book, chapter)).text)
        lines = (verse['lines'] for verse in response['verses'])
        return [text['text'] for line in lines for text in line
                if text['text'] not in headings]

    headings = set()
    headings_filepath = ''.join(('headings/', book, '.json'))
    with open(headings_filepath, 'r') as headings_file:
        headings = set(json.loads(headings_file.read()))
    return (extract_text(book, chapter + 1) for chapter in range(chapters))


def transform(text):
    def remove_note_marks(line):
        return re['note_mark'].sub('', line)

    def is_sentence_end(line):
        return re['sentence_end'].search(line)

    def is_quote_start(line):
        return re['quote_start'].search(line)

    def to_lower(line):
        return ''.join((tuple(line)[0].lower(), *tuple(line)[1:]))

    def fix_spacing(line):
        return re['extra_space'].sub(' ', re['em_dash'].sub('—', line))

    for i, _ in enumerate(text):
        text[i] = remove_note_marks(text[i]).strip()
        if i == 0:
            continue
        if not is_sentence_end(text[i - 1]) and not is_quote_start(text[i]):
            text[i] = to_lower(text[i])
    return fix_spacing(' '.join(text))


def main():
    book, chapters = sys.argv[1], int(sys.argv[2])
    text = ' '.join(transform(text) for text in extract(book, chapters))
    output_filepath = ''.join(('output/', book, '.txt'))
    with open(output_filepath, 'w') as output_file:
        output_file.write(text)


if __name__ == '__main__':
    main()
