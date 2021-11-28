from nmigen import *
from nmigen.build import *
from nmigen_boards.blackice_ii import *

from  st7789 import *
from hex import Hex
from pll import PLL

oled_pmod = [
    Resource("oled", 0,
            Subsignal("oled_clk",  Pins("7", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_mosi", Pins("8", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_resn", Pins("3", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_dc",   Pins("1", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_csn",  Pins("2", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")))
]

class ST7789Test(Elaboratable):
    def elaborate(self, platform):
        m = Module()

        clk_in = platform.request(platform.default_clk, dir='-')[0]
        led = [platform.request("led", i) for i in range(4)]
        btn = platform.request("button",0)

        # Clock generation
        m.submodules.pll = pll = PLL(freq_in_mhz=100, freq_out_mhz=50)
        m.d.comb += pll.clk_pin.eq(clk_in)
        m.d.comb += pll.rst_pin.eq(btn)
        m.domains.sync = pll.domain

        # OLED
        oled  = platform.request("oled")
        oled_clk  = oled.oled_clk
        oled_mosi = oled.oled_mosi
        oled_dc   = oled.oled_dc
        oled_resn = oled.oled_resn
        oled_csn  = oled.oled_csn

        st7789 = ST7789(150000)
        m.submodules.st7789 = st7789
       
        #x = Signal(8)
        #y = Signal(8)
        #next_pixel = Signal()
 
        m.d.comb += [
            oled_clk .eq(st7789.spi_clk),
            oled_mosi.eq(st7789.spi_mosi),
            oled_dc  .eq(st7789.spi_dc),
            oled_resn.eq(st7789.spi_resn),
            oled_csn .eq(1),
            #next_pixel.eq(st7789.next_pixel),
            #x.eq(st7789.x),
            #y.eq(st7789.y),
        ]

        #with m.If(x[4] ^ y[4]):
        #    m.d.comb += st7789.color.eq(x[3:8] << 6)
        #with m.Else():
        #    m.d.comb += st7789.color.eq(y[3:8] << 11)

        m.submodules.hx = hx = Hex()
        d = Signal(64,reset=0x0123456789abcdef)

        m.d.comb += [
            hx.data.eq(Cat(d,d)),
            hx.x.eq(st7789.x),
            hx.y.eq(st7789.y),
            st7789.color.eq(hx.color)
        ]

        m.d.comb += [
            Cat([i.o for i in led]).eq(st7789.init)
        ]

        return m

if __name__ == "__main__":
    platform = BlackIceIIPlatform()
    
    # Add the OLED resource defined above to the platform so we
    # can reference it below.
    platform.add_resources(oled_pmod)

    platform.build(ST7789Test(), do_program=True)
