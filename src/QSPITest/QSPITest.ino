#include <MyStorm.h>
#include <QSPI.h>

#define PIN_DIRECTION PIN_BUTTON2

void set_output() {
  pinMode(PIN_BUTTON2, OUTPUT);
  pinMode(PIN_SPI2_MOSI, OUTPUT);
  pinMode(PIN_SPI2_MISO, OUTPUT);
  pinMode(PIN_SPI2_SCK, OUTPUT);
}

void set_output() {
  pinMode(PIN_BUTTON2, INPUT);
  pinMode(PIN_SPI2_MOSI, INPUT);
  pinMode(PIN_SPI2_MISO, INPUT);
  pinMode(PIN_SPI2_SCK, INPUT);
}

void set_event(int n) {
  digitalWrite(PIN_BUTTON2, n & 0x8);
  digitalWrite(PIN_SPI2_MOSI, n & 0x4);
  digitalWrite(PIN_SPI2_MISO, n & 0x2);
  digitalWrite(PIN_SPI2_SCK, n & 0x1);
}

void get_event () {
  return digitalRead(PIN_BUTTON1) << 3 |
         digitalRead(PIN_SPI2_MOSI << 2 |
         digitalRead(PIN_SPI2_MISO << 1 |
         digitalRead(PIN_MODE_SCK);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PIN_DIRECTION, INPUT);  // direction
  setOutput();
  QSPI.begin(40000000, QSPI.Mode3);
  Serial.begin(9600);
  QSPI.beginTransaction();
}

static char[16] tx_pkt = {0x01, 0x23, 0x45, 0x67, 0x89, 0x89, 0xab, 0xcd, 0xef,
                          0x01, 0x23, 0x45, 0x67, 0x89, 0x89, 0xab, 0xcd, 0xef}

static char[17] rx_pkt;

void loop() {
  // Write to peripheral 0
  // First set event zero
  pinMode(PIN_DIRECTION, OUTPUT);
  set_event(0);
  pinMode(PIN_DIRECTION, INPUT);

  // Then write the packet
  if (!QSPI.write(tx_pkt, 16))
    Serial.println("QSPI.transmit failed");

  // Wait for direction to be set to 1
  Serial.println("Waiting for read request from ice40");
  while (digitalRead(PIN_DIRECTION) == 0);

  // Print the event
  Serial.println(get_event());

  // Then do a read
  if (!QSPI.read(rx_pkt, 16))
    Serial.println("QSPI.receive failed");

  // Print the received packet
  rx_pkt[16] = 0;
  Serial.println(rx_pkt);
}

