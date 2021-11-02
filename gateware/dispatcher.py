from nmigen import *

from qspi_tx import QspiTx
from qspi_rx import QspiRx

class Dispatcher(Elaboratable):
    def __init__(self, pkt_size=16, num_periphs=15):
        # Parameters
        self.pkt_size = pkt_size
        self.num_periphs = num_periphs
        
        # QSPI pins
        self.csn  = Signal()
        self.sclk = Signal()
        self.qd_i = Signal(4)
        self.qd_o = Signal(4)
        self.qdir = Signal()
        self.ev_i = Signal(4)
        self.ev_o = Signal(4)

        # Peripherals
        self.periph    = [None] * num_periphs
        self.rx_periph = [None] * num_periphs
        self.tx_periph = [None] * num_periphs

    def register(self, i, mod, rx, tx):
        self.periph[i] = mod
        if (rx):
            self.rx_periph[i] = mod
        if (tx):
            self.rx_periph[i] = mod

    def elaborate(self, platform):

        m = Module()

        pkt       = Signal(self.pkt_size)
        rx_valid  = Signal()
        periph_ev = Signal(4)

        m.submodules.tx = tx = QspiTx(pkt_size = self.pkt_size)
        m.submodules.rx = rx = QspiRx(pkt_size = self.pkt_size)

        for p in self.periph:
            if p is not None:
                m.submodules += p
                m.d.comb += p.i_pkt.eq(pkt)
        
        m.d.comb += [
            tx.csn.eq(self.csn),
            tx.sclk.eq(self.sclk),
            tx.qd.eq(self.qd_o),
            rx.csn.eq(self.csn),
            rx.sclk.eq(self.sclk),
            rx.qd.eq(self.qd_i)
        ]

        # Set valid for rx_periph
        for i in range(self.num_periphs):
            p = self.rx_periph[i]
            if p is not None:
                m.d.comb += p.i_valid.eq(rx_valid & (periph_ev == i))

        with m.FSM():
            with m.State("IDLE"):
                with m.If(self.ev_i != 0xf):
                    m.d.sync += periph_ev.eq(self.ev_i)
                    m.next = "STM_EVENT"
                with m.Else():
                    # look for valid output from tx_periph
                    for i in range(self.num_periphs):
                        p = self.tx_periph[i]
                        if p is not None:
                            with m.If(p.o_valid):
                                m.d.sync += [
                                    periph_ev.eq(i),
                                ]
                            m.next = "PERIPH_EVENT"
            with m.State("STM_EVENT"):
                with m.If(~self.csn):
                    m.next = "RECEIVING"
            with m.State("RECEIVING"):
                with m.If(self.csn):
                    m.d.sync += [
                        rx_valid.eq(1),
                        pkt.eq(rx.pkt)
                    ]
                    m.next = "RECEIVE_HANDSHAKE"
            with m.State("RECEIVE_HANDSHAKE"):
                for i in range(self.num_periphs):
                    p = self.rx_periph[i]
                    if p is not None:
                        with m.If((i == periph_ev) & p.o_ready):
                            m.d.sync += rx_valid.eq(0)
                            m.next = "IDLE"
            with m.State("PERIPH_EVENT"):
                with m.If(self.ev_i == 0xF):
                    with m.Switch(periph_ev):
                        for i in range(self.num_periphs):
                            p = self.tx_periph[i]
                            if p is not None:
                                with m.Case(i):
                                    m.d.sync += [
                                        pkt.eq(self.rx_periph[i].o_pkt),
                                        self.rx_periph[i].i_ack.eq(1)
                                    ]
                    m.d.sync += [
                        self.qdir.eq(1),
                        self.ev_o.eq(periph_ev)
                    ]
                    m.next = "SEND"
            with m.State("SEND"):
                with m.If(~self.csn):
                    m.next = "SENDING"
            with m.State("SENDING"):
                with m.If(self.csn):
                    m.d.sync += self.qdir.eq(0) # TODO: do this earlier?
                    m.next = "IDLE"

        return m

