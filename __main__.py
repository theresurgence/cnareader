import curses 
import sys
from src.front import print_main_menu


def main(stdscr):
    curses.curs_set(0)
    # stdscr.keypad(1) # TODO Need this or not
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_YELLOW)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    print_main_menu(stdscr)


if __name__ == '__main__':
    # TODO directories for RSS cache
    # create temp file?
    # windows hidden file?
    match (sys.platform):
        case 'win32':
            pass
        case 'linux':
            pass
    curses.wrapper(main)

