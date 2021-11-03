from nmigen import *
from nmigen_boards.blackice_ii import *

from nmigen.build import *

from dispatcher import Dispatcher

qspi = [
    Resource("csn",  0, Pins("81", dir="o"),  Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("sclk", 0, Pins("82", dir="o"),  Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   0, Pins("83", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   1, Pins("84", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   2, Pins("79", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   3, Pins("80", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS"))
]

class QSPITest(Elaboratable):
    def elaborate(self, platform):
        led   = platform.request("led", 0)
        csn   = platform.request("csn")
        sclk  = platform.request("sclk")
        qd0   = platform.request("qd", 0)
        qd1   = platform.request("qd", 1)
        qd2   = platform.request("qd", 2)
        qd3   = platform.request("qd", 3)

        m = Module()

        m.submodules.dispatch = dispatch = Dispatcher()

        m.d.comb += [
            dispatch.csn.eq(csn),
            dispatch.sclk.eq(sclk),
            dispatch.qd_i.eq(Cat([qd0.i, qd1.i, qd2.i, qd3.i])),
            Cat([qd0.o, qd1.o, qd2.o, qd3.o]).eq(dispatch.qd_o)
        ]

        return m

if __name__ == "__main__":
    platform = BlackIceIIPlatform()
    platform.add_resources(qspi)
    platform.build(QSPITest(), do_program=True)

