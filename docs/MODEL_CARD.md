# 🧠 Model Card — RGF-Net (Aura Watch Student)

> Format adapted from **Mitchell et al., "Model Cards for Model Reporting" (FAT* 2019, arXiv:1810.03993)**.

---

## 1. Model Details

| Field | Value |
|---|---|
| **Model name** | RGF-Net (Ring-Buffer GRU + FiLM) |
| **Version** | v0.1 (hackathon submission) |
| **Date** | 2026-04-27 |
| **Type** | Recurrent neural network (single-layer GRU + FiLM conditioning + linear classifier) |
| **Parameters** | **37,554** (full-precision) |
| **Quantized footprint** | **36.7 KB** (INT8 post-training quantization) |
| **Framework** | PyTorch 2.x → ONNX → TensorFlow Lite |
| **Teacher model** | SeizureTransformerTeacher (~661K params) |
| **Distillation** | Hinton soft-label KD + class-weighted CE + TimeKD feature alignment |
| **License** | MIT |
| **Reference deployment** | [HF Space `Babajaan/Aura-Agent-Neural-Guardian`](https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian) |
| **Maintainer** | Jaan ([waadalharbi2@gmail.com](mailto:waadalharbi2@gmail.com)) |

### Architecture sketch

```
EEG window (19, 1280)            Biometrics (6,)
        │                              │
        ▼                              ▼
   Conv1d stem                     MLP encoder
        │                              │
        └──────► Ring-Buffer GRU ◄─────┘  (FiLM modulation: (1+γ)⊙h + β)
                       │
                       ▼
                 Linear classifier
                       │
                       ▼
                P(pre-ictal) ∈ [0,1]
```

---

## 2. Intended Use

### Primary intended use
- **Research prototype** for on-device pre-ictal prediction of tonic-clonic seizures.
- **Educational demonstrations** of edge-AI knowledge distillation for medical signals.
- **Hackathon demonstration** of the Aura Watch concept.

### Primary intended users
- Researchers in epilepsy and edge AI
- Mobile/wearable engineers exploring health applications
- Open-source contributors

### Out-of-scope use cases
- ❌ **Sole means** of seizure management or medication adjustment
- ❌ Clinical diagnosis without supervised EEG
- ❌ Detection of **non-tonic-clonic** seizure types (absence, focal aware) — the model was not trained on these
- ❌ Pediatric use under 6 years (training data demographics differ)
- ❌ Replacement for emergency services

---

## 3. Factors

### Relevant factors
- **Sensor modality**: trained on 19-channel scalp EEG (10-20 system @ 256 Hz). Performance is undefined on any other modality without re-training.
- **Patient cohort**: training data skews toward adolescent and adult tonic-clonic episodes.
- **Recording conditions**: clean clinical EEG; ambulatory-grade headbands will introduce artifact distributions the model has not seen.

### Evaluation factors
We evaluate on held-out subjects (subject-level split, never temporal split within subject) to avoid leakage.

---

## 4. Metrics

| Metric | Target (design goal) | Reference (HF Space) | Production-validated? |
|---|---|---|---|
| Pre-ictal sensitivity | ≥ 90% | matches teacher within 3 pp | ❌ no IRB study yet |
| Specificity | ≥ 95% | matches teacher within 3 pp | ❌ |
| False alarms per week | ≤ 1 | not yet measured in vivo | ❌ |
| Inference latency (Pixel 7, NNAPI) | < 50 ms | **~22 ms median** | ✅ measured |
| Model size (INT8 TFLite) | ≤ 40 KB | **36.7 KB** | ✅ measured |
| Lead time before seizure onset | ≥ 30 s | up to ~30 min on HF reference clip set | ❌ not in vivo |

> ⚠️ All target rows are **engineering goals**, not validated clinical claims. The "Reference" column reflects synthetic / curated benchmarks on the HF Space, not deployment data.

---

## 5. Training Data

| Aspect | Description |
|---|---|
| **Dataset** | CHB-MIT Scalp EEG Database (PhysioNet) + curated pre-ictal segments |
| **Channels** | 19 (10-20 international montage) |
| **Sample rate** | 256 Hz |
| **Window** | 5 seconds (1280 samples) |
| **Biometric augment** | Synthetic 6-channel biometrics (HR, HRV, accel x/y/z, SpO₂) generated to correlate with EEG state |
| **Train/val split** | Subject-level holdout (no subject leakage) |
| **Class balance** | Pre-ictal vs. interictal, weighted CE to compensate ~1:50 imbalance |

