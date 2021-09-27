#define Pin1 31
#define Pin2 33
#define Pin3 35

char data = 0;                //Variable for storing received data

char EMSOn = HIGH;
char EMSOff = LOW;


void setup()
{
  Serial.begin(9600);
  pinMode(Pin1, OUTPUT);
  pinMode(Pin2, OUTPUT);
  pinMode(Pin3, OUTPUT);
  digitalWrite(Pin1, EMSOff);
  digitalWrite(Pin2, EMSOff);
  digitalWrite(Pin3, EMSOff);
}
void loop()
{
  if (Serial.available() > 0) // Send data only when you receive data:
  {
    data = Serial.read();      //Read the incoming data and store it into variable data
    Serial.print(data);
    Serial.print("\n");
    if (data == 'A')
      digitalWrite(Pin1, EMSOn);
    else if (data == 'a')
      digitalWrite(Pin1, EMSOff);
    else if (data == 'B')
      digitalWrite(Pin2, EMSOn);
    else if (data == 'b')
      digitalWrite(Pin2, EMSOff);
    else if (data == 'C')
      digitalWrite(Pin3, EMSOn);
    else if (data == 'c')
      digitalWrite(Pin3, EMSOff);
  }
}
