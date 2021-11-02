from nmigen import *

class TestBoth(Elaboratable):
    """ Test of RX peripheral that receives data from the host """
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # Inputs
        self.i_pkt    = Signal(self.pkt_size * 8)
        self.i_valid  = Signal()
        self.i_ack    = Signal()

        # Outputs
        self.o_ready  = Signal()
        self.o_valid  = Signal()
        self.o_pkt    = Signal(pkt_size)

        self.led      = Signal(8)

    def elaborate(self, platform):
        m = Module()

        with m.If(self.i_valid):
            m.d.sync += self.led.eq(self.i_pkt[:8])
        
        m.d.comb += self.o_ready.eq(1)

        m.d.comb += self.o_valid.eq(0)

        return m

