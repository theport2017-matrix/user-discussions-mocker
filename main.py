#!/usr/bin/env python3

import sys
from threading import Thread

from crowd import ScriptRoller, UserLink


def help_message():
    print("Usage: ./main.py script ...")


def run_script(filename):
    print(filename)
    user_link = UserLink().tryLoginElseRegister("nicolatesla")
    script_roller = ScriptRoller(user_link)
    script_roller.rollfile(filename)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        help_message()
        sys.exit(0)

    threads = []
    for arg in sys.argv[1:]:
        thread = Thread(target=run_script, args=(arg,))
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
