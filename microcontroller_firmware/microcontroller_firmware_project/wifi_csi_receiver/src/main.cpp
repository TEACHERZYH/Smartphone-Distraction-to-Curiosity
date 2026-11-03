#include <Arduino.h>
#include <WiFi.h>
#include "esp_wifi.h"
#include "esp_system.h"
#include "csi_parser.h"

// ============================================================================
// Wi-Fi CSI Receiver Configuration
// ============================================================================
#define CSI_TARGET_SSID         "EE-Lab-CSI-01"
#define CSI_TARGET_PASSWORD     "12345678"
#define CSI_TARGET_CHANNEL      6
#define SERIAL_OUTPUT_BAUD      115200      // 115200 or 921600 bps for high throughput

#define FORMAT_CSV_HUMAN        1           // 1: Human-readable CSV for lab debugging; 0: Binary stream

static uint32_t g_rx_packets_count = 0;
static uint32_t g_last_seq_id = 0;
static uint32_t g_dropped_packets = 0;
static csi_serial_frame_t g_out_frame;

// Precomputed mapping array of 52 valid subcarrier indices from 64 raw carriers
static int g_subcarrier_map[CSI_EFFECTIVE_SUBCARRIERS];

void init_subcarrier_mapping() {
    int count = 0;
    // Map logical subcarrier index from -32 to 31 into standard 64-FFT bin offset
    for (int sc = -32; sc < 32; sc++) {
        if (is_valid_csi_data_subcarrier(sc)) {
            // In ESP32-S3 HT20 buffer: first 32 are 0..31, next 32 are -32..-1
            int buf_idx = (sc >= 0) ? sc : (sc + 64);
            g_subcarrier_map[count++] = buf_idx;
            if (count >= CSI_EFFECTIVE_SUBCARRIERS) break;
        }
    }
}

// ============================================================================
// CSI Raw Packet Rx Callback (Fired from Wi-Fi Core ISR context)
// ============================================================================
static void IRAM_ATTR wifi_csi_rx_callback(void *ctx, wifi_csi_info_t *info) {
    if (!info || !info->buf) {
        return;
    }

    wifi_csi_info_t* csi_info = info;
    int8_t* raw_buf = (int8_t*)csi_info->buf;

    // 1. DMA Anomaly Guard: check if first word is invalid offset
    if (csi_info->first_word_invalid) {
        raw_buf += 4; // Shift forward 4 bytes to bypass DMA header misalignment
    }

    g_rx_packets_count++;

    // 2. Extract 52 Valid Data Subcarriers Amplitudes
    // In ESP-IDF: raw_buf contains interleaved [Imaginary, Real] signed 8-bit integers
    // buf[2*i] = Imaginary, buf[2*i + 1] = Real
    for (int k = 0; k < CSI_EFFECTIVE_SUBCARRIERS; k++) {
        int buf_idx = g_subcarrier_map[k];
        float imag = (float)raw_buf[buf_idx * 2];
        float real = (float)raw_buf[buf_idx * 2 + 1];
        
        // Amplitude: a_k = sqrt(I_k^2 + Q_k^2)
        float amp = sqrtf(real * real + imag * imag);
        g_out_frame.amplitudes[k] = (uint16_t)(amp * 10.0f); // 1-decimal fixed point
    }

    // 3. Populate Telemetry Header Metadata
    g_out_frame.magic = CSI_STREAM_HEADER_MAGIC;
    g_out_frame.rssi = csi_info->rx_ctrl.rssi;
    g_out_frame.noise_floor = csi_info->rx_ctrl.noise_floor;
    g_out_frame.channel = csi_info->rx_ctrl.channel;
    g_out_frame.timestamp_ms = millis();
    g_out_frame.sequence_id = g_rx_packets_count;

    // 4. Output to Serial Bus
#if FORMAT_CSV_HUMAN
    // Format: "CSI,Seq,RSSI,Noise,Amp0,Amp1,...,Amp51"
    Serial.printf("CSI,%u,%d,%d", g_out_frame.sequence_id, g_out_frame.rssi, g_out_frame.noise_floor);
    for (int k = 0; k < CSI_EFFECTIVE_SUBCARRIERS; k++) {
        Serial.printf(",%u", g_out_frame.amplitudes[k]);
    }
    Serial.println();
#else
    // Binary high-speed stream
    uint16_t csum = 0;
    uint8_t* p = (uint8_t*)&g_out_frame;
    for (size_t i = 0; i < sizeof(csi_serial_frame_t) - 2; i++) {
        csum += p[i];
    }
    g_out_frame.checksum = csum;
    Serial.write((uint8_t*)&g_out_frame, sizeof(csi_serial_frame_t));
#endif
}

