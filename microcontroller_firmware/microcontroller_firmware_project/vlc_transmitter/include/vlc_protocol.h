#ifndef VLC_PROTOCOL_H
#define VLC_PROTOCOL_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Visible Light Communication (VLC/OCC) Protocol & System Constants
// ============================================================================

// Hardware Pinout Configuration
#define VLC_PWM_PIN             4   // GPIO4 connected to MOSFET SIG pin
#define VLC_BUTTON_PIN          0   // GPIO0 on-board BOOT button for mode switching
#define VLC_LED_STATUS_PIN      2   // GPIO2 on-board status indicator LED

// Physical Layer Modulation Parameters
#define VLC_FREQ_BIT_0          250     // Logic '0' square wave modulation frequency (Hz)
#define VLC_FREQ_BIT_1          500     // Logic '1' square wave modulation frequency (Hz)
#define VLC_SYMBOL_DURATION_MS  250     // Duration per transmitted bit symbol (ms)
#define VLC_PWM_CHANNEL         0       // ESP32 LEDC PWM channel (0 - 15)
#define VLC_PWM_RESOLUTION      8       // 8-bit timer resolution (0 - 255)
#define VLC_DEFAULT_DUTY        128     // 50% duty cycle (128 / 256)

// 40-bit Communication Frame Format (MSB First)
// [Preamble: 8-bit] + [Delimiter: 8-bit] + [Length: 8-bit] + [Payload: N*8-bit]
#define VLC_FRAME_PREAMBLE      0xAA    // 0b10101010 - Clock synchronization preamble
#define VLC_FRAME_DELIMITER     0xE2    // 0b11100010 - Unique frame start delimiter
#define VLC_MAX_PAYLOAD_LEN     32      // Maximum payload bytes per frame
#define VLC_GUARD_INTERVAL_MS   1000    // Dark guard interval between consecutive frames (ms)

// Operating Modes for Educational Inquiry
typedef enum {
    VLC_MODE_FRAME_LOOP = 0,    // Mode 1: Continuously transmit structured 40-bit frame (e.g. "OK")
    VLC_MODE_CW_250HZ,          // Mode 2: Continuous wave at 250 Hz (for spatial stripe baseline calibration)
    VLC_MODE_CW_500HZ,          // Mode 3: Continuous wave at 500 Hz (for spatial stripe baseline calibration)
    VLC_MODE_DUTY_CHALLENGE,    // Mode 4: Cycle duty cycle (25% -> 50% -> 75%) for single-variable challenge
    VLC_MODE_STANDBY            // Mode 5: LED Off (Standby / Idle)
} vlc_mode_t;

// Frame Structure Definition
typedef struct {
    uint8_t preamble;                   // Preamble byte (0xAA)
    uint8_t delimiter;                  // Frame delimiter (0xE2)
    uint8_t length;                     // Payload length in bytes (N)
    uint8_t payload[VLC_MAX_PAYLOAD_LEN]; // ASCII characters payload
    uint16_t total_bits;                // Total bits in frame = (3 + length) * 8
} vlc_frame_t;

#ifdef __cplusplus
}
#endif

#endif // VLC_PROTOCOL_H
