/* Code for the Arduino EMS controller.
 *
 * This code enables the relays on the Arduino to be controlled and queried via
 * serial to allow digital switching of EMS from other programs.
 *
 * Supported commands:
 * Command                    Syntax              Return
 * Switch relay on            +<relay>            <Nothing>
 * Switch relay off           -<relay>            <Nothing>
 * Periodically pulse relay   !<relay><interval>  <Nothing>
 * Query relay state          ?<relay>            0 if off; 1 if on
 *
 * <relay>    must be one of 'A', 'B', 'C' or 'D' for relays 1-4, respectively.
 *            Currently, relay 1 maps to pin 35, 2 to 37, 3 to 39 and 4 to 41.
 * <interval> Must be an integer number of milliseconds to wait between
 *            switching the state of the given relay. The interval between
 *            successive switches should always be equal to or exceed this
 *            interval. Set to 0 to disable pulsing the relay. Note that the
 *            state of the relay after pulsing is stopped is not guaranteed.
 * Note:      All commands silently ignore invalid input while still consuming
 *            two bytes of data from the serial connection. However, this is
 *            reset every 100ms.
 */

const int PIN[4] = {35, 37, 39, 41};
const char EMS_ON = HIGH, EMS_OFF = LOW;

unsigned long last_pulse[4] = {0, 0, 0, 0};
long pulse_interval[4] = {0, 0, 0, 0};

void setup() {
  /* Setup code. */
  Serial.begin(9600);
  // Reduce serial read timeout or it causes too much of a delay.
  Serial.setTimeout(100);

  // Configure pins to be in output mode and set them to a known value.
  for (int i = 0; i < 4; i++) {
    pinMode(PIN[i], OUTPUT);
    digitalWrite(PIN[i], EMS_OFF);
  }
}

void loop() {
  /* Handle pulsing of relays.
   * Reading of commands is done in serialEvent().
   */
  for (int i = 0; i < 4; i++) {
    if (pulse_interval[i] > 0) {
      if (millis() - last_pulse[i] >= pulse_interval[i]) {
        if (digitalRead(PIN[i]) == LOW)
          digitalWrite(PIN[i], HIGH);
        else
          digitalWrite(PIN[i], LOW);
        last_pulse[i] = millis();
      }
    }
  }
}

void serialEvent() {
  /* Read commands over serial. */
  char cmdstr[2];
  int pinNo;

  // Commands are always at least two characters long.
  Serial.readBytes(cmdstr, 2);

  // Get the index of the pin to which the command refers.
  switch (cmdstr[1]) {
    case 'A':
      pinNo = 0;
      break;
    case 'B':
      pinNo = 1;
      break;
    case 'C':
      pinNo = 2;
      break;
    case 'D':
      pinNo = 3;
      break;
    default:
      // Erroneous pin.
      return;
  }

  // Act on the command.
  switch (cmdstr[0]) {
    case '+':
      // Allow EMS through relay.
      digitalWrite(PIN[pinNo], EMS_ON);
      break;
    case '-':
      // Block EMS through relay.
      digitalWrite(PIN[pinNo], EMS_OFF);
      break;
    case '!':
      // Pulse relay.
      pulse_interval[pinNo] = Serial.parseInt();
      break;
    case '?':
      // Query state of relay.
      Serial.println(digitalRead(PIN[pinNo]));
      break;
    default:
      // Erroneous command.
      return;
  }
}
