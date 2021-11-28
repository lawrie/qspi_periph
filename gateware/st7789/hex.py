from nmigen import *
from nmigen.utils import bits_for

from readbin import readbin

from math import log2, ceil, floor

def is_pow_2(x):
    return floor(log2(x)) == ceil(log2(x))

class Hex(Elaboratable):
    def __init__(self, data_len=256, hex_digits=32, 
                 font="hex_font.mem", font_width=6, font_depth=8,
                 x_res= 240, y_res = 240, 
                 fore_color=0xffff, back_color=0x0000, color_bits=16):
        # Parameter checks
        assert(is_pow_2(data_len))
        assert(is_pow_2(hex_digits))
        assert(hex_digits * font_width <= x_res)
        assert(font_depth == 8)
        assert(bits_for(fore_color) <= color_bits)
        assert(bits_for(back_color) <= color_bits)

        # Parameters
        self.data_len   = data_len              # Number of bits in data
        self.hex_digits = hex_digits            # Number of hex digits per row
        self.row_bits   = int(log2(hex_digits)) # Number of bits used for hex digit index
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
        self.data  = Signal(data_len)           # The data to display in hex
        self.x     = Signal(self.x_bits)        # The current x co-ordinate
        self.y     = Signal(self.y_bits)        # The curreny y co-ordinate

        # Outputs
        self.color = Signal(color_bits)         # The color of the pixel at the given co-ordinate

    def elaborate(self, platform):

        m = Module()

        # Read the font file and create memory
        init = readbin(self.font)
        oled_font = Memory(width=6, depth=len(init), init=init)
        m.submodules.r = r = oled_font.read_port()

        # Signals
        r_x1         = Signal(self.x_bits)
        r_x2         = Signal(self.x_bits)
        r_y1         = Signal(self.y_bits)
        r_y2         = Signal(self.y_bits)
        r_xdiv       = Signal(self.row_bits)
        r_xmod       = Signal(3)
        r_xmod2      = Signal(3)
        r_pixel_on   = Signal()

        # Constants
        row_size = (self.data_len * self.font_width) >> (int(log2(self.data_len)) - self.row_bits)
        rows = (self.data_len // 4) // self.hex_digits
        margin = (self.x_res - row_size) // 2

        # Centre the data
        x = self.x - margin

        # Stage 1
        m.d.sync += [
            r_xdiv.eq(x // self.font_width),
            r_xmod.eq(x % self.font_width),
            r_x1.eq(x),
            r_y1.eq(self.y)
        ]

        # Stage 2
        m.d.sync += [
            # This assumes font depth is 8
            r.addr.eq(Cat(r_y1[:3], self.data.word_select(Cat(r_xdiv, r_y1[3:]), 4))),
            r_xmod2.eq(r_xmod),
            r_x2.eq(r_x1),
            r_y2.eq(r_y1)
        ]

        # Stage 3
        m.d.sync += [
            # This assumes font depth is 8
            r_pixel_on.eq(Mux((r_xmod2 < (self.font_width - 1)) & (r_x2 < row_size) & (r_y2[3:] < rows), 
                              r.data.bit_select(self.font_width - 2 - r_xmod2[:self.font_width-1],1), 0))
        ]

        # Stage 4
        m.d.sync += [
            self.color.eq(Mux(r_pixel_on, self.fore_color, self.back_color))
        ]

        return m

