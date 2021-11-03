from nmigen import *
from nmigen.sim import *

from dispatcher import Dispatcher
from test_rx import TestRx
from test_tx import TestTx
from test_both import TestBoth

if __name__ == "__main__":

    def process():
        yield dut.csn.eq(1)
        yield dut.ev_i.eq(0)
        yield
        yield dut.ev_i.eq(0xf)
        yield

        yield dut.sclk.eq(0)
        yield dut.csn.eq(0)
        nibble = 0

        for i in range(32):
            yield dut.qd_i.eq(i & 0xF)

            yield 
            yield dut.sclk.eq(1)
            yield
            yield dut.sclk.eq(0)
        
        yield 
        
        yield dut.csn.eq(1)
        
        for i in range(10):
            ev_o = yield dut.ev_o
            if (ev_o == 1):
                break
            yield

        yield dut.sclk.eq(0)
        yield dut.csn.eq(0)
        for i in range(2):
            yield 
        
        yield dut.csn.eq(1)

        for i in range(2):
            yield 

    m = Module()

    dut = Dispatcher()
    dut.register(0, TestBoth(), True, True)
    dut.register(1, TestTx(), False, True)
    m.submodules.dut = dut

    sim = Simulator(m)
    sim.add_clock(1e-6)
    sim.add_sync_process(process)

    with sim.write_vcd("dispatch.vcd", "dispatch.gtkw"):
        sim.run()