// ============================================================================
// Initialization & Main Execution
// ============================================================================
void setup() {
    Serial.begin(SERIAL_OUTPUT_BAUD);
    delay(500);

    Serial.println("\r\n============================================================");
    Serial.println("  Wi-Fi CSI Sensing Lab: Receiver Node (RX) Firmware v2.1    ");
    Serial.println("  Hardware: ESP32-S3 | 52 Subcarrier CFR Matrix Extraction   ");
    Serial.println("  Output: Serial Stream to Web Platform Processing Engine    ");
    Serial.println("============================================================\r\n");

    init_subcarrier_mapping();

    // 1. Initialize Wi-Fi in Station Mode and Connect to Lab AP
    WiFi.mode(WIFI_STA);
    WiFi.begin(CSI_TARGET_SSID, CSI_TARGET_PASSWORD, CSI_TARGET_CHANNEL);

    Serial.printf("[RX] Connecting to SoftAP \"%s\" on Channel %d...\r\n", CSI_TARGET_SSID, CSI_TARGET_CHANNEL);
    int retries = 0;
    while (WiFi.status() != WL_CONNECTED && retries < 20) {
        delay(300);
        Serial.print(".");
        retries++;
    }
    Serial.println();

    if (WiFi.status() == WL_CONNECTED) {
        Serial.printf("[RX] Associated! IP: %s | RSSI: %d dBm\r\n",
                      WiFi.localIP().toString().c_str(), WiFi.RSSI());
    } else {
        Serial.println("[WARN] AP not yet connected, continuing in promiscuous CSI capture mode...");
    }

    // 2. CRITICAL: Disable Wi-Fi Power Save Mode (Ensure Continuous CSI Capture)
    esp_wifi_set_ps(WIFI_PS_NONE);

    // 3. Configure and Enable CSI Acquisition
    wifi_csi_config_t csi_config = {
        .lltf_en = true,
        .htltf_en = true,
        .stbc_htltf2_en = false,
        .ltf_merge_en = false,
        .channel_filter_en = false,
        .manu_scale = false
    };

    ESP_ERROR_CHECK(esp_wifi_set_csi_config(&csi_config));
    ESP_ERROR_CHECK(esp_wifi_set_csi_rx_cb(&wifi_csi_rx_callback, NULL));
    ESP_ERROR_CHECK(esp_wifi_set_csi(true));

    Serial.println("[RX] CSI Subsystem successfully initialized and listening on Channel 6.\r\n");
}

void loop() {
    // 1 Hz Health Diagnostics
    static unsigned long last_check = 0;
    static uint32_t last_count = 0;

    if (millis() - last_check >= 1000) {
        last_check = millis();
        uint32_t pkts_per_sec = g_rx_packets_count - last_count;
        last_count = g_rx_packets_count;

        // Print diagnostic summary if running in human debug mode
#if FORMAT_CSV_HUMAN
        Serial.printf("# [DIAG] Ingress Rate: %u pkts/s | Cumulative: %u | FreeHeap: %u B\r\n",
                      pkts_per_sec, g_rx_packets_count, esp_get_free_heap_size());
#endif
    }
    delay(20);
}
