from nmigen import *
from nmigen.build import *
from nmigen.utils import bits_for

seven_seg_pmod = [
    Resource("seven_seg", 0,
            Subsignal("aa", Pins("1", dir="o", conn=("pmod",4)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("ab", Pins("2", dir="o", conn=("pmod",4)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("ac", Pins("3", dir="o", conn=("pmod",4)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("ad", Pins("4", dir="o", conn=("pmod",4)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("ae", Pins("1", dir="o", conn=("pmod",3)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("af", Pins("2", dir="o", conn=("pmod",3)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("ag", Pins("3", dir="o", conn=("pmod",3)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("ca", Pins("4", dir="o", conn=("pmod",3)), Attrs(IO_STANDARD="SB_LVCMOS")))
]

class SevenRx(Elaboratable):
    """ Test of RX peripheral that write to seven segment display """
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # Inputs
        self.i_pkt    = Signal(self.pkt_size * 8)
        self.i_valid  = Signal()
        self.i_nb     = Signal()
        self.i_flags  = Signal(4)

        # Outputs
        self.o_ready  = Signal()

    def elaborate(self, platform):
        m = Module()

        # Add the Pmod
        platform.add_resources(seven_seg_pmod)

        # Get the pins
        seg_pins = platform.request("seven_seg")
        leds7 = Cat([seg_pins.aa, seg_pins.ab, seg_pins.ac, seg_pins.ad,
                     seg_pins.ae, seg_pins.af, seg_pins.ag])

        # The input value
        byte = Signal(8)

        # Timer
        timer = Signal(bits_for(int(platform.default_clk_frequency // 100)) + 1)
        m.d.sync += timer.eq(timer + 1)

        # Seven segment patterns
        vals = Array([
            0b0111111, # 0
            0b0000110, # 1
            0b1011011, # 2
            0b1001111, # 3
            0b1100110, # 4
            0b1101101, # 5
            0b1111101, # 6
            0b0000111, # 7
            0b1111111, # 8
            0b1101111, # 9
            0b1110111, # A
            0b1111100, # B
            0b0111001, # C
            0b1011110, # D
            0b1111001, # E
            0b1110001  # F
        ])

        # Connect pins 
        m.d.comb += [
            leds7.eq(Mux(timer[-1], vals[byte[4:]], vals[byte[:4]])),
            # Each digit refreshed at 100Hz
            seg_pins.ca.eq(timer[-1])
        ]

        # Set the byte when valid input
        with m.If(self.i_valid):
            m.d.sync += byte.eq(self.i_pkt[:8])
        
        # Always ready
        m.d.comb += self.o_ready.eq(1)


        return m

