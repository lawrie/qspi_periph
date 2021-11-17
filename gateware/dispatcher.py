from nmigen import *
from nmigen.utils import bits_for

from nmigen.lib.cdc import FFSynchronizer

from qspi_tx import QspiTx
from qspi_rx import QspiRx

class Dispatcher(Elaboratable):
    """ Interface between QSPI and peripherals """
    def __init__(self, pkt_size=16, num_periphs=15):
        # Parameters
        self.pkt_size    = pkt_size
        self.num_periphs = num_periphs
        
        # QSPI pins
        self.csn  =  Signal()                      # The chip select pin
        self.sclk =  Signal()                      # The QSPI clock pin
        self.qd_i =  Signal(4)                     # The QSPI pins in read mode
        self.qd_o =  Signal(4)                     # The QSPI pins in write mode
        self.qd_oe = Signal(reset=1)
        self.qdir =  Signal(reset=0)               # The direction pin. Zero means STM32 -> ice40 

        # Outputs
        self.led = Signal(4)

        # Peripherals
        self.periph    = [None] * num_periphs # Contains all peripherals
        self.rx_periph = [None] * num_periphs # Contains only peripheral that receive data from STM32
        self.tx_periph = [None] * num_periphs # Contains only peripherals that send data  to STM32

    # Register a peripheral with a specified id, and say whether it receives or sends data, or both
    def register(self, i, mod, rx, tx):
        self.periph[i] = mod
        if (rx):
            self.rx_periph[i] = mod
        if (tx):
            self.tx_periph[i] = mod

    # Elaboration
    def elaborate(self, platform):

        m = Module()

        # Constants
        ok_to_send = Const(0xF0, 8)
        not_ready  = Const(0xFF, 8)

        # Signals
        tx_pkt    = Signal(self.pkt_size * 8)  # Send packet buffer
        rx_pkt    = Signal(self.pkt_size * 8)  # Receive packet buffer
        rx_valid  = Signal()                   # Set when data has been received from STM
        periph_ev = Signal(4)                  # The event id for both directions

        # De-gltch sclk
        sclk = Signal()
        m.submodules += FFSynchronizer(i=self.sclk, o=sclk)

        # De-glitch cs
        csn = Signal()
        m.submodules += FFSynchronizer(i=self.csn, o=csn)

        # QSPI send and receive modules
        m.submodules.tx = tx = QspiTx(pkt_size = self.pkt_size)
        m.submodules.rx = rx = QspiRx(pkt_size = self.pkt_size)

        # Add the registered peripherals
        for p in self.periph:
            if p is not None:
                m.submodules += p
        
        # Connect the QSPI modules
        m.d.comb += [
            tx.csn.eq(csn),
            tx.sclk.eq(sclk),
            tx.pkt.eq(tx_pkt),
            self.qd_o.eq(tx.qd),
            rx.csn.eq(csn),
            rx.sclk.eq(sclk),
            rx.qd.eq(self.qd_i)
        ]

        m.d.comb += self.led.eq(self.periph[0].led)

        # Set valid for the selected rx_periph and set the input packet
        for i in range(self.num_periphs):
            p = self.rx_periph[i]
            if p is not None:
                m.d.comb += [
                    p.i_valid.eq(rx_valid & (periph_ev == i)),
                    p.i_pkt.eq(rx_pkt)
                ]

        # Set ack to false by default for all tx peripherals
        for p in self.tx_periph:
            if p is not None:
                m.d.sync += p.i_ack.eq(0)

        # State machine
        with m.FSM():
            with m.State("START"):
                m.d.sync += tx_pkt[-8:].eq(ok_to_send)
                m.next = "IDLE"
            # In the IDLE state, we are waiting for events.
            # The qdir pin is set to 0 to allow the STM to send data,
            # but qd.oe is set to 1, as the first transaction is always
            # a read transaction.
            # If csn goes low it means that the STM wants to send data and
            # has started a read transaction to check that it is OK to send.
            # This is the to cover the case where both ends want to send data
            # at the same time, and the case where the ice40 is not ready to receive.
            # If csn does not go low, we check whether any peripheral has data 
            # to send to the STM and if so, go to PERIPH_EVENT state.
            with m.State("IDLE"):
                # If a transaction has started send ok-to-send
                with m.If(~csn):
                    m.next = "OK_TO_SEND"
                # Otherwise look at all the registered tx peripherals to 
                # see if they have valid output, and set the peripheral event.
                # We also set qdir=1 to interrupt the STM32 to tell if we have data to send.
                with m.Else():
                    first = True
                    for i in range(self.num_periphs):
                        p = self.tx_periph[i]
                        if p is not None:
                            if first:
                                with m.If(p.o_valid):
                                    m.d.sync += [
                                        tx_pkt[-8:].eq(Cat(C(0,4), C(i,4))), # nbytes not yet used
                                        periph_ev.eq(i),
                                        self.qdir.eq(1)
                                    ]
                                    m.next = "SEND_EVENT"
                                first = False
                            else:
                                with m.Elif(p.o_valid):
                                    m.d.sync += [
                                        tx_pkt[-8:].eq(Cat(C(0,4), C(i, 4))),
                                        periph_ev.eq(i),
                                        self.qdir.eq(1)
                                    ]
                                    m.next = "SEND_EVENT"
            # In OK_TO_SEND state, the STM32 has started a transaction
            # to see if it is OK to send. Wait for csn to go high.
            with m.State("OK_TO_SEND"):
                with m.If(csn):
                    m.next = "WAIT_STM_DATA"
            # In WAIT_STM_DATA state, we are waiting for the STM to send
            # the data packet
            with m.State("WAIT_STM_DATA"):
                with m.If(~csn):
                    m.d.sync += self.qd_oe.eq(0) # Allow read from qd
                    m.next = "RECEIVING"
            # In RECEIVING state we receive the data via QSPI
            with m.State("RECEIVING"):
                with m.If(csn):
                    m.d.sync += [
                        rx_valid.eq(1), # We have valid data for the selected peripheral
                        rx_pkt.eq(rx.pkt),  # Copy the data to the packet buffer
                        self.qd_oe.eq(1), # Allow write to qd, by default
                        periph_ev.eq(rx.pkt[-4:]),
                        tx_pkt[-8:].eq(not_ready)
                    ]
                    m.next = "RECEIVE_HANDSHAKE"
            # IN RECEIVE_HANDSHAKE state, we wait for the selected peripheral to be ready
            # to consume the data, and then set valid false.
            # We then go to the WAIT_FOR_TXN state.
            with m.State("RECEIVE_HANDSHAKE"):
                for i in range(self.num_periphs):
                    p = self.rx_periph[i]
                    if p is not None:
                        with m.If((i == periph_ev) & p.o_ready):
                            m.d.sync += rx_valid.eq(0)
                            m.next = "WAIT_FOR_TXN"
            # In WAIT_FOR_TXN, we wait for the completion of any request to send
            # read transaction (that will have been replied to with not_ready),
            # before going back to the IDLE state
            with m.State("WAIT_FOR_TXN"):
                with m.If(csn):
                    m.d.sync += tx_pkt[-8:].eq(ok_to_send)
                    m.next = "IDLE"
            # In SEND_EVENT state, we wait for the read transaction to start.
            with m.State("SEND_EVENT"):
                with m.If(~csn):
                    m.next = "SENDING_EVENT"
            # In SENDING_EVENT state we wait for the end of the read transaction and then
            # go to the SEND DATA state to wait for the read transactiion for the data
            with m.State("SENDING_EVENT"):
                with m.If(csn):
                    m.next =  "PERIPH_EVENT"
            # In PERIPH_EVENT state, we copy the data from the selected peripheral,
            # to tx_pkt, ack the peripheral and go to SEND_EVENT state.
            with m.State("PERIPH_EVENT"):
                with m.Switch(periph_ev):
                    for i in range(self.num_periphs):
                        p = self.tx_periph[i]
                        if p is not None:
                            with m.Case(i):
                                m.d.sync += [
                                    tx_pkt.eq(self.tx_periph[i].o_pkt),
                                    self.tx_periph[i].i_ack.eq(1)
                                ]
                m.next = "SEND_DATA"
            # In SEND_DATA state we are waiting for the read transaction to start.
            with m.State("SEND_DATA"):
                with m.If(~csn):
                    m.next = "SENDING"
            # In SENDING mode, we are using QSPI to send the packet to the STM32.
            # When this is done, we set the direction back to STM32 -> ice40.
            with m.State("SENDING"):
                with m.If(csn):
                    m.d.sync += tx_pkt[-8:].eq(ok_to_send)
                    m.d.sync += self.qdir.eq(0)
                    m.next = "IDLE"

        return m

