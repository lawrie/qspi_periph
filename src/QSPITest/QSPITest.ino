#include <MyStorm.h>
#include <QSPI.h>

#include "stm32l4_wiring_private.h"

#define PIN_DIRECTION PIN_BUTTON1

void set_output() {
  pinMode(PIN_SPI2_SCK, OUTPUT);
  pinMode(PIN_SPI2_MISO, OUTPUT);
  pinMode(PIN_SPI2_MOSI, OUTPUT);
  pinMode(PIN_BUTTON2, OUTPUT);
}

void set_input() {
  pinMode(PIN_SPI2_SCK, INPUT);
  pinMode(PIN_SPI2_MISO, INPUT);
  pinMode(PIN_SPI2_MOSI, INPUT);
  pinMode(PIN_BUTTON2, INPUT);
}

void set_event(int n) {
  digitalWrite(PIN_SPI2_MOSI, n & 0x8);
  digitalWrite(PIN_SPI2_MISO, n & 0x4);
  digitalWrite(PIN_SPI2_SCK, n & 0x2);
  digitalWrite(PIN_BUTTON2, n & 0x1);
}

int get_event () {
  return (digitalRead(PIN_SPI2_MOSI) << 3) |
         (digitalRead(PIN_SPI2_MISO) << 2) |
         (digitalRead(PIN_SPI2_SCK) << 1) |
         digitalRead(PIN_BUTTON2);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PIN_DIRECTION, INPUT);  // direction
  // set_output();
  QSPI.begin(10000000, QSPI.Mode0);
  Serial.begin(9600);
  QSPI.beginTransaction();
}

static char tx_pkt[] = {0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
                        0x01, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef};

static char rx_pkt[17];

static bool configured = false;

static int cnt = 0;

void loop() {
  if (!Serial.available())
    return;
  if (!configured) {
    digitalWrite(LED_BUILTIN, 1);
    if (myStorm.FPGAConfigure(Serial)) {
      while (Serial.available())
        Serial.read();
      configured = true;
      Serial.println("Configured");
    }
    digitalWrite(LED_BUILTIN, 0);

  } else {
    // Main loop
    cnt++;
    Serial.print("Direction is ");
    Serial.println(digitalRead(PIN_DIRECTION));
    Serial.print("Event is ");
    Serial.println(get_event());

    // Look for reads first
    if (digitalRead(PIN_DIRECTION) == 1 && get_event() != 0xF) {
      set_input();
      Serial.print("Read event is ");
      Serial.println(get_event());
      
      if (get_event() != 0xF) {
        Serial.println("Reading");
        // Do a read
        if (!QSPI.read(rx_pkt, 16))
          Serial.println("QSPI.receive failed");

        // Print the received packet
        rx_pkt[16] = 0;
        Serial.println(rx_pkt);
        for(int i=0;i<16;i++) {
          Serial.print(rx_pkt[i],HEX);
          Serial.print(" ");
        }
        Serial.println();
      }
    } else if (digitalRead(PIN_DIRECTION) == 0) {
      Serial.println("Writing event 0");
      // Write to peripheral 0
      // First set event zero for a short period
      set_output();
      set_event(0);
      set_input();

      // If direction is still set for write then write packet
      if (digitalRead(PIN_DIRECTION) == 0) {
        // Then write the packet
        if (!QSPI.write(tx_pkt, 16))
          Serial.println("QSPI.transmit failed");
        // Rotate the packet
        char t = tx_pkt[15];
        for(int i=15;i>0;i--) tx_pkt[i] = tx_pkt[i-1];
        tx_pkt[0] = t;
      }
    }
    delay(1000);
  }
}

