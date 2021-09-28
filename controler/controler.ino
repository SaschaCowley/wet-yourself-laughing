const int PIN_1 = 35, PIN_2 = 37, PIN_3 = 39, PIN_4 = 41;
const char EMS_ON = HIGH, EMS_OFF = LOW;

char data = 0;  // Variable for storing received data

void setup() {
  Serial.begin(9600);
  pinMode(PIN_1, OUTPUT);
  pinMode(PIN_2, OUTPUT);
  pinMode(PIN_3, OUTPUT);
  pinMode(PIN_4, OUTPUT);
  digitalWrite(PIN_1, EMS_OFF);
  digitalWrite(PIN_2, EMS_OFF);
  digitalWrite(PIN_3, EMS_OFF);
  digitalWrite(PIN_4, EMS_OFF);
}

void loop() {
  if (Serial.available() > 0)  // Send data only when you receive data:
  {
    // Read the incoming data and store it into variable data
    data = Serial.read();
    Serial.print(data);
    Serial.print("\n");
    if (data == 'A')
      digitalWrite(PIN_1, EMS_ON);
    else if (data == 'a')
      digitalWrite(PIN_1, EMS_OFF);
    else if (data == 'B')
      digitalWrite(PIN_2, EMS_ON);
    else if (data == 'b')
      digitalWrite(PIN_2, EMS_OFF);
    else if (data == 'C')
      digitalWrite(PIN_3, EMS_ON);
    else if (data == 'c')
      digitalWrite(PIN_3, EMS_OFF);
    else if (data == 'D')
      digitalWrite(PIN_4, EMS_ON);
    else if (data == 'd')
      digitalWrite(PIN_4, EMS_OFF);
  }
}
