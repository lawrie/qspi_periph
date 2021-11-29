from nmigen import *
from nmigen.build import *
from nmigen.utils import bits_for

from text import Text
from st7789 import ST7789

class LCD(Elaboratable):
    """ LCD text peripheral """
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

        # The text to display
        text = Signal(240)

        # OLED
        oled  = platform.request("oled")
        oled_clk  = oled.oled_clk
        oled_mosi = oled.oled_mosi
        oled_dc   = oled.oled_dc
        oled_resn = oled.oled_resn
        oled_csn  = oled.oled_csn

        st7789 = ST7789(150000)
        m.submodules.st7789 = st7789

        m.d.comb += [
            oled_clk .eq(st7789.spi_clk),
            oled_mosi.eq(st7789.spi_mosi),
            oled_dc  .eq(st7789.spi_dc),
            oled_resn.eq(st7789.spi_resn),
            oled_csn .eq(1),
        ]

        m.submodules.txt = txt = Text(fore_color=0x001f)

        m.d.comb += [
            txt.text.eq(text),
            txt.x.eq(st7789.x),
            txt.y.eq(st7789.y),
            st7789.color.eq(txt.color)
        ]

        # When valid input, copy to text
        with m.If(self.i_valid):
            m.d.sync += text.eq(self.i_pkt[:-8])

        # Always ready
        m.d.comb += self.o_ready.eq(1)

        return m

