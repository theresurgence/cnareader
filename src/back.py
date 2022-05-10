import feedparser
import textwrap
import requests
import os
import time
from bs4 import BeautifulSoup

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
    except Exception: # filepath non-existent
        return -1

def write_to_file(filepath, content):
    with open(filepath, 'w') as outputfile:
        outputfile.write(content)

def get_request(url):
    try: 
        res = requests.get(url,headers=BROWSER_HEADER)
        res.raise_for_status()
    except:
        # TODO: Notification/ Page that unable to connect
        exit()
    return res.text

def parse_rss(rss_raw):
    rss_data = feedparser.parse(rss_raw)
    entries = rss_data['entries']
    headlines=[]
    headline_urls = []

    for entry in entries:
        # consider enumerate ....
        # TODO: truncate title
        # Scrollable box of titles
        headlines.append(entry['title'])
        headline_urls.append(entry['link'])
    return (headlines, headline_urls)



def parse_article(article_html):
    soup = BeautifulSoup(article_html, 'html.parser')

    title_select = soup.select('.h1--page-title')
    body_paras_select = soup.select('div .text-long p')

    return (title_select, body_paras_select)

def wrap_article(title_select, body_paras_select, text_width):
    title_text = title_select[0].text.strip()
    title = textwrap.fill(title_text, text_width)

    body_paras= []
    for para in body_paras_select:
        wrapped = textwrap.fill(para.text, text_width)
        body_paras.append(wrapped)

    lines = []
    for para in body_paras:
        lines.append(para.split('\n'))

    return title, lines
