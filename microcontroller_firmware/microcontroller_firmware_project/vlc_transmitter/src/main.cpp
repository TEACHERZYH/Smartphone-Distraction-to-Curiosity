#include <Arduino.h>
#include "vlc_protocol.h"

// ============================================================================
// State Variables & Global Buffers
// ============================================================================
static vlc_mode_t current_mode = VLC_MODE_FRAME_LOOP;
static uint32_t current_duty_val = VLC_DEFAULT_DUTY;  // Default 50% (128/255)
static char default_payload[] = "OK";
static vlc_frame_t tx_frame;

// FSM States for Bit-by-Bit Transmission
typedef enum {
    TX_STATE_PREAMBLE = 0,
    TX_STATE_DELIMITER,
    TX_STATE_LENGTH,
    TX_STATE_PAYLOAD,
    TX_STATE_GUARD_INTERVAL
} tx_fsm_state_t;

static tx_fsm_state_t fsm_state = TX_STATE_PREAMBLE;
static int current_byte_idx = 0;
static int current_bit_idx = 7;       // MSB first (bit 7 down to bit 0)
static unsigned long bit_start_time = 0;
static unsigned long last_btn_press = 0;

// ============================================================================
// Hardware Abstraction: LEDC PWM Control
// ============================================================================
void vlc_set_output_freq(uint32_t freq_hz, uint32_t duty) {
    if (freq_hz == 0 || duty == 0) {
        ledcWrite(VLC_PWM_CHANNEL, 0);
        return;
    }
    ledcSetup(VLC_PWM_CHANNEL, freq_hz, VLC_PWM_RESOLUTION);
    ledcWrite(VLC_PWM_CHANNEL, duty);
}

void vlc_turn_off() {
    ledcWrite(VLC_PWM_CHANNEL, 0);
}

// ============================================================================
// Protocol Assembly & Helper Functions
// ============================================================================
void vlc_build_frame(const char* text_payload) {
    tx_frame.preamble = VLC_FRAME_PREAMBLE;
    tx_frame.delimiter = VLC_FRAME_DELIMITER;
    
    size_t len = strlen(text_payload);
    if (len > VLC_MAX_PAYLOAD_LEN) {
        len = VLC_MAX_PAYLOAD_LEN;
    }
    tx_frame.length = (uint8_t)len;
    
    for (size_t i = 0; i < len; i++) {
        tx_frame.payload[i] = (uint8_t)text_payload[i];
    }
    tx_frame.total_bits = (3 + len) * 8;
    
    Serial.printf("[VLC] Frame assembled: Preamble=0x%02X, Delimiter=0x%02X, Len=%d, Payload=\"%s\" (%d bits)\r\n",
                  tx_frame.preamble, tx_frame.delimiter, tx_frame.length, text_payload, tx_frame.total_bits);
}

// Transmit a single logical bit (0 -> 250 Hz, 1 -> 500 Hz)
void vlc_transmit_bit(uint8_t bit_val) {
    uint32_t target_freq = (bit_val == 1) ? VLC_FREQ_BIT_1 : VLC_FREQ_BIT_0;
    vlc_set_output_freq(target_freq, current_duty_val);
}

