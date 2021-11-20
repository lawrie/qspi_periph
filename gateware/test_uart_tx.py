from nmigen import *
from nmigen_stdio.serial import *

class TestUartTx(Elaboratable):
    """ Test of RX peripheral that receives data from the host """
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # Inputs
        self.i_pkt    = Signal(self.pkt_size * 8)
        self.i_valid  = Signal()
        self.i_nb     = Signal(4)

        # Outputs
        self.o_ready  = Signal()

    def elaborate(self, platform):
        m = Module()

        uart = platform.request("uart")

        divisor = int(platform.default_clk_frequency // 115200);

        m.submodules.tx = tx = AsyncSerialTX(divisor=divisor, pins=uart)

        pkt = Signal(self.pkt_size * 8)
        nb = Signal(4, reset=0)

        # We are ready when there are no bytes to transmit
        m.d.comb += self.o_ready.eq(nb == 0)

        # Consume packet when valid and ready
        with m.If(self.i_valid & self.o_ready):
            m.d.sync += [
                nb.eq(self.i_nb),
                pkt.eq(self.i_pkt)
            ]

        # Connect uart
        m.d.comb += [
            tx.data.eq(pkt.word_select(nb -1, 8)),
            tx.ack.eq(nb > 0)
        ]

        # Move on when byte written
        with m.If(tx.ack & tx.rdy):
            m.d.sync += nb.eq(nb - 1)

        return m

