from nmigen import *

class QspiTx(Elaboratable):
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # QSPI pins
        self.csn  = Signal()
        self.sclk = Signal()
        self.qd   = Signal(4)

        # Inputs
        self.pkt   = Signal(self.pkt_size * 8)

        # Outputs
        self.ready = Signal()

    def elaborate(self, platform):
        m = Module()

        with m.If(self.csn):
            m.d.sync += self.ready.eq(0)
        with m.Else():
            m.d.sync += [
                self.ready.eq(1)
            ]

        return m

