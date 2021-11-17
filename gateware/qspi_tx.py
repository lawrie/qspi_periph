from nmigen import *
from nmigen.utils import bits_for

from nmigen.hdl.ast import Rose, Fell

class QspiTx(Elaboratable):
    def __init__(self, pkt_size=16, qw=4):
        # Parameters
        self.pkt_size = pkt_size
        self.qw       = qw

        # QSPI pins
        self.csn  = Signal()
        self.sclk = Signal()
        self.qd   = Signal(qw)

        # Inputs
        self.pkt   = Signal(self.pkt_size * 8)

        # Outputs
        self.ready = Signal()

    def elaborate(self, platform):
        m = Module()

        chunks = Signal(bits_for(self.pkt_size) * (8 // self.qw))
        shift_reg = Signal(self.pkt_size * 8)

        with m.If(self.csn):
            m.d.sync += [
                chunks.eq(0),
                shift_reg.eq(self.pkt)
            ]
        with m.Else():
            with m.If(Fell(self.sclk)):
                m.d.sync += [
                    chunks.eq(chunks+1),
                    shift_reg.eq(Cat(C(0,self.qw), shift_reg[:-self.qw]))
                ]

        m.d.comb += self.qd.eq(shift_reg[-self.qw:]),
        m.d.comb += self.ready.eq(chunks == self.pkt_size * (8 // self.qw))

        return m

