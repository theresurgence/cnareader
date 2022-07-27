import curses
import os
import sys
import tempfile
import textwrap
import time

from src.back import file_age_hours, write_to_file, get_request, parse_rss, parse_article, wrap_article
# TODO: implement cache functionality in temporary files
from src.classes.keystroke import KeyStrokeParser
from src.classes.page import Page

LATEST_NEWS_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml'
ASIA_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511'
BUSINESS_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6936'
SINGAPORE_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10416'
SPORT_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=10296'
WORLD_URL = 'https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6311'

RSS_URLS = [LATEST_NEWS_URL, BUSINESS_URL, WORLD_URL, ASIA_URL, SINGAPORE_URL, SPORT_URL]
RSS_CACHE_PATHS = r'latest_news.xml business.xml world.xml asia.xml singapore.xml ' \
                  r'sport.xml'.split(' ')

MIN_HEIGHT = 25
MIN_WIDTH = 100
text_w_ratio = 1.15
text_h_ratio = 1.3

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

TITLE2 = [
    r"██████╗███╗   ██╗ █████╗     ██████╗ ███████╗ █████╗ ██████╗ ███████╗██████╗",
    r"██╔════╝████╗  ██║██╔══██╗    ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗",
    r"██║     ██╔██╗ ██║███████║    ██████╔╝█████╗  ███████║██║  ██║█████╗  ██████╔╝",
    r"██║     ██║╚██╗██║██╔══██║    ██╔══██╗██╔══╝  ██╔══██║██║  ██║██╔══╝  ██╔══██╗",
    r"╚██████╗██║ ╚████║██║  ██║    ██║  ██║███████╗██║  ██║██████╔╝███████╗██║  ██║",
    r"╚═════╝╚═╝  ╚═══╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝"

]

page = Page.MAIN


def set_page(new_page):
    global page
    if new_page == Page.MAIN:
        page = Page.MAIN
    elif new_page == Page.HEADLINE:
        page = Page.HEADLINE
    elif new_page == Page.ARTICLE:
        page = Page.ARTICLE
    else:
        exit(0)


def init_front(screen):
    # Maximize cmd window, set optimal size
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 3)
        curses.resize_term(30, 119)

    ks_parser = KeyStrokeParser(screen)
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_RED)
    print_main_menu(screen, ks_parser)


def get_str_max_len(items):
    max_len = 0
    for i in items:
        if len(i) > max_len:
            max_len = len(i)
    return max_len


def get_rss_cache_path(option):
    temp_dir = tempfile.gettempdir()
    return os.path.join(temp_dir, RSS_CACHE_PATHS[option])


def get_rss_last_refresh_time(path):
    mod_time = os.path.getmtime(path)
    time_list = time.ctime(mod_time).split()
    return ' '.join(time_list[:-1])


