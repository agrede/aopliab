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

//Set up multiplexing shields
#define SHLDS 2
Adafruit_MCP23008 mcp[SHLDS];
byte mcpState[SHLDS];
String msg;

//Set up bluetooth shield
#include <SoftwareSerial.h>   //Software Serial Port
#define RxD 6
#define TxD 7
#define DEBUG_ENABLED  1
SoftwareSerial blueToothSerial(RxD,TxD);

void setup() {
  Serial.begin(9600); //begin serial communication
  pinMode(RxD, INPUT);
  pinMode(TxD, OUTPUT);
  setupBlueToothConnection();

  //Initialize all shields by setting multiplexer IO pins to outputs, then reset all of the relays on the shield
  for (int i=0; i<SHLDS; i++) {
    mcp[i].begin(i);
    rstShield(i);
  }
}//setup

void rstShield(int n) {

  for (int i = 0; i < 8; i++)
  {
    mcp[n].pinMode(i, OUTPUT);
    delay(5);
    mcp[n].digitalWrite(i, LOW);
    delay(5);
  } //outputs

  //reset all relays
  for (int i = 0; i < 5; i = i + 2)
  {
    mcp[n].digitalWrite(i, HIGH);
    delay(5);
    mcp[n].digitalWrite(i, LOW);
    delay(5);
  } //reset
  mcpState[n] = 0;
  setNewState(n, io(0));
}

//pulses the selected pin on and off
void pulse(int n, int gpio_pin) {
  delay(5);
  mcp[n].digitalWrite(gpio_pin, HIGH);
  delay(5);
  mcp[n].digitalWrite(gpio_pin, LOW);
}


void setNewState(int n, byte newState) {
  byte a = mcpState[n] ^ newState;
//  Serial.println(a, BIN);
//  Serial.println(newState, BIN);
//  Serial.println(mcpState[n], BIN);
  mcpState[n] = newState;
  int i = 0;
  while (a > 0) {
      pulse(n, 2*i + int(newState & 1));
    a = a >> 1;
    newState = newState >> 1;
    i++;
  }

}//pulse


void setupBlueToothConnection()
{
  blueToothSerial.begin(38400); //Set BluetoothBee BaudRate to default baud rate 38400
  blueToothSerial.print("\r\n+STWMOD=0\r\n"); //set the bluetooth work in slave mode
  blueToothSerial.print("\r\n+STNA=BTMultiplexer\r\n"); //set the bluetooth name as "SeeedBTSlave"
  blueToothSerial.print("\r\n+STOAUT=1\r\n"); // Permit Paired device to connect me
  blueToothSerial.print("\r\n+STAUTO=0\r\n"); // Auto-connection should be forbidden here
  delay(2000); // This delay is required.
  blueToothSerial.print("\r\n+INQ=1\r\n"); //make the slave bluetooth inquirable
  Serial.println("The slave bluetooth is inquirable!");
  delay(2000); // This delay is required.
  blueToothSerial.flush();
}


//Link variables from truth table to GPIO pins
byte io(byte pin)  {
  //invert first bit because x2 is inverted on the board
  //swap x1 and x0 because they are switched on the board
  //sum up all pins to turn on the ones that are necessary
  return ((~pin & B100) | ((pin & B010) >> 1) | ((pin & B001) << 1));
}

void loop() {
  //Initialize variables
  int shld = 0;
  byte pin = 0;
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

  
  while (1) {
    if((blueToothSerial.available())) {
    msg = blueToothSerial.readStringUntil('\n');
    Serial.println(msg);
    blueToothSerial.println(msg);
    
    if (msg.substring(0, 3) == "set")  {
      shld = msg.substring(4, 5).toInt();
      pin = io(byte(msg.substring(6, 7).toInt()));
      setNewState(shld, pin);
      Serial.print("Pin : ");
      blueToothSerial.print("Pin : ");
      
      Serial.println(io(pin));
      blueToothSerial.println(io(pin));

      
    } else if (msg == "rst") {
      for (int i = 0; i < SHLDS; i++) {
        rstShield(i);
      }
    } else if (msg == "state") {
      for (int i = 0; i < SHLDS; i++) {
        Serial.println(io(mcpState[i]));
        blueToothSerial.println(io(mcpState[i]));
      }
    }
  }//while(Serial.avail)
  }
}//loop

