# Smartphone-Distraction-to-Curiosity
### Scaffolding Authentic Inquiry in Engineering Laboratories via Smartphone Cross-Modal Signal Experiments: A Process Traceability Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)]()
[![Hardware: ESP32](https://img.shields.io/badge/Hardware-ESP32--C3-red.svg)]()
[![Ethics Approval](https://img.shields.io/badge/IRB-IRB--2023--EE--042-success.svg)]()

This repository contains the open-source software artifacts, microcontroller firmware, and analytical regression suites supporting the engineering education study submitted to *Computer Applications in Engineering Education* (CAEE, Wiley).

---

## Data Availability and Privacy

The de-identified student-level teaching evaluation dataset is **not included** in this public repository, in accordance with institutional ethics and student privacy requirements (IRB Protocol No. IRB-2023-EE-042). Researchers may request access to eligible de-identified records from the corresponding author, subject to institutional approval.

The repository includes an **aggregated class-level statistical summary** and a reproducibility script. These materials do not contain student-level records or questionnaire-level responses. The source workbook used by the script remains private and must be obtained separately through the approved data-request process.

---

## Repository Structure

- `analysis_scripts/python_data_analysis_scripts/`: signal-processing verification routines and the class-level descriptive analysis script.
- `docs/`: manuscript-related documentation, experiment guidance, and the aggregated class-level analysis report.
- `microcontroller_firmware/`: ESP32 firmware and device-side tools.
- `web_platform/`: the local web experiment platform and its tests.

## Reproducing the Analysis

The repository contains two distinct analysis workflows. They should not be confused:

### 1. Signal-processing verification

Install the signal-processing dependencies and run:

```bash
python -m pip install -r analysis_scripts/python_data_analysis_scripts/requirements.txt
python analysis_scripts/python_data_analysis_scripts/run_all_analyses.py
```

This entry point runs synthetic verification routines for VLC/OCC, acoustic ranging, and Wi-Fi CSI processing. It does **not** analyse the student teaching-evaluation dataset.

### 2. Teaching-evaluation descriptive analysis

Install the additional tabular-data dependencies:

```bash
python -m pip install pandas openpyxl
```

Then provide the separately obtained teaching-evaluation workbook:

```bash
python analysis_scripts/python_data_analysis_scripts/reproduce_class_level_descriptives.py /path/to/deidentified_teaching_evaluation_dataset.xlsx
```

The script groups records by academic year and intact class (experimental/control) and prints the three annual class-pair contrasts for pre-test, post-test, score gain, and valid inquiry-loop counts.

**Important design and inference note:** the intervention was allocated at the intact-class level: one experimental class and one control class per academic year, across three academic years. Students and teams are nested observations, not independent treatment replications. Only three annual class pairs are available, and class-level randomization has not been documented in the information supplied for this analysis. The script therefore reports descriptive contrasts only and intentionally does not calculate student- or team-level treatment-effect p-values.

See:
- [Class-level analysis notes](docs/CLASS_LEVEL_ANALYSIS_NOTES.md)
- [Statistical reanalysis report (Markdown)](docs/STATISTICAL_REANALYSIS_REPORT.md)

---

## Ethics and Citation

- **Ethics review:** IRB Protocol No. **IRB-2023-EE-042**.
- **Corresponding author:** for academic correspondence and eligible data requests, refer to the contact details in the manuscript.
- Please cite the associated research article when using the software or documentation.
