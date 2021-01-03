#
# (c) 2020 Yoichi Tanibayashi
#
"""
__main__.py
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021/01'

import click
import cuilib
from . import StepMtr, StepMtrTh
from .my_logger import get_logger


class Sample:
    """サンプル"""
    SEQ = [StepMtr.SEQ_FULL, StepMtr.SEQ_HALF, StepMtr.SEQ_WAVE]
    SEQ_STR = ['FULL', 'HALF', 'WAVE']

    DIRECTION_STR = {StepMtr.CW: 'CW', StepMtr.CCW: 'CCW'}

    SPEED2INTERVAL = (1,
                      0.5,
                      0.25,
                      0.125,
                      0.06,
                      0.03,
                      0.015,
                      0.008,
                      0.004,
                      0.002,
                      0.0015)

    def __init__(self, pin1, pin2, pin3, pin4, debug=False):
        self._dbg = debug
        self.__log = get_logger(__class__.__name__, self._dbg)
        self.__log.debug('pins=%s', (pin1, pin2, pin3, pin4))

        self._pin1 = pin1
        self._pin2 = pin2
        self._pin3 = pin3
        self._pin4 = pin4

        self._speed = 1
        self._direction = StepMtr.CW
        self._seq_i = 0

        self._mtr = StepMtrTh(
            self._pin1, self._pin2, self._pin3, self._pin4,
            seq=self.SEQ[self._seq_i],
            interval=self.SPEED2INTERVAL[self._speed],
            count=-1,
            direction=self._direction,
            debug=self._dbg)

        self._cui = cuilib.Cui(debug=self._dbg)

        self._cui.add(
            ['w', 'x', 'KEY_UP', 'KEY_DOWN'],
            self.speed,
            'Speed: Up/Down')

        self._cui.add(
            ['a', 'd', 'KEY_RIGHT', 'KEY_LEFT'],
            self.direction,
            'Direction: CW/CCW')

        self._cui.add(
            [' ', 'KEY_PGUP', 'KEY_PGDOWN'],
            self.seq,
            'Sequence: FULL/HALF/WAVE')

        self._cui.add(
            ['q', 'Q', 'KEY_ESCAPE', '\x04'],
            self.quit,
            'Quit')

        self._cui.add('hH?', self.help, 'command list')

    def speed(self, key_sym):
        """ speed """
        self.__log.debug('key_sym=%s', key_sym)

        if key_sym in ('w', 'KEY_UP'):
            self._speed = min(self._speed + 1,
                              len(self.SPEED2INTERVAL) - 1)

        if key_sym in ('x', 'KEY_DOWN'):
            self._speed = max(self._speed - 1, 0)

        print('speed: %s (interval=%s sec)' % (
            self._speed, self.SPEED2INTERVAL[self._speed]))

        self._mtr.set_interval(self.SPEED2INTERVAL[self._speed])

    def direction(self, key_sym):
        """ direction """
        self.__log.debug('key_sym=%s', key_sym)

        if key_sym in ('d', 'KEY_RIGHT'):
            self._direction = StepMtr.CW

        if key_sym in ('a', 'KEY_LEFT'):
            self._direction = StepMtr.CCW

        print('direction: %s' % (self.DIRECTION_STR[self._direction]))

        self._mtr.set_direction(self._direction)

    def seq(self, key_sym):
        """ seq """
        self.__log.debug('key_sym=%a', key_sym)

        if key_sym in (' ', 'KEY_PGUP'):
            self._seq_i = (self._seq_i + 1) % len(self.SEQ)

        if key_sym in ('KEY_PGDOWN',):
            self._seq_i = (self._seq_i - 1) % len(self.SEQ)

        print('seq: %s' % (self.SEQ_STR[self._seq_i]))

        self._mtr.set_seq(self.SEQ[self._seq_i])

    def quit(self, key_sym):
        """ quit """
        self.__log.debug('key_sym=%s', key_sym)
        print('*** Quit ***')
        self._cui.end()

    def help(self, key_sym):
        """ help """
        self.__log.debug('key_sym=%s', key_sym)
        print('command list:')
        self._cui.help(True)

    def main(self):
        """ main """
        self.__log.debug('')

        self._mtr.start()
        self._cui.start()
        print('*** Start ***')
        print('speed: %s (interval=%s sec)' % (
            self._speed, self.SPEED2INTERVAL[self._speed]))
        print('direction: %s' % (self.DIRECTION_STR[self._direction]))
        print('seq: %s' % (self.SEQ_STR[self._seq_i]))

        self._cui.join()

    def end(self):
        """ end """
        self.__log.debug('')
        self._mtr.end()


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help="""
Stepper Motor Interactive Test Program
""")
@click.argument('pin1', type=int)
@click.argument('pin2', type=int)
@click.argument('pin3', type=int)
@click.argument('pin4', type=int)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin1, pin2, pin3, pin4, debug):
    """ サンプル起動用メイン関数 """
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
