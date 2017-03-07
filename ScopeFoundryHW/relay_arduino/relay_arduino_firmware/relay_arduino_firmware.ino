/*
Relay Shield Module by Alan Buckley

Commands:
"o" for Open (opens relay circuit) or,
"c" for Close (closes relay circuit), and
Numeric in range 1 through 4 which correspond to Relays/LEDs 1 through 4 respectively.

"?" Queries the board regarding the status of each pin.

Examples: 
"o4" opens relay circuit 4
"c1" closes relay circuit 1.

"?" gives a response much like the following:
"1010"
This set of four values correspond to pins 1 through 4 in ascending order.
This particular case tells you Relays 1 and 3 are active.

*/

#define RELAY1 7
#define RELAY2 6
#define RELAY3 5
#define RELAY4 4

int state_array[4] = {0,0,0,0};
const int state_array_size = 4;
String inputString = "";  //serial readout
boolean stringComplete = false; //string termination flag


void setup() {
  Serial.setTimeout(50);
  Serial.begin(9600);
  pinMode(RELAY1, OUTPUT);
  pinMode(RELAY2, OUTPUT);
  pinMode(RELAY3, OUTPUT);
  pinMode(RELAY4, OUTPUT);
}

void loop() {
    serial_parse();
    if (stringComplete) {
       //Serial.println(inputString);
       if (inputString[1] == '1') {
          if (inputString[0] == 'c') {
              digitalWrite(RELAY1, HIGH);
              state_array[0] = 1;
          }
          else if (inputString[0] == 'o') {
              digitalWrite(RELAY1, LOW);
              state_array[0] = 0;
          }  
       }
       
       else if (inputString[1] == '2') {
          if (inputString[0] == 'c') {
              digitalWrite(RELAY2, HIGH);
              state_array[1] = 1;
          }
          else if (inputString[0] == 'o') {
              digitalWrite(RELAY2, LOW);
              state_array[1] = 0;
          }
       }
       

       else if (inputString[1] == '3') {
          if (inputString[0] == 'c') {
              digitalWrite(RELAY3, HIGH);
              state_array[2] = 1;
          }
          else if (inputString[0] == 'o') {
              digitalWrite(RELAY3, LOW);
              state_array[2] = 0;
          }
       }

       else if (inputString[1] == '4') {
          if (inputString[0] == 'c') {
              digitalWrite(RELAY4, HIGH);
              state_array[3] = 1;
          }
          else if (inputString[0] == 'o') {
              digitalWrite(RELAY4, LOW);
              state_array[3] = 0;
          }
       }
       else if (inputString[0] == '?') {
          print_array();
       }

        inputString = "";
        stringComplete = false;
    }
}



// serial line handling
void serial_parse() {
    while (Serial.available()) {
          //readout
          char readout = (char)Serial.read();
          inputString += readout;
          if (readout == '\n') {
              stringComplete = true;
          }
       }
}

void print_array() {
    for (int i = 0; i < state_array_size; i++)
    {
      Serial.print(state_array[i]);
    }
    Serial.println("");
}


