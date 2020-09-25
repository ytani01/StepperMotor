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
import time

from MyLogger import get_logger


class StepMtr(threading.Thread):
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
        self._log.debug('seq=%s, interval=%s, count=%s, direction=%s, pi=%s',
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
                       self.interval, self.count, self.direction, self.seq)

        self.active = True

        seq_i = 0

        counter = 0
        while self.active:
            if seq_i >= len(self.seq):
                # sequence is changed by main routine
                seq_i = 0

            self.write(self.seq[seq_i])
            seq_i = (seq_i + self.direction) % len(self.seq)
            counter += 1

            if self.count > 0 and counter >= self.count:
                break

            time.sleep(self.interval)

        self.stop()


class StepMtrThread(threading.Thread):
    """
    TBD
    """
    def __init__(self):
        super().__init__()
        self.setDaemon(True)

    def run(self):
        self._log.debug('')
        self.move(self.interval)


class Sample:
    SEQ = {'wave': StepMtr.SEQ_WAVE,
           'full': StepMtr.SEQ_FULL,
           'half': StepMtr.SEQ_HALF}

    DIRECTION = {'cw': StepMtr.CW,
                 'ccw': StepMtr.CCW}

    def __init__(self, pin1, pin2, pin3, pin4,
                 interval=StepMtr.DEF_INTERVAL,
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
        self.count = count
        self.seq = self.SEQ[seq]
        if ccw:
            self.direction = StepMtr.CCW
        else:
            self.direction = StepMtr.CW

        self.sm = StepMtr(pin1, pin2, pin3, pin4, seq=self.seq,
                          debug=self._dbg)

    def main(self):
        self._log.debug('')

        th_mode = False
        sm_th = None

        while True:
            if th_mode:
                if sm_th is None:
                    sm_th = threading.Thread(target=self.sm.move)
                    sm_th.setDaemon(True)
                    sm_th.start()

                self.sm.count = self.count = 0
                self.sm.interval = self.interval
                self.sm.direction = self.direction
                self.sm.seq = self.seq

            else:
                if sm_th is not None:
                    self._log.info('stop thread ..')
                    self.sm.stop()
                    sm_th.join()
                    sm_th = None
                    self._log.info('stop thread .. done')

                self.sm.move(self.interval, self.count, self.direction,
                             self.seq)

            prompt = '[continuous=0|count>0'
            prompt += '|interval[sec]<1'
            prompt += '|cw|ccw|wave|full|half'
            prompt += '] '
            line1 = input(prompt)
            self._log.debug('line1=%a', line1)
            if len(line1) == 0:
                break

            if line1 == 'cw' or line1 == 'ccw':
                self.direction = self.DIRECTION[line1]
                self._log.info('direction=%s', self.direction)
                continue

            if line1 == 'wave' or line1 == 'full' or line1 == 'half':
                self.seq = self.SEQ[line1]
                continue

            try:
                num = float(line1)
            except Exception:
                self._log.error('invalid command: %a', line1)
                continue

            if num < 0:
                self._log.warning('num=%s ??', num)
                continue

            # num >= 0

            if 0 < num < 1:
                self.interval = num
                self._log.info('interval=%s', self.interval)
                continue

            self.sm.count = self.count = int(num)

            if self.count == 0:
                # continuous
                th_mode = True
                continue

            # self.count >= 1

            th_mode = False
            self.count = int(num)
            self._log.info('count=%s', self.count)

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
@click.option('--interval', '-i', 'interval', type=float,
              default=StepMtr.DEF_INTERVAL,
              help='interval sec')
@click.option('--ccw', 'ccw', is_flag=True, default=False,
              help='direction CCW')
@click.option('--count', '-c', 'count', type=int, default=1,
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

    app = Sample(pin1, pin2, pin3, pin4, interval, ccw, count, seq,
                 debug=debug)

    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()
        log.debug('end')


if __name__ == '__main__':
    main()
