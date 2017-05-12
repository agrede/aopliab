#include <Wire.h>
#include "Adafruit_MCP23008.h"
#include <SoftwareSerial.h>   //Software serial port for bluetooth shield

//Values for multiplexing shields
#define SHLDS 2                 //number of shields
Adafruit_MCP23008 mcp[SHLDS];   //array of multiplexer objects
byte mcpState[SHLDS];           //array of present pin states
String msg;

//Values for bluetooth shield
#define RxD 6
#define TxD 7
#define DEBUG_ENABLED  1

SoftwareSerial blueToothSerial(RxD, TxD);

void setup() {
  Serial.begin(9600);           //begin serial communication
  pinMode(RxD, INPUT);          //set Rx and Tx for bluetooth shield
  pinMode(TxD, OUTPUT);
  setupBlueToothConnection();   //Run bluetooth shield

  //reset the multiplexer relays
  for (int i = 0; i < SHLDS; i++) {
    mcp[i].begin(i);
    rstShield(i);
  }

}//setup

//Initialize all shields by setting multiplexer IO pins to outputs,
//then reset all of the relays on the shield
void rstShield(int n) {

  //set all multiplexer pins to outputs
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
}//rstShield

//pulses the selected pin on and off to switch the relay states
void pulse(int n, int gpio_pin) {
  delay(5);
  mcp[n].digitalWrite(gpio_pin, HIGH);
  delay(5);
  mcp[n].digitalWrite(gpio_pin, LOW);
}//pulse

//Set the relays to a new state
void setNewState(int n, byte newState) {
  byte a = mcpState[n] ^ newState;  //compare desired pins to presently set pins w/ bitwise XOR

  
  if (DEBUG_ENABLED) {
    Serial.println(a, BIN);
    Serial.println(newState, BIN);
    Serial.println(mcpState[n], BIN);
  } //if debug
  mcpState[n] = newState; //update the relay status

  //shift bit-by-bit and pulse the required pins
  int i = 0;
  while (a > 0) {
    pulse(n, 2 * i + int(newState & 1));
    a = a >> 1;
    newState = newState >> 1;
    i++;
  } //while...a


}//setNewState

//Initialize the bluetooth shield
void setupBlueToothConnection()
{
  blueToothSerial.begin(38400); //Set BluetoothBee BaudRate to default baud rate 38400
  blueToothSerial.print("\r\n+STWMOD=0\r\n"); //set the bluetooth work in slave mode
  blueToothSerial.print("\r\n+STNA=BTMultiplexer\r\n"); //set the bluetooth name as "BTMultiplexer"
  blueToothSerial.print("\r\n+CONN=9c,b6,d0,d7,cb,18\r\n"); // connect to PC
  blueToothSerial.print("\r\n+STOAUT=1\r\n"); // Permit Paired device to connect me
  blueToothSerial.print("\r\n+STAUTO=1\r\n"); // Auto-connection should be forbidden here
  delay(2000); // This delay is required.
  blueToothSerial.print("\r\n+INQ=1\r\n"); //make the slave bluetooth inquirable 
  Serial.println("The slave bluetooth is inquirable!");
  delay(2000); // This delay is required.
  blueToothSerial.flush();
}//setupBlueToothConnection


//Link variables from truth table to GPIO pins
//  invert first bit because x2 is inverted on the board
//  swap x1 and x0 because they are switched on the board
//  sum up all pins to turn on the ones that are necessary
byte io(byte pin)  {
  return ((~pin & B100) | ((pin & B010) >> 1) | ((pin & B001) << 1));
}//io

//three primary commands are:
//  "set n m", where n = shield address, and m = pin number, which sets the output pin on a shield to high
//  "rst", which resets the shield
//  "state", which polls the present pin status on a shield
void loop() {
  //Initialize variables
  int shld = 0;
  byte pin = 0;

  while (1) {
    if ((blueToothSerial.available())) {
      msg = blueToothSerial.readStringUntil('\n');
      if(DEBUG_ENABLED)
        Serial.println(msg);
      
      blueToothSerial.println(msg);

      //set pins
      if (msg.substring(0, 3) == "set")  {
        shld = msg.substring(4, 5).toInt(); //pull the shield address
        pin = io(byte(msg.substring(6, 7).toInt())); //convert the desired pin to the corresponding bits from the truth table
        setNewState(shld, pin);

        blueToothSerial.print("Pin : ");
        blueToothSerial.println(io(pin));
        if (DEBUG_ENABLED) {
          Serial.print("Pin : ");
          Serial.println(io(pin));
        } //if...debug

//reset
      } else if (msg == "rst") {
        for (int i = 0; i < SHLDS; i++) {
          rstShield(i);
        }//for...shlds

        //poll status
      } else if (msg == "state") {
        for (int i = 0; i < SHLDS; i++) {
          blueToothSerial.println(io(mcpState[i]));          
          if (DEBUG_ENABLED)
            Serial.println(io(mcpState[i]));
        }///for...shlds
        
      }//if...state
    }//if(btSerial.avail)
  }//while(1)
  
}//loop

