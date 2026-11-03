#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, time

base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(base_dir, "vlc_analysis"))
sys.path.append(os.path.join(base_dir, "acoustic_analysis"))
sys.path.append(os.path.join(base_dir, "csi_analysis"))

from test_vlc_synth import run_vlc_end_to_end_test
from test_acoustic_synth import run_acoustic_end_to_end_test
from test_csi_synth import run_csi_end_to_end_test

def main():
    print("=====================================================================")
    print("  Cross-Modal Smartphone Signal & IoT Sensing Educational Lab        ")
    print("  Comprehensive Python Signal Processing & Demodulation Suite        ")
    print("=====================================================================\n")
    t0 = time.time()
    
    print(">>> 1/3 Running VLC/OCC Stripe Demodulator Verification...")
    run_vlc_end_to_end_test()
    
    print("\n>>> 2/3 Running Acoustic FMCW Sonar Ranging Engine Verification...")
    run_acoustic_end_to_end_test()
    
    print("\n>>> 3/3 Running Wi-Fi CSI 52-Subcarrier RF Sensing Verification...")
    run_csi_end_to_end_test()
    
    print(f"\nAll modules executed successfully in {time.time()-t0:.2f} seconds!")
    print(f"Artifacts saved to: {os.path.join(base_dir, 'output_results')}")

if __name__ == "__main__":
    main()
