# Real Data Deployment Plan
## Aura Watch — From Synthetic to Clinical-Grade
**Version:** 1.0 | **Date:** 2026-04-28

---

## The Core Problem

The current model trains on `SyntheticEEGDataset` — procedurally generated sine waves. This produces 100% validation accuracy because the model memorizes artificial signal patterns. On real EEG it will perform near-randomly.

Every phase in this plan is a prerequisite for the next. Do not skip.

---

## Phase 0 — Understand What Real Data Looks Like

### What the model expects (non-negotiable)
```
Input:  (N, 19, 1280)   — 19 EEG channels, 256 Hz, 5-second windows
        (N, 6)           — biometrics [age_norm, sex, resting_hr, hrv_sdnn,
                                       hours_since_seizure, medication_adherence]
Label:  (N,)             — 0=inter-ictal, 1=pre-ictal (30-min window before seizure)
```

### What real clinical EEG looks like
- Sampling rates vary: 256 Hz, 512 Hz, 1024 Hz — must resample to 256 Hz
- Channel counts vary: some datasets have 23, 18, or 21 channels — must map to 10-20 standard
- Artifacts everywhere: eye blinks (EOG), muscle noise (EMG), electrode pops, 50/60 Hz line noise
- Class imbalance: pre-ictal windows are rare (~5–10% of total recording time)
- Seizure onset labels have uncertainty: ±30 seconds is typical inter-rater reliability

---

## Phase 1 — Real Dataset Acquisition

### Tier 1: Free, publicly available, start here

| Dataset | Patients | Seizures | Format | Where |
|---|---|---|---|---|
| **CHB-MIT Scalp EEG** | 23 pediatric | 198 | EDF, 256 Hz, 23 ch | physionet.org/content/chbmit |
| **Siena Scalp EEG** | 14 adult | 47 | EDF, 512 Hz, 29 ch | physionet.org/content/siena-scalp-eeg |
| **Helsinki University** | 79 neonatal | 460 | EDF, 256 Hz, 19 ch | physionet.org/content/neonatal-eeg |
| **EPILEPSIAE** | 30 adult | 277 | EDF, 1024 Hz, 19–93 ch | epilepsiae.eu (registration) |
| **TUH EEG Corpus** | 10,000+ | ~3,500 | EDF, various | isip.piconepress.com (apply) |

### Tier 2: Apply for access (weeks to months)

| Dataset | Size | Notes |
|---|---|---|
| **iEEG.org portal** | 1,000+ hours | Mix of scalp + intracranial |
| **IEEG Portal** | 100+ patients | Requires institutional affiliation |
| **UK Biobank (EEG)** | 8,000+ subjects | Resting state, no seizure labels |

### Start with: **CHB-MIT**
- Freely downloadable today
- Gold standard in seizure research since 2010
- 256 Hz native — perfect match for our config
- Has pre-ictal annotations (seizure onset + offset times)

```bash
# Download CHB-MIT (≈13 GB)
wget -r -N -c -np https://physionet.org/files/chbmit/1.0.0/ -P data/chbmit/
```

---

## Phase 2 — Data Pipeline (Replace SyntheticEEGDataset)

### 2.1 Install real EEG processing stack
```bash
pip install mne pyedflib numpy scipy scikit-learn torch
```

### 2.2 Build `ml/real_data_pipeline.py`

```
raw EDF file
    ↓  mne.io.read_raw_edf()
    ↓  Resample to 256 Hz
    ↓  Pick 19 channels (10-20 standard)
    ↓  Bandpass filter 0.5–100 Hz (4th-order Butterworth)
    ↓  Notch filter 50/60 Hz (power line)
    ↓  Z-score normalize per channel per recording
    ↓  Artifact rejection (amplitude > 500 µV → discard window)
    ↓  Epoch into 5s windows with 50% overlap
    ↓  Label: pre-ictal if window ends within 30 min before seizure onset
             AND is >4h from any other seizure (inter-ictal gap rule)
    ↓  Save: (N, 19, 1280) float32 + (N,) int64 labels
```

