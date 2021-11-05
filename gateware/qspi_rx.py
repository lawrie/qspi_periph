from nmigen import *
from nmigen.utils import bits_for

from nmigen.hdl.ast import Rose, Fell
from nmigen.lib.cdc import FFSynchronizer

class QspiRx(Elaboratable):
    """ QSPI Slave Receive data """
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

        # De-glitch sclk
        sclk = Signal()
        m.submodules += FFSynchronizer(i=self.sclk, o=sclk)
        
        # De-glitch sclk
        csn = Signal()
        m.submodules += FFSynchronizer(i=self.csn, o=csn)
        
        nibbles = Signal(bits_for(self.pkt_size) * 2)

        with m.If(csn):
            m.d.sync += [
                nibbles.eq(0),
                self.pkt.eq(0)
            ]
        with m.Else():
            with m.If(Rose(sclk)):
                m.d.sync += [
                    self.pkt.eq(Cat(self.qd, self.pkt[:-4])),
                    nibbles.eq(nibbles+1)
                ]

        m.d.comb += self.ready.eq(nibbles == self.pkt_size * 2)

        return m

