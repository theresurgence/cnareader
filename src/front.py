import curses
from enum import Enum

from src.back import file_age_hours, write_to_file, get_request, parse_rss, parse_article, wrap_article
import textwrap
import os

import pdb # TODO remove

# TODO: implement cache functionality in temporary files
LATEST_NEWS_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml'
ASIA_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511'
BUSINESS_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936'
SINGAPORE_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416'
SPORT_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10296'
WORLD_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6311'

RSS_URLS = [ LATEST_NEWS_URL, BUSINESS_URL, WORLD_URL, ASIA_URL, SINGAPORE_URL, SPORT_URL ]
RSS_CACHE_PATHS = r'/tmp/latest_news.xml /tmp/business.xml /tmp/world.xml /tmp/asia.xml /tmp/singapore.xml /tmp/sport.xml'.split(' ')


# MIN_HEIGHT = 25
# MIN_WIDTH = 100
MIN_HEIGHT = 0
MIN_WIDTH = 0

TITLE = [
r"  ______  __    __  ______       _______  ________  ______  _______  ________ _______  ",
r" /      \|  \  |  \/      \     |       \|        \/      \|       \|        \       \ ",
r"|  ▓▓▓▓▓▓\ ▓▓\ | ▓▓  ▓▓▓▓▓▓\    | ▓▓▓▓▓▓▓\ ▓▓▓▓▓▓▓▓  ▓▓▓▓▓▓\ ▓▓▓▓▓▓▓\ ▓▓▓▓▓▓▓▓ ▓▓▓▓▓▓▓\ ",
r"| ▓▓   \▓▓ ▓▓▓\| ▓▓ ▓▓__| ▓▓    | ▓▓__| ▓▓ ▓▓__   | ▓▓__| ▓▓ ▓▓  | ▓▓ ▓▓__   | ▓▓__| ▓▓",
r"| ▓▓     | ▓▓▓▓\ ▓▓ ▓▓    ▓▓    | ▓▓    ▓▓ ▓▓  \  | ▓▓    ▓▓ ▓▓  | ▓▓ ▓▓  \  | ▓▓    ▓▓",
r"| ▓▓   __| ▓▓\▓▓ ▓▓ ▓▓▓▓▓▓▓▓    | ▓▓▓▓▓▓▓\ ▓▓▓▓▓  | ▓▓▓▓▓▓▓▓ ▓▓  | ▓▓ ▓▓▓▓▓  | ▓▓▓▓▓▓▓\ ",
r"| ▓▓__/  \ ▓▓ \▓▓▓▓ ▓▓  | ▓▓    | ▓▓  | ▓▓ ▓▓_____| ▓▓  | ▓▓ ▓▓__/ ▓▓ ▓▓_____| ▓▓  | ▓▓",
r" \▓▓    ▓▓ ▓▓  \▓▓▓ ▓▓  | ▓▓    | ▓▓  | ▓▓ ▓▓     \ ▓▓  | ▓▓ ▓▓    ▓▓ ▓▓     \ ▓▓  | ▓▓",
r"  \▓▓▓▓▓▓ \▓▓   \▓▓\▓▓   \▓▓     \▓▓   \▓▓\▓▓▓▓▓▓▓▓\▓▓   \▓▓\▓▓▓▓▓▓▓ \▓▓▓▓▓▓▓▓\▓▓   \▓▓"
]

stdscr = None
# ks_parser = None


class Page(Enum):
    MAIN = 0
    HEADLINE = 1
    ARTICLE = 2

page = Page.MAIN

def init_front(stdscr_main):
    global stdscr

    stdscr  = stdscr_main
    ks_parser = KeyStrokeParser(stdscr)

    curses.curs_set(0)
    # stdscr.keypad(1) # TODO Need this or not
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    print_main_menu(stdscr, ks_parser)

def get_str_max_len(items):
    max_len = 0
    for i in items:
        if len(i) > max_len:
            max_len = len(i)
    return max_len

