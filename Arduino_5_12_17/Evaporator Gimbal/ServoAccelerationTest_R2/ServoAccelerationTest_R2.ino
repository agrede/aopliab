/***************************************************
  Try to accelerate the servo semi-continuously
 ****************************************************/

#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();


#define SERVOMIN  101 // this is the 'minimum' pulse length count (out of 4096)
#define SERVOMAX  532 // this is the 'maximum' pulse length count (out of 4096)

void setup() {
  Serial.begin(9600);
  Serial.println("Limit Test for 180 Degree Servo");

  pwm.begin();

  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
}

//F-001 - fixed 0-180 degree metal feedback micro servo from adafruit (BatanB2122)
//      min:101 (this isn't quite there, but going to 100 makes it jump several clicks and then start to bind)
//      max:532

//C-001 - continuous micro servo from adafruit (
//    0 = stopped
//    1 = half-speed clockwise
//    >2 = full speed
//    >~250 slows down incrementally
//    322 = bareky moving clockwise (jerky $ not smooth)
//    323-342 = no movement
//    343 = half-speed counterclockwise
//    400 = ~max speed


void loop() {
  int flipflop = 0; //0 = nothing; 1 = rotate back and forth
  int servonum = 1; //Servo output on the adafruit board
  uint16_t pulselen = 0;

  int minDegSweep = -89;
  int minDegCal = -89;

  //Open up the servo monitor and type numbers...
  while (Serial.available() > 0) {
    //Manually type in single positions to tune out the servo
    flipflop = Serial.parseInt();
    Serial.println(flipflop);
    //pulselength = map(degrees, 0, 180, SERVOMIN, SERVOMAX);



    if (flipflop = 1)
    {
      Serial.println("Ramp up");
      for (int degs = minDegSweep; degs < 90; degs++) {
        pulselen = map(degs,minDegCal,90, SERVOMIN, SERVOMAX);
        pwm.setPWM(servonum, 0, pulselen);
      }
      delay(500);

      Serial.println("Ramp down");
      for (int degs = 90; degs > minDegSweep; degs--) {
        pulselen = map(degs, minDegCal,90, SERVOMIN, SERVOMAX);
        pwm.setPWM(servonum, 0, pulselen);
      }
      delay(500);

      pulselen = map(0, minDegCal,90, SERVOMIN, SERVOMAX);
      pwm.setPWM(servonum, 0, pulselen); //reset to the middle
    }
    else
    {
      pwm.setPWM(servonum, 0, (SERVOMAX-SERVOMIN)/2);
    }
  }
}

