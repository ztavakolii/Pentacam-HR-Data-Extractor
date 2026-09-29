
# Pentacam HR — Automated Batch Data Extraction Pipeline

> A UI-automation pipeline for high-throughput extraction of corneal densitometry 
> maps and diagnostic reports from the OCULUS Pentacam HR system.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)
![Status](https://img.shields.io/badge/Status-Active%20Development-yellow)

---

This repository is part of an **ongoing clinical research project** conducted at the 
Medical Image & Signal Processing Research Center (MISP), Isfahan University of 
Medical Sciences, in collaboration with the Ophthalmology Department of Feiz 
Hospital, Isfahan.

---

## Motivation

The OCULUS Pentacam HR is a gold-standard Scheimpflug tomography device used for 
corneal diagnostics. It produces several clinically valuable outputs, including:

- **Corneal Optical Densitometry** maps — quantified backscatter of light 
  through corneal layers (anterior, central, posterior).
- **Topometric / KC-Staging** reports.
- **Belin/Ambrósio Enhanced Ectasia Display** maps.
- **4 Maps Refractive** and **4 Maps Selectable** overviews.
- **Scheimpflug Image Overview** sequences.

For a large-scale retrospective study (order of **thousands of eyes**), acquiring 
these outputs manually is infeasible. This project builds an automated pipeline 
that drives the vendor software through its own UI, exports the required images for 
each eye of each patient, and organizes them into a structured on-disk dataset.

---

## Why Not Just Read the Raw Files? (The Real Bottleneck)

The most obvious approach — parsing the device's own output files — was attempted 
first and **failed** for well-documented reasons. This section is important: it 
explains why UI automation was chosen over every other alternative.

### 1. Proprietary binary formats (`.UDM`, `.SPR`, `.U12`)

The Pentacam software stores examinations in three undocumented, vendor-proprietary 
formats:

- `.UDM` — examination data
- `.SPR` — report data
- `.U12` — internal device format

**No public specification exists.** No third-party parser exists. OCULUS has never 
released the structure of these files.

**Reverse-engineering attempt (and outcome):**
- Converted binaries to hexadecimal and attempted to locate known file signatures 
  (JPEG, BMP, ZIP, etc.) — none found.
- Ran `binwalk` and entropy analysis under Linux — **entropy was near-maximal**, 
  indicating compression and/or encryption.
- Attempted to decompile the C++ binary (the software is built on **Qt**) inside an 
  isolated environment to locate the read/write routines — infeasible without 
  specialized reverse-engineering expertise and beyond the scope of a clinical 
  research project.

**Conclusion:** The raw files are a dead end without vendor cooperation.

### 2. DICOM export — technically possible, practically unusable

DICOM is the correct standards-based approach, and the Pentacam can export DICOM — 
**but**:

- The DICOM export feature requires an **additional commercial license** from the 
  local OCULUS distributor.
- Even after licensing, the exported DICOM files **do not contain the raw 
  densitometry maps we need**. They contain **PDF-style screen captures** of the software's 
  displays — sufficient for a physician's reading, but **not usable for quantitative 
  image analysis or CNN training**.
- The research specifically requires the **three-layer densitometry images per 
  eye** — these are simply not present in the DICOM export.

**Conclusion:** DICOM export solves a compliance problem, not our data problem.

### 3. Bitmap / Excel export — manual and incomplete

The software offers a manual `Bitmap` and `Excel` export. Problems:

- **Manual per-patient workflow** — infeasible for thousands of patients.
- **Only aggregate metrics** (maximum and mean densitometry values) are exported; 
  the actual **layer-wise and zone-wise images** required by the study are **not** 
  included.

**Conclusion:** Insufficient data, unacceptable labor.

### 4. Chosen solution: UI automation

Since every file-level and standards-level path was blocked by the vendor, the only 
remaining option was to **drive the software the way a human operator would** — via 
its own graphical interface. This is what `pywinauto` enables.

---

## Pipeline Overview

The pipeline is split into two almost-identical scripts — one per eye:

| Script | Target eye | Output folder |
| --- | --- | --- |
| `pentaGo_OD.py` | Right eye (Oculus Dexter) | `.../OD/...` |
| `pentaGo_OS.py` | Left eye (Oculus Sinister) | `.../OS/...` |

### High-level flow

```
For each patient row in the Patient Data Management list:
├── Select the patient
├── Wait for the examination list to refresh
├── Group examinations by eye (OD / OS)
├── For the target eye:
│   ├── Select the latest examination
│   ├── Launch the Pentacam module from the Patient Data Manager
│   ├── Dismiss any "no communication with Pentacam" dialog
│   ├── Create the per-patient / per-eye directory tree
│   ├── Switch to Corneal Optical Densitometry
│   │   ├── Capture anterior layer  → densito/anterior.JPG
│   │   ├── Capture central layer   → densito/center.JPG
│   │   └── Capture posterior layer → densito/posterior.JPG
│   ├── Switch to 4 Maps Selectable → ref/4 map.JPG
│   ├── Switch to Belin/Ambrósio    → ref/belin.JPG
│   ├── Switch to Topometric/KC     → ref/kc-staging.JPG
│   ├── Switch to 4 Maps Refractive → 4 map.JPG
│   └── Close the Pentacam window
└── Move to the next patient
```

### Extraction mechanism

Two mechanisms are used in combination, because the Pentacam UI is only **partially** 
accessible to Windows UI Automation:

1. **UI Automation (when possible)** — The patient list, examination list, and the 
   "Pentacam" launch button are accessible via the UIA backend. These are driven 
   through `pywinauto` using `auto_id` and `control_type` selectors, which makes 
   those steps robust to layout changes and DPI scaling.

2. **Screen-coordinate interaction (when necessary)** — Menu items inside the 
   Pentacam viewer (e.g., switching between `Corneal Optical Densitometry`, 
   `4 Maps Selectable`, `Belin/Ambrósio`, etc.) are **not exposed** to UI Automation. 
   For these, the pipeline uses `pywinauto.mouse` with fixed screen coordinates. A 
   `menu_select()` call is attempted first and falls back to coordinate clicks on 
   failure.

> ⚠️ **Resolution dependency:** because of the coordinate-based steps, the scripts 
> assume a specific screen layout. They were developed and validated on a 
> **1920×1080** display. See [Configuration](#configuration).

### Outputs per eye

For every patient and every eye, the following files are exported:

| File | Description |
| --- | --- |
| `densito/anterior.JPG` | Corneal densitometry — anterior layer |
| `densito/center.JPG`   | Corneal densitometry — central layer |
| `densito/posterior.JPG`| Corneal densitometry — posterior layer |
| `ref/4 map.JPG`        | 4 Maps Selectable overview |
| `ref/belin.JPG`        | Belin/Ambrósio Enhanced Ectasia Display |
| `ref/kc-staging.JPG`   | Topometric / KC-Staging report |
| `4 map.JPG`            | 4 Maps Refractive overview |
| `belin.JPG`            | Belin/Ambrósio (secondary copy in refractive workflow) |

### Directory layout

Two parallel roots are used so the raw densitometry set and the reference set can 
be processed independently downstream:

```
D:\dat1\<patient_id>\<OD|OS>\
├── densito\
│   ├── anterior.JPG
│   ├── center.JPG
│   └── posterior.JPG
└── ref\
    ├── 4 map.JPG
    ├── belin.JPG
    └── kc-staging.JPG

D:\dat2\<patient_id>\<OD|OS>\
├── 4 map.JPG
└── belin.JPG
```

Each `<patient_id>` is derived from the patient's index in the source list plus an 
offset, so IDs remain stable and de-identified across the extraction run.

---

## Requirements

- **OS:** Windows 10 / 11 (the target software is Windows-only)
- **Python:** 3.10+
- **Hardware:** display at **1920×1080**, non-scaled (100% DPI) — required by the 
  coordinate-based steps
- **Software:**
  - `OCULUS Pentacam HR` (with the Patient Data Management module, `GO.exe`, 
    and the viewer, `PENTACAM.exe`)
  - `Inspect.exe` (Windows SDK) — useful for verifying that UI elements are 
    accessible before relying on coordinates

### Python dependencies

```
pywinauto
pyautogui
```

---

## Configuration

Before running, edit the following constants at the top of each script:

| Constant | Meaning |
| --- | --- |
| `number_of_pre_patients` | Offset added to the loop index to produce a stable patient ID. Set this to the number of patients that already exist in your archive **before** the first row you want to process. |
| `base_dir` (`D:\dat1`, `D:\dat2`) | Output roots. |
| `app=Application(...).start("...GO.exe")` | Path to the Patient Data Management executable. |
| `app2=Application(...).connect(path="...PENTACAM.exe")` | Path to the viewer executable. |
| Starting row & iteration count | Controlled by the `range(...)` and `{DOWN n}` calls. |

---

## Usage

> Ensure the Pentacam software is installed, licensed, and can open a patient 
> record manually **before** running the automation.

```bash
# Right eye
python src/pentaGo_OD.py

# Left eye
python src/pentaGo_OS.py
```

The scripts launch the Patient Data Management window, iterate over the patient 
list, and write the extracted images to the configured directories. Progress and 
exceptions are printed to stdout.

---

## Known Limitations

- **Coordinate dependency.** Menu navigation inside the Pentacam viewer relies on 
  fixed screen coordinates. Any change to display resolution, DPI scaling, theme, 
  or window position will break those steps. UIA-based selection is attempted first, 
  but the vendor software does not expose all controls.
- **Single-workstation design.** The current version runs on one workstation. 
  Parallelization across multiple installed copies is possible in principle but 
  has not been implemented.
- **Exception swallowing.** Some `except: continue` blocks are used to make the 
  long-running batch resilient to transient UI issues; a proper logging layer is 
  planned.
- **Vendor lock-in.** The pipeline is tightly coupled to a specific Pentacam 
  software version. Version upgrades may break selectors and coordinates.

---

## Ethical & Legal Notice

- This repository **does not contain any patient data**. Only the automation code 
  is published.
- No personally identifiable information (PII) or protected health information 
  (PHI) is stored, logged, or transmitted by this code.
- Any use of this pipeline on clinical data must comply with the applicable 
  institutional review board (IRB) approvals and data-protection regulations.
- The authors are not affiliated with OCULUS Optikgeräte GmbH. All product names 
  are trademarks of their respective owners. This project is an independent 
  research tool that interacts with the vendor software through its public UI.

---

## Acknowledgements

This work was carried out at the **Medical Image & Signal Processing Research 
Center (MISP)**, Isfahan University of Medical Sciences, in collaboration with the 
Ophthalmology Department of **Feiz Hospital**, Isfahan, under the supervision of 
**Dr. Hossein Rabbani** and **Dr. Mohsen Pourazizi**.

---

## Citation

If you find this pipeline useful in your own work, please cite it as:

```bibtex
@misc{tavakoli_pentacam_extractor,
  author       = {Tavakoli, Zahra},
  title        = {Pentacam HR — Automated Batch Data Extraction Pipeline},
  howpublished = {\url{https://github.com/ztavakolii/Pentacam-HR-Data-Extractor}},
  year         = {2025},
  note         = {Research tool developed at MISP, Isfahan University of Medical Sciences}
}
```


---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) 
file for details.


<img width="600" height="600" alt="unnamed_1" src="https://github.com/user-attachments/assets/73056eee-d602-4c69-bfd1-2e00d5ec4079" />
<img width="1200" height="740" alt="posterior" src="https://github.com/user-attachments/assets/0817a18c-6b7f-4db9-904e-435b537d6256" />

<img width="1200" height="740" alt="belin" src="https://github.com/user-attachments/assets/d85dec00-5a7b-4855-a5fb-0421fba3753d" />
<img width="1200" height="740" alt="kc-staging" src="https://github.com/user-attachments/assets/f67c653d-1fa5-4f2f-982f-935078a358c5" />
<img width="1200" height="740" alt="4map" src="https://github.com/user-attachments/assets/060fa216-8893-4928-b4ce-e1a773893e19" />