### 2.3 Key labeling rules (from literature)
```python
PREICTAL_WINDOW_MINUTES   = 30   # windows ending 0–30 min before seizure
INTERICTAL_GAP_MINUTES    = 240  # exclude 4h after seizure ends
SEIZURE_BUFFER_SECONDS    = 5    # exclude windows overlapping with ictal period
MAX_AMPLITUDE_UV          = 500  # artifact threshold
WINDOW_SEC                = 5.0
OVERLAP_RATIO             = 0.5
```

### 2.4 Class balance strategy
Real data is severely imbalanced (~10:1 interictal vs pre-ictal). Handle with:
1. **Weighted sampling** — `pos_weight=10.0` in CrossEntropyLoss (already in KDConfig)
2. **SMOTE** — synthetic minority oversampling in feature space (after conv extraction)
3. **Focal loss** — down-weight easy negatives
4. **Hard negative mining** — keep interictal windows near artifacts (confounders)

---

## Phase 3 — Real Model Training

### 3.1 Prerequisite: GPU
CHB-MIT training with real data needs a GPU. Options:
- Google Colab Pro (A100, free tier T4)
- Kaggle Notebooks (2×T4, free)
- Local GPU (RTX 3080+)
- AWS p3.2xlarge ($3/hr)

### 3.2 Patient-independent cross-validation
**Critical:** never mix windows from the same patient in train and test sets.

```
Leave-One-Patient-Out (LOPO) cross-validation:
  - 23 patients → 23 folds
  - Each fold: train on 22 patients, test on 1
  - Report: mean sensitivity, mean specificity, mean AUC across all 23 folds
```

This is the only evaluation methodology journals and regulators accept.

### 3.3 Updated training protocol
```python
# Teacher: 200 epochs (not 10), cosine LR decay
teacher_lr    = 1e-3
teacher_epochs = 200
batch_size     = 64

# Student KD: 150 epochs
student_lr    = 3e-4
student_epochs = 150
temperature   = 4.0
alpha         = 0.7   # KD soft label weight
lambda_feat   = 0.3   # feature distillation weight
pos_weight    = 10.0  # class imbalance correction
```

### 3.4 Minimum acceptable performance targets

| Metric | Minimum | Target |
|---|---|---|
| Sensitivity (recall) | 70% | 90%+ |
| Specificity | 85% | 95%+ |
| False positive rate | <2/hr | <1/hr |
| AUC-ROC | 0.80 | 0.92+ |
| Prediction horizon | 10 min | 30 min |

If sensitivity < 70% or FP rate > 2/hr, **do not proceed to device deployment.**

---

## Phase 4 — Real Sensor Hardware Decision

This is the most important architectural decision in the entire project.

### Option A: EEG Headband (recommended for pre-ictal prediction)

| Device | Channels | Hz | Price | Android SDK |
|---|---|---|---|---|
| **Muse 2 / S** | 4 ch | 256 Hz | $300 | MuseDirect API |
| **OpenBCI Cyton** | 8–16 ch | 250 Hz | $500 | BrainFlow (Android) |
| **Neurosity Crown** | 8 ch | 256 Hz | $999 | REST API |
| **Emotiv EPOC X** | 14 ch | 128 Hz | $849 | Emotiv SDK |

**Gap:** Our model needs 19 channels. A 4-channel Muse gives partial coverage. Options:
1. Retrain with 4-channel Muse input (reduce `n_channels=4`, rerun full pipeline)
2. Use OpenBCI with 8–16 channels (closer to full coverage)
3. Interpolate missing channels using spherical spline (MNE supports this)

### Option B: Watch-only motion-based detection (tonic-clonic only, no pre-ictal)

Instead of predicting pre-ictal (needs EEG), detect the seizure in progress from movement:

| Sensor | What it captures | Seizure signal |
|---|---|---|
| Accelerometer 50Hz | rhythmic jerking | High-amplitude 1–5 Hz burst |
| Gyroscope 50Hz | rotation/convulsion | Coupled with accel |
| PPG/HR | ictal tachycardia | HR spike >150% baseline |

This is clinically validated (Apple Watch Study 2020, Embrace2 FDA-cleared device).