// ============================================================================
// Non-blocking Transmission FSM Engine
// ============================================================================
void vlc_process_frame_fsm() {
    unsigned long now = millis();
    if (now - bit_start_time < VLC_SYMBOL_DURATION_MS) {
        return; // Current symbol still active
    }
    bit_start_time = now;

    uint8_t current_bit = 0;

    switch (fsm_state) {
        case TX_STATE_PREAMBLE:
            current_bit = (tx_frame.preamble >> current_bit_idx) & 0x01;
            vlc_transmit_bit(current_bit);
            current_bit_idx--;
            if (current_bit_idx < 0) {
                current_bit_idx = 7;
                fsm_state = TX_STATE_DELIMITER;
            }
            break;

        case TX_STATE_DELIMITER:
            current_bit = (tx_frame.delimiter >> current_bit_idx) & 0x01;
            vlc_transmit_bit(current_bit);
            current_bit_idx--;
            if (current_bit_idx < 0) {
                current_bit_idx = 7;
                fsm_state = TX_STATE_LENGTH;
            }
            break;

        case TX_STATE_LENGTH:
            current_bit = (tx_frame.length >> current_bit_idx) & 0x01;
            vlc_transmit_bit(current_bit);
            current_bit_idx--;
            if (current_bit_idx < 0) {
                current_bit_idx = 7;
                current_byte_idx = 0;
                fsm_state = (tx_frame.length > 0) ? TX_STATE_PAYLOAD : TX_STATE_GUARD_INTERVAL;
            }
            break;

        case TX_STATE_PAYLOAD:
            current_bit = (tx_frame.payload[current_byte_idx] >> current_bit_idx) & 0x01;
            vlc_transmit_bit(current_bit);
            current_bit_idx--;
            if (current_bit_idx < 0) {
                current_bit_idx = 7;
                current_byte_idx++;
                if (current_byte_idx >= tx_frame.length) {
                    fsm_state = TX_STATE_GUARD_INTERVAL;
                }
            }
            break;

        case TX_STATE_GUARD_INTERVAL:
            vlc_turn_off(); // Extinguish LED during dark guard time
            if (now - bit_start_time >= VLC_GUARD_INTERVAL_MS) {
                // Reset FSM to repeat transmission
                fsm_state = TX_STATE_PREAMBLE;
                current_byte_idx = 0;
                current_bit_idx = 7;
                bit_start_time = millis();
                Serial.println("[VLC] --- Frame Cycle Completed. Restarting next iteration ---");
            }
            break;
    }
}

// ============================================================================
// Mode Execution & Serial Command Processor (CLI)
// ============================================================================
void vlc_switch_mode(vlc_mode_t new_mode) {
    current_mode = new_mode;
    fsm_state = TX_STATE_PREAMBLE;
    current_byte_idx = 0;
    current_bit_idx = 7;

    switch (current_mode) {
        case VLC_MODE_FRAME_LOOP:
            Serial.printf("[MODE] Mode 1: 40-bit 2FSK Frame Loop (Payload: \"%s\", Symbol=%dms)\r\n", 
                          default_payload, VLC_SYMBOL_DURATION_MS);
            digitalWrite(VLC_LED_STATUS_PIN, HIGH);
            break;
        case VLC_MODE_CW_250HZ:
            Serial.println("[MODE] Mode 2: Continuous Wave 250 Hz (Logic '0' Calibration Baseline)");
            vlc_set_output_freq(VLC_FREQ_BIT_0, current_duty_val);
            digitalWrite(VLC_LED_STATUS_PIN, LOW);
            break;
        case VLC_MODE_CW_500HZ:
            Serial.println("[MODE] Mode 3: Continuous Wave 500 Hz (Logic '1' Calibration Baseline)");
            vlc_set_output_freq(VLC_FREQ_BIT_1, current_duty_val);
            digitalWrite(VLC_LED_STATUS_PIN, LOW);
            break;
        case VLC_MODE_DUTY_CHALLENGE:
            Serial.println("[MODE] Mode 4: Duty Cycle Challenge (Cycling 25% -> 50% -> 75%)");
            break;
        case VLC_MODE_STANDBY:
            Serial.println("[MODE] Mode 5: Standby (LED Off)");
            vlc_turn_off();
            digitalWrite(VLC_LED_STATUS_PIN, LOW);
            break;
    }
}

