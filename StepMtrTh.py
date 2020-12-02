#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
ステッピングモーター制御: マルチスレッド版
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2020/12'

from StepMtr import StepMtr
import threading

from MyLogger import get_logger


class StepMtrTh:
    """ステッピングモーター制御: マルチスレッド版

    ``start()``で動作を開始し、
    ``stop()``で途中で停止することができる。

    動作中に回転方向、速度などを変更することもできる。

    Attributes
    ----------
    sm: StepMtr
        ステッピングモーター(シングルスレッド版)オブジェクト
    worker: threading.Thread
        ワーカー・スレッド
    """

    def __init__(self, pin1, pin2, pin3, pin4,
                 seq=StepMtr.SEQ_WAVE,
                 interval=StepMtr.DEF_INTERVAL,
                 count=0,
                 direction=StepMtr.CW,
                 pi=None,
                 debug=False):
        """コンストラクタ

        Parameters
        ----------
        pin1, pin2, pin3, pin4: int
            GPIOピン番号
        seq: list, default StepMtr.SEQ_WAVE
            信号パターンリスト
        interval: float, default StepMtr.DEF_INTERVAL
            ステップの間隔(sec)
        count: int, default 0
            ステップ数
            < 0: 連続回転
        direction: int, default StepMtr.CW
            回転方向
            StepMtr.CW | StepMtr.CCW
        pi: pigpio.pi
            pigpioオブジェクト
        debug: bool
            デバッグフラグ
        """
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('pins=%s', (pin1, pin2, pin3, pin4))
        self._log.debug('seq=%s', seq)
        self._log.debug('interval=%s, count=%s, direction=%s',
                        interval, count, direction)
        self._log.debug('pi=%s', pi)

        self.mtr = StepMtr(pin1, pin2, pin3, pin4,
                           seq, interval, count, direction, pi,
                           debug=self._dbg)

        self.worker = None

    def set_count(self, count):
        """
        """
        self._log.debug('count=%s', count)

        self.mtr.count = count
        self.start()

    def set_interval(self, interval):
        """
        """
        self._log.debug('interval=%s', interval)

        self.mtr.interval = interval
        self.start()

    def set_direction(self, direction):
        """
        """
        self._log.debug('direction=%s', direction)

        self.mtr.direction = direction
        self.start()

    def set_seq(self, seq):
        """
        """
        self._log.debug('seq=%s', seq)

        self.mtr.seq = seq
        self.start()

    def start(self):
        """スタート

        内部でスレッドを起動する。
        モーター動作中に``stop()``で停止することができる。
        """
        self._log.debug('')

        self.stop()

        # start thread
        self.worker = threading.Thread(target=self.mtr.move)
        self.worker.setDaemon(True)
        self.worker.start()

    def stop(self):
        """ストップ

        モーターの動作を停止し、スレッドを削除する。
        """
        self._log.debug('')

        if self.worker is not None:
            self._log.debug('stopping thread ..')
            self.mtr.stop()
            self.worker.join()
            self.worker = None
            self._log.debug('stopping thread .. done')

    def end(self):
        """終了処理

        プログラム終了時に呼ぶこと
        """
        self._log.debug('doing ..')
        self.stop()
        self.mtr.end()
        self._log.debug('done')


"""
以下、サンプル・コード
"""


class Sample:
    """サンプル
    """
    SEQ = {'wave': StepMtr.SEQ_WAVE,
           'full': StepMtr.SEQ_FULL,
           'half': StepMtr.SEQ_HALF}

    DIRECTION = {'cw': StepMtr.CW,
                 'ccw': StepMtr.CCW}

    def __init__(self, pin1, pin2, pin3, pin4, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('pins=%s', (pin1, pin2, pin3, pin4))

        # ``StepMtrTh``オブジェクト作成
        self.mtr = StepMtrTh(pin1, pin2, pin3, pin4, debug=self._dbg)

    def main(self):
        self._log.debug('')

        # スタート
        self.mtr.start()

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

                self.mtr.set_direction(direction)
                continue

            if line1 == 'wave' or line1 == 'full' or line1 == 'half':
                seq = self.SEQ[line1]
                self._log.info('seq=%s', seq)

                self.mtr.set_seq(seq)
                continue

            try:
                num = float(line1)
            except Exception:
                self._log.error('invalid command: %a', line1)
                continue

            if 0 < num < 1:
                interval = num
                self._log.info('interval=%s', interval)

                self.mtr.set_interval(interval)
                continue

            self.count = int(num)
            self._log.info('count=%s', self.count)

            self.mtr.set_count(self.count)

    def end(self):
        self._log.debug('')
        self.mtr.end()


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
    """サンプル起動用メイン関数
    """
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