def print_network_error(screen):
    screen.erase()
    h, w = screen.getmaxyx()

    text = 'Network Connection Error!'
    screen.addstr(h // 2, w // 2 - len(text) // 2, text, curses.A_BOLD)
    screen.addstr(0, 0, " " * (w - 1), curses.color_pair(4))  # top bar
    screen.addstr(h - 1, 0, " " * (w - 1), curses.color_pair(4))  # bottom bar

    for i in range(h):
        screen.addstr(i, 0, "  ", curses.color_pair(4))  # left bar
        screen.addstr(i, w - 3, "  ", curses.color_pair(4))  # right bar
    screen.refresh()
    curses.napms(1000)
    screen.erase()


def check_term_size(screen, is_error, ks_parser):
    while True:
        screen.erase()
        screen.refresh()

        h, w = screen.getmaxyx()

        if h >= MIN_HEIGHT and w >= MIN_WIDTH and not is_error:
            break

        is_error = False
        screen.erase()
        h, w = screen.getmaxyx()

        text = 'Terminal Window Too Small!'
        screen.addstr(h // 2, w // 2 - len(text) // 2, text, curses.A_BOLD | curses.A_BLINK)
        screen.addstr(0, 0, " " * (w - 1), curses.color_pair(3))  # top bar
        screen.addstr(h - 1, 0, " " * (w - 1), curses.color_pair(3))  # bottom bar

        for i in range(h):
            screen.addstr(i, 0, "  ", curses.color_pair(3))  # left bar
            screen.addstr(i, w - 3, "  ", curses.color_pair(3))  # right bar
        screen.refresh()

        # Wait for changes in terminal size
        key = ks_parser.get_key()
        if ks_parser.has_resize(key):
            continue
        ks_parser.check_quit(key)


def print_bottom_bar(screen, h, w):
    text_list = ['q Quit', '↑ Up', '↓ Down', '← Back', '→ Enter']
    text_len = len(''.join(text_list))
    num_spaces = ((w - text_len) // 6) + 1

    y_pos = 0
    for text in text_list:
        screen.addstr(h - 1, y_pos, " " * num_spaces)  # Initial Spaces
        y_pos += num_spaces
        screen.addstr(h - 1, y_pos, text, curses.color_pair(2) | curses.A_BOLD)
        y_pos += len(text)


# TODO print article date....
def print_article(screen, url, ks_parser):
    global text_w_ratio
    global text_h_ratio
    set_page(Page.ARTICLE)
    select_pos = 0

    article_html = get_request(url, screen)
    if article_html == -1:
        set_page(Page.HEADLINE)
    else:

        title_sel, body_sel = parse_article(article_html)
        title_pad = curses.newpad(3, 200)
        body_pad = curses.newpad(400, 200)
        screen.refresh()

    while page == Page.ARTICLE:
        try:

            h, w = screen.getmaxyx()
            text_w = w // text_w_ratio  # TODO: variable depending on window size
            text_h = h // text_h_ratio

            article_title_list, article_body_paras = wrap_article(title_sel, body_sel, text_w)

            screen.erase()
            screen.refresh()
            # TODO
            # screen.addstr(0, 0, f'wr{text_w_ratio}, hr{text_h_ratio},tw{text_w}')
            text_top_y = 1  # Where article title
            text_top_x = int(w // 2 - text_w // 2) - 1
            text_bot_y = int(h // 2 + text_h // 2) + 1
            text_bot_x = int(w // 2 + text_w // 2) + 1

            body_pad.erase()
            title_pad.erase()

            for idx, art_title in enumerate(article_title_list):
                title_x = int(text_w // 2 - len(art_title) // 2)
                title_pad.addstr(idx, title_x, art_title, curses.A_BOLD | curses.A_UNDERLINE)

            title_pad.refresh(0, 0,
                              text_top_y, text_top_x,
                              text_top_y + 2, text_bot_x)

            line_num = 0
            for para in article_body_paras:
                for line in para:
                    body_pad.addstr(line_num, 0, line)
                    line_num += 1
                line_num += 1

            # max_scroll_height = line_num - (text_bot_x-text_top_x) TODO

            body_pad.refresh(select_pos, 0,
                             text_top_y + len(article_title_list) + 1, text_top_x,
                             text_bot_y, text_bot_x)

            print_bottom_bar(screen, h, w)
            screen.refresh()
        except Exception:
            check_term_size(screen, True, ks_parser)
            continue

        select_pos, text_w_ratio, text_h_ratio = ks_parser.parse_article(select_pos, text_w_ratio, text_h_ratio)


# TODO print title "Category eg. Business, Latest News etc"
# TODO Maybe have an 'r' for refresh.
def print_headlines(screen, option, ks_parser):
    set_page(Page.HEADLINE)
    select_pos = 0

    rss_cache_path = get_rss_cache_path(option)
    rss_cache_age = file_age_hours(rss_cache_path)

    # Refresh cache older than 1 hour or does not exist
    if rss_cache_age > 1 or rss_cache_age == -1:
        rss_raw = get_request(RSS_URLS[option], screen)
        if rss_raw == -1:
            set_page(Page.MAIN)
        else:
            write_to_file(rss_cache_path, rss_raw)
            headlines, headline_urls = parse_rss(rss_raw)
    else:
        headlines, headline_urls = parse_rss(rss_cache_path)

    while page == Page.HEADLINE:
        screen.erase()
        h, w = screen.getmaxyx()
        try:
            # screen.addstr(0, 0, f'h: {h} w: {w} pos:{select_pos}')

            rss_last_refresh_time = get_rss_last_refresh_time(rss_cache_path)
            last_refresh_text = f'Last Refreshed: {rss_last_refresh_time}'
            refresh_w = w - len(last_refresh_text) - 1

            screen.addstr(0, refresh_w, last_refresh_text)

            max_len_options = int(w // 1.2)

            for idx, row in enumerate(headlines):
                x = (w // 2) - (max_len_options // 2)
                y = h // 2 - len(headlines) // 2 + idx

                # TODO: Scrolling textbox, double spacing
                if idx + 1 < 10:
                    row = f'{idx + 1}.  ' + row
                else:
                    row = f'{idx + 1}. ' + row

                row = textwrap.shorten(row, max_len_options, placeholder="...")

                if idx == select_pos:
                    screen.addstr(y, x, row, curses.A_REVERSE)
                else:
                    screen.addstr(y, x, row)

            print_bottom_bar(screen, h, w)
            screen.refresh()
            select_pos = ks_parser.parse_headlines(select_pos, len(headlines), headline_urls[select_pos])

        except Exception:
            check_term_size(screen, True, ks_parser)
            continue


def print_main_menu(screen, ks_parser):
    options = ['1. Latest News', '2. Business', '3. World', '4. Asia', '5. Singapore', '6. Sport']
    select_pos = 0

    while True:

        screen.erase()
        screen.refresh()
        h, w = screen.getmaxyx()
        # screen.addstr(0, 0, f'h: {h} w: {w} pid: {os.getpid()}')

        try:
            # Print Title
            max_len_title = get_str_max_len(TITLE2)
            for index, text in enumerate(TITLE2):
                screen.addstr(3 + index, w // 2 - max_len_title // 2, text)

            max_len_options = get_str_max_len(options)
            for idx, row in enumerate(options):
                x = (w // 2) - (max_len_options // 2)
                # y = h // 2 + idx
                y = h // 2 - 1 + idx * 2
                if select_pos == idx:
                    screen.addstr(y, x, row, curses.A_REVERSE)
                else:
                    screen.addstr(y, x, row)

            # Print Bottom Bar
            print_bottom_bar(screen, h, w)
            screen.refresh()
        except Exception:
            check_term_size(screen, True, ks_parser)
            continue

        select_pos = ks_parser.parse_main(select_pos, len(options))
