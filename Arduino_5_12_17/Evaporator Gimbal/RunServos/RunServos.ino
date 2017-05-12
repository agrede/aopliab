/***************************************************
  Try to accelerate the servo semi-continuously
 ****************************************************/
 //Servo 1 - modded (fixed) HobbyTon Tactic High Speed microservo
 //go CCW -> appears to be less friction; the puck doesn't jump
 //full CW = 290
 //slow CW = 350
 //stop = 369
 //slow CCW = 380
 //full CCW = 460
 // set to 600

 //Servo 2 - run at 600 CCW
 // full CW = 270
 // slow CW = 400
 // stop = 435
 // set to 600


#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();


#define SERVOMIN  117 // this is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  526 // this is the 'maximum' pulse length count (out of 4096)

#define STOPSPEED 0 // pulse length at which the continuous servo is stopped
#define FULLSPEED 600  // pulse length where we want to operate

#define DWELL 45 //number of minutes to wait before starting

  int servoC_1 = 0; //continous servo output on the board
  int servoC_2 = 1; //continous servo output on the board
  //int servoF_1 = 15; //180 Degree servo output on the board
  uint16_t pulselen = 0;
  uint16_t flipTime = 360;  //time for a full 180 degree rotation
  int go = 1;

  int minDegSweep = -90;
  int maxDegSweep = 90;

  
void setup() {
  Serial.begin(9600);
  Serial.println("Limit Test for 180 Degree Servo");

  pwm.begin();
  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
}

void loop() {
  //Before everything starts, stop movement on the continuous servo
    pwm.setPWM(servoC_1, 0, STOPSPEED);
    pwm.setPWM(servoC_2, 0, STOPSPEED);

  //and then have the fixed range servo do a sweep
//    pulselen = map(minDegSweep, -90, 90, SERVOMIN, SERVOMAX);
//    pwm.setPWM(servoF_1, 0, pulselen); delay(60); pwm.setPWM(servoF_1, 0, pulselen);
//    delay(flipTime);
//  
//    pulselen = map(maxDegSweep, -90, 90, SERVOMIN, SERVOMAX);
//    pwm.setPWM(servoF_1, 0, pulselen); delay(60); pwm.setPWM(servoF_1, 0, pulselen);
//    delay(flipTime);


  // wait for [DWELL] minutes; for some reason, a single long delay didn't work...
  for (int mins = 0; mins < DWELL; mins++)
  {
    //1 minute
    for (int secs = 0; secs < 60; secs++)
    {
      delay(1000);  //delay for 1 secod
    } //for...secs
  } //for...mins

//  delay(8000);
  while ( go == 1)
  {
    //Set the continuous servo to rotate
    pwm.setPWM(servoC_1, 0, FULLSPEED);
    pwm.setPWM(servoC_2, 0, FULLSPEED);

//    pulselen = map(minDegSweep, -90, 90, SERVOMIN, SERVOMAX);
//    pwm.setPWM(servoF_1, 0, pulselen); delay(60); pwm.setPWM(servoF_1, 0, pulselen);
//    delay(flipTime);
//
//    pulselen = map(maxDegSweep, -90, 90, SERVOMIN, SERVOMAX);
//    pwm.setPWM(servoF_1, 0, pulselen); delay(60); pwm.setPWM(servoF_1, 0, pulselen);
//    delay(flipTime);
  } //while...go



} //end - void loop

// Flip flop the other servo
//Serial.println("Ramp up");
//      for (int degs = minDegSweep; degs < 90; degs++) {
//        pulselen = map(degs,minDegCal,90, SERVOMIN, SERVOMAX);
//        pwm.setPWM(servoF_1, 0, pulselen);
//      }
//      delay(2000);
//
//      //Serial.println("Ramp down");
//      for (int degs = 90; degs > minDegSweep; degs--) {
//        pulselen = map(degs, minDegCal,90, SERVOMIN, SERVOMAX);
//        pwm.setPWM(servoF_1, 0, pulselen);
//      }
//      delay(2000);

