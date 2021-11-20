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
        self.i_nb     = Signal()

        # Outputs
        self.o_ready  = Signal()
        self.o_valid  = Signal()
        self.o_pkt    = Signal(pkt_size * 8)
        self.o_nb     = Signal(5)

        self.led      = Signal(8)

    def elaborate(self, platform):
        m = Module()

        # Put valid input on the leds
        with m.If(self.i_valid):
            m.d.sync += self.led.eq(self.i_pkt[:8])
        
        # No output
        m.d.comb += [
            self.o_ready.eq(1),
            self.o_valid.eq(0),
            self.o_nb.eq(16)
        ]

        return m

