//#include <Wire.h>
//#include "Adafruit_MCP23008.h"
//
//// Basic toggle test for i/o expansion. flips pin #0 of a MCP23008 i2c
//// pin expander up and down. Public domain
//
//// Connect pin #1 of the expander to Analog 5 (i2c clock)
//// Connect pin #2 of the expander to Analog 4 (i2c data)
//// Connect pins #3, 4 and 5 of the expander to ground (address selection)
//// Connect pin #6 and 18 of the expander to 5V (power and reset disable)
//// Connect pin #9 of the expander to ground (common ground)
//
//// Output #0 is on pin 10 so connect an LED or whatever from that to ground
//
//Adafruit_MCP23008 mcp;
//  
//void setup() {  
//  Serial.begin(9600);
//  Serial.println("Initializing");
//  mcp.begin();      // use default address 0
//  mcp.pinMode(0, OUTPUT);
//
//  Serial.println("Moving to loop");
//}
//
//
//// flip the pin #0 up and down
//
//void loop() {
//  int msg;
//  delay(3000);
////
////  while (Serial.available() > 0) {
////        msg = Serial.readString();
////  
////    // set pin on
////    if(msg == "set_dwell")  {
////      msg = Serial.readString();
////      dwell_time = msg.toInt();
////      Serial.println(dwell_time);
////    }  //msg==set_dwell    
////
////  } // while...Serial.avail
//
//  mcp.digitalWrite(0, HIGH);
//  delay(3);
//  mcp.digitalWrite(0, LOW);
//
//  mcp.digitalWrite(0, HIGH);
//  delay(3);
//  mcp.digitalWrite(0, LOW);
//
//  if(msg == 1) {
//      Serial.println("flip");
//      msg = 0; }
//    else {
//      Serial.println("flop");
//      msg = 1;
//    }
//    
//}

#include <Wire.h>

void setup()
{
Wire.begin(); //creates a Wire object

// set I/O pins to outputs
Wire.beginTransmission(0x20); //begins talking to the slave device
Wire.write(0x00); //selects the IODIRA register
Wire.write(0x00); //this sets all port A pins to outputs
Wire.endTransmission(); //stops talking to device
}

void loop()
{
  while(1) {
    delay(3000);

    Wire.beginTransmission(0x20); //starts talking to slave device
    Wire.write(0x09); //selects the GPIO pins
    Wire.write(0x01); // turns on pins 0 and 1 of GPIOA

    delay(2);
    
    Wire.write(0x09); //selects the GPIO pins
    Wire.write(0x00); // turns on pins 0 and 1 of GPIOA

    delay(3000);
    
    Wire.beginTransmission(0x20); //starts talking to slave device
    Wire.write(0x09); //selects the GPIO pins
    Wire.write(0x02); // turns on pins 0 and 1 of GPIOA

    delay(2);
    
    Wire.write(0x09); //selects the GPIO pins
    Wire.write(0x00); // turns on pins 0 and 1 of GPIOA
    Wire.endTransmission();

  }
}
