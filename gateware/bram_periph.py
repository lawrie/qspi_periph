from nmigen import *

class BramPeriph(Elaboratable):
    """ BRAM peripheral """
    def __init__(self, pkt_size=16, depth=4096):
        # Parameters
        self.pkt_size = pkt_size
        self.depth    = depth

        # Inputs
        self.i_pkt    = Signal(pkt_size * 8)
        self.i_valid  = Signal()
        self.i_nb     = Signal(4)
        self.i_ack    = Signal()

        # Outputs
        self.o_ready  = Signal()
        self.o_valid  = Signal()
        self.o_nb     = Signal(4)
        self.o_pkt    = Signal(pkt_size * 8)

    def elaborate(self, platform):
        m = Module()

        mem = Memory(width=8, depth=self.depth)
        m.submodules.w = w = mem.write_port()
        m.submodules.r = r = mem.read_port()

        i_nb  = Signal(4)
        addr  = Signal(15)
        i_pkt = Signal(self.pkt_size * 8)
        req   = Signal()

        req_byte = self.i_pkt.bit_select(Cat(C(0,3), self.i_nb) - 1, 1)

        # Copy in the packet when valid and ready
        with m.If(self.i_valid & self.o_ready):
            m.d.sync += [
                i_pkt.eq(self.i_pkt),
                addr.eq(self.i_pkt.bit_select(Cat(C(0,3), self.i_nb) - 16, 15)),
                req.eq(req_byte),
                i_nb.eq(Mux(req_byte == 1, self.i_nb - 2, self.i_pkt[:8] + 1)),
                self.o_nb.eq(self.i_pkt[:8]) # Only used for reads
            ]
        
        # We are ready when we have written all the bytes, and, for reads, the output has been acked
        m.d.comb += self.o_ready.eq((i_nb == 0) & ~self.o_valid)

        # Connect to memory
        m.d.comb += [
            w.en.eq((i_nb > 0) & (req == 1)),
            w.data.eq(i_pkt.word_select(i_nb - 1, 8)),
            w.addr.eq(addr),
            r.addr.eq(addr)
        ]

        # Decrement number of byte each cycle
        with m.If(i_nb > 0):
            m.d.sync += i_nb.eq(i_nb - 1)

        # Increment address for all but first byte
        with m.If(i_nb > 0):
            m.d.sync += addr.eq(addr+1)

        # For read requests, copy bytes to o_pkt
        with m.If(req == 0 & (i_nb > 0)):
            m.d.sync += self.o_pkt.word_select(self.pkt_size - 1 - self.o_nb + i_nb, 8).eq(r.data)

        # Set o_valid when reading last byte
        with m.If((req == 0) & (i_nb == 1)):
            m.d.sync += self.o_valid.eq(1)

        # Unset o_valid when acked
        with m.If(self.i_ack):
            m.d.sync += self.o_valid.eq(0)

        return m

