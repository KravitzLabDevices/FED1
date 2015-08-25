#include <avr/sleep.h>
#include <avr/power.h>
#include <avr/wdt.h>
#include <SdFat.h>                // SD and RTC libraries
#include "RTClib.h"
#include <Wire.h>
#include <Stepper.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SharpMem.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <SoftwareSerial.h>


#define DISPLAY_SERIAL_RX_PIN 255 // we don't need a receive pin, 255 indicates this
// Connect the Arduino pin 3 to the rx pin on the 7 segment display
#define DISPLAY_SERIAL_TX_PIN 9

SoftwareSerial LEDserial = SoftwareSerial(DISPLAY_SERIAL_RX_PIN, DISPLAY_SERIAL_TX_PIN);
SdFat SD;


long previousMillis = 0;
long startTime = 0;
long timeElapsed = 0;
const long day2 = 86400000; // 86400000 milliseconds in a day
const long hour2 = 3600000; // 3600000 milliseconds in an hour
const long minute2 = 60000; // 60000 milliseconds in a minute
const long second2 =  1000; // 1000 milliseconds in a second

const int CS_pin = 10;
RTC_DS1307 RTC;    // refer to the real-time clock on the SD shield
String time;
File dataFile;

const int MOTOR_INPUT1_PIN = 7 ;
const int MOTOR_INPUT2_PIN = 6;
const int MOTOR_INPUT3_PIN = 5;
const int MOTOR_INPUT4_PIN = 4;
const int steps = 64;
const int MOTOR_STEPS_PER_REVOLUTION = 512;
const int MOTOR_ENABLE12_PIN = 8;
const int MOTOR_ENABLE34_PIN = 11;
const int TTL = 3;


int PIState = 1;
int lastState = 1;
int PIPin = 2;

int pelletCount = 0;

Stepper motor(MOTOR_STEPS_PER_REVOLUTION, MOTOR_INPUT1_PIN, MOTOR_INPUT2_PIN, MOTOR_INPUT3_PIN, MOTOR_INPUT4_PIN);

int logData() {
  String year, month, day, hour, minute, second;
  DateTime datetime = RTC.now();
  year = String(datetime.year(), DEC);
  month = String(datetime.month(), DEC);
  day  = String(datetime.day(),  DEC);
  hour  = String(datetime.hour(),  DEC);
  minute = String(datetime.minute(), DEC);
  second = String(datetime.second(), DEC);

  // concatenates the strings defined above into date and time
  time = month + "/" + day + " " + hour + ":" + minute + ":" + second;

  // opens a file on the SD card and prints a new line with the
  // current reinforcement schedule, the time stamp,
  // the number of sucrose deliveries, the number of active and
  // inactive pokes, and the number of drinking well entries.

  dataFile = SD.open("PELLETJuly.csv", FILE_WRITE);
  if (dataFile) {
    Serial.println(F("File successfully written..."));
    Serial.println(time);
    dataFile.print(time);
    dataFile.print(",");
    dataFile.print(pelletCount);
    dataFile.print(",");
    dataFile.println(timeElapsed);
    dataFile.close();
  }
}

void setMotorToTurn() {
    pinMode(MOTOR_INPUT1_PIN, OUTPUT);
    pinMode(MOTOR_INPUT2_PIN, OUTPUT);
    pinMode(MOTOR_INPUT3_PIN, OUTPUT);
    pinMode(MOTOR_INPUT4_PIN, OUTPUT);

    pinMode(MOTOR_ENABLE12_PIN, OUTPUT);
    pinMode(MOTOR_ENABLE34_PIN, OUTPUT);
    digitalWrite(MOTOR_ENABLE12_PIN, HIGH);
    digitalWrite(MOTOR_ENABLE34_PIN, HIGH);
}

void setMotorToSleep() 
{
    digitalWrite(MOTOR_ENABLE12_PIN, LOW);
    digitalWrite(MOTOR_ENABLE34_PIN, LOW);  

    pinMode(MOTOR_INPUT1_PIN, INPUT_PULLUP);
    pinMode(MOTOR_INPUT2_PIN, INPUT_PULLUP);
    pinMode(MOTOR_INPUT3_PIN, INPUT_PULLUP);
    pinMode(MOTOR_INPUT4_PIN, INPUT_PULLUP);
}

