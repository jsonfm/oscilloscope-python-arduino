/*Simple signal Sampler
 * 
 * Author: Jason Francisco Macas Mora
 * Emai: franciscomacas3@gmail.com
*/

const int analogInput1 = A1;

unsigned int fs = 100; // Sample frequency (Hz)

const unsigned long scaleTimeFactor = 1000; // 1000 -> ms | 1000000 -> us
unsigned long dt = scaleTimeFactor / fs; // Sample Time 
unsigned long t = 0; // time
unsigned long currentTime = 0; // Actual

unsigned int variable = 0;

void sampleSignal(){
  
  // currentTime = micros(); // if you choose scaleTimeFactor = 1ˆ06
  currentTime = millis();
  
  if(currentTime - t >= dt){
     t = currentTime;
     variable = analogRead(analogInput1);
     Serial.println("{\"x\": " + String(variable) + "}");   
  }
  
}

void setup() {
  Serial.begin(9600);
}

void loop() {
  sampleSignal();
}