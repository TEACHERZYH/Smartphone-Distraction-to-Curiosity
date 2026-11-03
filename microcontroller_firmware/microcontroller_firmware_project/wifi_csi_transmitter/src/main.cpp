#include <Arduino.h>
#include <WiFi.h>
#include "esp_wifi.h"
#include "esp_timer.h"
#include "esp_system.h"

// ============================================================================
// Wi-Fi CSI RF Transmitter Configuration
// ============================================================================
#define CSI_TX_SSID             "EE-Lab-CSI-01"
#define CSI_TX_PASSWORD         "12345678"
#define CSI_TX_CHANNEL          6           // 2.437 GHz (Fixed channel)
#define CSI_TX_PACKET_RATE_HZ   100         // 100 Hz nominal rate (10 ms interval)
#define CSI_TX_INTERVAL_US      (1000000 / CSI_TX_PACKET_RATE_HZ) // 10000 us

#define LED_INDICATOR_PIN       2           // On-board status LED
#define CSI_MAGIC_HEADER        0x53435349  // ASCII 'SCSI' magic signature

// Custom Probe Action Packet Payload Structure
typedef struct __attribute__((packed)) {
    uint32_t magic;             // Magic identifier ('SCSI')
    uint32_t sequence_num;      // Monotonically increasing sequence ID
    uint64_t timestamp_us;      // High-precision microsecond hardware timestamp
    uint8_t  node_id;           // Transmitter node identifier (e.g. 0x01)
    uint8_t  reserved[15];      // Padding to ensure HT20 payload length
} csi_probe_packet_t;

// Standard 802.11 Action Frame Raw Header Template
static uint8_t raw_action_frame[128] = {
    0xd0, 0x00,                         // Frame Control: Action Frame
    0x00, 0x00,                         // Duration
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, // Destination: Broadcast
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Source: Self AP MAC (filled at boot)
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, // BSSID: Broadcast
    0x00, 0x00,                         // Sequence Control
    0x7f, 0x08, 0x00, 0x00, 0x00, 0x00  // Vendor Specific Category
};

static volatile uint32_t g_seq_counter = 0;
static volatile uint32_t g_packets_sent_total = 0;
static esp_timer_handle_t g_tx_timer = NULL;

// ============================================================================
// High-Precision Hardware Timer ISR Callback (100 Hz)
// ============================================================================
static void IRAM_ATTR csi_tx_timer_callback(void* arg) {
    csi_probe_packet_t* packet = (csi_probe_packet_t*)&raw_action_frame[24];
    packet->magic = CSI_MAGIC_HEADER;
    packet->sequence_num = ++g_seq_counter;
    packet->timestamp_us = esp_timer_get_time();
    packet->node_id = 0x01;

    // Transmit raw IEEE 802.11 packet via Wi-Fi MAC layer
    esp_err_t err = esp_wifi_80211_tx(WIFI_IF_AP, raw_action_frame, sizeof(raw_action_frame), true);
    if (err == ESP_OK) {
        g_packets_sent_total++;
    }
}

// ============================================================================
// Initialization & Main Routine
// ============================================================================
void setup() {
    Serial.begin(115200);
    delay(500);

    Serial.println("\r\n============================================================");
    Serial.println("  Wi-Fi CSI Sensing Lab: RF Transmitter Node (TX) v2.1       ");
    Serial.println("  Hardware: ESP32-S3 | Mode: SoftAP HT20 | Channel: 6        ");
    Serial.println("  Nominal Rate: 100 Hz (10 ms) Continuous Probe Broadcast     ");
    Serial.println("============================================================\r\n");

    pinMode(LED_INDICATOR_PIN, OUTPUT);
    digitalWrite(LED_INDICATOR_PIN, LOW);

    // 1. Initialize Wi-Fi in SoftAP Mode
    WiFi.mode(WIFI_AP);
    bool ap_ok = WiFi.softAP(CSI_TX_SSID, CSI_TX_PASSWORD, CSI_TX_CHANNEL, 0, 4);
    if (!ap_ok) {
        Serial.println("[ERR] Failed to start SoftAP!");
        while (1) { delay(1000); }
    }

    // 2. Lock RF Power and Force HT20 Physical Mode
    esp_wifi_set_bandwidth(WIFI_IF_AP, WIFI_BW_HT20);
    esp_wifi_set_max_tx_power(80); // 80 * 0.25 dBm = 20 dBm (Maximum lawful transmit power)
    
    // Copy local MAC address into source address field
    uint8_t local_mac[6];
    esp_wifi_get_mac(WIFI_IF_AP, local_mac);
    memcpy(&raw_action_frame[10], local_mac, 6);

    Serial.printf("[TX] SoftAP Started: SSID=\"%s\", Channel=%d, IP=%s\r\n",
                  CSI_TX_SSID, CSI_TX_CHANNEL, WiFi.softAPIP().toString().c_str());
    Serial.printf("[TX] MAC Address: %02X:%02X:%02X:%02X:%02X:%02X\r\n",
                  local_mac[0], local_mac[1], local_mac[2], local_mac[3], local_mac[4], local_mac[5]);

    // 3. Configure Hardware Microsecond Timer for 100 Hz Transmit
    const esp_timer_create_args_t timer_args = {
        .callback = &csi_tx_timer_callback,
        .arg = NULL,
        .dispatch_method = ESP_TIMER_TASK,
        .name = "csi_100hz_tx"
    };

    esp_err_t err = esp_timer_create(&timer_args, &g_tx_timer);
    if (err == ESP_OK) {
        esp_timer_start_periodic(g_tx_timer, CSI_TX_INTERVAL_US);
        Serial.printf("[TX] Periodic 100 Hz hardware timer started (%d us interval).\r\n", CSI_TX_INTERVAL_US);
    } else {
        Serial.printf("[ERR] Failed to create timer, err=0x%x\r\n", err);
    }
}

void loop() {
    // 1 Hz Status Telemetry & Heartbeat LED Toggle
    static unsigned long last_report = 0;
    static uint32_t last_packets = 0;

    if (millis() - last_report >= 1000) {
        last_report = millis();
        uint32_t delta = g_packets_sent_total - last_packets;
        last_packets = g_packets_sent_total;

        digitalWrite(LED_INDICATOR_PIN, !digitalRead(LED_INDICATOR_PIN));

        Serial.printf("[TX-HEARTBEAT] Rate: %d pkts/s | Total Sent: %u pkts | Seq: #%u | Uptime: %lu s\r\n",
                      delta, g_packets_sent_total, g_seq_counter, millis() / 1000);
    }
    delay(10);
}
