#
# (c) 2020 Yoichi Tanibayashi
#
"""
ステッピングモーター制御: マルチスレッド版
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2021/01'

import threading
from .stepmtr import StepMtr
from .my_logger import get_logger


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
        Parameters
        ----------
        count: int
        """
        self._log.debug('count=%s', count)

        self.mtr.count = count
        self.start()

    def set_interval(self, interval):
        """
        Parameters
        ----------
        interval: float
        """
        self._log.debug('interval=%s', interval)

        self.mtr.interval = interval
        self.start()

    def set_direction(self, direction):
        """
        Parameters
        ----------
        direction: int
            StepMtr.CW or StepMtr.CCW
        """
        self._log.debug('direction=%s', direction)

        self.mtr.direction = direction
        self.start()

    def set_seq(self, seq):
        """
        Parameters
        ----------
        seq: list of list of int
            StepMtr.SEQ_WAVE|FULL|HALF
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
