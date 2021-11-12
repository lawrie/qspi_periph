from nmigen import *
from nmigen.utils import bits_for

from nmigen.hdl.ast import Rose, Fell

class QspiRx(Elaboratable):
    """ QSPI Slave Receive data """
    def __init__(self, pkt_size=16, qw=4):
        # Parameters
        self.pkt_size = pkt_size
        self.qw       = 4

        # QSPI pins
        self.csn  = Signal()
        self.sclk = Signal()
        self.qd   = Signal(qw)

        # Outputs
        self.pkt   = Signal(self.pkt_size * 8)
        self.ready = Signal()

    def elaborate(self, platform):
        m = Module()

        chunks = Signal(bits_for(self.pkt_size) * (8 // self.qw))

        with m.If(self.csn):
            m.d.sync += [
                chunks.eq(0),
                self.pkt.eq(0)
            ]
        with m.Else():
            with m.If(Rose(self.sclk)):
                m.d.sync += [
                    self.pkt.eq(Cat(self.qd, self.pkt[:-self.qw])),
                    chunks.eq(chunks+1)
                ]

        m.d.comb += self.ready.eq(chunks == self.pkt_size * (8 // self.qw))

        return m

