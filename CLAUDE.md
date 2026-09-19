# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project Overview

**Aura Watch** is a hackathon submission: a fully on-device seizure pre-ictal prediction system combining mobile sensing, edge AI, and real-time alerting across a Wear OS watch, Android phone, and Next.js caregiver dashboard.

**Key differentiator**: Knowledge-distilled RGF-Net (37.5K parameters, 36.7 KB TFLite) predicts seizures 30+ seconds before onset, running entirely on-device with zero cloud dependency.

---

## Repository Structure

```
seizure-Project/
├── ml/                    ← PyTorch training pipeline (teacher/student KD, TFLite export)
├── web/                   ← Next.js 15 caregiver dashboard (React 19, Tailwind, Recharts)
├── android/               ← Kotlin multi-module project
│   ├── app/               ← Phone: TFLite inference, SOS orchestration, event logging
│   ├── wear/              ← Wear OS: sensor capture, alert UI, 15s countdown
│   └── shared/            ← SensorPacket data model (both platforms)
├── docs/                  ← ARCHITECTURE.md, MODEL_CARD.md, DEMO_SCRIPT.md, ROADMAP.md
├── reference/             ← HuggingFace Space reference (PyTorch source models)
└── [root]
    ├── README.md          ← Full project overview
    ├── 1.prd              ← Product requirements
    ├── 00_START_HERE.md   ← Hackathon submission quickstart
```

---

## Build & Run Commands

### ML Pipeline (PyTorch → ONNX → TFLite)

```bash
# Setup (Python 3.11–3.13; 3.11 most reliable for TF/ONNX toolchain)
cd ml
python3.11 -m venv .venv
source .venv/bin/activate
pip install torch numpy onnx onnxruntime onnx2tf tensorflow tf-keras

# Run end-to-end training & export (~5–15 min on CPU)
python train_and_export.py
# Outputs: rgf_net.tflite, rgf_net.onnx, teacher_best.pt, student_best.pt, training_report.json
```

**Key**: Produces `rgf_net.tflite` (~36.7 KB INT8) for Android; INT8 quantization is attempted first, falls back to float16/float32 if GRU ops don't cleanly quantize.

**Configuration**: Edit `train_and_export.py:train()` to adjust epochs, batch size, dataset size. Uses synthetic EEG by default; replace `SyntheticEEGDataset.generate()` with real CHB-MIT/TUH loader for production.

### Web Dashboard (Next.js 15)

```bash
cd web
npm install                # or pnpm install
npm run dev                # http://localhost:3000
npm run build && npm start # production
npm run lint               # Next.js linter
```

**Stack**: Next.js 15 (App Router) · React 19 · TypeScript (strict) · Tailwind CSS 3.4 · Framer Motion · Recharts · Lucide icons · Radix UI.

**Sections**: Hero (animated brain) · Monitor (EEG + risk gauge) · Architecture (KD diagram) · Watch (mockup) · Simulator (biometric sliders POSTing to `/api/infer`) · Footprint (model size compare).

### Android (Kotlin + Gradle 8.5.2)

```bash
cd android

# Phone app (Pixel 7, API 34 recommended)
./gradlew :app:installDebug

# Wear OS app (Wear OS 4 small round, API 33)
./gradlew :wear:installDebug

# Build both
./gradlew build
```

**TFLite model placement**: Drop `rgf_net.tflite` into `app/src/main/assets/`. Falls back to deterministic stub if missing (dashboard still renders, no real inference).

**Emulator setup**: Phone (Pixel 7 API 34) + Wear OS emulator, paired via Companion app or Device Manager. Grant permissions: `BODY_SENSORS`, `SEND_SMS`, `CALL_PHONE`, `ACCESS_FINE_LOCATION`, `POST_NOTIFICATIONS`.

**Full build**: Run in Android Studio Hedgehog (2023.1.1+) or gradle from CLI.

---

## Data Flow & Architecture

### End-to-End Pipeline

```
Wear OS Watch                Android Phone                 Next.js Dashboard
    ↓                            ↓                              ↓
  Sensors                 Inference Engine            Caregiver Console
  (accel, HR,     →    RGF-Net TFLite INT8    →    Live risk tile
   gyro, SpO₂,          SOS Orchestration           Episode log
   temp)                                             JSON replay
                        ↓
                   P(pre-ictal) > 0.75?
                        ↓
                   15s Cancellable Countdown
                        ↓ (if not dismissed)
                   SMS + Haptic + Alarm
```

### Key Components

| Component | Location | Responsibility |
|-----------|----------|-----------------|
| **RGF-Net** | `ml/train_and_export.py` | 37.5K params; knowledge-distilled from 661K Transformer teacher via Hinton KD + feature distillation |
| **Model I/O** | `ml/README.md` | Inputs: `eeg_input` (B, 19, 1280) + `biometric_cond` (B, 6); Outputs: logits (B, 2) + embeddings (B, 128) |
| **Watch sensors** | `android/wear/sensors/SensorService.kt` | Captures 6 biometric channels at 1–50 Hz; ring-buffered to 10 s |
| **EEG simulator** | `android/app/Sensor19ChEegSimulator.kt` | Demo-only: synthesizes 19-ch EEG @ 256 Hz from biometrics (replaced by real headband in Phase 1) |
| **Inference** | `android/app/ml/RgfNetRunner.kt` | TFLite NNAPI delegate; ~22 ms median latency on Pixel 7 |
| **Decision logic** | `android/app/logic/PreIctalGate.kt` | Hysteresis gate: requires 3 consecutive frames > 0.75 before triggering |
| **SOS escalation** | `android/app/sos/EmergencyDispatcher.kt` | SMS to ICE contacts + watch alarm + caregiver dashboard push |
| **Watch alert** | `android/wear/ui/AlertCountdownScreen.kt` | 15s cancellable countdown + haptic pattern + user "I'm OK" button |

