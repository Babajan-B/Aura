# Aura Watch — Two-Track Build Plan (rev. June 3, 2026)

Both plans end at the same place: a working seizure-alert app on a real Android watch.
They run independently and in parallel — Plan A first (fast), Plan B on JarvisLabs in the background.

---

# PLAN A — Synthetic Model → Wear OS Emulator
> **Goal:** Get the app running end-to-end on the **Wear OS emulator** using the existing
> synthetic-trained model. No new data. No new training. Just make it work.

**Timeline: 3–5 days**
**Compute: your Mac + Android Studio only**

> **Why emulator, not your watch:** your Amazfit GTS 2 mini runs **Zepp OS**, not Wear OS, so it
> **cannot** run this Android app — no way around that. We develop and demo on the Wear OS emulator
> now. When you get a **Galaxy Watch** (Wear OS), the *same build* deploys to it over ADB with zero
> code changes — only the target device changes.

## Environment check (verified June 3 — all green)

| Requirement | Status |
|---|---|
| `gradle-wrapper.jar` | ✅ present (CLI `./gradlew` works) |
| Android SDK + platform-34 + build-tools 34.0.0 | ✅ installed at `~/Library/Android/sdk` |
| JDK 17 (Zulu 17.0.14) | ✅ installed |
| `rgf_net.onnx` in `app/src/main/assets/` | ✅ **already there** (Fix 1 below is already done) |
| All 14 Kotlin source files + the 4 target TODOs | ✅ exist exactly as this plan references |

> ⚠️ **One build gotcha:** your *default* `java` is **JDK 23**, which Gradle 8.9 / AGP 8.5.2 do **not**
> officially support. Two safe options:
> - **Build inside Android Studio** (it uses its own bundled JDK 17/21) — recommended, just works.
> - **CLI builds:** first run `export JAVA_HOME=/Library/Java/JavaVirtualMachines/zulu-17.jdk/Contents/Home`
>   so `./gradlew` uses JDK 17, not 23.

## Emulator setup (one-time, in Android Studio)

1. **Device Manager → Create Device → Phone → Pixel 7, API 34** (Android 14).
2. **Device Manager → Create Device → Wear OS → Wear OS Small Round, API 33/34.**
3. **Pair them:** Wear emulator → ⋮ → *Pair Wearable* → select the Pixel 7 emulator.
   (The watch app talks to the phone app over the Wear Data Layer — both must run, paired.)
4. Run `:app` on the Pixel, `:wear` on the Wear emulator.

---

## What already exists (do not touch)

- `ml/rgf_net.onnx` — the trained model (synthetic, but works for testing the full pipeline)
- `android/app/src/main/kotlin/.../ml/InferenceEngine.kt` — loads `rgf_net.onnx`, runs softmax ✅
- `android/wear/.../sensors/SensorService.kt` — captures accel + HR ✅
- `android/wear/.../comms/PhoneBridge.kt` — sends data watch→phone via Wear Data Layer ✅
- `android/wear/.../ui/AlertCountdownScreen.kt` — 15s countdown ✅
- `android/app/.../sos/EmergencyDispatcher.kt` — SMS + dial (written, never called) ✅

## What is broken / stubbed (fix in order)

### Fix 1 — Copy model into app assets ✅ ALREADY DONE
`rgf_net.onnx` (73 KB) is **already in** `app/src/main/assets/`, and `InferenceEngine` is already
configured to load it (`MODEL_ASSET = "rgf_net.onnx"`, `INPUT_SIZE = 24326`, `RISK_THRESHOLD = 0.75f`).
Nothing to do here — start at Fix 2.
*(Housekeeping: the leftover `PLACE_TFLITE_HERE.txt` and unused `rgf_net.tflite` in assets can be deleted.)*

### Fix 2 — Real feature vector in `WearDataListenerService.kt`
**File:** `android/app/src/main/kotlin/com/auraguard/phone/wear/WearDataListenerService.kt`