void setup()
{
  // make all unused pins inputs with pullups enabled by default, lowest power drain
  // leave pins 0 & 1 (Arduino RX and TX) as they are
  for (byte i=2; i <= 20; i++) {    
    pinMode(i, INPUT_PULLUP);     
  }
  ADCSRA = 0;  // disable ADC as we won't be using it

  Serial.begin(9600);
  Serial.println(F("Starting up..."));

  // Display setup
  LEDserial.begin(9600); 
  pinMode(DISPLAY_SERIAL_TX_PIN, OUTPUT);
  setDisplayBrightness(64);
  clearDisplay();
  delay(1); // allow a very short delay for display response
  setDisplayValues(pelletCount);
  
  pinMode(PIPin, INPUT);
  pinMode(TTL, OUTPUT);
  pinMode(CS_pin, OUTPUT);
  pinMode(SS, OUTPUT);

  Wire.begin();
  RTC.begin(); // RTC library needs Wire

  if (! RTC.isrunning()) {
    Serial.println(F("RTC is NOT running!"));
    // following line sets the RTC to the date & time this sketch was compiled
    RTC.adjust(DateTime(F(__DATE__), F(__TIME__)));
    // This line sets the RTC with an explicit date & time, for example to set
    // January 21, 2014 at 3am you would call:
    // rtc.adjust(DateTime(2014, 1, 21, 3, 0, 0));
  }

  if (!SD.begin(CS_pin)) {
    Serial.println(F("Card failed, or not present"));
    // don't do anything more:
    while (1) ;
  }

  Serial.println(F("Card initialized."));

  dataFile = SD.open("PELLETJuly.csv", FILE_WRITE);
  if (! dataFile) {
    Serial.println(F("Error opening datalog.txt"));
    // Wait forever since we cant write data
    while (1) ;
  }

  else {
    dataFile.print(time);
    dataFile.println(F("Time,Pellet Count,Pellet Drop Delay"));
    dataFile.close();
  }

  motor.setSpeed(35);
  delay (500);
}

void loop()
{
  PIState = digitalRead(PIPin);
  Serial.print("Photointerrupter State: ");
  Serial.println(PIState);
  digitalWrite(TTL, LOW);

  if (PIState == 1  & PIState != lastState) {
    setMotorToTurn();
  
    digitalWrite(TTL, HIGH);
    delay(50);
    digitalWrite(MOTOR_INPUT1_PIN, HIGH);
    digitalWrite(MOTOR_INPUT2_PIN, HIGH);
    digitalWrite(MOTOR_INPUT3_PIN, HIGH);
    digitalWrite(MOTOR_INPUT4_PIN, HIGH);
    startTime = millis();
    Serial.print(F("Time Elapsed Check: "));
    Serial.println(timeElapsed);
    timecounter(timeElapsed);
    logData();
    pelletCount ++;
    Serial.println(F("It did work"));
    clearDisplay();
    delay(1); // allow a very short delay for display response
    setDisplayValues(pelletCount);
    lastState = PIState;

  }
  else if (PIState == 1) {
    Serial.println(F("Turning motor..."));
    motor.step(-steps / 2);
    motor.step(steps);
    lastState = PIState;
  }
  
  else if (PIState == 0 & PIState != lastState) {
    Serial.print(F("Time Elapsed Since Last Pellet: "));
    timeElapsed = millis() - startTime;
    Serial.println(timeElapsed);
    lastState = PIState;
    
  }
    
  else  {
    lastState = PIState;
    digitalWrite(MOTOR_INPUT1_PIN, LOW);
    digitalWrite(MOTOR_INPUT2_PIN, LOW);
    digitalWrite(MOTOR_INPUT3_PIN, LOW);
    digitalWrite(MOTOR_INPUT4_PIN, LOW);
    setMotorToSleep();
    enterSleep();
  }
  
  delay(100);
}


void timecounter(long timeNow) {

  Serial.println(timeNow);
  int days = timeNow / day2 ;                                //number of days
  int hours = (timeNow % day2) / hour2;                       //the remainder from days division (in milliseconds) divided by hours, this gives the full hours
  int minutes = ((timeNow % day2) % hour2) / minute2 ;         //and so on...
  int seconds = (((timeNow % day2) % hour2) % minute2) / second2;
  int mil = ((((timeNow % day2) % hour2) % minute2) % second2);

  // digital clock display of current time
  printDigits(hours); Serial.print(":");
  printDigits(minutes); Serial.print(":");
  printDigits(seconds); Serial.print(":");
  printDigits(mil);
  Serial.println();

}

// utility function for digital clock display: prints colon and leading 0
void printDigits(byte digits) {
  if (digits < 10) {
    Serial.print('0');
  }
  Serial.print(digits, DEC);
}

void enterSleep()
{
  sleep_enable();

  attachInterrupt(0, pinInterrupt, RISING);
  lastState = 0;
  delay(100);

  set_sleep_mode(SLEEP_MODE_PWR_DOWN);   /* EDIT: could also use SLEEP_MODE_PWR_DOWN for lowest power consumption. */
  cli();
  sleep_bod_disable();
  sei();
  sleep_cpu();
  sleep_disable();
}

void pinInterrupt(void)
{
  detachInterrupt(0);

  /* The program will continue from here after the WDT timeout*/
  sleep_disable(); /* First thing to do is disable sleep. */

  /* Re-enable the peripherals. */
  power_all_enable();

}

// Send the clear display command (0x76)
//  This will clear the display and reset the cursor
void clearDisplay()
{
  LEDserial.write(0x76);  // Clear display command
}

// Set the displays brightness. Should receive byte with the value
//  to set the brightness to
//  dimmest------------->brightest
//     0--------127--------255
void setDisplayBrightness(byte value)
{
  LEDserial.write(0x7A);  // Set brightness command byte
  LEDserial.write(value);  // brightness data byte
}

void setDisplayValues(int value)
{
  LEDserial.print(value);
}

