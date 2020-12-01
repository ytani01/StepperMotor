#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2020/12'

from StepMtr import StepMtr
import threading

from MyLogger import get_logger


class StepMtrTh:
    def __init__(self, pin1, pin2, pin3, pin4,
                 seq=StepMtr.SEQ_WAVE,
                 interval=StepMtr.DEF_INTERVAL,
                 count=0,
                 direction=StepMtr.CW,
                 pi=None,
                 debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('pin1,pin2,pin3,pin4=%s,%s,%s,%s',
                        pin1, pin2, pin3, pin4)

        self._log.debug('seq=%s,interval=%s,count=%s,direction=%s,pi=%s',
                        seq, interval, count, direction, pi)

        self.sm = StepMtr(pin1, pin2, pin3, pin4,
                          seq, interval, count, direction, pi,
                          debug=self._dbg)

        self.worker = None

    def set_count(self, count):
        self._log.debug('count=%s', count)

        self.sm.count = count
        self.move()

    def set_interval(self, interval):
        self._log.debug('interval=%s', interval)

        self.sm.interval = interval

    def set_direction(self, direction):
        self._log.debug('direction=%s', direction)

        self.sm.direction = direction
        self.move()

    def set_seq(self, seq):
        self._log.debug('seq=%s', seq)

        self.sm.seq = seq
        self.move()

    def move(self):
        self._log.debug('')

        self.stop()

        """
        # set params
        self.sm.count = self.count
        self.sm.interval = self.interval
        self.sm.direction = self.direction
        self.sm.seq = self.seq
        """

        # start thread
        self.worker = threading.Thread(target=self.sm.move)
        self.worker.setDaemon(True)
        self.worker.start()

    def stop(self):
        self._log.debug('')

        if self.worker is not None:
            self._log.info('stop thread ..')
            self.sm.stop()
            self.worker.join()
            self.worker = None
            self._log.info('stop thread .. done')

    def end(self):
        self._log.debug('')
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

        self.sm_th = StepMtrTh(pin1, pin2, pin3, pin4,
                               StepMtr.SEQ_WAVE,
                               StepMtr.DEF_INTERVAL,
                               0,
                               StepMtr.CW,
                               debug=self._dbg)

    def main(self):
        self._log.debug('')

        self.sm_th.move()

        while True:
            prompt = '[0<=count|0>continuous'
            prompt += '|0<interval[sec]<1'
            prompt += '|cw|ccw'
            prompt += '|wave|full|half'
            prompt += '|NULL=end] '
            line1 = input(prompt)
            self._log.debug('line1=%a', line1)

            if len(line1) == 0:
                # end
                break

            if line1 == 'cw' or line1 == 'ccw':
                direction = self.DIRECTION[line1]
                self._log.info('direction=%s', direction)

                self.sm_th.set_direction(direction)
                continue

            if line1 == 'wave' or line1 == 'full' or line1 == 'half':
                seq = self.SEQ[line1]
                self._log.info('seq=%s', seq)

                self.sm_th.set_seq(seq)
                continue

            try:
                num = float(line1)
            except Exception:
                self._log.error('invalid command: %a', line1)
                continue

            if 0 < num < 1:
                interval = num
                self._log.info('interval=%s', interval)

                self.sm_th.set_interval(interval)
                continue

            self.count = int(num)
            self._log.info('count=%s', self.count)

            self.sm_th.set_count(self.count)

    def end(self):
        self._log.debug('')
        self.sm_th.end()


import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help="""
""")
@click.argument('pin1', type=int)
@click.argument('pin2', type=int)
@click.argument('pin3', type=int)
@click.argument('pin4', type=int)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin1, pin2, pin3, pin4, debug):
    log = get_logger(__name__, debug)
    log.debug('pins=%s', (pin1, pin2, pin3, pin4))

    app = Sample(pin1, pin2, pin3, pin4, debug=debug)

    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()
        log.info('end')


if __name__ == '__main__':
    main()