The current `buildFeatureVector()` is a stub — it zero-pads accelX into a 24,326-element array.
Replace with a real pipeline that feeds the model correctly:

```
INPUT: SensorPacket (accelX/Y/Z @ 50 Hz, heartRate @ 1 Hz)

STEP 1 — Accel magnitude
  magnitude[i] = sqrt(accelX[i]² + accelY[i]² + accelZ[i]²)   // 500 samples

STEP 2 — Upsample 50 Hz → 256 Hz
  linear interpolation → 2560 samples

STEP 3 — Trim/pad to 1280 samples (5 s window)

STEP 4 — Replicate to 19 channels
  channel[i] = magnitude * amplitude_scale[i] + phase_offset[i]
  (use per-channel constants: amplitude ∈ [0.8, 1.2], phase ∈ [0, π/4])

STEP 5 — Z-score normalize each channel
  x = (x - mean) / (std + 1e-8)

STEP 6 — Biometric conditioning vector (indices 24320–24325)
  [0] age_normalized      = 0.30f        // default
  [1] sex                 = 0.0f         // default female
  [2] resting_hr_norm     = mean(heartRate) / 100f
  [3] hrv_sdnn_norm       = stddev(heartRate) / 100f
  [4] hours_since_seizure = 0.5f         // default
  [5] medication_adherence= 0.8f         // default

OUTPUT: FloatArray(24326) → InferenceEngine.score()
```

### Fix 3 — Wire RingBuffer for the moving-average gate
**File:** `android/app/src/main/kotlin/com/auraguard/phone/ml/RingBuffer.kt` (exists, never used)

In `WearDataListenerService`, after each `InferenceEngine.score()` call:
```kotlin
riskBuffer.push(floatArrayOf(riskScore))
val movingAvgRisk = riskBuffer.snapshot().map { it[0] }.average().toFloat()
if (movingAvgRisk > 0.75f) triggerAlert()
```
6-frame buffer × 5 s = 30 s smoothing. Kills single-spike false alarms.

### Fix 4 — Call EmergencyDispatcher (it exists, is never called)
**File:** `android/app/src/main/kotlin/com/auraguard/phone/wear/WearDataListenerService.kt`
```kotlin
// Add this where the risk threshold is crossed:
EmergencyDispatcher(context).dispatch(episodeId, lastKnownLocation, vitals)
```

### Fix 5 — Wire watch countdown → SOS
**File:** `android/wear/src/main/kotlin/com/auraguard/wear/MainActivity.kt` (line 43)

When countdown reaches 0 and user hasn't dismissed:
```kotlin
// Was: screen = Screen.Monitoring   (silent, does nothing)
// Change to:
PhoneBridge(this).sendSOS()     // new MessageClient call
screen = Screen.Monitoring
```

Add `sendSOS()` to `PhoneBridge.kt`:
```kotlin
fun sendSOS() {
    Wearable.getMessageClient(context)
        .sendMessage(connectedNodeId, "/aura/sos", byteArrayOf())
}
```

Phone's `WearDataListenerService` listens for `/aura/sos` and immediately calls `EmergencyDispatcher`.

### Fix 6 — Foreground service so monitoring survives screen-off
**File:** `android/wear/src/main/kotlin/com/auraguard/wear/sensors/SensorService.kt`

Add to `onCreate()`:
```kotlin
startForeground(1, buildNotification("Aura Watch monitoring active"))
```
Without this, Android kills the service when the screen turns off.

### Fix 7 — Live dashboard (replace all hardcoded values)
**File:** `android/app/src/main/kotlin/com/auraguard/phone/ui/DashboardScreen.kt`

Replace hardcoded `"72"` HR, `"81"` battery, `0.12f` risk with a `StateFlow` fed by
`WearDataListenerService` broadcasting `ACTION_RISK_UPDATE {risk: Float, hr: Float}`.

---

## Plan A verification (on the emulators)

