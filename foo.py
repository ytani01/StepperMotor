#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
"""
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

import pigpio
import threading
import sys
import time

from MyLogger import get_logger

PIN_DIR = 17
PIN_STEP = 27


import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help="""
StepMtr class
""")
@click.argument('sleep_sec', type=float, default=0.1)
def main(sleep_sec):
    pi = pigpio.pi()
    pi.set_mode(PIN_STEP, pigpio.OUTPUT)
    pi.set_mode(PIN_DIR, pigpio.OUTPUT)

    try:
        while True:
            pi.write(PIN_STEP, 1)
            time.sleep(sleep_sec)
            pi.write(PIN_STEP, 0)
            time.sleep(sleep_sec)
            print('.', end='')
            sys.stdout.flush()

    finally:
        print('finally')
        pi.stop()


if __name__ == '__main__':
    main()
