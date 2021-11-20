from nmigen import *
from nmigen_boards.blackice_ii import *

from nmigen.build import *

from dispatcher import Dispatcher
from test_both import TestBoth
from hello_tx import HelloTx
from test_uart_tx import TestUartTx

qspi = [
    Resource("csn",  0, Pins("81", dir="i"),  Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("sclk", 0, Pins("82", dir="i"),  Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   0, Pins("83", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   1, Pins("84", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   2, Pins("79", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   3, Pins("80", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qdir", 0, Pins("63", dir="o"),  Attrs(IO_STANDARD="SB_LBCMOS"))
]

class QSPITest(Elaboratable):
    def __init__(self):
        self.dispatcher = Dispatcher()

        self.dispatcher.register(0, TestBoth(), True, True)
        self.dispatcher.register(1, HelloTx(), False, True)
        self.dispatcher.register(2, TestUartTx(), True, False)

    def elaborate(self, platform):
        led0  = platform.request("led", 0)
        led1  = platform.request("led", 1)
        led2  = platform.request("led", 2)
        led3  = platform.request("led", 3)
        csn   = platform.request("csn")
        sclk  = platform.request("sclk")
        qd0   = platform.request("qd", 0)
        qd1   = platform.request("qd", 1)
        qd2   = platform.request("qd", 2)
        qd3   = platform.request("qd", 3)
        qdir  = platform.request("qdir")

        m = Module()

        m.submodules.dispatch = dispatch = self.dispatcher

        # Connect the dispatcher
        m.d.comb += [
            dispatch.csn.eq(csn),
            dispatch.sclk.eq(sclk),
            qdir.eq(dispatch.qdir),
            dispatch.qd_i.eq(Cat([qd0.i, qd1.i, qd2.i, qd3.i])),
            Cat([qd0.o, qd1.o, qd2.o, qd3.o]).eq(dispatch.qd_o),
            qd0.oe.eq(dispatch.qd_oe),
            qd1.oe.eq(dispatch.qd_oe),
            qd2.oe.eq(dispatch.qd_oe),
            qd3.oe.eq(dispatch.qd_oe),
            Cat([led3, led2, led1, led0]).eq(dispatch.led)
        ]

        return m

if __name__ == "__main__":
    platform = BlackIceIIPlatform()
    platform.add_resources(qspi)
    platform.build(QSPITest(), do_program=True)

