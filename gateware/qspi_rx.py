from nmigen import *

class QspiRx(Elaboratable):
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # QSPI pins
        self.csn  = Signal()
        self.sclk = Signal()
        self.qd   = Signal(4)

        # Outputs
        self.pkt   = Signal(self.pkt_size * 8)
        self.ready = Signal()

    def elaborate(self, platform):
        m = Module()

        with m.If(self.csn):
            m.d.sync += self.ready.eq(0)
        with m.Else():
            m.d.sync += [
                self.ready.eq(1)
            ]

        if platform is None:
            m.d.comb += self.pkt.eq(self.qd)

        return m