### Known dataset limitations

- Demographic skew (US-based hospital population in CHB-MIT)
- Small absolute number of subjects (~24) — generalization beyond cohort is unproven
- Synthetic biometric augmentation does **not** reflect real wearable sensor noise

---

## 6. Evaluation Data

- Held-out subjects from CHB-MIT not seen during training.
- The HF reference Space serves as a **regression baseline**: any deployed RGF-Net build must reproduce reference probabilities on stored seed clips within ±0.05.

---

## 7. Ethical Considerations

| Issue | Mitigation |
|---|---|
| **False negatives → missed seizures** | Threshold conservatively tuned (0.75); cancellable countdown means false positives are cheap, false negatives are not — we err high-recall |
| **False positives → alert fatigue** | 15-second cancellation window + Bayesian threshold-personalization (Phase 1) |
| **Privacy of medical data** | Model runs **fully on-device**. No cloud inference, no telemetry, no remote model fetch. See [`ARCHITECTURE.md`](ARCHITECTURE.md) §5 |
| **Auto-dialing emergency contacts** | Opt-in only, user-confirmed contact list, dismissable from watch + phone |
| **Bias across demographics** | Acknowledged training-data skew; Phase 3 clinical pilot includes diversity sampling |
| **Anthropomorphism / trust calibration** | UI shows raw probability + threshold, never a binary "you will have a seizure" claim |
| **Liability** | Disclaimer: not an FDA-cleared device. Research prototype only. |

---

## 8. Caveats & Limitations

### 🚨 The big one: EEG vs. watch sensors

The PRD ([`1.prd`](../1.prd)) targets a **smartwatch** form factor that exposes accelerometer, gyroscope, and PPG — **not EEG**. The trained RGF-Net, however, **expects 19-channel EEG input**.

The hackathon demo bridges this gap with `Sensor19ChEegSimulator` on the phone, which synthesises plausible 19-channel EEG conditioned on the watch's biometric stream. **This is a demonstration trick, not a production solution.**

| Path forward | Where it lives |
|---|---|
| **Real EEG headband** integration (OpenBCI, Muse S, Naptune) over BLE | [`ROADMAP.md`](ROADMAP.md) Phase 1 |
| **Motion-only sibling model** trained from accel/gyro/PPG directly | [`ROADMAP.md`](ROADMAP.md) Phase 4 |

We are explicit about this gap in the README, the architecture doc, and the live demo narration.

### Other limitations

- **No seizure-type discrimination** — outputs a single pre-ictal probability, not a typed prediction.
- **Window-level only** — does not estimate exact seizure onset time, only "soon".
- **Cohort generalization** — CHB-MIT subject pool is small; cross-population transfer unproven.
- **Adversarial robustness** — model has not been red-teamed against motion artifact attacks.
- **Battery numbers** in the PRD are **targets**, not measured.

---

## 9. Recommendations

- Use this model as a **secondary, advisory** signal — never as a primary clinical decision.
- Always pair with a redundant safety mechanism (caregiver, manual emergency button).
- Re-validate with subject-specific calibration data before relying on the threshold default of 0.75.
- Treat synthesized EEG path as a **technology preview**; the production roadmap requires real EEG hardware.

---

## 10. Citation

```bibtex
@software{aura_watch_2026,
  author = {Jaan},
  title  = {Aura Watch — On-Device Seizure Pre-Ictal Guardian},
  year   = {2026},
  note   = {AI Hackathon 2026 submission. Built on the Aura-Agent-Neural-Guardian reference deployment.},
  url    = {https://huggingface.co/spaces/Babajaan/Aura-Agent-Neural-Guardian}
}
```

---

## 11. References

| Paper | Topic | ArXiv |
|---|---|---|
| Mitchell et al. | Model Cards | 1810.03993 |
| Hinton et al. | Knowledge Distillation | 1503.02531 |
| Perez et al. | FiLM | 1709.07871 |
| TimeKD | Privileged KD for time-series | 2505.02138 |
| STAN | Spatio-Temporal Attention Networks | 2511.01275 |
| Spiking Conformer | Efficient EEG seizure detection | 2402.09424 |
| Edge DL | Quantized models for neural implants | 2012.00307 |
