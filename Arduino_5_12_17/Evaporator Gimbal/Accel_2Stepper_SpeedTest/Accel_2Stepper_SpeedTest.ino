//// Shows how to run AccelStepper in the simplest,
//// fixed speed mode with no accelerations
//// Requires the Adafruit_Motorshield v2 library
////   https://github.com/adafruit/Adafruit_Motor_Shield_V2_Library
//// And AccelStepper with AFMotor support
////   https://github.com/adafruit/AccelStepper
//
//
//#include <AccelStepper.h>
//#include <Wire.h>
//#include <Adafruit_MotorShield.h>
//#include "utility/Adafruit_MS_PWMServoDriver.h"
//
//// Create the motor shield object with the default I2C address
//Adafruit_MotorShield AFMS = Adafruit_MotorShield();
//
//// Connect a stepper motor with 200 steps per revolution (1.8 degree)
//Adafruit_StepperMotor *myStepper1 = AFMS.getStepper(200, 1);
//Adafruit_StepperMotor *myStepper2 = AFMS.getStepper(200, 2);
//
//#define DWELL 45 //number of minutes to wait before starting
//int go = 1;
//
//
//// you can change these to DOUBLE or INTERLEAVE or MICROSTEP!
//void forwardstep1() {
//  myStepper1->onestep(FORWARD, SINGLE);
//}
//void backwardstep1() {
//  myStepper1->onestep(BACKWARD, SINGLE);
//}
//
//// Functions to move second Stepper
//void forwardstep2() {
//  myStepper2->onestep(FORWARD, SINGLE);
//}
//void backwardstep2() {
//  myStepper2->onestep(BACKWARD, SINGLE);
//}
//
//AccelStepper stepper1(forwardstep1, backwardstep1); // use functions to step
//AccelStepper stepper2(forwardstep2, backwardstep2); // use functions to step
//
//void setup()
//{
//  Serial.begin(9600);           // set up Serial library at 9600 bps
//  Serial.println("Stepper test!");
//
//    AFMS.begin();  // create with the default frequency 1.6KHz
//  //AFMS.begin(2000);
//
//  //Stuff for the first rotation once the main loop starts
//    stepper1.setMaxSpeed(1000.0);
//    stepper1.setAcceleration(1000.0);
//    stepper1.moveTo(2000);
//  
//    stepper2.setMaxSpeed(2000.0);
//    stepper2.setAcceleration(1000.0);
//    stepper2.moveTo(2000);
//
//  //Speed when after the DWELL time
//    stepper1.setSpeed(1000);
//    stepper2.setSpeed(-1000);
//
//}
//
//void loop()
//{
// //Run Steppers when microcontroller and power are turned on
//  stepper1.run();
//
//  stepper1.setSpeed(100);
//  stepper1.step(10000,FORWARD,SINGLE);
//  delay(3000);
//
//  stepper1.setSpeed(250);
//  stepper1.step(10000,FORWARD,SINGLE);
//  delay(3000);
//
//  stepper1.setSpeed(500);
//  stepper1.step(10000,FORWARD,SINGLE);
//  delay(3000);
//  
////  stepper2.run();
////  delay(1000);  //delay for 1 second
//
////    // wait for [DWELL] minutes; for some reason, a single long delay didn't work...
////    for (int mins = 0; mins < DWELL; mins++)
////    {
////      //1 minute
////      for (int secs = 0; secs < 60; secs++)
////      {
////        delay(1000);  //delay for 1 second
////      } //for...secs
////    } //for...mins
////
////  while ( go == 1)
////  {
////    stepper1.runSpeed();
////    stepper2.runSpeed();
////  } //while...go
//
//} //void...loop



#include <AFMotor.h>


AF_Stepper motor(48, 2);


void setup() {
  Serial.begin(9600);           // set up Serial library at 9600 bps
  Serial.println("Stepper test!");

  motor.setSpeed(10);  // 10 rpm   

  motor.step(100, FORWARD, SINGLE); 
  motor.release();
  delay(1000);
}

void loop() {
  motor.step(100, FORWARD, SINGLE); 
  motor.step(100, BACKWARD, SINGLE); 

  motor.step(100, FORWARD, DOUBLE); 
  motor.step(100, BACKWARD, DOUBLE);

  motor.step(100, FORWARD, INTERLEAVE); 
  motor.step(100, BACKWARD, INTERLEAVE); 

  motor.step(100, FORWARD, MICROSTEP); 
  motor.step(100, BACKWARD, MICROSTEP); 
}
