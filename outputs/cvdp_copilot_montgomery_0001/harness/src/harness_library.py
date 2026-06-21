
import cocotb
from cocotb.triggers import FallingEdge, RisingEdge, ReadOnly, NextTimeStep, Timer
import random



async def dut_init(dut):
    # iterate all the input signals and initialize with 0
    for signal in dut:
        try:
            signal.value = 0
        except Exception:
            pass

def redc(T, N, R_INVERSE):
    t = (T*R_INVERSE)%N
    return t