from nmigen import *
from nmigen.sim import *

from dispatcher import Dispatcher
from test_rx import TestRx
from test_tx import TestTx
from test_both import TestBoth

if __name__ == "__main__":

    def process():
        # csn high and event zero by default
        yield dut.csn.eq(1)

        # Start a write transaction by setting the event
        # and then setting it back to F
        print("Starting write txn - sending 0x0123456789abcdef0123456789abcdef")
        yield dut.ev_i.eq(0)
        yield
        yield dut.ev_i.eq(0xf)
        yield

        # Set spi clock low by default
        yield dut.sclk.eq(0)

        # Start the transaction
        yield dut.csn.eq(0)
        nibble = 0

        # Send 0-F nibbles twice
        for i in range(32):
            yield dut.qd_i.eq(i & 0xF)

            yield 
            yield dut.sclk.eq(1)
            yield
            yield dut.sclk.eq(0)
        
        # End the transaction 
        yield dut.csn.eq(1)
        
        print("Waiting for read request")

        # Look for a read request
        for i in range(10):
            ev_o = yield dut.ev_o
            if (ev_o == 1):
                break
            yield

        # Set spi clock low and start the transaction
        yield dut.sclk.eq(0)
        yield dut.csn.eq(0)
        
        print("Read ", end='')

        # Read nibbles
        for i in range(32):
            yield 
            yield dut.sclk.eq(1)
            yield
            qd_o = yield dut.qd_o;
            print("{:x}".format(qd_o),end='')
            yield dut.sclk.eq(0)

        print()
        
        # End the transaction
        yield dut.csn.eq(1)
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

