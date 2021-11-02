from nmigen import *

class TestTx(Elaboratable):
    """ Test of TX peripheral that sends data to the host"""
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # Inputs
        self.i_ack     = Signal()
        self.sw        = Signal(4)

        # Outputs
        self.o_pkt    = Signal(pkt_size)
        self.o_valid  = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.o_valid.eq(1)
        m.d.comb += self.o_pkt.eq(self.sw)

        return m

