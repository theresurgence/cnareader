import os
import textwrap
import time

import feedparser
import requests
from bs4 import BeautifulSoup

import src.front

BROWSER_HEADER = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:91.0) Gecko/20100101 Firefox/91.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1'
}

TEXT_WRAP_WIDTH = 80


def file_age_hours(filepath):
    try:
        age_seconds = time.time() - os.path.getmtime(filepath)
        return age_seconds / 3600
    except Exception:  # filepath non-existent
        return -1


def write_to_file(filepath, content):
    with open(filepath, 'w') as outfile:
        outfile.write(content)


def get_request(url, screen):
    try:
        res = requests.get(url, headers=BROWSER_HEADER)
        res.raise_for_status()
    except requests.exceptions.ConnectionError:
        src.front.print_network_error(screen)
        return -1

    return res.text


def parse_rss(rss_raw):
    rss_data = feedparser.parse(rss_raw)
    entries = rss_data['entries']
    headlines = []
    headline_urls = []

    for entry in entries:
        # Scrollable box of titles
        headlines.append(entry['title'])
        headline_urls.append(entry['link'])
    return headlines, headline_urls


def parse_article(article_html):
    soup = BeautifulSoup(article_html, 'html.parser')

    title_select = soup.select('.h1--page-title')
    body_paras_select = soup.select('div .text-long p')

    return title_select, body_paras_select


def wrap_article(title_select, body_paras_select, text_width):
    title_text = title_select[0].text.strip()
    title_lines = textwrap.wrap(title_text, text_width)

    # TODO: wrap text evenly for title
    match (len(title_lines)):
        case 1:
            art_width = text_width
        case 2:
            art_width = text_width // 1.1
        case 3:
            art_width = text_width // 1.3
        case _:
            art_width = text_width // 1.5

    title_lines_even = textwrap.wrap(title_text, art_width)

    body_paras = []
    for para in body_paras_select:
        wrapped = textwrap.fill(para.text, text_width)
        body_paras.append(wrapped)

    body_lines = []
    for para in body_paras:
        body_lines.append(para.split('\n'))

    return title_lines_even, body_lines
