from nmigen import *
from nmigen.utils import bits_for

from qspi_tx import QspiTx
from qspi_rx import QspiRx

class Dispatcher(Elaboratable):
    """ Interface between QSPI and peripherals """
    def __init__(self, pkt_size=16, num_periphs=15):
        # Parameters
        self.pkt_size    = pkt_size
        self.num_periphs = num_periphs
        
        # QSPI pins
        self.csn  = Signal()                      # The chip select pin
        self.sclk = Signal()                      # The QSPI clock pin
        self.qd_i = Signal(4)                     # The QSPI pins in read mode
        self.qd_o = Signal(4)                     # The QSPI pins in write mode
        self.qdir = Signal(reset=0)               # The direction pin. Zero means STM32 -> ice40 
        self.ev_i = Signal(bits_for(num_periphs)) # The event lines in read mode. Selects a peripheral
        self.ev_o = Signal(bits_for(num_periphs)) # The event lines in write mode.

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

        # Signals
        pkt       = Signal(self.pkt_size)  # Packet buffer
        rx_valid  = Signal()               # Set when data has been received from STM
        periph_ev = Signal(4)              # The event id for both directions

        # QSPI send and receive modules
        m.submodules.tx = tx = QspiTx(pkt_size = self.pkt_size)
        m.submodules.rx = rx = QspiRx(pkt_size = self.pkt_size)

        # Add the registered peripherals
        for p in self.periph:
            if p is not None:
                m.submodules += p
        
        # Connect the QSPI modules
        m.d.comb += [
            tx.csn.eq(self.csn),
            tx.sclk.eq(self.sclk),
            tx.qd.eq(self.qd_o),
            rx.csn.eq(self.csn),
            rx.sclk.eq(self.sclk),
            rx.qd.eq(self.qd_i)
        ]

        # Set valid for the selected rx_periph and set the input packet
        for i in range(self.num_periphs):
            p = self.rx_periph[i]
            if p is not None:
                m.d.comb += [
                    p.i_valid.eq(rx_valid & (periph_ev == i)),
                    p.i_pkt.eq(pkt)
                ]

        # Set ack to false by default for all tx peripherals
        for p in self.tx_periph:
            if p is not None:
                m.d.sync += p.i_ack.eq(0)

        # State machine
        with m.FSM():
            # In the IDLE state the STM32 can write to the event pins. 
            # We are waiting for data to be sent from the STM32,
            # or a peripheral to have output data to send to the STM32
            with m.State("IDLE"):
                # If the STM32 sets an event, process the incoming data
                with m.If(~self.ev_i.all()):
                    m.d.sync += periph_ev.eq(self.ev_i)
                    m.next = "STM_EVENT"
                # Otherwise look at all the registered tx peripherals to 
                # see if they have valid output, and set the peripheral event.
                with m.Else():
                    first = False
                    for i in range(self.num_periphs):
                        p = self.tx_periph[i]
                        if p is not None:
                            if first:
                                with m.If(p.o_valid):
                                    m.d.sync += periph_ev.eq(i)
                                    m.next = "PERIPH_EVENT"
                                first = False
                            else:
                                with m.Elif(p.o_valid):
                                    m.d.sync += periph_ev.eq(i)
                                    m.next = "PERIPH_EVENT"
            # In STM_EVENT state, the STM32 is sending data
            # Wait for CSn to go low, to start receiving the data
            with m.State("STM_EVENT"):
                with m.If(~self.csn):
                    m.next = "RECEIVING"
            # In RECEIVING state we receive the data via QSPI
            with m.State("RECEIVING"):
                with m.If(self.csn):
                    m.d.sync += [
                        rx_valid.eq(1), # We have valid data for the selected peripheral
                        pkt.eq(rx.pkt)  # Copy the data to the packet buffer
                    ]
                    m.next = "RECEIVE_HANDSHAKE"
            # IN RECEIVE_HANDSHAKE state, we wait for the selected peripheral to be ready
            # to consume the data, and then set valid false.
            # We then go back to the IDLE state
            with m.State("RECEIVE_HANDSHAKE"):
                for i in range(self.num_periphs):
                    p = self.rx_periph[i]
                    if p is not None:
                        with m.If((i == periph_ev) & p.o_ready):
                            m.d.sync += rx_valid.eq(0)
                            m.next = "IDLE"
            # In PERIPH_EVENT state, we check for race condition where both sides try to
            # send data at the same time. The STM32 detects this and does the read instead.
            # But we must wait for the event lines to be pulled up when the STM32 sets input mode.
            # We can then go into SEND mode. 
            # We need to first copy the data from the peripheral to the packet buffer and acknowledge it.
            # Also before going into SEND mode, we set the direction to ice40 -> STM32 and set the
            # event lines to the id of the selected peripheral.
            with m.State("PERIPH_EVENT"):
                with m.If(self.ev_i.all()):
                    with m.Switch(periph_ev):
                        for i in range(self.num_periphs):
                            p = self.tx_periph[i]
                            if p is not None:
                                with m.Case(i):
                                    m.d.sync += [
                                        pkt.eq(self.tx_periph[i].o_pkt),
                                        self.tx_periph[i].i_ack.eq(1)
                                    ]
                    m.d.sync += [
                        self.qdir.eq(1),
                        self.ev_o.eq(periph_ev)
                    ]
                    m.next = "SEND"
            # In SEND mode we are waiting for the read transaction to start.
            with m.State("SEND"):
                with m.If(~self.csn):
                    m.next = "SENDING"
            # In SENDING mode, we are using QSPI to send the packet to the STM32.
            # When this is done, we set the direction back to STM32 -> ice40.
            with m.State("SENDING"):
                with m.If(self.csn):
                    m.d.sync += self.qdir.eq(0) # TODO: do this earlier?
                    m.next = "IDLE"

        return m

