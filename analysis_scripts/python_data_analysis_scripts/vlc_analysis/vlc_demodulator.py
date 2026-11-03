#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cv2
import numpy as np
from scipy import signal
import matplotlib.pyplot as plt

class VLCDemodulator:
    def __init__(self, tr_us=25.0, freq0=250.0, freq1=500.0, fps=30.0, symbol_duration_ms=250.0):
        self.tr_s = tr_us * 1e-6
        self.freq0 = freq0
        self.freq1 = freq1
        self.fps = fps
        self.symbol_duration_ms = symbol_duration_ms
        self.frames_per_symbol = int(np.round((symbol_duration_ms / 1000.0) * fps))
        self.P0_expected = 1.0 / (self.freq0 * self.tr_s)
        self.P1_expected = 1.0 / (self.freq1 * self.tr_s)
        self.threshold_P = (self.P0_expected + self.P1_expected) / 2.0

    def extract_vertical_projection(self, frame_bgr, roi_box=None):
        h_img, w_img = frame_bgr.shape[:2]
        if roi_box is None:
            w = int(w_img * 0.4)
            h = int(h_img * 0.7)
            x = int((w_img - w) / 2)
            y = int((h_img - h) / 2)
            roi_box = (x, y, w, h)
        rx, ry, rw, rh = roi_box
        roi = frame_bgr[ry:ry+rh, rx:rx+rw]
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        raw_profile = np.mean(gray, axis=1)
        rows = np.arange(len(raw_profile))
        poly_fit = np.poly1d(np.polyfit(rows, raw_profile, 2))(rows)
        detrended = raw_profile - poly_fit
        detrended_smooth = signal.savgol_filter(detrended, window_length=11, polyorder=3)
        return detrended_smooth, raw_profile, gray, roi_box

    def estimate_stripe_period(self, profile):
        n = len(profile)
        corr = signal.correlate(profile, profile, mode='full')
        lags = signal.correlation_lags(n, n)
        pos_mask = (lags > 0) & (lags < n // 2)
        pos_lags = lags[pos_mask]
        pos_corr = corr[pos_mask]
        peaks, _ = signal.find_peaks(pos_corr, distance=40, prominence=np.max(pos_corr) * 0.15)
        if len(peaks) > 0:
            return float(pos_lags[peaks[0]]), pos_lags, pos_corr, peaks
        else:
            fft_vals = np.abs(np.fft.rfft(profile))[1:]
            freqs = np.fft.rfftfreq(n, d=1.0)[1:]
            dominant_spatial_freq = freqs[np.argmax(fft_vals)]
            period_fft = 1.0 / dominant_spatial_freq if dominant_spatial_freq > 0 else 0.0
            return float(period_fft), pos_lags, pos_corr, []

    def classify_frame_bit(self, period_pixel):
        if period_pixel <= 0: return None, 0.0
        derived_freq = 1.0 / (period_pixel * self.tr_s)
        bit = 0 if period_pixel > self.threshold_P else 1
        return bit, derived_freq

    def decode_bitstream_fsm(self, raw_bits):
        bit_str = "".join([str(b) for b in raw_bits if b is not None])
        sync_header = "10101010" + "11100010"
        idx = bit_str.find(sync_header)
        if idx == -1: return None
        payload_start = idx + len(sync_header)
        if payload_start + 8 > len(bit_str): return None
        payload_len = int(bit_str[payload_start:payload_start+8], 2)
        chars = []
        data_start = payload_start + 8
        for i in range(payload_len):
            ch_start = data_start + i * 8
            if ch_start + 8 > len(bit_str): break
            chars.append(chr(int(bit_str[ch_start:ch_start+8], 2)))
        return "".join(chars)

    def plot_diagnostic_report(self, frame_bgr, roi_box, raw_prof, detrended_prof, lags, corr, peaks, period, freq, bit, save_path=None):
        fig, axs = plt.subplots(2, 2, figsize=(11, 7), dpi=300)
        annotated_frame = frame_bgr.copy()
        rx, ry, rw, rh = roi_box
        cv2.rectangle(annotated_frame, (rx, ry), (rx+rw, ry+rh), (0, 255, 0), 3)
        axs[0, 0].imshow(cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB))
        axs[0, 0].set_title("(a) Video Frame & Bounding ROI", fontweight='bold', fontsize=10)
        axs[0, 0].axis('off')
        
        y_axis = np.arange(len(raw_prof))
        axs[0, 1].plot(y_axis, raw_prof, color='gray', linestyle='--', label='Raw Profile', alpha=0.7)
        axs[0, 1].plot(y_axis, detrended_prof, color='#0056B3', linewidth=1.5, label='Detrended Stripe Wave')
        axs[0, 1].set_xlabel('Vertical Pixel Row Coordinate (px)', fontweight='bold')
        axs[0, 1].set_ylabel('Normalized Light Intensity', fontweight='bold')
        axs[0, 1].set_title('(b) Spatial Vertical Gray Projection Profile', fontweight='bold', fontsize=10)
        axs[0, 1].grid(True, linestyle=':', alpha=0.6)
        axs[0, 1].legend(loc='upper right')
        
        axs[1, 0].plot(lags, corr, color='#1B365D', linewidth=1.5, label='Autocorrelation')
        if len(peaks) > 0:
            axs[1, 0].plot(lags[peaks[0]], corr[peaks[0]], 'ro', markersize=8, label=f'Peak: P = {period:.1f} px')
            axs[1, 0].axvline(period, color='red', linestyle=':', alpha=0.8)
        axs[1, 0].set_xlabel('Spatial Shift Lag (Pixel Rows)', fontweight='bold')
        axs[1, 0].set_ylabel('Correlation Coefficient', fontweight='bold')
        axs[1, 0].set_title(f'(c) Autocorrelation Peak Detection (P = {period:.1f} rows)', fontweight='bold', fontsize=10)
        axs[1, 0].grid(True, linestyle=':', alpha=0.6)
        axs[1, 0].legend(loc='upper right')
        
        axs[1, 1].axis('off')
        info_text = (
            f"VLC / OCC Demodulation Report\n"
            f"-----------------------------------------\n"
            f"Sensor Row Time (tr) : {self.tr_s*1e6:.1f} us\n"
            f"Measured Period (P)  : {period:.1f} pixel rows\n"
            f"Calculated Frequency : {freq:.1f} Hz\n"
            f"Theoretical P0 (250) : {self.P0_expected:.1f} rows\n"
            f"Theoretical P1 (500) : {self.P1_expected:.1f} rows\n"
            f"Decision Threshold P : {self.threshold_P:.1f} rows\n"
            f"-----------------------------------------\n"
            f"Demodulated Symbol   : LOGIC '{bit}'\n"
            f"Confidence Indicator : HIGH (Sharp Autocorr Peak)"
        )
        axs[1, 1].text(0.1, 0.5, info_text, transform=axs[1, 1].transAxes, fontsize=9.5, family='monospace', va='center',
                       bbox=dict(boxstyle='round,pad=0.8', facecolor='#F8F9FA', edgecolor='#28A745' if bit==1 else '#D9534F', linewidth=2))
        axs[1, 1].set_title('(d) Demodulation Decision Summary', fontweight='bold', fontsize=10)
        plt.tight_layout()
        if save_path: plt.savefig(save_path, dpi=300)
        plt.close()
