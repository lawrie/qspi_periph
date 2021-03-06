from nmigen import *

class HelloTx(Elaboratable):
    """ Test of TX peripheral that sends `Hello World!` to the host"""
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # Inputs
        self.i_ack     = Signal()

        # Outputs
        self.o_pkt    = Signal(pkt_size * 8)
        self.o_valid  = Signal()
        self.o_nb     = Signal(5)

    def elaborate(self, platform):
        m = Module()

        # Count used to periodically generate valid output
        cnt = Signal(28)
        m.d.sync += cnt.eq(cnt + 1)

        # Hello World! output packet (16 bytes)
        m.d.comb += [
            self.o_pkt.eq(0x202048656c6c6f20576f726c64212020),
            self.o_nb.eq(16)
        ]

        # Generate valid output every couple of seconds
        with m.If(cnt == 0):
            m.d.sync += self.o_valid.eq(1)

        # Unset o_valid when acked
        with m.If(self.i_ack):
            m.d.sync += self.o_valid.eq(0)

        return m

