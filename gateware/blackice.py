from nmigen import *
from nmigen_boards.blackice_ii import *

from nmigen.build import *

from dispatcher import Dispatcher
from periph.led import Led
from periph.hello_tx import HelloTx
from periph.uart import Uart
from periph.sevseg import SevenRx
from periph.bram_periph import BramPeriph
from periph.lcd import LCD

from pll import PLL

qspi = [
    Resource("csn",  0, Pins("81", dir="i"),  Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("sclk", 0, Pins("82", dir="i"),  Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   0, Pins("83", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   1, Pins("84", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   2, Pins("79", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qd",   3, Pins("80", dir="io"), Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("qdir", 0, Pins("63", dir="o"),  Attrs(IO_STANDARD="SB_LBCMOS")),
    Resource("btn", 0,  Pins("64", dir="o"),  Attrs(IO_STANDARD="SB_LBCMOS"))
]

oled_pmod = [
    Resource("oled", 0,
            Subsignal("oled_clk",  Pins("7", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_mosi", Pins("8", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_resn", Pins("3", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_dc",   Pins("1", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")),
            Subsignal("oled_csn",  Pins("2", dir="o", conn=("pmod",2)), Attrs(IO_STANDARD="SB_LVCMOS")))
]

class QSPITest(Elaboratable):
    def __init__(self):
        self.dispatcher = Dispatcher()

        self.dispatcher.register(0, Led(), True,  False)
        self.dispatcher.register(1, HelloTx(),  False, True)
        self.dispatcher.register(2, Uart(), True,  True)
        self.dispatcher.register(3, SevenRx(),  True,  False)
        self.dispatcher.register(4, BramPeriph(),   True,  True)
        self.dispatcher.register(5, LCD(),   True,  False)

    def elaborate(self, platform):
        clk_in = platform.request(platform.default_clk, dir='-')[0]
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
        btn   = platform.request("btn")

        m = Module()

        # Clock generation
        m.submodules.pll = pll = PLL(freq_in_mhz=100, freq_out_mhz=50, domain_name="spi")
        m.d.comb += pll.clk_pin.eq(clk_in)
        m.d.comb += pll.rst_pin.eq(btn)
        m.domains.spi = pll.domain
        platform.add_clock_constraint(pll.domain.clk, 50000000)

        # Make sync domain
        m.domains.sync = cd_sync = ClockDomain("sync")
        m.d.comb += ClockSignal().eq(clk_in)
        platform.add_clock_constraint(cd_sync.clk, 100000000)

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
    platform.add_resources(oled_pmod)
    platform.build(QSPITest(), nextpnr_opts="--timing-allow-fail", do_program=True)

