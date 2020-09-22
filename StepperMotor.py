#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
"""
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

import pigpio
import time

from MyLogger import get_logger


class StepperMotor:
    CW = 1
    CCW = -1

    SEQ_WAVE = [[1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [0, 0, 0, 1]]

    SEQ_FULL = [[1, 0, 0, 1],
                [1, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 1]]

    SEQ_HALF = [[1, 0, 0, 1],
                [1, 0, 0, 0],
                [1, 1, 0, 0],
                [0, 1, 0, 0],
                [0, 1, 1, 0],
                [0, 0, 1, 0],
                [0, 0, 1, 1],
                [0, 0, 0, 1]]


    def __init__(self, pin1, pin2, pin3, pin4, seq=SEQ_WAVE, pi=None,
                 debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('pin1,pin2,pin3,pin4=%s,%s,%s,%s',
                        pin1, pin2, pin3, pin4)
        self._log.debug('seq=%s, pi=%s', seq, pi)

        self.pin = (pin1, pin2, pin3, pin4)
        self.seq = seq

        self.pin_n = len(self.pin)

        self.mypi = False
        self.pi = pi
        if pi is None:
            self.mypi = True
            self.pi = pigpio.pi()

        for i in range(self.pin_n):
            self.pi.set_mode(self.pin[i], pigpio.OUTPUT)
            self.pi.write(self.pin[i], 0)

        self.cur_i = 0

    def end(self):
        self._log.debug('')
        self.stop()
        if self.mypi:
            self.pi.stop()

    def stop(self):
        self._log.debug('')
        self.write([0, 0, 0, 0])

    def write(self, val):
        self._log.debug('val=%s', val)

        self.pi.write(self.pin[0], val[0])
        self.pi.write(self.pin[1], val[1])
        self.pi.write(self.pin[2], val[2])
        self.pi.write(self.pin[3], val[3])

    def move1(self, direction=CW):
        self._log.debug('direction=%s', direction)

        self.write(self.seq[self.cur_i])
        self.cur_i = (self.cur_i + direction) % len(self.seq)

    def move(self, interval, count=0, direction=CW):
        self._log.debug('count=%s, direction=%s', count, direction)

        self.active = True

        counter = 0
        while self.active:
            self.move1(direction)
            counter += 1
            if count > 0 and counter >= count:
                break

            time.sleep(interval)

        self.stop()
        self.active = False


class Sample:
    DEF_INTERVAL = 0.005  # sec
    SEQ = {'wave': StepperMotor.SEQ_WAVE,
           'full': StepperMotor.SEQ_FULL,
           'half': StepperMotor.SEQ_HALF}

    def __init__(self, pin1, pin2, pin3, pin4,
                 interval=DEF_INTERVAL,
                 ccw=False,
                 count=0,
                 seq=SEQ['wave'],
                 debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('pin1,pin2,pin3,pin4=%s,%s,%s,%s',
                        pin1, pin2, pin3, pin4)
        self._log.debug('interval=%s, ccw=%s, count=%s, seq=%s',
                        interval, ccw, count, seq)

        self.interval = interval
        if ccw:
            self.direction = StepperMotor.CCW
        else:
            self.direction = StepperMotor.CW

        self.count = count
        self.seq = self.SEQ[seq]

        self.sm = StepperMotor(pin1, pin2, pin3, pin4, seq=self.seq,
                               debug=self._dbg)

    def main(self):
        self._log.debug('')
        self.sm.move(self.interval, count=self.count, direction=self.direction)

    def end(self):
        self._log.debug('')
        self.sm.end()


import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help="""
StepperMotor class
""")
@click.argument('pin1', type=int)
@click.argument('pin2', type=int)
@click.argument('pin3', type=int)
@click.argument('pin4', type=int)
@click.option('--interval', '-i', 'interval', type=float,
              default=Sample.DEF_INTERVAL,
              help='interval sec')
@click.option('--ccw', 'ccw', is_flag=True, default=False,
              help='direction CCW')
@click.option('--count', '-c', 'count', type=int, default=0,
              help='count')
@click.option('--seq', '-s', 'seq', type=str, default="wave",
              help='drive sequence')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin1, pin2, pin3, pin4, interval, ccw, count, seq, debug):
    log = get_logger(__name__, debug)
    log.debug('(pin1, pin2, pin3, pin4)=%s', (pin1, pin2, pin3, pin4))
    log.debug('interval=%s, ccw=%s, count=%s, seq=%s',
              interval, ccw, count, seq)

    log.info('start')

    app = Sample(pin1, pin2, pin3, pin4, interval, ccw, count, seq, debug=debug)

    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()
        log.debug('end')


if __name__ == '__main__':
    main()
