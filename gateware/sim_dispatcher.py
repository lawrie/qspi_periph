from nmigen import *
from nmigen.sim import *

from dispatcher import Dispatcher
from test_rx import TestRx

if __name__ == "__main__":

    def process():
        yield dut.csn.eq(1)
        yield dut.ev_i.eq(0)
        yield
        yield dut.ev_i.eq(0xf)
        yield

        yield dut.csn.eq(0)
        yield dut.qd_i.eq(10)

        for i in range(2):
            yield 
        
        yield dut.csn.eq(1)
        
        for i in range(5):
            yield 

    m = Module()

    dut = Dispatcher()
    dut.register(0, TestRx(), True, False)
    m.submodules.dut = dut

    sim = Simulator(m)
    sim.add_clock(1e-6)
    sim.add_sync_process(process)

    with sim.write_vcd("dispatch.vcd", "dispatch.gtkw"):
        sim.run()

