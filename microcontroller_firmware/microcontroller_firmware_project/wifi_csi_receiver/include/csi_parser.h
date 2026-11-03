#ifndef CSI_PARSER_H
#define CSI_PARSER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// IEEE 802.11n HT20 CSI Specification & Subcarrier Indices
// ============================================================================
// Total subcarriers in 20 MHz HT20 mode: 64 (indices -32 to 31)
// - DC subcarrier: index 0 (1 carrier)
// - Guard band subcarriers: indices -32..-29, 29..31 (7 carriers)
// - Dedicated Pilot subcarriers: indices -21, -7, 7, 21 (4 carriers)
// -> Effective Data Subcarriers for Sensing: 64 - 1 - 7 - 4 = 52 subcarriers
#define CSI_TOTAL_SUBCARRIERS       64
#define CSI_EFFECTIVE_SUBCARRIERS   52

// Serial Stream Output Protocol Magic Signature
#define CSI_STREAM_HEADER_MAGIC     0xA55A

// Binary Telemetry Frame sent to PC via Serial (USB-UART 115200 / 921600 bps)
typedef struct __attribute__((packed)) {
    uint16_t magic;             // Magic header (0xA55A)
    uint32_t sequence_id;       // Frame sequence counter from transmitter
    int8_t   rssi;              // Received Signal Strength Indication (dBm)
    int8_t   noise_floor;       // Radio noise floor (dBm)
    uint16_t channel;           // Active RF channel (6)
    uint32_t timestamp_ms;      // Local receiver arrival timestamp (ms)
    
    // 52 Subcarrier Instantaneous Amplitude Values: a_k = sqrt(I_k^2 + Q_k^2)
    // Scaled by 10 for integer transmission (e.g., 15.4 -> 154)
    uint16_t amplitudes[CSI_EFFECTIVE_SUBCARRIERS];
    
    uint16_t checksum;          // XOR / additive checksum across payload
} csi_serial_frame_t;

// Filter Mask: true if subcarrier index in [-28..-1, 1..28] is valid data (not pilot)
// In standard ESP32-S3 HT20 buffer: 64 complex numbers (int8_t imaginary, int8_t real)
static inline bool is_valid_csi_data_subcarrier(int sc_idx) {
    if (sc_idx == 0) return false;                  // DC
    if (sc_idx < -28 || sc_idx > 28) return false;  // Guard bands
    if (sc_idx == -21 || sc_idx == -7 || sc_idx == 7 || sc_idx == 21) return false; // Pilots
    return true;
}

#ifdef __cplusplus
}
#endif

#endif // CSI_PARSER_H
