import curses
import sys

from src.front import init_front


def main(screen):
    init_front(screen)


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
