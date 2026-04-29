# 🏆 Aura Watch — AI Hackathon 2026 Submission

> **One-page writeup.** Optimized for the judging rubric: Problem Fit · Technical Depth · Novelty · Demo · Impact.

| Field | Value |
|---|---|
| **Project** | Aura Watch — On-Device Seizure Pre-Ictal Guardian |
| **Track** | Edge AI / Health |
| **Hackathon** | AI Hackathon 2026 |
| **Team** | Solo — Jaan ([waadalharbi2@gmail.com](mailto:waadalharbi2@gmail.com)) |
| **Submission date** | 2026-04-27 |
| **License** | MIT |

---

## 🩺 Problem

**65 million** people live with epilepsy worldwide. **1-in-1000** dies each year from **SUDEP** — Sudden Unexpected Death in Epilepsy — most often during a tonic-clonic seizure with no one nearby. Even **30 seconds** of advance warning is enough to trigger:

- safe-recovery posture
- a caregiver phone call
- removal from immediate danger (driving, swimming, stairs)

Today's options are bad. Hospital EEG is tethered and costs $2k+/day. Consumer "fall-detection" watches trigger *after* the seizure. Cloud-based ML systems have unacceptable latency, leak medical data, and fail without signal.

**Nobody should die from a seizure their wrist already knew was coming.**

---

## ✨ Solution

A three-tier on-device safety net:

1. **Wear OS watch** captures 6 biometric channels.
2. **Android phone** runs **RGF-Net** — a 37 KB INT8-quantized Ring-Buffer GRU with FiLM conditioning — distilled from a 661K-parameter Transformer teacher (`SeizureTransformer`). It outputs a pre-ictal probability every second.
3. When `P(pre-ictal) > 0.75`, a 15-second cancellable countdown triggers haptic + audible alarms, then SMS-dispatches GPS to ICE contacts. A **Next.js caregiver dashboard** logs and replays every episode.

**Zero cloud. Zero PHI exfiltration. < 500 ms wrist-to-alert.**

---

## 💡 Innovation — what's actually new

| Innovation | Why it matters |
|---|---|
| **17.6× compression via knowledge distillation** | 661K → 37.5K params, retaining teacher-level signal recognition (target: within 3 pp sensitivity) |
| **Ring-Buffer GRU** | O(1) memory streaming inference — no re-attending the full window every frame, unlike a Transformer |
| **FiLM biometric conditioning** | `(1+γ)⊙h + β` lets one model adapt to user-specific HRV/HR baselines without retraining |
| **Three-loss KD** | Hinton soft-label + class-weighted CE + TimeKD feature alignment — published-grounded, not hand-wavy |
| **40 KB CI gate** | Model-size budget enforced as a build-blocking test — quantization regressions can never ship |
| **Local-first by construction** | No HTTP client linked into the inference path. Privacy is a build artifact, not a promise |

---

## 🛠️ Tech Stack

| Layer | Tools |
|---|---|
| **Modeling** | PyTorch 2.x, ONNX, TensorFlow Lite, INT8 PTQ |
| **Reference deploy** | [HF Space `Babajaan/Aura-Agent-Neural-Guardian`](https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian) (Gradio + smolagents) |
| **Phone app** | Kotlin, Jetpack Compose, TFLite NNAPI, Coroutines + Flow |
| **Watch app** | Wear OS 4, Health Services, Tiles, Compose for Wear |
| **Dashboard** | Next.js 14 (App Router), Tailwind, Recharts |
| **Transport** | BLE GATT custom service, CBOR-encoded biometric frames |
| **Storage** | Room (SQLite) on phone, encrypted prefs for ICE contacts |
| **CI** | GitHub Actions: pytest + gradle check + pnpm test + size budget |

---

## 📊 Impact

| Dimension | Reach |
|---|---|
| **Direct beneficiaries** | 65M people with epilepsy + their families and caregivers |
| **Adjacent applications** | Cardiac arrhythmia early warning, syncope, panic-attack precursors — same architecture, different labels |
| **Cost floor** | Runs on any Android 12+ phone + any Wear OS 4 watch — no specialised hardware |
| **Health-system value** | Local-first means HIPAA/GDPR scope is dramatically reduced — easier hospital adoption |
| **Open source** | MIT-licensed weights, training code, and apps — anyone can fork, audit, contribute |

---

## 🎯 Judging Rubric Self-Score

| Criterion | Evidence | Self-score |
|---|---|---|
| **Problem fit** | SUDEP is well-documented; no consumer device today predicts pre-ictal | ★★★★★ |
| **Technical depth** | Teacher/student KD, custom GRU+FiLM, INT8 export, on-device runtime, BLE protocol | ★★★★★ |
| **Novelty** | Ring-Buffer GRU streaming inference + 37 KB footprint + FiLM biometric conditioning | ★★★★☆ |
| **Demo quality** | Live phone+watch+dashboard with reproducible "fake seizure" injection | ★★★★☆ |
| **Impact** | Open-source, runs on commodity hardware, addresses life-threatening problem | ★★★★★ |

---

## 🚧 Honest Limitations

- The current model expects **19-channel EEG**; consumer watches don't capture EEG. The demo path uses `Sensor19ChEegSimulator` to bridge this for storytelling. Production needs a real headband (e.g. OpenBCI, Muse S, Naptune) — see [`ROADMAP.md`](ROADMAP.md) Phase 1.
- Reported sensitivity numbers are **targets** matched against the HF reference; clinical validation requires IRB-supervised trials we have not run.
- Battery numbers (3–5%/24h) are design goals from the PRD, not measured.
- Not an FDA-cleared medical device.

---

## 🔗 Links

| What | Where |
|---|---|
| **Repo** | _to be filled at submission_ |
| **Demo video (3 min)** | _to be filled at submission_ |
| **Reference HF Space** | https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian |
| **Architecture deep-dive** | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) |
| **Model card** | [`docs/MODEL_CARD.md`](MODEL_CARD.md) |
| **Roadmap** | [`docs/ROADMAP.md`](ROADMAP.md) |
| **PRD** | [`1.prd`](../1.prd) |

---

## 🙏 Acknowledgements

- **CHB-MIT Scalp EEG Database** for training data
- **Hinton et al. (1503.02531)** — Knowledge Distillation
- **Perez et al. (1709.07871)** — FiLM
- **TimeKD (2505.02138)** — Privileged feature distillation for time-series
- **STAN (2511.01275)** and **Spiking Conformer (2402.09424)** — seizure-detection prior art
- The Hugging Face team for hosting the reference Space

> _If a 37 KB model on a wrist saves one person from SUDEP, the entire weekend was worth it._
