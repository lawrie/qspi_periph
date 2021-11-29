from nmigen import *
from nmigen.utils import bits_for

from readbin import readbin

from math import log2, ceil, floor

def is_pow_2(x):
    return floor(log2(x)) == ceil(log2(x))

class Text(Elaboratable):
    def __init__(self,  
                 font="font_bizcat8x16.mem", font_width=8, font_depth=16,
                 x_res= 240, y_res = 240, text_len=240, 
                 fore_color=0xffff, back_color=0x0000, color_bits=16):
        # Parameter checks
        assert(font_width == 8)
        assert(font_depth == 16)
        assert(bits_for(fore_color) <= color_bits)
        assert(bits_for(back_color) <= color_bits)

        # Parameters
        self.font_width = font_width            # Width of font in pixels
        self.font_depth = font_depth            # Depth of font in pixels
        self.font       = font                  # Font file name
        self.x_res      = x_res                 # x resolution in pixels
        self.y_res      = y_res                 # y resolution in pixels
        self.x_bits     = bits_for(x_res)       # Number of bits for x value
        self.y_bits     = bits_for(y_res)       # Number of bits for y value
        self.color_bits = color_bits            # Color resolution
        self.fore_color = fore_color            # Foreground color
        self.back_color = back_color            # Background color

        # Inputs
        self.text  = Signal(text_len)           # The text to display
        self.x     = Signal(self.x_bits)        # The current x co-ordinate
        self.y     = Signal(self.y_bits)        # The curreny y co-ordinate

        # Outputs
        self.color = Signal(color_bits)         # The color of the pixel at the given co-ordinate

    def elaborate(self, platform):

        m = Module()

        # Read the font file and create memory
        init = readbin(self.font)
        oled_font = Memory(width=8, depth=len(init), init=init)
        m.submodules.r = r = oled_font.read_port()

        # Signals
        r_x1         = Signal(self.x_bits)
        r_x2         = Signal(self.x_bits)
        r_y1         = Signal(self.y_bits)
        r_y2         = Signal(self.y_bits)
        r_xdiv       = Signal(5)
        r_xmod       = Signal(3)
        r_xmod2      = Signal(3)
        r_pixel_on   = Signal()

        rows = 1

        # Stage 1
        m.d.sync += [
            r_xdiv.eq(self.x // self.font_width),
            r_xmod.eq(self.x % self.font_width),
            r_x1.eq(self.x),
            r_y1.eq(self.y)
        ]

        # Stage 2
        m.d.sync += [
            # This assumes font depth is 16
            r.addr.eq(Cat(r_y1[:4], self.text.word_select(r_xdiv, 8))),
            r_xmod2.eq(r_xmod),
            r_x2.eq(r_x1),
            r_y2.eq(r_y1)
        ]

        # Stage 3
        m.d.sync += [
            # This assumes font depth is 8
            r_pixel_on.eq(Mux(r_y2[4:] < rows, 
                              r.data.bit_select(r_xmod,1), 0))
        ]

        # Stage 4
        m.d.sync += [
            self.color.eq(Mux(r_pixel_on, self.fore_color, self.back_color))
        ]

        return m

