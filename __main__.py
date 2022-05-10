import curses

from src.front import init_front


def main(screen):
    init_front(screen)


if __name__ == '__main__':
    curses.wrapper(main)