def check_term_size(stdscr, is_error):
    while True:
        h, w = stdscr.getmaxyx()
        
        if h >= MIN_HEIGHT and w >= MIN_WIDTH and not is_error:
            break

        is_error = False
        stdscr.erase()
        h, w = stdscr.getmaxyx()

        text = 'Terminal Window Too Small!'
        stdscr.addstr(h // 2, w // 2 - len(text) // 2, text, curses.A_BOLD | curses.A_BLINK)

        stdscr.addstr(0, 0, " " * (w-1), curses.color_pair(3)) # top bar
        stdscr.addstr(h-1, 0, " " * (w-1), curses.color_pair(3)) # bottom bar

        for i in range(h):
            stdscr.addstr(i, 0, "  ", curses.color_pair(3)) # left bar
            stdscr.addstr(i, w-3, "  ", curses.color_pair(3)) # right bar
        stdscr.refresh()

        # Wait for changes in terminal size
        key = get_keystroke(stdscr)
        if key == curses.KEY_RESIZE:
            continue
        if key == ord('q'):
            exit(0)

def get_keystroke(stdscr):
    try:
        return stdscr.getch()
    except Exception: 
        return None

## Different Mode... can go back....
class KeyStrokeParser:
    def __init__(self, stdscr):
        self.stdscr = stdscr

    def resize(self, key):
        if key == curses.KEY_RESIZE:
            check_term_size(self.stdscr, is_error=False)

    def quit(self, key):
        if key == ord('q'):
            exit()

    def main_menu(self, key, select_pos, num_options):
        self.resize(key)
        self.quit(key)

        if key == curses.KEY_DOWN and select_pos < num_options - 1:
            return select_pos + 1

        if key == curses.KEY_UP and select_pos > 0:
            return select_pos - 1

        if key == curses.KEY_RIGHT:
            print_headlines(stdscr, select_pos, self)

        return select_pos

    def headlines(self, key, select_pos, num_options, url):
        global page
        self.resize(key)
        self.quit(key)

        if key == curses.KEY_DOWN and select_pos < num_options - 1:
            return select_pos + 1

        if key == curses.KEY_UP and select_pos > 0:
            return select_pos - 1

        if key == curses.KEY_LEFT:
            page = Page.MAIN

        elif key == curses.KEY_RIGHT: 
            print_article(self.stdscr, url, self)

        return select_pos

    def article(self, key, select_pos):
        global page
        self.resize(key)
        self.quit(key)

        # TODO max scrollabale
        if key == curses.KEY_DOWN and select_pos < 100:
            select_pos += 1
        elif key == curses.KEY_UP and select_pos > 0:
            select_pos -= 1
        elif key == curses.KEY_LEFT:
            page = Page.HEADLINE

        return select_pos

    # TODO: how avoid recursion
    def check_term(self, key):
        pass


def print_bottom_bar(stdscr, h, w):
    text_list = ['q Quit', '↑ Up', '↓ Down', '← Back', '→ Enter' ]
    text_len = len(''.join(text_list))
    num_spaces = (w - text_len) // 6 - 1

    stdscr.addstr(h-1, 0 , " " * num_spaces ) # Initial Spaces
    y_pos = num_spaces
    for text in text_list:
        stdscr.addstr(h-1, y_pos, text, curses.color_pair(2) | curses.A_BOLD)
        stdscr.addstr(h-1, y_pos + len(text), " " * num_spaces )
        y_pos += len(text) + num_spaces

# TODO print article date....
def print_article(stdscr, url, ks_parser):
    global page
    page = Page.ARTICLE 
    select_pos = 0

    article_html = get_request(url)
    title_sel, body_sel= parse_article(article_html)
 
    title_pad = curses.newpad(1,200)
    body_pad = curses.newpad(400,200)
    stdscr.refresh()

    max_scroll_height = 300

    while page == Page.ARTICLE:
        try:
            h, w = stdscr.getmaxyx()
            text_w = w // 1.15 # TODO: variable depending on window size
            text_h = h // 1.3

            article_title, article_body_paras =  wrap_article(title_sel, body_sel, text_w) 

            stdscr.erase()
            stdscr.refresh()
            text_top_y = int(h//2 - text_h//2)-1
            text_top_x = int(w//2 - text_w//2)-1
            text_bot_y = int(h//2 + text_h//2)+1 
            text_bot_x = int(w//2 + text_w//2)+1

            title_x = int(text_w//2 - len(article_title)//2)

            body_pad.erase()
            title_pad.erase()

            title_pad.addstr(0, title_x, article_title, curses.A_BOLD | curses.A_UNDERLINE)
            title_pad.refresh(0, 0, 
                    text_top_y, text_top_x,
                    text_top_y, text_bot_x)

            line_num = 0
            for para in article_body_paras:
                for line in para:
                    body_pad.addstr(line_num, 0, line)
                    line_num += 1
                line_num += 1

            # max_scroll_height = line_num - (text_bot_x-text_top_x) TODO
            
            body_pad.refresh(select_pos,0, 
                    text_top_y+2, text_top_x,
                    text_bot_y, text_bot_x)

            print_bottom_bar(stdscr, h, w)
            stdscr.refresh()
        except Exception:
            check_term_size(stdscr, True)

        key = get_keystroke(stdscr)
        select_pos = ks_parser.article(key, select_pos) 


#TODO print title "Category eg. Business, Latest News etc"
# Maybe have an 'r' for refrsh.
# take note of last time of refresh.... get from date/time of xml
def print_headlines(stdscr, option, ks_parser): 
    global page
    page = Page.HEADLINE 
    select_pos = 0

    rss_cache_path = RSS_CACHE_PATHS[option]
    rss_cache_age = file_age_hours(rss_cache_path) 

    # cache older than 1 hour or does not exist
    if rss_cache_age > 1 or rss_cache_age == -1:
        rss_raw = get_request(RSS_URLS[option])
        write_to_file(rss_cache_path, rss_raw)
        headlines, headline_urls = parse_rss(rss_raw)
    else:
        headlines, headline_urls = parse_rss(rss_cache_path)

    while page == Page.HEADLINE:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        try:
            stdscr.addstr(0,0, f'h: {h} w: {w} pos:{select_pos}') 
            max_len_options = int(w // 1.2)
            #max_len_options = get_str_max_len(headlines)

            for idx, row in enumerate(headlines):
                x = (w // 2) - (max_len_options// 2) 
                y = h // 2 - len(headlines) // 2  + idx

                # TODO: Scrolling textbox, double spacing
                if idx + 1 < 10:
                    row = f'{idx+1}.  ' + row
                else:
                    row = f'{idx+1}. ' + row

                row = textwrap.shorten(row, max_len_options , placeholder="...")

                if idx == select_pos:
                    stdscr.addstr(y,x, row, curses.A_REVERSE)
                else:
                    stdscr.addstr(y,x, row)

            print_bottom_bar(stdscr, h, w)
            stdscr.refresh()

        except Exception:
            check_term_size(stdscr, True)

        key = get_keystroke(stdscr)
        select_pos = ks_parser.headlines(key, select_pos, len(headlines), headline_urls[select_pos]) 


  
def print_main_menu(stdscr, ks_parser):

    options = ['1. Latest News', '2. Business', '3. World', '4. Asia', '5. Singapore', '6. Sport']
    select_pos = 0
    key = None

    while True:

        stdscr.erase()
        h, w = stdscr.getmaxyx()
        stdscr.addstr(0,0, f'h: {h} w: {w} pid: {os.getpid()}') 

        try:
            # Print Title
            max_len_title = get_str_max_len(TITLE)
            for index, text in enumerate(TITLE):
                stdscr.addstr(1 + index, w // 2 - max_len_title//2, text)

            max_len_options = get_str_max_len(options)
            for idx, row in enumerate(options):
                x = (w // 2) - (max_len_options// 2) 
                # y = h // 2 + idx
                y = h // 2 - 1 + idx*2
                if select_pos == idx:
                    stdscr.addstr(y, x, row, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, x, row )

            # Print Bottom Bar
            print_bottom_bar(stdscr,h,w)
            stdscr.refresh()
        except Exception:
            check_term_size(stdscr, True)

        key = get_keystroke(stdscr)
        # pdb.set_trace()
        select_pos = ks_parser.main_menu(key, select_pos, len(options))




