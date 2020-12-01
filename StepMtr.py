#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
"""
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2020/12'

import pigpio
import time

from MyLogger import get_logger


class StepMtr:
    CW = 1
    CCW = -1

    DEF_INTERVAL = 0.005  # sec

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

    def __init__(self, pin1, pin2, pin3, pin4,
                 seq=SEQ_WAVE,
                 interval=DEF_INTERVAL,
                 count=0,
                 direction=CW,
                 pi=None,
                 debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('pin1,pin2,pin3,pin4=%s,%s,%s,%s',
                        pin1, pin2, pin3, pin4)
        self._log.debug('seq=%s,interval=%s,count=%s,direction=%s,pi=%s',
                        seq, interval, count, direction, pi)

        self.pin = (pin1, pin2, pin3, pin4)
        self.seq = seq
        self.interval = interval
        self.direction = direction
        self.count = count

        self.pin_n = len(self.pin)

        self.mypi = False
        self.pi = pi
        if pi is None:
            self.mypi = True
            self.pi = pigpio.pi()

        for i in range(self.pin_n):
            self.pi.set_mode(self.pin[i], pigpio.OUTPUT)
            self.pi.write(self.pin[i], 0)

        self.active = False

    def end(self):
        self.active = False
        self.stop()
        if self.mypi:
            self.pi.stop()

        self._log.info('done')

    def write(self, val):
        self._log.debug('val=%s', val)

        self.pi.write(self.pin[0], val[0])
        self.pi.write(self.pin[1], val[1])
        self.pi.write(self.pin[2], val[2])
        self.pi.write(self.pin[3], val[3])

    def stop(self):
        self._log.debug('')
        self.active = False
        self.write([0, 0, 0, 0])
        time.sleep(0.5)  # Important!

    def move(self, interval=None, count=None, direction=None, seq=None):
        self._log.debug('interval=%s, count=%s, direction=%s, seq=%s',
                        interval, count, direction, seq)

        if interval is not None:
            self.interval = interval

        if count is not None:
            self.count = count

        if direction is not None:
            self.direction = direction

        if seq is not None:
            self.seq = seq

        self._log.info('interval=%s, count=%s, direction=%s, seq=%s',
                       self.interval, self.count, self.direction,
                       self.seq)

        self.active = True

        seq_i = 0

        counter = 0
        while self.active:
            if seq_i >= len(self.seq):
                # sequence is changed by main routine
                seq_i = 0

            if self.count >= 0 and counter >= self.count:
                break

            self.write(self.seq[seq_i])
            seq_i = (seq_i + self.direction) % len(self.seq)
            counter += 1

            time.sleep(self.interval)

        self.stop()


class Sample:
    SEQ = {'wave': StepMtr.SEQ_WAVE,
           'full': StepMtr.SEQ_FULL,
           'half': StepMtr.SEQ_HALF}

    DIRECTION = {'cw': StepMtr.CW,
                 'ccw': StepMtr.CCW}

    def __init__(self, pin1, pin2, pin3, pin4, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('pin1,pin2,pin3,pin4=%s,%s,%s,%s',
                        pin1, pin2, pin3, pin4)

        self.sm = StepMtr(pin1, pin2, pin3, pin4,
                          debug=self._dbg)

    def main(self):
        self._log.debug('')

        while True:
            self._log.info('moving ..')
            self.sm.move()

            prompt = '[0<=count'
            prompt += '|0<interval[sec]<1'
            prompt += '|cw|ccw'
            prompt += '|wave|full|half'
            prompt += 'NULL=end] '
            line1 = input(prompt)
            self._log.debug('line1=%a', line1)
            if len(line1) == 0:
                break

            if line1 == 'cw' or line1 == 'ccw':
                self.sm.direction = self.DIRECTION[line1]
                self._log.info('direction=%s', self.sm.direction)
                continue

            if line1 == 'wave' or line1 == 'full' or line1 == 'half':
                self.sm.seq = self.SEQ[line1]
                self._log.info('seq=%s', self.sm.seq)
                continue

            try:
                num = float(line1)
            except Exception:
                self._log.error('invalid command: %a', line1)
                continue

            if 0 < num < 1:
                self.sm.interval = num
                self._log.info('interval=%s', self.sm.interval)
                continue

            self.sm.count = int(num)
            self._log.info('count=%s', self.sm.count)

            if self.sm.count < 0:
                self._log.warning('move forever .. Ctrl-C to stop')

    def end(self):
        self._log.debug('')
        self.sm.end()


import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help="""
StepMtr class
""")
@click.argument('pin1', type=int)
@click.argument('pin2', type=int)
@click.argument('pin3', type=int)
@click.argument('pin4', type=int)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin1, pin2, pin3, pin4, debug):
    log = get_logger(__name__, debug)
    log.debug('(pin1, pin2, pin3, pin4)=%s', (pin1, pin2, pin3, pin4))

    app = Sample(pin1, pin2, pin3, pin4, debug=debug)

    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()
        log.debug('end')


if __name__ == '__main__':
    main()