---

## Threading & Concurrency (Android)

**Phone process**:
- `main thread` — UI only, never blocks
- `SensorIoCoroutine` — BLE read loop (`Dispatchers.IO`)
- `InferenceCoroutine` — single-thread executor pinned to NNAPI (no contention)
- `LogicCoroutine` — collects inference flow, runs decision gate
- `SosCoroutine` — cold-started only on escalation (`Dispatchers.IO`)

**Watch process**:
- `main thread` — Compose UI
- `SensorCoroutine` — Health Services + SensorManager
- `BleAdvertiseService` — foreground service, GATT server

**Critical constraints**:
- No blocking calls on main thread
- Single inference thread (prevents NNAPI contention)
- Backpressure: BLE → inference uses `Channel(capacity=1, onBufferOverflow=DROP_OLDEST)` — stale windows dropped, never queued
- Cold SOS: escalation coroutine created only at threshold-crossing time

---

## Model Card & Thresholds

See `docs/MODEL_CARD.md` for full specs. Key numbers:

| Metric | Value | Notes |
|--------|-------|-------|
| Model size | 36.7 KB | INT8 quantized TFLite |
| Parameters | 37,554 | 17.6× compression vs. teacher (661K) |
| Latency | ~22 ms | Inference on Pixel 7 CPU (5s window, 256 Hz, 19 ch) |
| Risk threshold | 0.75 | Pre-ictal probability cutoff; triggers after 3 consecutive frames |
| Moving average window | 6 (30 s) | Smoothing before alert escalation |
| Input window | 5 s @ 256 Hz | 19 channels (10–20 EEG system) |
| Biometric conditioning | 6 fields | age, sex, resting HR, HRV, hours since seizure, medication adherence |

---

## Important Files & Directories

### ML
- `train_and_export.py` — Master training + export driver; edit `train()` for hyperparams
- `rgf_net.tflite` — Deployed model (check size/quantization mode in output)
- `training_report.json` — Full history + param breakdown
- `../reference/aura_agent/` — PyTorch source models (teacher, student, feature extractors)

### Android
- `app/src/main/assets/` — Drop `rgf_net.tflite` here before build
- `app/build.gradle.kts` — Phone app dependencies + TFLite/NNAPI config
- `wear/build.gradle.kts` — Wear OS app + sensor/comms config
- `shared/src/main/kotlin/SensorPacket.kt` — Serializable DTO for BLE payloads

### Web
- `app/` — Next.js App Router (pages, layout, API routes)
- `app/api/infer` — Mock inference endpoint (mirrors RGF-Net I/O signature)
- `components/` — UI sections (Hero, Monitor, Watch, Simulator, Footprint)

### Docs
- `ARCHITECTURE.md` — System topology, data flow, threading, module breakdown
- `MODEL_CARD.md` — Fairness, limitations, training data, intended use
- `DEMO_SCRIPT.md` — 3–15 min live demo runbook
- `ROADMAP.md` — Phase 1 (real EEG headband), Phase 2 (on-device TTS), Phase 3 (multi-seizure types)

---

## Development Workflow

1. **Add features**: Modify source code in `ml/`, `web/`, or `android/` as needed.
2. **Test ML changes**: Run `python train_and_export.py` to regenerate `rgf_net.tflite`.
3. **Copy model to Android**: Place `ml/rgf_net.tflite` → `android/app/src/main/assets/`.
4. **Build Android**: `./gradlew :app:installDebug && ./gradlew :wear:installDebug`.
5. **Run web**: `cd web && npm run dev`.
6. **Test integration**: Use emulators or real devices; simulator on web dashboard accepts biometric sliders.

---

## Known Limitations & TODOs

### ML
- **Synthetic data**: Uses synthetic EEG for demo; replace with CHB-MIT/TUH for real validation.
- **INT8 quantization**: GRU ops may not cleanly quantize; falls back to float16/float32 (still <200 KB).
- **Stub fallback**: If `onnx2tf` fails, model is a placeholder CNN with correct I/O shape; requires working `onnx2tf` / TF / GRU-quant toolchain for real seizure detection.

### Android
- **Simulated EEG**: `Sensor19ChEegSimulator` is demo-only; Phase 1 replaces with real EEG headband.
- **Room Database**: Event log uses in-memory DAO; wire to real `RoomDatabase` for persistence.
- **Foreground service**: `SensorService` should be a true foreground service with notification.
- **Watch-to-phone risk feedback**: Implement `MessageClient` channel so phone can push risk scores back to watch.
- **Unit tests**: Add tests for `RingBuffer` and `EmergencyDispatcher`.

### Web
- **Mock inference**: `/api/infer` uses heuristic shape; replace with real RGF-Net WASM or REST call to phone.
- **No state persistence**: Dashboard doesn't persist episodes; wire to a backend if needed.

---

## Submission & Demo

- **Hackathon quick start**: See `00_START_HERE.md`
- **Live demo**: `cd web && npm run dev` → http://localhost:3000
- **Full runbook**: `docs/DEMO_SCRIPT.md`
- **HuggingFace reference**: https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian

---

## Resources

- **Root README**: Full problem statement, solution overview, metrics
- **Docs**: `ARCHITECTURE.md` (detailed system design), `MODEL_CARD.md` (ML specs), `ROADMAP.md` (future phases)
- **PRD**: `1.prd` (product requirements, Watch Edition)

---

## Contact

**Author**: Jaan (waadalharbi2@gmail.com)  
**GitHub**: @Babajaan  
**HuggingFace**: https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian
