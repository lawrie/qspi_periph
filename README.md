# QSPIE

Prototyping nMigen QSPIE peripheral events for LogicDeck board

## Introduction

QSPIE is an efficient method of communicating between the STM32 co-processor of the LogicDeck board and its ice40 FPGA using QSPI.

The pins used are:

- QSS     : Which indicates when a transaction is in progress
- QCLK    : The clock pin
- QD[3:0] : The 4 bi-directional data pins
- QDIR    : Which indicates the current direction of data transfer, and is used as an interupt from the ice40 to the STM32.

The STM32 side is the controller and the ice40 is the peripheral side.

However, the ice40 is in control of when data is transferred and in which direction, as it controls the QDIR pin.

Data is transferred in packets of up to 16 bytes using DMA on the STM32 side.

Before data can be transferred a single-byte packet is sent from the ice40 to indicate if it is ready to receive data, or to
specify what data it is ready to send.

The system supports up to 15 peripherals.

## Protocol

The IDLE state of the protocol has QDIR set to 0, which allows transfer from the STM32 to the ice40. But before the STM32 can send data, is reads one byte to see if the ice40 is ready to receive. There are three possible replies. The first two are OK-TO-SEND and NOT_READY. The third reply only happens when the STM32 and the ice40 simultanesouly require to send data, and in that case the reply is a request to receive data from a peripheral.

If the STM32 gets the OK-TO-SEND reply it sends a packet of data to the ice40. The first nibble of the packet is the peripheral to send to (0-14), and the second nibble are special flags, which the peripheral can use any way it wants. This first byte is followed by up to 15 bytes of data.

If the STM32 gets the NOT-READY reply it tries again after an optional wait.

If it gets a reply with the first nibble less than 0xF then the ice40 has requested to send data at the same time as the STM32, and the ice40 get precedence. In this case QDIR will have been set to 1.

If the STM32 gets a rising edge interrupt on QDIR, it means that the ice40 has data to send, so the STM32 reads a single byte (if it hasn't already started that). The first nibble of that byte is the peripheral (0 - 14) that is sending the data and the second nibble is the number of bytes of data to send (0 - 15, where 0 means 16 bytes).

The STM32 then starts a read transaction for the required number of bytes and passes the data to the STM32 code that deals with the selected peripheral.

When the data has been sent, the ice40 sets QDIR back to 0.

## nMigen ice40 implementation

The nMigen implementation consists of a dispatcher component that controls the QSPI interface and dispatches data to and from up to 15 registered peripherals.

Peripheral can be regiistered as RX peripheral that just receive data, or TX peripherals that just send data, or as both RX and TX. 

### Registering peripherals

Peripheral registration uses a register function of the dispatcher component. It will typically be done in the __init__ method of the top level nMigen component.

For example:

```python
    def __init__(self):
        self.dispatcher = Dispatcher()

        self.dispatcher.register(0, Led(), True,  False)
        self.dispatcher.register(1, HelloTx(),  False, True)
        self.dispatcher.register(2, Uart(), True,  True)
        self.dispatcher.register(3, SevenRx(),  True,  False)
        self.dispatcher.register(4, BramPeriph(),   True,  True)
        self.dispatcher.register(5, LCD(),   True,  False)
```        

The first parameter is the peripheral identifier, the second is the peripheral module, the third parameter is set fdor RX perpheral and the fourth for TX peripherals.

### Peripheral interface

For peripheral written in nmMgen, the interface is:

```python
    def __init__(self, pkt_size=16):
        # Parameters
        self.pkt_size = pkt_size

        # Inputs
        self.i_pkt    = Signal(self.pkt_size * 8)
        self.i_valid  = Signal()
        self.i_ack    = Signal()
        self.i_nb     = Signal()
        self.i_flags  = Signal(4)

        # Outputs
        self.o_ready  = Signal()
        self.o_valid  = Signal()
        self.o_pkt    = Signal(pkt_size * 8)
        self.o_nb     = Signal(5)tc
```

For RX peripheral a stream interface is used with the o_ready signal indicating that the peripheral is ready to receive data. When the dispatcher has data for the
peripheral it sets i_valid to true, i_nb to the number of bytes in the packet (0 - 15), i_pkt to the darta, and i_flags to the flags nibble.

Data is consumed when I-Valid and o_ready are asserted.

For TX peripherals, when data is ready to send to the STM32, o_valid, o_nb and o_pkt are set.

This data is consumed when the 10-cycle strobe, i_ack, is set.


### Prototype nMigen peripherals

The peripherals currently implemented are:

- LED:         An RX peripheral which put the last nibble of the packet sent on 4 leds
- HelloTx :    A TX peripheral which periodically sends a packet containing "Hello World!"
- Uart :       An RX and TX peripheral that reads and writes data using a uart connected to the ice40
- BramPeriph : An RX and TX peripheral that allows the STM32 to write bytes to BRAM and read them back
- LCD :        An RX peripheral that displays the packet of data received on an ST7789 LCD
- SevenRX :    An RX peripheral that displays a byte received as hex on a Digilent 7-segment Pmod

These are all in the gateware/periph directory.

## Blackice II implementation

A prototype interface has been produced for the Blackice II boards which supports QSPI from the STM32 to tthe ice40 - see gateware/blackice.py.

The STM32 side uses mystorm Arduino - see src/QSPIETest

![QSPIE](https://github.com/lawrie/lawrie.github.io/blob/master/images/qspie.jpg)

