from nmigen import *
from nmigen.utils import bits_for

from nmigen.hdl.ast import Rose


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

        nibbles = Signal(bits_for(self.pkt_size) * 2)
        shift_reg = Signal(self.pkt_size * 8)

        with m.If(self.csn):
            m.d.sync += [
                nibbles.eq(0),
                shift_reg.eq(self.pkt)
            ]
        with m.Else():
            with m.If(Rose(self.sclk)):
                m.d.sync += [
                    nibbles.eq(nibbles+1),
                    shift_reg.eq(Cat(C(0,4), shift_reg[:-4]))
                ]

        m.d.comb += self.qd.eq(shift_reg[-4:]),
        m.d.comb += self.ready.eq(nibbles == self.pkt_size * 2)

        return m

