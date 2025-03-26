#include <Wire.h>
#include <Adafruit_ADS1X15.h>

Adafruit_ADS1115 ads1115;

const int ADC_PIN = 34;
unsigned long previousMillis = 0;
const unsigned long freq = 10; //10ms = 100Hz

uint16_t photocell_read(){
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= freq){
    previousMillis = currentMillis;
    uint16_t adc0_raw = ads1115.readADC_SingleEnded(0);
    uint8_t normalized_val = map(adc0_raw, 0, 32767, 0, 100);
    return normalized_val;
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  ads1115.begin();
  ads1115.setGain(GAIN_TWO);
}

void loop() {
  uint8_t mapped_adc = photocell_read();
  Serial.println(mapped_adc);
}