**Recommendation for hackathon → production path:**
- **Demo:** Watch-only accel+HR model (simpler, deployable today)
- **Production:** EEG headband + watch for full pre-ictal prediction

---

## Phase 5 — Clinical Validation

### 5.1 Institutional Requirements
Before collecting data from any patient, you need:

| Requirement | Body | Timeline |
|---|---|---|
| IRB/Ethics approval | Your institution or hospital IRB | 2–6 months |
| Data Use Agreement | Hospital or data custodian | 1–3 months |
| HIPAA compliance plan | Your institution's privacy officer | 4–8 weeks |
| Informed consent protocol | IRB-approved form | With IRB |

**You cannot collect new patient EEG without IRB approval. Using existing public datasets (CHB-MIT) does not require IRB.**

### 5.2 Minimum study design (for publishable results)

```
Retrospective validation study:
  - Dataset: CHB-MIT (23 patients, 198 seizures)
  - Method: LOPO cross-validation
  - Primary endpoint: sensitivity ≥ 70% at FPR ≤ 0.15/hr
  - Secondary endpoints: prediction horizon, alert lead time distribution
  - Comparison: baseline methods from literature (SVM, LSTM-only)
  - Report: ROC curves, confusion matrices, per-patient performance
```

### 5.3 Path to prospective study (after retrospective validation)
1. Partner with epilepsy clinic (neurology department at a hospital)
2. Recruit 20–50 patients with refractory focal epilepsy
3. Patients wear device for 4 weeks
4. Neurologist reviews every alert (gold standard labeling)
5. Pre-register the study at ClinicalTrials.gov

---

## Phase 6 — Regulatory Pathway

### 6.1 FDA (United States)

| Classification | Device type | Path | Timeline |
|---|---|---|---|
| **Class II** | Non-implantable seizure detection aid (decision support) | 510(k) clearance | 3–12 months |
| **Class III** | Implantable or standalone diagnostic device | PMA | 3–7 years |

**Your device = Class II, 510(k).**

Predicate devices for 510(k):
- Empatica Embrace2 (K193921) — wrist wearable seizure detection
- Neurologic Solutions PathFinder (K082453) — EEG seizure detection

Key 510(k) requirements:
- Substantial equivalence to predicate
- Bench testing (signal processing accuracy)
- Clinical performance data (sensitivity/specificity)
- Software documentation (IEC 62304 compliance)
- Cybersecurity analysis (FDA 2023 guidance)

### 6.2 EU MDR (Europe)
- Class IIa medical device (Rule 11 — active therapeutic device)
- Requires CE marking via Notified Body
- Clinical evaluation report (CER)
- Post-market surveillance plan
- Timeline: 18–36 months, €100K–300K

### 6.3 SAUDI ARABIA / GCC (if relevant given your location)
- SFDA (Saudi Food and Drug Authority) — Medical Device Regulation
- Class B (medium risk) — requires SFDA registration
- Accepts FDA 510(k) or CE mark as basis for SFDA registration
- Timeline: 6–18 months after FDA/CE

---

## Phase 7 — Production Architecture

### 7.1 Full system with real sensors

```
┌────────────────────┐   BLE 5.0    ┌─────────────────────┐
│  EEG HEADBAND      │────────────►│  WEAR OS WATCH      │
│  (Muse 2 / OCBC)   │             │  - Aggregates EEG    │
│  4–16 ch, 256 Hz   │             │  - Accel + HR        │
└────────────────────┘             │  - Ring buffer 10s   │
                                   └──────────┬──────────┘
                                              │ BLE
                                              ▼
                                   ┌─────────────────────┐
                                   │  ANDROID PHONE      │
                                   │  - Full 19-ch EEG   │
                                   │    (interpolated)   │
                                   │  - RGF-Net ONNX     │
                                   │    inference        │
                                   │  - Risk score ≥0.75 │
                                   │    → alert          │
                                   └──────────┬──────────┘
                                              │
                                              ▼
                                   Emergency Contact
                                   + Neurologist Portal
                                   (encrypted, HIPAA)
```

### 7.2 Data privacy (non-negotiable)

