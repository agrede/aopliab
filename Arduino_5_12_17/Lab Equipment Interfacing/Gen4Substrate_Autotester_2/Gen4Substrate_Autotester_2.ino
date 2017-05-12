#include <Wire.h>
#include "Adafruit_MCP23008.h"

// Basic toggle test for i/o expansion. flips pin #0 of a MCP23008 i2c
// pin expander up and down. Public domain

// Connect pin #1 of the expander to Analog 5 (i2c clock)
// Connect pin #2 of the expander to Analog 4 (i2c data)
// Connect pins #3, 4 and 5 of the expander to ground (address selection)
// Connect pin #6 and 18 of the expander to 5V (power and reset disable)
// Connect pin #9 of the expander to ground (common ground)

// Output #0 is on pin 10 so connect an LED or whatever from that to ground

Adafruit_MCP23008 mcp;
  
void setup() {  
  Serial.begin(9600); //begin serial communication
  mcp.begin(0);    // use default address 0

  //set all pins to outputs
  for(int i=0; i<8; i++)
  {
    mcp.pinMode(i, OUTPUT);
    delay(5);
    mcp.digitalWrite(i, LOW);
    delay(5);
  }

  //reset all relays
  for(int i=0; i<5; i=i+2)
  {
    mcp.digitalWrite(i, HIGH);
    delay(5);
    mcp.digitalWrite(i, LOW);
    delay(5);
  }
}//setup

//pulses the selected pin on and off
void pulse(int gpio_pin){
  delay(5);
  mcp.digitalWrite(gpio_pin, HIGH);
  delay(5);
  mcp.digitalWrite(gpio_pin, LOW);
}//pulse

////sets the inputs to the truth table
//void IO(int x0, int x1, int x2){
//  if(x0)
//    pulse(3);
//  else
//    pulse(2);
//  
//}

// flip the pin #0 up and down

void loop() {
  int pin;
  while(Serial.available() > 0){
    pin = Serial.readString().toInt();
    pulse(pin);

//    Serial.println(pin);
    
  }//while(Serial.avail)
}//loop














//
//  /*
//BluetoothShield Demo Code Slave.pde. This sketch could be used with
//Master.pde to establish connection between two Arduino. It can also
//be used for one slave bluetooth connected by the device(PC/Smart Phone)
//with bluetooth function.
//2011 Copyright (c) Seeed Technology Inc.  All right reserved.
// 
//Author: Steve Chang
// 
//This demo code is free software; you can redistribute it and/or
//modify it under the terms of the GNU Lesser General Public
//License as published by the Free Software Foundation; either
//version 2.1 of the License, or (at your option) any later version.
// 
//This library is distributed in the hope that it will be useful,
//but WITHOUT ANY WARRANTY; without even the implied warranty of 
//MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
//Lesser General Public License for more details.
// 
//You should have received a copy of the GNU Lesser General Public
//License along with this library; if not, write to the Free Software
//Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
// 
//For more details about the product please check http://www.seeedstudio.com/depot/
// 
//*/
// 
// 
///* Upload this sketch into Seeeduino and press reset*/
// 
//#include <SoftwareSerial.h>   //Software Serial Port
//#define RxD 6
//#define TxD 7
// 
//#define DEBUG_ENABLED  1
// 
//SoftwareSerial blueToothSerial(RxD,TxD);
// 
//void setup() 
//{ 
//  Serial.begin(9600);
//  pinMode(RxD, INPUT);
//  pinMode(TxD, OUTPUT);
//  setupBlueToothConnection();
// 
//} 
// 
//void loop() 
//{ 
//  char recvChar;
//  while(1){
//    if(blueToothSerial.available()){//check if there's any data sent from the remote bluetooth shield
//      recvChar = blueToothSerial.read();
//      Serial.print(recvChar);
//    }
//    if(Serial.available()){//check if there's any data sent from the local serial terminal, you can add the other applications here
//      recvChar  = Serial.read();
//      blueToothSerial.print(recvChar);
//    }
//  }
//} 
// 
//void setupBlueToothConnection()
//{
//  blueToothSerial.begin(38400); //Set BluetoothBee BaudRate to default baud rate 38400
//  blueToothSerial.print("\r\n+STWMOD=0\r\n"); //set the bluetooth work in slave mode
//  blueToothSerial.print("\r\n+STNA=BTMultiplexer\r\n"); //set the bluetooth name as "SeeedBTSlave"
//  blueToothSerial.print("\r\n+STOAUT=1\r\n"); // Permit Paired device to connect me
//  blueToothSerial.print("\r\n+STAUTO=0\r\n"); // Auto-connection should be forbidden here
//  delay(2000); // This delay is required.
//  blueToothSerial.print("\r\n+INQ=1\r\n"); //make the slave bluetooth inquirable 
//  Serial.println("The slave bluetooth is inquirable!");
//  delay(2000); // This delay is required.
//  blueToothSerial.flush();
//}
//
//
//
//*/
// */