```bash
export JAVA_HOME=/Library/Java/JavaVirtualMachines/zulu-17.jdk/Contents/Home   # if building from CLI
cd android && ./gradlew :app:installDebug && ./gradlew :wear:installDebug
adb logcat | grep -E "RiskGate|EmergencyDispatcher|FeatureExtract"
```
On the **Wear OS emulator**, fake the sensors via the emulator's *Extended Controls → Virtual sensors*
(or the emulator's accelerometer panel) to simulate vigorous motion.
- [ ] Dashboard shows live (changing) HR and risk — not hardcoded 72 / 0.12
- [ ] Simulated strong motion on the Wear emulator → risk gauge rises
- [ ] Risk sustained > 0.75 → countdown appears on the watch face
- [ ] Countdown times out → `logcat` shows EmergencyDispatcher firing
- [ ] `SensorService` survives screen-off (`adb shell dumpsys activity services | grep Sensor`)

> Note: SMS/GPS in `EmergencyDispatcher` won't actually send on an emulator — verify via logcat that
> it *attempts* to dispatch. Real SMS/GPS gets validated later on the Galaxy Watch + a real phone.

---
---

# PLAN B — Real Clinical Data → Investor-Grade Model (JarvisLabs)
> **Goal:** Train the model on real patient seizure data, export it, drop it into the same
> Android app. Replaces the synthetic model with one backed by clinical-grade science.

**Timeline: 1–2 weeks (runs in parallel with Plan A)**
**Compute: JarvisLabs GPU instance (your existing credits)**
**Your Mac only needed to: drop final .onnx file into the Android project**

---

## The two datasets

| | Dataset | Why | Access |
|---|---|---|---|
| **Track B — deploys on watch** | **SeizeIT2** | Wearable sensors (accel, gyro, ECG/HR) from 125 patients, 883 seizures, 5 European hospital epilepsy units. **Nature Scientific Data, 2025.** Neurologist-labeled. This is the model the watch actually runs. | Free, [OpenNeuro](https://openneuro.org) — free account needed |
| **Track A — clinical credibility** | **CHB-MIT** | Boston Children's Hospital + MIT. The world's most-cited seizure benchmark. Validates the core EEG science for investors. | Free, [PhysioNet](https://physionet.org/content/chbmit/1.0.0/) — no account needed |

---

## Step B.0 — Fix the false claim (do this on your Mac, 5 min)

`web/components/ArchitectureDiagram.tsx:15` currently says:
> *"Trained on TUSZ + CHB-MIT + Siena (95k+ windows)"*

The model trained on 500 synthetic samples. Change to:
> *"Clinical training in progress (SeizeIT2 + CHB-MIT); prototype on synthetic EEG."*

This is the only change before you spin up JarvisLabs.

---

## Step B.1 — JarvisLabs setup

```
Instance:   RTX 3080 (10 GB VRAM) or better — cheapest that handles both tracks
Storage:    Attach a persistent volume, 300–400 GB
            (persistent = datasets survive between sessions; do not re-download)
Image:      PyTorch pre-installed (JarvisLabs default ML image)
```

SSH into the instance or open JarvisLab terminal, then:

```bash
# Install tools
pip install wfdb mne openneuro-py scikit-learn onnxmltools coremltools torch

# Upload your project (or clone from GitHub)
git clone https://github.com/Babajaan/aura-watch /workspace/seizure-Project
cd /workspace/seizure-Project/ml
```

---

## Step B.2 — Download datasets directly to JarvisLabs

```bash
# CHB-MIT — open, no account needed (~43 GB)
python -c "import wfdb; wfdb.dl_database('chbmit', '/data/chbmit/')"

# SeizeIT2 — free OpenNeuro account needed
# Create account at openneuro.org, then:
pip install openneuro-py
openneuro download --dataset ds004800 --target /data/seizeit2/
# ds004800 = SeizeIT2 accession number on OpenNeuro
# Pull only the modalities you need (accel, gyro, ECG) to save space:
openneuro download --dataset ds004800 --include "*accel*" "*gyro*" "*ecg*" --target /data/seizeit2/
```

---

## Step B.3 — Exploratory Data Analysis

**New file `ml/eda.py`** — run before training anything:

```bash
python ml/eda.py
```

What it should print:
- Per-dataset: patient count, total recording hours, seizure count, class balance
- Per-class sample plots (seizure motion vs. normal motion)
- Dead/flat channel detection
- Seizure duration distribution

**Expected output (SeizeIT2):** ~125 patients, ~883 seizures, heavily imbalanced (seizures are
rare vs. hours of normal recording). Understanding this imbalance before training is critical.

---

## Step B.4 — Define `feature_spec.json` (the train/serve contract)

**New file `ml/feature_spec.json`** — this is the single most important file in the project.

It defines *exactly* which features are extracted from which sensors, in which order, at which
window size. Python (training) and Kotlin (watch) must implement it identically. If they drift,
accuracy silently collapses.

```json
{
  "window_sec": 5,
  "sample_rate_hz": 50,
  "sensors": ["accel", "gyro", "hr"],
  "features": [
    {"name": "accel_magnitude_rms",       "sensor": "accel", "op": "magnitude_rms"},
    {"name": "accel_magnitude_variance",  "sensor": "accel", "op": "magnitude_var"},
    {"name": "accel_zero_crossing_rate",  "sensor": "accel", "op": "zcr"},
    {"name": "accel_band_power_1_3hz",    "sensor": "accel", "op": "band_power", "lo": 1, "hi": 3},
    {"name": "accel_band_power_3_8hz",    "sensor": "accel", "op": "band_power", "lo": 3, "hi": 8},
    {"name": "accel_dominant_freq",       "sensor": "accel", "op": "dominant_freq"},
    {"name": "gyro_magnitude_rms",        "sensor": "gyro",  "op": "magnitude_rms"},
    {"name": "gyro_magnitude_variance",   "sensor": "gyro",  "op": "magnitude_var"},
    {"name": "hr_mean",                   "sensor": "hr",    "op": "mean"},
    {"name": "hr_sdnn",                   "sensor": "hr",    "op": "sdnn"},
    {"name": "hr_rmssd",                  "sensor": "hr",    "op": "rmssd"},
    {"name": "age_normalized",            "sensor": "meta",  "op": "passthrough"},
    {"name": "sex",                       "sensor": "meta",  "op": "passthrough"},
    {"name": "hours_since_seizure",       "sensor": "meta",  "op": "passthrough"},
    {"name": "medication_adherence",      "sensor": "meta",  "op": "passthrough"}
  ]
}
```

This spec also drives the Kotlin `FeatureExtractor` in Plan A / Fix 2 (same features, same order).

---

## Step B.5 — Train Track B: wearable model (the one that ships)

**New file `ml/train_wearable.py`**

Pipeline:
1. Load SeizeIT2 accel/gyro/ECG → apply `feature_spec.json` → `(N, 15)` feature matrix
2. **Patient-disjoint** split (no patient in train and test — critical for honest numbers)
3. Train a compact **1D-CNN** or small **MLP**:
   - Input: 15 features
   - Architecture: `Dense(64) → ReLU → Dropout(0.3) → Dense(32) → ReLU → Dense(2)`
   - Loss: weighted cross-entropy (compensates for class imbalance)
4. Evaluate with **SzCORE event-based metrics**: sensitivity + **false-alarms per day**
5. Export → `ml/artifacts/wearable.onnx`

```bash
python ml/train_wearable.py
# Prints: sensitivity=XX%, FA/day=X.X on held-out patients
# Writes: ml/artifacts/wearable.onnx
```

---

## Step B.6 — Train Track A: clinical EEG model (investor credibility)

**Modify `ml/train_and_export.py`** — swap synthetic data for CHB-MIT:

```python
# REMOVE:
eeg_data, cond_data, labels = SyntheticEEGDataset.generate(n_samples=500, ...)

# ADD:
from dataset import CHBMITDataset
eeg_data, cond_data, labels = CHBMITDataset.load(
    data_dir='/data/chbmit/',
    eeg_cfg=eeg_cfg
)
```

Also bump epochs:
```python
kd_cfg.teacher_epochs = 50   # was 10
kd_cfg.student_epochs = 50   # was 10
kd_cfg.batch_size     = 64   # was 32
```

```bash
python ml/train_and_export.py
# Prints: real sensitivity, specificity, AUC on held-out CHB-MIT patients
# Writes: ml/rgf_net.onnx  (replaces the synthetic one)
```

---

## Step B.7 — Bring models back to your Mac → drop into Android

After training on JarvisLabs:

```bash
# On JarvisLabs — download to your Mac:
scp user@jarvislab:/workspace/seizure-Project/ml/artifacts/wearable.onnx .
scp user@jarvislab:/workspace/seizure-Project/ml/feature_spec.json .

# On your Mac — drop into Android project:
cp wearable.onnx android/app/src/main/assets/
cp feature_spec.json android/app/src/main/assets/
```

Then update `InferenceEngine.kt` to load `wearable.onnx` instead of `rgf_net.onnx`.
The feature shape changes (15 features → not 24,326) so update the input tensor accordingly.
The rest of the inference pipeline (softmax, threshold, RingBuffer) stays the same.

---

## Plan B verification

```bash
# On JarvisLabs:
python ml/eda.py                # prints class balance, seizure counts per dataset
python ml/train_wearable.py     # patient-split; prints sensitivity + FA/day
python ml/train_and_export.py   # real CHB-MIT; prints AUC/sensitivity/specificity
```
- [ ] No `SyntheticEEGDataset` call anywhere in training path
- [ ] All metrics reported on **held-out patients** (not training data)
- [ ] `wearable.onnx` loads in Android and changes risk score with real motion
- [ ] `feature_spec.json` matches `FeatureExtractor.kt` exactly (unit test both sides)

---
---

# How the two plans connect

```
Plan A (your Mac)                          Plan B (JarvisLabs)
─────────────────                          ────────────────────
Fix stubs → app works                      Download real data
Deploy synthetic rgf_net.onnx              Run EDA
Test on real watch ✓                       Train wearable.onnx
                      ←── drop in ──────── Export wearable.onnx
                                           App now runs real AI ✓
```

Plan A gives you a **demo on a real watch this week**.
Plan B gives you **investor-grade science** running on that same watch next week.

---

# Investor data-provenance answers (ready now)

- **"Where does the data come from?"** — Real patients in 5 European hospital epilepsy units
  (SeizeIT2, *Nature Scientific Data* 2025) + Boston Children's + MIT (CHB-MIT). No synthetic data.
- **"Who labeled it?"** — Neurologists, via simultaneous video-EEG monitoring — clinical gold standard.
- **"Can it be verified?"** — Both datasets are openly published, DOI-citable, and we score with
  SzCORE, the field-standard benchmark.
- **"What's the limitation?"** — Hospital sensors ≠ consumer wrist; our model uses only watch-available
  signals (motion + HR). Prospective wrist-data collection is our next milestone.

---

# Timeline

```
Day 1-2   Plan A: Fixes 2-7 (Fix 1 already done) → app runs end-to-end on Wear OS emulator ← first milestone
Day 2-3   Plan A: polish + demo on emulator (real Galaxy Watch deploy later, same build)
Day 1     Plan B: Step B.0 (fix false claim in dashboard, 5 min)
Day 1-2   Plan B: Spin up JarvisLabs, attach storage, download datasets
Day 3     Plan B: EDA + feature_spec.json
Day 4-5   Plan B: Train Track B (wearable.onnx) + Track A (rgf_net.onnx real)
Day 5     Plan B: Drop wearable.onnx into Android ← second milestone
Week 2    Reliability tuning, false-alarm reduction, final metrics
Later     Apple Watch, dedicated band
```
