#include <MyStorm.h>
#include <QSPI.h>

#include "stm32l4_wiring_private.h"

#define PIN_DIRECTION PIN_BUTTON1

static char hello[] = "\x20" "Hello World!\n";

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

static char sev_pkt[] = {0x30, 0x00};

static char bram_write[] = {0x40, 0x80, 0x00, 0x30, 0x31, 0x32, 0x33, 0x34,
                            0x35, 0x36, 0x37, 0x38, 0x39, 0x40, 0x41};

static char bram_read[] = {0x40, 0x00, 0x00, 0x04};

static bool configured = false;

static int cnt = 0;

static char sev_val;

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

      int nb = rx_pkt[0] & 0xf;
      if (nb == 0) nb = 16;

      Serial.print("Number of bytes: ");
      Serial.println(nb);
      
      // Do a read
      if (!QSPI.read(rx_pkt, nb))
        Serial.println("QSPI.receive failed");

      // Print the received packet
      rx_pkt[nb] = 0;
      Serial.println(rx_pkt);
      for(int i=0;i<nb;i++) {
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
      
      // Write to peripheral 0 or 2 o2 3
      // If ready to send, write the packet
      if (rx_pkt[0] == 0xF0 || rx_pkt[0] == 0xB0) { // B0 is temporary hack
        if (cnt % 5 == 0) {
          Serial.println("Writing event 0");
          if (!QSPI.write(tx_pkt, 16))
            Serial.println("QSPI.transmit failed");
          // Rotate the packet
          char t = tx_pkt[15];
          for(int i=15;i>1;i--) tx_pkt[i] = tx_pkt[i-1];
          tx_pkt[1] = t;
        } else if (cnt % 5 == 1) {
          Serial.println("Writing event 0");
          if (!QSPI.write(hello, 14))
            Serial.println("QSPI.transmit failed");
        } else if (cnt % 5 == 2){
          Serial.println("Writing event 3");
          sev_pkt[1] = sev_val++;
          if (!QSPI.write(sev_pkt, 2))
            Serial.println("QSPI.transmit failed");          
        } else if (cnt % 5 == 3) {
          Serial.println("Writing event 4 (write)");
          if (!QSPI.write(bram_write, 15))
            Serial.println("QSPI.transmit failed");
        } else {
          Serial.println("Writing event 4 (read)");
          if (!QSPI.write(bram_read, 4))
            Serial.println("QSPI.transmit failed");
        }
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
    delay(500);
  }
}

