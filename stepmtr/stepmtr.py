#
# (c) 2019 Yoichi Tanibayashi
#
"""
ステッピングモーター制御: シングルスレッド版
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2021/01'

import pigpio
import time
from .my_logger import get_logger


class StepMtr:
    """ステッピングモーター制御: シングルスレッド版

    ``move()``を呼ぶと指定されたステップ数の動作が終了するまで、
    戻ってこない。
    カウント数を負の値にすると連続回転し、
    Ctrl-Cなどで強制終了するまで動き続ける。
    """
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
        """終了処理

        プログラム終了時に呼ぶこと
        """
        self._log.debug('doing ..')
        self.active = False
        self.stop()
        if self.mypi:
            self.pi.stop()
        self._log.info('done')

    def write(self, val):
        """
        """
        self._log.debug('val=%s', val)

        self.pi.write(self.pin[0], val[0])
        self.pi.write(self.pin[1], val[1])
        self.pi.write(self.pin[2], val[2])
        self.pi.write(self.pin[3], val[3])

    def stop(self):
        """ストップ
        """
        self._log.debug('')
        self.active = False
        self.write([0, 0, 0, 0])
        time.sleep(0.5)  # Important!

    def move(self, interval=None, count=None, direction=None, seq=None):
        """モーター作動
        """
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

        self._log.debug('interval=%s, count=%s, direction=%s, seq=%s',
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
                self.count = 0
                break

            self.write(self.seq[seq_i])
            seq_i = (seq_i + self.direction) % len(self.seq)
            counter += 1

            time.sleep(self.interval)

        self.stop()
