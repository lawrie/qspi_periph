from nmigen import *
from nmigen_stdio.serial import *

class TestUart(Elaboratable):
    """ Uart peripheral using ngigen-stdio """
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # Inputs
        self.i_pkt    = Signal(pkt_size * 8)
        self.i_valid  = Signal()
        self.i_ack    = Signal()
        self.i_nb     = Signal(4)
        self.i_flags  = Signal(4)

        # Outputs
        self.o_ready  = Signal()
        self.o_valid  = Signal()
        self.o_pkt    = Signal(pkt_size * 8)
        self.o_nb     = Signal(4)

    def elaborate(self, platform):
        m = Module()

        uart = platform.request("uart")

        divisor = int(platform.default_clk_frequency // 115200);

        m.submodules.ser = ser = AsyncSerial(divisor=divisor, pins=uart)

        i_pkt = Signal(self.pkt_size * 8)
        i_nb =  Signal(4, reset=0)

        # We are ready when there are no bytes to transmit
        m.d.comb += self.o_ready.eq(i_nb == 0)

        # Consume packet when valid and ready
        with m.If(self.i_valid & self.o_ready):
            m.d.sync += [
                i_nb.eq(self.i_nb),
                i_pkt.eq(self.i_pkt)
            ]

        # Connect uart
        m.d.comb += [
            ser.tx.data.eq(i_pkt.word_select(i_nb -1, 8)),
            ser.tx.ack.eq(i_nb > 0)
        ]

        # Move on when byte written
        with m.If(ser.tx.ack & ser.tx.rdy):
            m.d.sync += i_nb.eq(i_nb - 1)

        # Allow input when we have no output
        m.d.comb += ser.rx.ack.eq(~self.o_valid)

        # Output packets are 1 byte
        m.d.comb += self.o_nb.eq(1)

        # Consume input when ack and rdy
        with m.If(ser.rx.ack & ser.rx.rdy):
            m.d.sync += [
                self.o_valid.eq(1),
                self.o_pkt[-8:].eq(ser.rx.data)
            ]

        # Unset o_valid when data acked
        with m.If(self.i_ack):
            m.d.sync += self.o_valid.eq(0)

        return m

