/*Simple signal Sampler
 * 
 * Author: Jason Francisco Macas Mora
 * Emai: franciscomacas3@gmail.com
*/

// ----------- PINS VARIABLES ---------
const int analogInput1 = A1;

// --------- SAMPLER VARIABLES --------
unsigned int Fs = 50; // Sample frequency (Hz)
const unsigned long SCALE_TIME_FACTOR = 1000; // 1000 -> ms | 1000000 -> us
unsigned long dt = SCALE_TIME_FACTOR / Fs; // Sample interval (ms)
unsigned long t = 0; 
unsigned long currentTime = 0;

const float voltageScaleFactor = 0.00488; // | Vcc / ADC_resolution | -> 5/1024

// -------- 
float variable = 0;

// -------- SAMPLER FUNCTIONS ---------

void sampleSignal(){
  
  // currentTime = micros(); // if you choose scaleTimeFactor = 1ˆ06
  currentTime = millis();
  
  if(currentTime - t >= dt){
     t = currentTime;
     variable = analogRead(analogInput1) * voltageScaleFactor;
     
     // As JSON
     //Serial.println("{\"x\": " + String(variable) + "}");   

     // Normal
     Serial.println(variable);
  }
  
}

void setup() {
  Serial.begin(9600);
}

void loop() {
  sampleSignal();
}
