#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python PC-Side Helper Tool: Read ESP32-S3 Serial CSI Data Stream,
calculate 52-subcarrier variance, and plot real-time waterfall / variance wave.
"""
import sys
import time
import numpy as np

def simulate_csi_stream():
    """Simulate CSI stream for offline testing when hardware COM port is unavailable."""
    print("[SIMULATION] Generating synthetic Wi-Fi CSI 52-subcarrier stream...")
    print("[SIMULATION] Press Ctrl+C to stop.\n")
    
    seq = 0
    subcarriers = 52
    baseline = np.random.normal(150, 10, subcarriers)
    
    try:
        while True:
            seq += 1
            # Add dynamic perturbation every 4 seconds to simulate human walking
            is_moving = (seq % 40) < 15
            noise = np.random.normal(0, 35 if is_moving else 2, subcarriers)
            amps = np.clip(baseline + noise, 10, 300).astype(int)
            
            # Format: CSI,Seq,RSSI,Noise,Amp0,Amp1,...,Amp51
            csv_line = f"CSI,{seq},-45,-92," + ",".join(map(str, amps))
            
            # Calculate mean variance across 52 subcarriers
            var_mean = np.var(amps)
            status = ">>> MOTION DETECTED <<<" if var_mean > 500 else "STATIC EMPTY ROOM"
            
            print(f"[{time.strftime('%H:%M:%S')}] Pkt #{seq:05d} | Mean Var: {var_mean:6.1f} | Status: {status}")
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\n[SIMULATION] Stream stopped by user.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "sim":
        port = sys.argv[1]
        baud = int(sys.argv[2]) if len(sys.argv) > 2 else 115200
        print(f"[CSI-LOGGER] Opening real serial port: {port} @ {baud} bps...")
        try:
            import serial
            ser = serial.Serial(port, baud, timeout=1)
            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("CSI,"):
                    parts = line.split(",")
                    seq = parts[1]
                    rssi = parts[2]
                    amps = [float(x)/10.0 for x in parts[4:]]
                    var = np.var(amps)
                    print(f"Pkt #{seq} | RSSI: {rssi} dBm | 52-Carrier Var: {var:.2f}")
        except Exception as e:
            print(f"[ERR] Serial error: {e}. Falling back to simulation.")
            simulate_csi_stream()
    else:
        simulate_csi_stream()
