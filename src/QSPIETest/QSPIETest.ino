#include <MyStorm.h>
#include <QSPI.h>

#include "stm32l4_wiring_private.h"

#define PIN_DIRECTION PIN_BUTTON1

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(PIN_DIRECTION, INPUT);  // direction
  QSPI.begin(10000000, QSPI.Mode0);
  Serial.begin(9600);
  QSPI.beginTransaction();
}

static char tx_pkt[] = {0x0F, 0x23, 0x45, 0x67, 0x89, 0xab, 0xcd, 0xef,
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

    // Look for reads first
    if (digitalRead(PIN_DIRECTION) == 1) {
      // Read the event
      if (!QSPI.read(rx_pkt, 1))
        Serial.println("QSPI.receive failed");
      Serial.print("Event is 0x");
      Serial.println(rx_pkt[0], HEX);
            
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
    } else {
      // First do a read transaction to see if we can send
      if (!QSPI.read(rx_pkt, 1))
        Serial.println("QSPI.receive failed");
      Serial.print("Reply is 0x");
      Serial.println(rx_pkt[0], HEX);
      
      // Write to peripheral 0
      // If ready to send, write the packet
      if (rx_pkt[0] == 0xF0 || rx_pkt[0] == 0xB0) { // Temporary hack as we seem to receive B0
        Serial.println("Writing event 0");
        if (!QSPI.write(tx_pkt, 16))
          Serial.println("QSPI.transmit failed");
        // Rotate the packet
        char t = tx_pkt[15];
        for(int i=15;i>1;i--) tx_pkt[i] = tx_pkt[i-1];
        tx_pkt[1] = t;
      } else if (rx_pkt[0] != 0xFF && digitalRead(PIN_DIRECTION) == 1) {
        Serial.println("Switching to receive");
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
    }
    delay(1000);
  }
}

