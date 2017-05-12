/***************************************************
  This is an example for our Adafruit 16-channel PWM & Servo driver
  Servo test - this will drive 16 servos, one after the other

  Pick one up today in the adafruit shop!
  ------> http://www.adafruit.com/products/815

  These displays use I2C to communicate, 2 pins are required to
  interface. For Arduino UNOs, thats SCL -> Analog 5, SDA -> Analog 4

  Adafruit invests time and resources providing this open source code,
  please support Adafruit and open-source hardware by purchasing
  products from Adafruit!

  Written by Limor Fried/Ladyada for Adafruit Industries.
  BSD license, all text above must be included in any redistribution
 ****************************************************/

 



#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

// called this way, it uses the default address 0x40
Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Depending on your servo make, the pulse width min and max may vary, you
// want these to be as small/large as possible without hitting the hard stop
// for max range. You'll have to tweak them as necessary to match the servos you
// have!
//#define SERVOMIN  200 // this is the 'minimum' pulse length count (out of 4096)
//#define SERVOMAX  600 // this is the 'maximum' pulse length count (out of 4096)

void setup() {
  Serial.begin(9600);
  Serial.println("Limit Test for 180 Degree Servo");

  pwm.begin();

  pwm.setPWMFreq(60);  // Analog servos run at ~60 Hz updates
}




void loop() {
  int servoMin = 300;
  int servoMax = 300;
  int servoPos = 300;


  //Open up the servo monitor and type numbers...
  while (Serial.available() > 0) {
    //Manually type in single positions to tune out the servo
      servoPos = Serial.parseInt();
      Serial.println(servoPos);
      pwm.setPWM(0, 0, servoPos);


    //  //type in a csv; servoMin,servoMax eg 200,600 (enter)
    //  while (Serial.available() > 0) {
    //    servoMin = Serial.parseInt();
    //    servoMax = Serial.parseInt();
    //
    //    Serial.println(servoMin);
    //    Serial.println(servoMax);
    //    Serial.println();
    //
    //    Serial.println("Ramp up");
    //    for (uint16_t pulselen = servoMin; pulselen < servoMax; pulselen++) {
    //      pwm.setPWM(servonum, 0, pulselen);
    //    }
    //    delay(1000);
    //
    //    Serial.println("Ramp down");
    //    for (uint16_t pulselen = servoMax; pulselen > servoMin; pulselen--) {
    //      pwm.setPWM(servonum, 0, pulselen);
    //    }
    //    delay(1000);

  }



  /*
       // Drive each servo one at a time
    Serial.println(servonum);
    for (uint16_t pulselen = SERVOMIN; pulselen < SERVOMAX; pulselen++) {
    pwm.setPWM(servonum, 0, pulselen);
    }
    delay(500);
    for (uint16_t pulselen = SERVOMAX; pulselen > SERVOMIN; pulselen--) {
    pwm.setPWM(servonum, 0, pulselen);
    }
    delay(500);

    servonum ++;
    if (servonum > 2) servonum = 0; */

}
