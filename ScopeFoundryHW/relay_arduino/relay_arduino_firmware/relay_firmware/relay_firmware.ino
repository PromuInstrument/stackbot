
/* Relay module rewritten by Lev Lozhkin */

#define NUM_RELAYS 4

#include <stdbool.h> // false
#include <Time.h> // time_t

// Follow style guide: https://www.arduino.cc/en/Reference/APIStyleGuide

typedef struct RELAY {
    // mapping between relay number, pin number, and channel
    byte num; // e.g. [1-4]
    byte pin; // e.g. [7-4]
    byte channel; // e.g. [0-3]

    // last set state of relay
    byte state; // LOW or HIGH

    // pulse config
    byte pulse_width;
    bool pulse_running; // true if pulse is ongoing
    time_t pulse_start_time;
} Relay;

// Relays and pulse being sent. Since we may be sending multiple pulses
// at the same time, we upkeep per-relay pulse config.
Relay RELAYS[NUM_RELAYS];

String INPUT_STRING = "";         // a String to hold incoming commands
boolean STRING_COMPLETE = false;  // whether current command is complete

// setup is called once to initialize program state
void setup() {
    Serial.setTimeout(50); // set maximum ms to wait for serial data
    Serial.begin(9600); // opens serial port, sets data rate to 9600 bps
    INPUT_STRING.reserve(20); // reserve 20 bytes for the INPUT_STRING

    // create relay structs and set relay pins as output
    for (int chan = 0; chan < NUM_RELAYS; chan++) {
        // map channel to relay to pin (e.g. chan: 0, relay: 1, pin: 7)
        int relay_num = chan + 1;
        int pin = 8 - relay_num;

        RELAYS[chan] = (Relay){relay_num, pin, chan, LOW, 10, false, 0};
        pinMode(pin, OUTPUT);
    }
}

// loop is called continuously, make sure to sleep
void loop() {
    handleCmd();
    timeCheck();
}

// serialEvent is called when data is available
void serialEvent() {
    while (Serial.available()) {
        char next = (char)Serial.read(); // get the next char
        INPUT_STRING += next;            // add to current input
        STRING_COMPLETE = next == '\n';  // signal end of input if reached
    }
}

void printRelays() {
    String delim = "|";
    for (int i = 0; i < NUM_RELAYS; i++) {
        Serial.print(delim + i);
        Serial.print(delim + RELAYS[i].state);
        Serial.print(delim + RELAYS[i].pulse_start_time);
        Serial.print(delim + RELAYS[i].pulse_running);
        Serial.println("");
    }
}

// write input to pin associated with given relay, record state
void writeToRelay(Relay &relay, int input) {
    digitalWrite(relay.pin, input);
    relay.state = input;
}

void startPulse(Relay &relay) {
    Serial.print("Relay ");
    Serial.println(relay.num);

    writeToRelay(relay, HIGH);
    relay.pulse_start_time = millis();
    relay.pulse_running = true;

    Serial.println("Pulse started");
}

void endPulse(Relay &relay) {
    Serial.print("Relay ");
    Serial.println(relay.num);

    writeToRelay(relay, LOW);
    relay.pulse_start_time = 0;
    relay.pulse_running = false;

    Serial.println("Pulse ended");
}

void clearCmd() {
    // clear the input buffer
    INPUT_STRING = "";
    STRING_COMPLETE = false;
}

void handleCmd() {
    if (!STRING_COMPLETE) return;

    // input expected of form 1c=0100
    if (INPUT_STRING.length() < 4) { // e.g. 1c=9
        Serial.print("Input string not long enough: ");
        Serial.println(INPUT_STRING);
        clearCmd();
        return;
    }

    // extract channel (int in range[0,3])
    int channel = INPUT_STRING[0] - '0'; // convert '1' (char) to 1 (int)
    if (channel < 0 || channel >= NUM_RELAYS) {
        Serial.print("Channel not in expected range: ");
        Serial.println(channel);
        clearCmd();
        return;
    }

    // extract mode (char in list ['c','o','t'])
    int mode = INPUT_STRING[1];
    Relay &relay = RELAYS[channel];

    switch (mode) {
        case 'c': writeToRelay(relay, HIGH); break;
        case 'o': writeToRelay(relay, LOW); break;
        case 't':
                  // extract pulse width (1c=100 -> 100)
                  relay.pulse_width = (byte)INPUT_STRING.substring(3).toInt();
                  startPulse(relay);
                  printRelays();
                  break;
        case '?':
                  printRelays();
                  break;
        default:
                  Serial.print("Unknown mode ");
                  Serial.println(mode);
    }

    clearCmd();
}

void timeCheck() {
    // Go through all relays and check if any pulses need to be ended, do so
    for (int i = 0; i < NUM_RELAYS; i++) {
        Relay &relay = RELAYS[i];
        time_t time_elapsed = millis() - relay.pulse_start_time;

        if (relay.pulse_running) {
            if (time_elapsed >= relay.pulse_width) {
                endPulse(relay);
                Serial.print("Time elapsed: ");
                Serial.println(time_elapsed);
            } else {
                Serial.print("Relay ");
                Serial.print(relay.num);
                Serial.print(" running pulse time: ");
                Serial.println(time_elapsed);
            }
        }
    }

    delay(1); // sleep a millisecond before checking for input again
}


