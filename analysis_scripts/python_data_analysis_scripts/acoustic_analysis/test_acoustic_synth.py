#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from acoustic_ranging import AcousticRangingEngine

def synthesize_acoustic_environment(engine, target_dist_m=1.50, direct_dist_m=0.048, total_duration_s=0.15, noise_amp=0.02):
    fs, c = engine.fs, engine.c
    t_total = np.linspace(0, total_duration_s, int(fs * total_duration_s), endpoint=False)
    rx = np.zeros_like(t_total)
    t0 = 0.010
    idx_dir = int((t0 + direct_dist_m / c) * fs)
    ref_len = len(engine.ref_chirp)
    rx[idx_dir:idx_dir+ref_len] += engine.ref_chirp * 1.0
    idx_echo = int((t0 + 2.0 * target_dist_m / c) * fs)
    rx[idx_echo:idx_echo+ref_len] += engine.ref_chirp * 0.35
    idx_mp = int((t0 + 2.2 / c) * fs)
    rx[idx_mp:idx_mp+ref_len] += engine.ref_chirp * 0.12
    return rx + np.random.normal(0, noise_amp, len(rx))

def run_acoustic_end_to_end_test():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output_results")
    os.makedirs(output_dir, exist_ok=True)
    engine = AcousticRangingEngine(sample_rate=48000, temperature_c=22.5)
    rx = synthesize_acoustic_environment(engine, target_dist_m=1.50)
    time_axis, envelope, rx_mono = engine.compute_cross_correlation(rx)
    res = engine.extract_ranging_peaks(time_axis, envelope)
    assert res is not None, "Acoustic peak extraction failed!"
    report_img = os.path.join(output_dir, "acoustic_ranging_report.png")
    engine.plot_diagnostic_report(time_axis, envelope, rx_mono, res, ground_truth_d=1.50, save_path=report_img)
    err_cm = abs(res["d_estimated_m"] - 1.50) * 100.0
    assert err_cm < 2.0, f"Error {err_cm:.2f} cm exceeds 2 cm threshold!"
    print(f"[ACOUSTIC-TEST] Distance: {res['d_estimated_m']:.4f} m (Error: {err_cm:.2f} cm) | Verified!")

if __name__ == "__main__":
    run_acoustic_end_to_end_test()
