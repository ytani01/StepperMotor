#!/usr/bin/env python3

import time
from  stepmtr import StepMtr, StepMtrTh

mtr = StepMtrTh(5, 6, 13, 19)
mtr.start()

mtr.set_count(300)
time.sleep(5)

mtr.set_direction(StepMtr.CCW)
mtr.set_count(300)
time.sleep(5)

mtr.set_count(-1)  # continuous rotation
time.sleep(5)

mtr.end()
