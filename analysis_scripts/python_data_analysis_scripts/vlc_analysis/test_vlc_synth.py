#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, cv2, numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from vlc_demodulator import VLCDemodulator

def synthesize_rolling_shutter_frame(freq_hz, tr_us=25.0, height=1080, width=1920, duty=0.5, noise_std=5.0):
    tr_s = tr_us * 1e-6
    row_indices = np.arange(height)
    phases = 2.0 * np.pi * freq_hz * (row_indices * tr_s)
    phase_mod = phases % (2.0 * np.pi)
    square_wave = np.where(phase_mod < (2.0 * np.pi * duty), 220.0, 35.0)
    frame_base = np.tile(square_wave[:, np.newaxis], (1, width))
    y_coords, x_coords = np.ogrid[:height, :width]
    dist_sq = ((y_coords - height/2.0)/(height/2.0))**2 + ((x_coords - width/2.0)/(width/2.0))**2
    vignette = np.clip(1.0 - 0.4 * dist_sq, 0.2, 1.0)
    final_frame = np.clip(frame_base * vignette + np.random.normal(0, noise_std, (height, width)), 0, 255).astype(np.uint8)
    return cv2.cvtColor(final_frame, cv2.COLOR_GRAY2BGR), 1.0 / (freq_hz * tr_s)

def run_vlc_end_to_end_test():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output_results")
    os.makedirs(output_dir, exist_ok=True)
    demod = VLCDemodulator(tr_us=25.0, freq0=250.0, freq1=500.0, fps=30.0)
    frame1, true_p1 = synthesize_rolling_shutter_frame(freq_hz=500.0, tr_us=25.0)
    prof, raw_p, _, roi_box = demod.extract_vertical_projection(frame1)
    p_est, lags, corr, peaks = demod.estimate_stripe_period(prof)
    b_est, f_est = demod.classify_frame_bit(p_est)
    diag_plot_path = os.path.join(output_dir, "vlc_demodulation_report.png")
    demod.plot_diagnostic_report(frame1, roi_box, raw_p, prof, lags, corr, peaks, p_est, f_est, b_est, save_path=diag_plot_path)
    assert b_est == 1, "VLC bit 1 decoding failed!"
    
    # 40-bit frame: Preamble 0xAA, Delimiter 0xE2, Len 2, "OK"
    bits_sequence = [1,0,1,0,1,0,1,0, 1,1,1,0,0,0,1,0, 0,0,0,0,0,0,1,0, 0,1,0,0,1,1,1,1, 0,1,0,0,1,0,1,1]
    demod_bits = []
    for b in bits_sequence:
        f_bgr, _ = synthesize_rolling_shutter_frame(freq_hz=500.0 if b==1 else 250.0, tr_us=25.0)
        p, _, _, _ = demod.extract_vertical_projection(f_bgr)
        pe, _, _, _ = demod.estimate_stripe_period(p)
        bit, _ = demod.classify_frame_bit(pe)
        demod_bits.append(bit)
    msg = demod.decode_bitstream_fsm(demod_bits)
    assert msg == "OK", "VLC 40-bit frame decoding failed!"
    print(f"[VLC-TEST] Frame Decoded: '{msg}' | Verified!")

if __name__ == "__main__":
    run_vlc_end_to_end_test()
