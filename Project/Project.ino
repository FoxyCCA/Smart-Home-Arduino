#include <TimerOne.h>

#define whiteLed 13
#define buttonMotion 2
#define heatingRelay 11
#define coolingRelay 12
#define photo A0
#define lm35 A1

int temp; // temperature
int illum; // illumination
int numOfMovADay = 0; // movements 

String space = " "; 

// Timer ISR prints the tempearature, illumination and motion detection in the format (18 60 1)
void TimerISR(){
  Serial.println(temp + space + illum + space + numOfMovADay);
  numOfMovADay = 0; // reset the number of movements after printing to serial port
}

void setup() {
  Serial.begin(9600);

  pinMode(lm35, INPUT);
  pinMode(photo, INPUT);
  // whiteLed is also a relay
  pinMode(whiteLed, OUTPUT);
  pinMode(heatingRelay, OUTPUT);
  pinMode(coolingRelay, OUTPUT);
  pinMode(buttonMotion, INPUT);

  Timer1.initialize(60000000000); // 600 seconds or 10 minutes
  Timer1.attachInterrupt(TimerISR);
}

// Auto temperature control state
boolean atcState = false;
// light auto mode state
boolean lamState = false;
// home security mode state
boolean hsmState = false;
boolean heating = false;
boolean cooling = false;

// for button logic
int currentStatus;
int previousStatus = HIGH;

unsigned long motionTime = millis();
unsigned long atcTime = millis();
volatile boolean buttonState = false;
volatile boolean atcSystemState = true;
boolean motionDetected = false;

void loop() {
  temp = (analogRead(lm35)*500.0)/1023;
  illum = map(analogRead(photo), 0, 1023, 0, 100);

  if(Serial.available() > 0){
    String Serial_input = Serial.readString();

    // Serial communication control
    // heating over serial
    if(Serial_input == "heating on"){
      heating = true;
      cooling = false; 
      atcState = false;
    } else if(Serial_input == "heating off"){
      heating = false;
      atcState = false;

    // cooling over serial
    } else if(Serial_input == "cooling on"){
      cooling = true;
      heating = false;
      atcState = false;
    } else if(Serial_input == "cooling off"){
      cooling = false;
      atcState = false;

    // auto temperature control over serial
    } else if(Serial_input == "auto temperature control on"){
      heating = true;
      atcState = true;
    } else if (Serial_input == "auto temperature control off"){
      atcState = false;
      heating = false;
      cooling = false;

    // light auto mode over serial
    } else if (Serial_input == "light auto mode on"){
      lamState = true;
    } else if (Serial_input == "light auto mode off"){
      lamState = false;

    // home secure mode over serial
    } else if (Serial_input == "home secure mode on"){
      hsmState = true;
    } else if (Serial_input == "home secure mode off"){
      hsmState = false;

    // light on or off over serial
    } else if (Serial_input == "light on"){
      digitalWrite(whiteLed, HIGH);
      atcState = false;
    } else if (Serial_input == "light off"){
      digitalWrite(whiteLed, LOW);
      atcState = false;
    }
  }

  // logic for turning on the heater
  if(heating){
    digitalWrite(heatingRelay, HIGH);
  } else {
    digitalWrite(heatingRelay, LOW);
  }

  // logic for turning on the cooler 
  if(cooling){
    digitalWrite(coolingRelay, HIGH);
  } else {
    digitalWrite(coolingRelay, LOW);
  }

  // auto temperature control
  // if the temperature is above 23, the cooler turns on and the heater turns off
  // if the temperature is below 17, the cooler turns off and the heater turns on
  // the heater is just a resistor
  // the cooler is DC motor
  if(atcState){
    if(temp > 23){
      cooling = true;
      heating = false;
    } 
    if(temp < 17) {
      heating = true;
      cooling = false;
    }

    // if(atcSystemState){
    //   atcTime = millis() + 10000;
    //   atcSystemState = false;
    // }

    // if(millis() > atcTime){
    //   atcSystemState = true;
    //   heating = !heating;
    //   cooling = !cooling;
    // }
  }

  // light auto mode
  // if this is turned on, the relay turns the light on if the illumination is below 30
  if(lamState){
    if(illum < 30){
      digitalWrite(whiteLed, HIGH);
    } else {
      digitalWrite(whiteLed, LOW);
    }
  }

  // home secure mode
  // Since we dont have a PIR sensor, we use a button instead, if the button is pressed, it counts as motion being detected.
  if(hsmState){
    currentStatus = digitalRead(buttonMotion);

    if(currentStatus != previousStatus){
      if(currentStatus==LOW){
        //state = !state;
        numOfMovADay++;
        motionTime = millis() + 10000;
        
        // when motion is detected, the light turns on for 10 seconds
        // if the button is pressed again in that period the timer gets prolonged and another motion detection gets added to the counter.
        if(!motionDetected){
          Serial.println("motion");
          // this prints only after the cooldown is off, this serial text then gets
          // read by python to send an email that states that motion was detected
          motionDetected = true;
        }

      }
    }

    if(motionDetected){
      digitalWrite(whiteLed, HIGH);
    }

    // after 10 second the light turnes off
    if (millis() > motionTime && motionDetected) {
      digitalWrite(whiteLed, LOW);
      motionDetected = false;
    }
    previousStatus = currentStatus;
  }
}

