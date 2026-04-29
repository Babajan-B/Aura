# 🛡️ Aura Watch — Hackathon Submission Package

**AI Hackathon 2026 | On-Device Seizure Pre-Ictal Guardian**

---

## 📦 What's Included

This submission contains:

1. **HACKATHON_SUBMISSION_PACKAGE.md** ← Start here
   - Complete project information
   - Problem statement & proposed solution
   - Project availability status
   - Technical specifications
   - Team information

2. **Full source codebase** (~1.3 MB, node_modules excluded)
   - `web/` — Next.js 15 dashboard (fully functional)
   - `android/` — Kotlin multi-module (phone + watch apps)
   - `ml/` — Python training + export pipeline
   - `reference/` — HuggingFace Space clone (PyTorch)
   - `docs/` — Architecture, demo script, model card

3. **SCREENSHOTS_GUIDE.md** ← How to view the dashboard live
   - Live server instructions
   - Dashboard section descriptions
   - Interactive features overview

---

## 🚀 Quick Start

### View the Dashboard (60 seconds)

```bash
# Extract and navigate
cd seizure-Project

# Start the web server
cd web
npm install    # (dependencies already installed in the zip)
npm run dev

# Open browser to: http://localhost:3001
```

**You'll see:**
- Animated brain visualization
- Live EEG waveform
- Risk detection gauge (green → red)
- Knowledge distillation architecture flow
- Wear OS watch face simulator
- Interactive biometric sliders
- Model footprint comparison chart

### Run the Android Apps (5 minutes setup)

```bash
# Open in Android Studio
cd android
# File → Open → seizure-Project/android

# Create emulators via Device Manager:
# 1. Pixel 7 (API 34) for phone app
# 2. Wear OS 4 (API 33) for watch app

# Run :app (phone) and :wear (watch)
# Test "Inject Seizure Pattern" flow
```

### Generate the TFLite Model (5 minutes)

```bash
cd ml
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python train_and_export.py

# Output: rgf_net.onnx + rgf_net.tflite
# Copy to: cp rgf_net.tflite ../android/app/src/main/assets/
```

---

## 📋 Submission Checklist

- [x] Complete project documentation (HACKATHON_SUBMISSION_PACKAGE.md)
- [x] Full codebase provided (all source files)
- [x] Web dashboard functional and live (port 3001)
- [x] Android phone app ready (Kotlin + TFLite inference)
- [x] Wear OS watch app ready (Compose UI + sensor service)
- [x] ML pipeline script provided (train + export)
- [x] Architecture documentation (ARCHITECTURE.md)
- [x] Model card included (MODEL_CARD.md)
- [x] Demo runbook provided (DEMO_SCRIPT.md)

---

## 🎯 Key Metrics

| Metric | Value |
|---|---|
| **Model size (INT8 quantized)** | 36.7 KB |
| **Model parameters (student)** | 37,554 |
| **Inference latency** | ~22 ms (Pixel 7) |
| **Model compression** | 17.6× (661K → 37.5K) |
| **Training data** | 500 synthetic samples |
| **Lines of code** | ~3,490 |
| **Source files** | 56 files |
| **Technologies** | Kotlin, TypeScript, Python |

---

## 📂 File Structure

```
seizure-Project/
├── README.md                              ← Project overview
├── HACKATHON_SUBMISSION_PACKAGE.md        ← ⭐ START HERE
├── SUBMISSION_README.md                   ← This file
├── SCREENSHOTS_GUIDE.md                   ← Dashboard walkthrough
├── full-project.md                        ← Detailed technical doc
├── 1.prd                                  ← Product requirements
│
├── web/                                   ← Next.js dashboard
│   ├── app/
│   │   ├── page.tsx                      (main dashboard)
│   │   ├── layout.tsx                    (root layout)
│   │   └── api/infer/route.ts            (risk API)
│   ├── components/
│   │   ├── Hero.tsx                      (brain + stats)
│   │   ├── EEGWaveform.tsx              (4-ch animated chart)
│   │   ├── RiskGauge.tsx                (SVG gauge)
│   │   ├── ArchitectureDiagram.tsx      (KD flow)
│   │   ├── WatchFace.tsx                (watch mockup)
│   │   ├── InferenceSimulator.tsx       (sliders + API)
│   │   └── FootprintChart.tsx           (model sizes)
│   ├── package.json                      (Next.js 15)
│   └── tailwind.config.ts
│
├── android/                               ← Kotlin multi-module
│   ├── app/                              (phone)
│   │   ├── src/main/kotlin/.../MainActivity.kt
│   │   ├── src/main/kotlin/.../ml/InferenceEngine.kt
│   │   ├── src/main/kotlin/.../ui/DashboardScreen.kt
│   │   ├── src/main/assets/rgf_net.tflite  ⬅️ Model goes here
│   │   └── build.gradle.kts
│   ├── wear/                             (watch)
│   │   ├── src/main/kotlin/.../MainActivity.kt
│   │   ├── src/main/kotlin/.../ui/AlertCountdownScreen.kt
│   │   └── build.gradle.kts
│   └── settings.gradle.kts
│
├── ml/                                   ← Python training
│   ├── train_and_export.py              (train → TFLite)
│   ├── README.md                         (pipeline docs)
│   └── .venv/                            (Python 3.13 env)
│
├── reference/                            ← HF Space clone
│   ├── main.py                           (training entry)
│   ├── app.py                            (Gradio demo)
│   ├── aura_agent/
│   │   ├── student.py                   (RGF-Net)
│   │   ├── teacher.py                   (Transformer)
│   │   ├── distillation.py              (KD trainer)
│   │   └── agent.py                     (LLaMA 3.3 agent)
│   └── requirements.txt
│
└── docs/                                 ← Documentation
    ├── ARCHITECTURE.md                  (system design)
    ├── DEMO_SCRIPT.md                   (3-min runbook)
    ├── MODEL_CARD.md                    (ML model card)
    ├── HACKATHON_SUBMISSION.md          (judge 1-pager)
    ├── REAL_DATA_DEPLOYMENT_PLAN.md     (post-hackathon)
    └── ROADMAP.md                       (future phases)
```

---

## 🔗 Reference Links

- **HuggingFace Space (reference model):** https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian
- **GitHub (source code):** https://github.com/Babajaan/seizure-Project
- **EEG Dataset:** https://physionet.org/content/chbmit/1.0.0/ (CHB-MIT Scalp EEG)

---

## 📞 Contact

**Builder:** Jaan Nawaz  
**Email:** waadalharbi2@gmail.com  
**GitHub:** @Babajaan

---

## ✅ Submission Status

| Item | Status |
|---|---|
| Source code | ✅ Complete |
| Documentation | ✅ Complete |
| Web dashboard | ✅ Functional |
| Android app | ✅ Ready to build |
| ML pipeline | ✅ Ready to run |
| Demo materials | ✅ Provided |

---

## 📄 License

MIT © 2026 Jaan

**Disclaimer:** Aura Watch is a research prototype intended for hackathon demonstration. It is **NOT** an FDA-cleared medical device. Do not rely on it as a sole means of seizure management.

---

**Last updated:** 2026-04-29  
**Ready for hackathon submission:** ✅ YES

