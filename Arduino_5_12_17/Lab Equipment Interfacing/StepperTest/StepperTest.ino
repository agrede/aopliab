
#include <Wire.h>
#define CW HIGH
#define CCW LOW
#define stp_pin 8 // stepper trigger
#define dir_pin 9 // direction pin for big easy driver

#define driver_enable 4 // pull this pin low to enable the big easy driver
#define MS1 5 //motor control pin 1
#define MS2 6 //motor control pin 2
#define MS3 7 //motor control pin 3

int step_count = 0;
int avgs = 5;           //number of times to average
int dwell_time = 500;  //time to sit between points
int stps = 1;           //number of steps per trigger
int max_steps = 210;

void setup() {
  // Initialize serial communication
    Serial.begin(9600); 

  // Set up microstepping control pins - see big easy driver board
    pinMode(driver_enable, OUTPUT);
    digitalWrite(driver_enable, LOW);    // Low enables the driving FETs; high disables them
    
    pinMode(MS1, OUTPUT);
    pinMode(MS2, OUTPUT);
    pinMode(MS3, OUTPUT);
    digitalWrite(MS1, LOW);    // Pull down both all pins for no microstepping
    digitalWrite(MS1, LOW);    // Pull down both all pins for no microstepping
    digitalWrite(MS2, LOW);    // Pull down both all pins for no microstepping
    digitalWrite(MS3, LOW);    // Pull down both all pins for no microstepping
  
  // Set up stepper control pins
    pinMode(stp_pin, OUTPUT);   // Step controlling pin
    pinMode(dir_pin, OUTPUT);   // direction of steps
    digitalWrite(stp_pin, CW);  // Pull down both pins
    digitalWrite(dir_pin, CW);  // set direction to cw
} //setup...

//flipflop a pin with a 1 ms dwell; this triggers a step or the trigger
void trig_pin(int pin)  {
    digitalWrite(pin, HIGH);
    delay(1);          
    digitalWrite(pin, LOW); 
    delay(1);    
} //trig_pin...

// set the direction of a stepper and step
void single_step(int pin, int dir) {
  // set direction
    digitalWrite(dir_pin, dir);  //set direction
    delay(1);
  // step
    trig_pin(pin);
} //single_step...

// set the direction of a stepper and step
void n_step(int pin, int dir, int n) {
  // set direction
  digitalWrite(dir_pin, dir);  //set direction
  delay(1);
  //step n times
  for(int i=0; i<n; i++)  {
    trig_pin(pin);
  } //for...i
} //n_step...

// main loop
void loop() {
  String msg;
    
  //Open up the servo monitor and type numbers...
  while (Serial.available() > 0) {
      msg = Serial.readString();

// ********************************************************************

      // set number of averages
      if(msg == "set_avgs")  {
        msg = Serial.readString();
        avgs = msg.toInt();
        Serial.println(avgs);
      } //msg=set_avgs

      if(msg == "set_steps")  {
        msg = Serial.readString();
        stps = msg.toInt();
        Serial.println(stps);
      } //msg=set_steps

      // set dwell time
      if(msg == "set_dwell")  {
        msg = Serial.readString();
        dwell_time = msg.toInt();
        Serial.println(dwell_time);
      }  //msg==set_dwell    

// ********************************************************************

      if(msg == " ")  {
          for(int d = 0; d<max_steps; d++) {
          n_step(stp_pin,CW,stps);  // step the voltage
          step_count++;
          delay(dwell_time);        //wait
          Serial.println(step_count);
          }
        } //msg==single      

      
      if(msg == "reset") {
            n_step(stp_pin,CCW,stps*step_count);
            step_count = 0;
            Serial.println("Position has been reset");
       } //msg==reset
       
  } //while...serial.avail
  
} //void loop()

