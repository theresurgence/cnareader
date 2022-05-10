import curses

from src import front
from src.classes.page import Page


def has_resize(key):
    return key == curses.KEY_RESIZE


def check_quit(key):
    if key == ord('q'):
        exit(0)


class KeyStrokeParser:
    def __init__(self, screen):
        self.screen = screen

    def get_key(self):
        try:
            return self.screen.getch()
        except KeyboardInterrupt or Exception:
            exit(0)

    def resize(self, key):
        if has_resize(key):
            front.check_term_size(self.screen, is_error=False, ks_parser=self)

    def parse_main(self, select_pos, num_options):
        key = self.get_key()
        self.resize(key)
        check_quit(key)

        if key == curses.KEY_DOWN and select_pos < num_options - 1:
            return select_pos + 1

        if key == curses.KEY_UP and select_pos > 0:
            return select_pos - 1

        if key == curses.KEY_RIGHT:
            front.print_headlines(self.screen, select_pos, self)

        return select_pos

    def parse_headlines(self, select_pos, num_options, url):
        key = self.get_key()
        self.resize(key)
        check_quit(key)

        if key == curses.KEY_DOWN and select_pos < num_options - 1:
            return select_pos + 1

        if key == curses.KEY_UP and select_pos > 0:
            return select_pos - 1

        if key == curses.KEY_LEFT:
            front.set_page(Page.MAIN)

        elif key == curses.KEY_RIGHT:
            front.print_article(self.screen, url, self)

        return select_pos

    def parse_article(self, select_pos):
        key = self.get_key()
        self.resize(key)
        check_quit(key)

        # TODO max scrollable
        if key == curses.KEY_DOWN and select_pos < 100:
            select_pos += 1
        elif key == curses.KEY_UP and select_pos > 0:
            select_pos -= 1
        elif key == curses.KEY_LEFT:
            front.set_page(Page.HEADLINE)

        return select_pos