| Requirement | Implementation |
|---|---|
| No raw EEG leaves device | All inference on-device only |
| Encrypted storage | Android Keystore, AES-256 |
| HIPAA-compliant logs | No PII in logs, de-identified events only |
| Consent revocation | One-tap delete all local data |
| Audit trail | Immutable local log of all alerts |

---

## Phase 8 — Immediate Next Steps (What to do right now)

### Week 1 — Get real data running

```bash
# 1. Download CHB-MIT (start now, 13 GB)
wget -r -N -c -np https://physionet.org/files/chbmit/1.0.0/ -P data/chbmit/

# 2. Install EEG processing stack
cd ml && source .venv/bin/activate
pip install mne pyedflib scipy scikit-learn

# 3. Build real_data_pipeline.py (replaces SyntheticEEGDataset)
# 4. Process CHB-MIT → train/val/test splits (patient-independent)
# 5. Retrain teacher + student on real data
# 6. Evaluate: sensitivity, specificity, FPR on held-out patients
```

### Week 2 — Hardware decision
- Order Muse 2 ($300) or OpenBCI Cyton ($500)
- Build BrainFlow Android integration (brainflow.org/android)
- Reduce model to 4-channel input if using Muse
- Test real BLE streaming → ring buffer → inference

### Week 3 — Validation
- Run LOPO cross-validation on CHB-MIT
- Compare performance vs published baselines
- If sensitivity ≥ 70%: proceed to hardware testing
- If sensitivity < 70%: revisit preprocessing / model architecture

### Month 2–3 — IRB + clinical partnership
- Contact nearest epilepsy clinic / neurology department
- Present retrospective validation results
- Propose a small pilot study (10 patients, 2 weeks)
- Submit IRB application

---

## Effort and Cost Estimate

| Phase | Timeline | Cost | Bottleneck |
|---|---|---|---|
| Phase 0–1: Dataset acquisition | 1 week | Free (CHB-MIT) | Download time |
| Phase 2: Data pipeline | 2–3 weeks | Free | Engineering |
| Phase 3: Real training | 2–4 weeks | $50–200 (GPU) | Model performance |
| Phase 4: Hardware integration | 4–8 weeks | $300–1000 | BLE SDK |
| Phase 5: Retrospective validation | 4–8 weeks | Free | Statistics |
| Phase 5: Prospective study | 6–18 months | $50K–200K | IRB, recruitment |
| Phase 6: FDA 510(k) | 12–24 months | $300K–800K | Regulatory |
| **Total to market** | **2–4 years** | **$500K–1.5M** | **Funding** |

---

## The Honest Bottom Line

| Stage | What you have | What you need |
|---|---|---|
| **Today** | Working prototype, real trained architecture, live demo | Replace synthetic data |
| **1 month** | Real CHB-MIT trained model, measured performance | GPU access, 2–3 weeks dev |
| **3 months** | Hardware-validated prototype with real EEG sensor | $300 Muse + dev time |
| **1 year** | IRB-approved pilot study underway | Clinical partner, ~$50K |
| **3 years** | FDA clearance, market-ready device | $500K+, regulatory team |

**The next single action:** Download CHB-MIT and build the real data pipeline. Everything else — hardware, clinical validation, regulatory — depends on first proving the model works on real EEG data. Until that is done, nothing else moves forward.

---

## Key References

| Topic | Reference |
|---|---|
| CHB-MIT dataset | Shoeb A. (2010). MIT PhD thesis |
| Seizure prediction review | Kuhlmann L. et al. (2018). Nature Reviews Neurology |
| Pre-ictal detection state-of-art | Rasheed K. et al. (2021). IEEE TNSRE |
| Knowledge Distillation | Hinton G. et al. (2015). arXiv 1503.02531 |
| FiLM conditioning | Perez E. et al. (2018). AAAI — arXiv 1709.07871 |
| Edge EEG deployment | Roy Y. et al. (2020). arXiv 2012.00307 |
| FDA 510(k) predicate | Empatica Embrace2 — K193921 |
| Wear OS EEG integration | BrainFlow SDK — brainflow.org |
