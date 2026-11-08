# Smartphone-Distraction-to-Curiosity

### From Digital Distraction to Inquiry-Driven Learning: Smartphone-Based Cross-Modal Signal Experiments Supported by Process Traceability

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)]()
[![Platform: FastAPI + WebSocket](https://img.shields.io/badge/Platform-FastAPI%20%2B%20HTML5-009688.svg)]()
[![Hardware: ESP32](https://img.shields.io/badge/Hardware-ESP32-red.svg)]()

This repository contains the complete open-source laboratory software stack—including the lightweight local-area-network (LAN) web experiment platform, peripheral ESP32 microcontroller firmware, cross-modal signal-processing scripts, and instructional laboratory documentation—supporting the engineering education study:

> **From Digital Distraction to Inquiry-Driven Learning: Smartphone-Based Cross-Modal Signal Experiments Supported by Process Traceability**

---

## 📖 Overview & Instructional Framework

While smartphones offer ubiquitous sensing capabilities for undergraduate engineering laboratories, unrelated digital activity can compete for student attention. This project implements an integrated laboratory learning framework that redirects personal mobile device engagement toward rigorous scientific inquiry and engineering problem solving:

1. **Counterintuitive Cross-Modal Signal Phenomena**: Students repurpose familiar smartphone hardware (CMOS rolling-shutter cameras, MEMS microphones, and zero-install mobile web browsers paired with ESP32 nodes) to investigate physical signal behaviors hidden during everyday use, creating cognitive discrepancies that stimulate epistemic curiosity.
2. **Five-Stage POE+CR Inquiry Cycle**: Each 180-minute laboratory module follows a structured **Predict (E1) → Observe (E2) → Explain (E3) → Challenge (E4) → Redesign (E5)** progression, guiding four-member student teams (with rotating roles: *Primary Hardware Operator*, *Data & Telemetry Recorder*, *Signal Analyst*, and *Quality Auditor & Systems Designer*) from quantitative mathematical prediction to iterative engineering system redesign.
3. **LAN-Based Process Traceability**: A zero-install web platform logs parameter trajectories, calibrated ambient baselines, raw multi-channel sensor waveforms, and parent–child experimental run lineages within a directed acyclic graph (**Run Record DAG**). An embedded **Valid Inquiry Loop** engine verifies single-variable parameter control ($\Delta k = 1$) and renders side-by-side **Diff Views**, making students' intermediate experimental decisions directly visible for instructional scaffolding and **ABET Student Outcomes (SO 1, SO 5, SO 6)** assessment.

![Conceptual Framework](docs/assets/Figure_1.png)

---

## 🔬 Cross-Modal Signal Experiment Suite

All three modules follow a unified five-stage signal-processing chain (**Source Modulation → Channel Dynamics → Transducer Sampling → Feature Extraction → Decision/Demodulation**):

| Physical Parameter | Module 1: Visible Light (VLC/OCC) | Module 2: Acoustic Ranging (Sonar) | Module 3: Radio-Frequency (Wi-Fi CSI) |
| :--- | :--- | :--- | :--- |
| **Physical Medium & Wave Type** | Electromagnetic Light Wave (400–790 THz) | Longitudinal Mechanical Pressure Wave | Electromagnetic RF Wave (2.4 GHz ISM) |
| **Propagation Speed in Air** | $c \approx 3.0 \times 10^8\text{ m/s}$ | $c_s \approx 343\text{ m/s}$ (at $20^\circ\text{C}$) | $c \approx 3.0 \times 10^8\text{ m/s}$ |
| **Signal Bandwidth & Modulation** | Square-wave 2-FSK intensity modulation ($250/500\text{ Hz}$; $50\%$ duty cycle) | Linear Chirp ($17\text{–}20\text{ kHz}$, $B = 3\text{ kHz}$) | IEEE 802.11n OFDM (52 active subcarriers, $20\text{ MHz}$) |
| **Primary Sensor & Interface** | Smartphone CMOS Rolling-Shutter Camera ($30\text{ fps}$) | Smartphone Audio Microphone ($44.1/48\text{ kHz}$, 16-bit) | Dual ESP32 Nodes (Smartphone as LAN Web Client) |
| **Counterintuitive Phenomenon** | Continuous flicker-free LED appears as spatial bright–dark zebra stripes | Matched-filter cross-correlation displays multipath ghost peaks alongside direct target echo | Human motion across a $3\text{-m}$ line-of-sight link perturbs specific OFDM subcarrier amplitudes |
| **Governing Analytical Model** | $P = \frac{1}{f_{\text{mod}} \cdot t_r}$ | $d_{\text{est}} = \frac{c_s \cdot \Delta \tau}{2}$ ($\Delta R = \frac{c_s}{2B} \approx 5.7\text{ cm}$) | $a_k(t) = \sqrt{I_k(t)^2 + Q_k(t)^2}$ |
| **Controlled Parameter (Stage E4)** | Camera exposure time $t_{\text{exp}}$, modulation frequency/duty cycle, distance, angle | Chirp duration, windowing function (Rectangular vs. Kaiser), reflector geometry | Subcarrier index selection mask, motion speed, sliding window length |

![Cross-Modal Phenomena and Waveforms](docs/assets/Figure_3.png)

---

## 💻 Platform Architecture & User Interfaces

The laboratory platform operates entirely over a standalone local area network (LAN) without external cloud dependencies or client-side app installation:

* **Student Mobile Web Interface**: Guides teams through the five POE+CR stages (`1 Predict` → `2 Observe` → `3 Explain` → `4 Challenge` → `5 Redesign`), displays real-time sensor waveforms and region-of-interest (ROI) stripe previews, enforces single-variable control (`Control variable: Change only 1 key parameter — Checked`), and automatically archives parameter snapshots and `Run Records`.
* **Instructor Live Telemetry Dashboard**: Aggregates real-time progress across all 12 four-person teams in the classroom, flags teams requesting help or experiencing repeated multi-variable alerts, and provides a `GROUP TRAIL` drill-down panel to inspect individual team evidence bundles and send targeted pedagogical hints.

![Teacher and Student Interfaces](docs/assets/ui_teacher_student_combined.png)

---

## 🔒 Data Availability & Privacy Notice

> **Confidentiality of Student Evaluation Records**: The complete open-source laboratory software stack, including microcontroller firmware, web-based platform deployment code, signal-processing scripts, and instructional manuals, is publicly accessible in this repository. In strict compliance with student privacy regulations and institutional ethical guidelines regarding academic performance records, **the de-identified teaching evaluation dataset ($N = 288$ students across six intact classes) is withheld from public repository access** (and explicitly excluded via `.gitignore`). Qualified academic researchers may request access to the de-identified dataset from the corresponding author upon reasonable academic request.

---

## 📁 Repository Structure

```text
Smartphone-Distraction-to-Curiosity/
├── web_platform/
│   └── web_platform_service/
│       ├── app.py                              # FastAPI + WebSocket backend & Run Record DAG engine
│       ├── test_app.py                         # Automated unit & regression tests for Valid Loop rules
│       ├── requirements.txt                    # Python backend dependencies
│       ├── README.md                           # Platform architecture & API documentation
│       └── 实验平台技术说明与使用指南.md          # Detailed Chinese deployment & operation guide
├── microcontroller_firmware/
│   └── microcontroller_firmware_project/
│       ├── platformio.ini                      # PlatformIO build & flash configuration for ESP32
│       ├── vlc_transmitter/                    # Module 1: 2-FSK optical PWM transmitter firmware
│       ├── wifi_csi_transmitter/               # Module 3: 802.11n OFDM CSI probe transmitter node
│       ├── wifi_csi_receiver/                  # Module 3: Promiscuous CSI sniffer & stream parser
│       ├── tools/                              # Serial CSI logger & VLC frame validation scripts
│       └── README.md                           # Hardware pinout & firmware flashing instructions
├── analysis_scripts/
│   └── python_data_analysis_scripts/
│       ├── vlc_analysis/                       # Rolling-shutter row integration & 2-FSK demodulator
│       ├── acoustic_analysis/                  # LFM chirp pulse-compression & Kaiser window sonar
│       ├── csi_analysis/                       # 52-subcarrier amplitude extraction & motion detector
│       ├── run_all_analyses.py                 # Master execution script for cross-modal verification
│       └── requirements.txt                    # Scientific computing dependencies (NumPy, SciPy, etc.)
├── docs/
│   ├── 智能手机跨模态信号与物联网感知实验指导书.pdf  # Comprehensive Laboratory Manual (PDF, 28 pages)
│   
├── .gitignore                                  # Strictly blocks student evaluation datasets (*.csv, *.xlsx)
├── LICENSE                                     # MIT Open-Source License
└── README.md                                   # Repository documentation
```

---

## 🚀 Quick Start Guide

### 1. Launching the Local LAN Web Platform
Connect the laboratory host computer and student smartphones to the same local Wi-Fi router, then start the FastAPI server:

```bash
cd web_platform/web_platform_service
pip install -r requirements.txt
python3 app.py
```

* **Student Mobile Client**: Open `http://<SERVER_LAN_IP>:8000` in any mobile browser (Safari, Chrome, Edge; zero app installation required).
* **Instructor Dashboard**: Open `http://<SERVER_LAN_IP>:8000/?view=teacher` on the instructor workstation.
* **Run Automated Platform Tests**:
  ```bash
  pytest test_app.py
  ```

### 2. Flashing ESP32 Microcontroller Nodes
Use [PlatformIO](https://platformio.org/) to compile and upload firmware to the ESP32 nodes:

```bash
cd microcontroller_firmware/microcontroller_firmware_project

# Flash Module 1 VLC 2-FSK optical transmitter
pio run -e vlc_tx --target upload

# Flash Module 3 Wi-Fi CSI transmitter & receiver pair
pio run -e csi_tx --target upload
pio run -e csi_rx --target upload
```

### 3. Running Cross-Modal Signal Processing Verification
To run the standalone signal-processing verification suite across synthetic and sample sensor traces:

```bash
cd analysis_scripts/python_data_analysis_scripts
pip install -r requirements.txt
python3 run_all_analyses.py
```

---

## 📜 License & Academic Correspondence

* **License**: This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
* **Academic Inquiries**: For questions regarding instructional implementation, rubric adaptation, or reasonable academic requests for the de-identified evaluation dataset, please contact the corresponding author listed in the article.
