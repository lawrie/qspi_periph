from nmigen import *
from readbin import readbin

class Hex(Elaboratable):
    def __init__(self, data_len=128, row_bits=4, font="hex_font.mem", x_bits=8, y_bits=8, 
                 fore_color=0xffff, back_color=0x0000, color_bits=16):
        # Parameters
        self.data_len   = data_len
        self.row_bits   = row_bits
        self.font       = font
        self.x_bits     = x_bits
        self.y_bits     = y_bits
        self.color_bits = color_bits
        self.fore_color = fore_color
        self.back_color = back_color

        # Inputs
        self.data  = Signal(data_len)
        self.x     = Signal(x_bits)
        self.y     = Signal(y_bits)

        # Outputs
        self.color = Signal(color_bits)

    def elaborate(self, platform):

        m = Module()

        # Read the font and create memory
        init = readbin(self.font)
        oled_font = Memory(width=6, depth=len(init), init=init)
        m.submodules.r = r = oled_font.read_port()

        # Signals
        r_x1         = Signal(self.x_bits)
        r_x2         = Signal(self.x_bits)
        r_y          = Signal(self.y_bits)
        r_xdiv       = Signal(self.row_bits)
        r_xmod       = Signal(3)
        r_xmod2      = Signal(3)
        r_pixel_on   = Signal()

        # Stage 1
        m.d.sync += [
            r_xdiv.eq(self.x // 6),
            r_xmod.eq(self.x % 6),
            r_x1.eq(self.x),
            r_y.eq(self.y)
        ]

        # Stage 2
        m.d.sync += [
            r.addr.eq(Cat(r_y[:3], self.data.word_select(r_xdiv, 4))),
            r_xmod2.eq(r_xmod),
            r_x2.eq(r_x1)
        ]

        # Stage 3
        m.d.sync += [
            r_pixel_on.eq(Mux((r_xmod2 < 5) & (r_x2 < (self.data_len * 3) // 2) , r.data.bit_select(r_xmod2,1), 0))
        ]

        # Stage 4
        m.d.sync += [
            self.color.eq(Mux(r_pixel_on, self.fore_color, self.back_color))
        ]

        return m

