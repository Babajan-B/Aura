<div align="center">

# 🛡️ Aura Watch — On-Device Seizure Pre-Ictal Guardian

**A pocket-sized neural early-warning system for tonic-clonic seizures.**

![Hackathon](https://img.shields.io/badge/AI%20Hackathon-2026-blueviolet?style=for-the-badge)
![Model](https://img.shields.io/badge/RGF--Net-37.5K%20params-success?style=for-the-badge)
![Footprint](https://img.shields.io/badge/INT8%20TFLite-37%20KB-brightgreen?style=for-the-badge)
![Latency](https://img.shields.io/badge/Latency-%3C500ms-orange?style=for-the-badge)
![Privacy](https://img.shields.io/badge/Cloud-Zero-black?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

[Live Reference Demo](https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian) · [Architecture](docs/ARCHITECTURE.md) · [Demo Script](docs/DEMO_SCRIPT.md) · [Model Card](docs/MODEL_CARD.md) · [Roadmap](docs/ROADMAP.md)

</div>

---

## 🩺 The Problem

> Roughly **65 million people** worldwide live with epilepsy. **1-in-1000** dies each year from **SUDEP** (Sudden Unexpected Death in Epilepsy) — a class of fatalities that an early warning of **even 30 seconds** can prevent by triggering recovery posture, calling a caregiver, or pulling someone away from danger.

Existing solutions either:

| Existing approach | Why it fails |
|---|---|
| Hospital EEG monitoring | Tethered, $$$, not portable |
| Reactive fall-detection watches | Trigger **after** the seizure — too late |
| Cloud-based ML services | High latency, privacy nightmare, useless without signal |

**Aura Watch** flips the model: a **37 KB neural network** runs **fully on-device**, fuses **EEG + biometrics**, and predicts the **pre-ictal phase** *before* the convulsion. No cloud. No latency. No data leaves the wrist.

---

## ✨ The Solution

A three-tier **edge-AI safety net** built around our distilled RGF-Net student model:

```
┌──────────────┐   BLE   ┌───────────────┐   USB/ADB  ┌────────────────┐
│  Wear OS     │ ──────▶ │  Android      │ ─────────▶ │  Next.js Web   │
│  Watch App   │ sensors │  Phone App    │  events    │  Dashboard     │
│              │         │               │            │  (caregivers)  │
│ • Haptic     │         │ • RGF-Net     │            │                │
│ • Countdown  │         │   TFLite INT8 │            │ • Live tile    │
│ • SOS UI     │         │ • SOS dialer  │            │ • Episode log  │
└──────────────┘         │ • GPS         │            │ • Replay       │
                         └───────────────┘            └────────────────┘
                                  │
                                  ▼
                          🧠 RGF-Net (37 KB)
                          Ring-Buffer GRU + FiLM
                          P(pre-ictal) > 0.75 → ALERT
```

**Why it's different**: knowledge distillation from a 661K-param Transformer **teacher** (`SeizureTransformer`) into a 37.5K-param **student** (`RGF-Net`) preserves clinical-grade signal-pattern recognition while collapsing the inference cost by **17.6x** — small enough to run on a watch SoC.

---

## 🏗️ Architecture (60-second tour)

| Layer | Stack | Responsibility |
|---|---|---|
| **Sensors** | Wear OS BodySensors API | 6 biometric channels @ 1–50 Hz (HR, HRV, accel, gyro, SpO₂, skin temp) |
| **Signal sim** | Android `Sensor19ChEegSimulator` | Synthesises 19-ch EEG @ 256 Hz from biometrics for the demo path |
| **Inference** | TensorFlow Lite (NNAPI delegate) | RGF-Net INT8, 5s window, ~22 ms per inference on Pixel 7 |
| **Logic** | Kotlin coroutines | Threshold check (P > 0.75), 15 s cancellable countdown, escalation |
| **Alert** | Wear OS haptics + audio + SMS | Local-first SOS to ICE contacts with last-known GPS |
| **Dashboard** | Next.js 14 + Tailwind + Recharts | Caregiver console, episode timeline, JSON replay |
| **Training** | PyTorch 2.x → ONNX → TFLite | Reproducible distillation pipeline in `ml/` |

Full system breakdown lives in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## 📁 Folder Layout

```
seizure-Project/
├── 1.prd                       ← Product Requirements (Watch Edition)
├── README.md                   ← you are here
├── docs/
│   ├── ARCHITECTURE.md         ← System diagrams + threading model
│   ├── DEMO_SCRIPT.md          ← 3-minute live demo runbook
│   ├── HACKATHON_SUBMISSION.md ← Judging rubric one-pager
│   ├── MODEL_CARD.md           ← Mitchell-style ML model card
│   └── ROADMAP.md              ← Post-hackathon plan
├── ml/                         ← Teacher/Student training, KD loss, TFLite export
├── web/                        ← Next.js caregiver dashboard
├── android/
│   ├── app/                    ← Phone app (inference + SOS orchestration)
│   ├── wear/                   ← Wear OS tile + complication
│   └── shared/                 ← Kotlin module shared between phone & watch
└── reference/                  ← Snapshot of the HF Space (gold-standard)
```

---

## 🚀 Quickstart

### 1. ML — train or load the RGF-Net student

```bash
cd ml
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Option A: download pre-trained weights from the HF reference
python scripts/fetch_weights.py

# Option B: re-run knowledge distillation end-to-end
python scripts/train_teacher.py --epochs 30
python scripts/distill_student.py --teacher checkpoints/teacher.pt
python scripts/export_tflite.py --quantize int8 --out artifacts/rgfnet_int8.tflite
```

### 2. Web — caregiver dashboard

```bash
cd web
pnpm install
pnpm dev          # http://localhost:3000
```

### 3. Android — phone + watch

```bash
cd android
./gradlew :app:installDebug      # phone
./gradlew :wear:installDebug     # paired Wear OS device or emulator
```

> 💡 **Demo without hardware**: the phone app ships with a `SimulatedEegStream` flag that replays a labelled CHB-MIT clip. See [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md).

---

## 🖼️ Screenshots

> Drop final captures into `docs/img/` before submission.

| Watch — countdown | Phone — alert | Dashboard — timeline |
|---|---|---|
| _placeholder_ | _placeholder_ | _placeholder_ |

---

## 🧪 Status & Targets

| Metric | Target | Reference (HF Space) |
|---|---|---|
| Model size | ≤ 40 KB | **36.7 KB** ✅ |
| Pre-ictal sensitivity | ≥ 90% (target) | matches teacher within 3 pp |
| False alarms / week | ≤ 1 (target) | not yet measured in vivo |
| Detection latency | < 500 ms | **~22 ms** inference on phone CPU |
| Battery draw | 3–5% / 24 h (target) | unmeasured |

> ⚠️ Numbers labelled **target** are design goals — see [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) for what is and isn't yet validated.

---

## 👤 Team

Built solo for AI Hackathon 2026 by **Jaan** ([waadalharbi2@gmail.com](mailto:waadalharbi2@gmail.com)).

Reference deployment: [`Babajaan/Aura-Agent-Neural-Guardian`](https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian).

---

## 📜 License

MIT © 2026 Jaan. See `LICENSE`.

> Aura Watch is **not** an FDA-cleared medical device. It is a research prototype intended for hackathon demonstration. Do not rely on it as a sole means of seizure management.
