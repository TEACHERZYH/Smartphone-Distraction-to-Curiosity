#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, numpy as np
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from wifi_csi_analyzer import WiFiCSIAnalyzer

def synthesize_csi_dataset(fs=100.0, num_subcarriers=52):
    total_seconds = 60.0
    n_total = int(fs * total_seconds)
    t = np.arange(n_total) / fs
    np.random.seed(42)
    base_channel = np.random.uniform(80.0, 180.0, num_subcarriers)
    amp_mat = np.tile(base_channel, (n_total, 1)) + np.random.normal(0, 1.5, (n_total, num_subcarriers))
    
    walk_mask = (t >= 25.0) & (t < 50.0)
    walk_indices = np.where(walk_mask)[0]
    walk_time = t[walk_indices] - 25.0
    for k in range(num_subcarriers):
        sens = np.sin((k / float(num_subcarriers)) * np.pi) * 1.5 + 0.3
        amp_mat[walk_indices, k] += np.sin(2.0 * np.pi * (3.5 + 0.5 * np.cos(k)) * walk_time) * (25.0 * sens)
        
    fall_mask = (t >= 52.0) & (t < 55.0)
    fall_indices = np.where(fall_mask)[0]
    fall_time = t[fall_indices] - 52.0
    for k in range(num_subcarriers):
        amp_mat[fall_indices, k] += np.exp(-((fall_time - 1.2) ** 2) / 0.3) * 65.0
        
    amp_mat = np.clip(amp_mat, 10.0, 255.0)
    return amp_mat, amp_mat[:int(20.0 * fs), :], amp_mat[int(30.0 * fs):int(45.0 * fs), :]

def run_csi_end_to_end_test():
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output_results")
    os.makedirs(output_dir, exist_ok=True)
    analyzer = WiFiCSIAnalyzer(sample_rate_hz=100.0, window_sec=4.0)
    full_mat, static_calib, moving_calib = synthesize_csi_dataset()
    analyzer.calibrate_static_baseline(static_calib)
    opt_th, bacc = analyzer.optimize_adaptive_threshold(static_calib, moving_calib)
    assert bacc > 0.90, "CSI threshold optimization failed!"
    features, timestamps = analyzer.compute_windowed_variance_features(full_mat)
    decisions = analyzer.classify_stream(features)
    assert "FALL_ALERT" in decisions, "CSI fall detection failed!"
    report_img = os.path.join(output_dir, "wifi_csi_analysis_report.png")
    analyzer.plot_diagnostic_report(full_mat, features, timestamps, decisions, save_path=report_img)
    print(f"[CSI-TEST] Balanced Accuracy: {bacc*100:.1f}% | Fall Detected! Verified!")

if __name__ == "__main__":
    run_csi_end_to_end_test()