void process_serial_command(String cmd) {
    cmd.trim();
    if (cmd.length() == 0) return;

    if (cmd.equalsIgnoreCase("HELP")) {
        Serial.println("=================================================");
        Serial.println(" VLC / OCC Optical Transmitter CLI Commands:     ");
        Serial.println("   HELP               - Display command menu    ");
        Serial.println("   MODE <1-5>         - Switch working mode     ");
        Serial.println("   SEND <string>      - Update payload (max 32) ");
        Serial.println("   DUTY <25|50|75>    - Adjust square wave duty ");
        Serial.println("   STATUS             - Print current parameters");
        Serial.println("=================================================");
    } else if (cmd.startsWith("MODE ") || cmd.startsWith("mode ")) {
        int m = cmd.substring(5).toInt();
        if (m >= 1 && m <= 5) {
            vlc_switch_mode((vlc_mode_t)(m - 1));
        } else {
            Serial.println("[ERR] Invalid mode. Choose 1 to 5.");
        }
    } else if (cmd.startsWith("SEND ") || cmd.startsWith("send ")) {
        String new_text = cmd.substring(5);
        new_text.replace("\"", "");
        new_text.trim();
        vlc_build_frame(new_text.c_str());
        vlc_switch_mode(VLC_MODE_FRAME_LOOP);
    } else if (cmd.startsWith("DUTY ") || cmd.startsWith("duty ")) {
        int pct = cmd.substring(5).toInt();
        if (pct >= 10 && pct <= 90) {
            current_duty_val = (uint32_t)(pct * 255.0 / 100.0);
            Serial.printf("[CFG] Duty cycle updated to %d%% (LEDC val: %d)\r\n", pct, current_duty_val);
            if (current_mode == VLC_MODE_CW_250HZ) vlc_set_output_freq(VLC_FREQ_BIT_0, current_duty_val);
            if (current_mode == VLC_MODE_CW_500HZ) vlc_set_output_freq(VLC_FREQ_BIT_1, current_duty_val);
        } else {
            Serial.println("[ERR] Duty must be between 10% and 90%.");
        }
    } else if (cmd.equalsIgnoreCase("STATUS")) {
        Serial.printf("[STATUS] Mode: %d | Duty: %d/255 | F0: %d Hz | F1: %d Hz | Pin: GPIO%d\r\n",
                      (int)current_mode + 1, current_duty_val, VLC_FREQ_BIT_0, VLC_FREQ_BIT_1, VLC_PWM_PIN);
    } else {
        Serial.println("[ERR] Unknown command. Type 'HELP' for instructions.");
    }
}

// ============================================================================
// Arduino Setup & Main Loop
// ============================================================================
void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("\r\n============================================================");
    Serial.println("  Cross-Modal Signal Lab: VLC/OCC Transmitter Firmware v2.1  ");
    Serial.println("  Target: ESP32 Core Board | Modulation: 2FSK (250/500 Hz)   ");
    Serial.println("  Author: Engineering Education Laboratory Teaching Team     ");
    Serial.println("============================================================\r\n");

    pinMode(VLC_BUTTON_PIN, INPUT_PULLUP);
    pinMode(VLC_LED_STATUS_PIN, OUTPUT);
    digitalWrite(VLC_LED_STATUS_PIN, LOW);

    // Initialize LEDC PWM Peripheral on GPIO4
    ledcAttachPin(VLC_PWM_PIN, VLC_PWM_CHANNEL);
    
    // Assemble initial default frame: "OK"
    vlc_build_frame(default_payload);
    vlc_switch_mode(VLC_MODE_FRAME_LOOP);

    bit_start_time = millis();
}

void loop() {
    // 1. Check Button for Physical Mode Cycling
    if (digitalRead(VLC_BUTTON_PIN) == LOW) {
        if (millis() - last_btn_press > 350) { // Software debounce
            last_btn_press = millis();
            int next_mode = ((int)current_mode + 1) % 5;
            vlc_switch_mode((vlc_mode_t)next_mode);
        }
    }

    // 2. Process FSM according to active mode
    if (current_mode == VLC_MODE_FRAME_LOOP) {
        vlc_process_frame_fsm();
    } else if (current_mode == VLC_MODE_DUTY_CHALLENGE) {
        // Automatically cycle duty: 25% for 4s, 50% for 4s, 75% for 4s
        static unsigned long duty_timer = 0;
        static int duty_state = 0;
        if (millis() - duty_timer > 4000) {
            duty_timer = millis();
            duty_state = (duty_state + 1) % 3;
            uint32_t test_duty = (duty_state == 0) ? 64 : ((duty_state == 1) ? 128 : 192);
            Serial.printf("[DUTY-CHALLENGE] Stepping Duty to: %d%% (LEDC: %d)\r\n", 
                          (duty_state == 0) ? 25 : ((duty_state == 1) ? 50 : 75), test_duty);
            vlc_set_output_freq(VLC_FREQ_BIT_1, test_duty);
        }
    }

    // 3. Process Serial Input Commands
    if (Serial.available() > 0) {
        String input = Serial.readStringUntil('\n');
        process_serial_command(input);
    }
}
