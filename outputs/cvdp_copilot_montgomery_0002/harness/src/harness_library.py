
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

def redc(T, N, R, N_PRIME):
    m = ((T%R)*N_PRIME)%R
    
    t = (T+ m*N)//R
    if t>=N:
        t = t-N
    else:
        t = t
    return t

def mod_mult(a, b, N):
    return a*b%N