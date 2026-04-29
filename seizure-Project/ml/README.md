# RGF-Net ML Pipeline

Hackathon ML pipeline that trains the RGF-Net seizure-prediction student model
(via knowledge distillation from a Transformer teacher), exports it to ONNX,
and converts it to TFLite for on-device Android inference.

Source model code lives in `../reference/aura_agent/` (PyTorch). This folder
contains only the training/export *driver* (`train_and_export.py`), the
generated artifacts (`rgf_net.onnx`, `rgf_net.tflite`), and a Python venv.

---

## Setup

This pipeline requires a Python where PyTorch + TensorFlow have wheels.
Python 3.14 has no torch wheels yet; Python 3.13 / 3.12 / 3.11 all work,
3.11 is the most reliable for the TF/ONNX toolchain.

```bash
# Pick the newest Python available locally (in our setup: python3.13).
# If torch fails to install, fall back to 3.12 or 3.11 (via pyenv).
python3.13 -m venv /Users/jaan/Desktop/seizure-Project/ml/.venv
source /Users/jaan/Desktop/seizure-Project/ml/.venv/bin/activate

pip install --upgrade pip
pip install \
  torch \
  numpy \
  onnx \
  onnxruntime \
  onnx2tf \
  tensorflow \
  tf-keras            # required by recent onnx2tf
# Optional, only if you want the demo UI:
# pip install gradio
```

If `onnx2tf` is unavailable on your platform, the script falls back to the
`onnx-tf` -> TF SavedModel -> `TFLiteConverter` path. Install with:

```bash
pip install onnx-tf
```

---

## Run

```bash
source /Users/jaan/Desktop/seizure-Project/ml/.venv/bin/activate
python /Users/jaan/Desktop/seizure-Project/ml/train_and_export.py
```

End-to-end on a laptop CPU: ~5-15 minutes with the hackathon defaults
(`teacher_epochs=10`, `student_epochs=10`, `n_samples=500`).

Outputs (all in this folder):
- `rgf_net.onnx`         - exported student in ONNX (opset 13)
- `rgf_net.tflite`       - TFLite model for Android (target < 200 KB)
- `teacher_best.pt`      - best teacher checkpoint
- `student_best.pt`      - best student checkpoint
- `training_report.json` - full training history + param breakdown

---

## Retraining with different hyperparameters

Edit `train_and_export.py` -> `train()`:

```python
kd_cfg.teacher_epochs = 10   # bump to 50-100 for real accuracy
kd_cfg.student_epochs = 10   # bump to 50-100 for real accuracy
kd_cfg.batch_size     = 32

eeg_data, cond_data, labels = SyntheticEEGDataset.generate(
    n_samples=500,           # bump to 2000+ for real accuracy
    eeg_cfg=eeg_cfg,
    preictal_ratio=0.3,
    seed=42,
)
```

For a real run, replace `SyntheticEEGDataset.generate(...)` with a CHB-MIT or
TUH EEG loader that returns the same three tensors with the same shapes.

---

## Model I/O Signature

The ONNX/TFLite student model has **two inputs** and **two outputs**.

### Inputs

| Name             | Shape                  | dtype   | Meaning |
|------------------|------------------------|---------|---------|
| `eeg_input`      | `(B, 19, 1280)`        | float32 | 5-second EEG window, 256 Hz, 19 channels (10-20 system, see `EEGConfig.channel_names`). Z-score normalized per channel. |
| `biometric_cond` | `(B, 6)`               | float32 | Biometric conditioning vector (see below). |

`B` is the batch dimension (dynamic, typically 1 on Android).

#### Biometric conditioning vector (`biometric_cond`)

Index | Field                       | Range / Encoding
------|-----------------------------|------------------------------------------
0     | `age_normalized`            | age / 100 (0-1)
1     | `sex`                       | 0.0 = female, 1.0 = male
2     | `resting_hr_normalized`     | bpm / 100  (typical 0.6-1.0)
3     | `hrv_sdnn_normalized`       | SDNN / max  (0-1)
4     | `hours_since_last_seizure`  | normalized 0-1 (e.g. hours / 168)
5     | `medication_adherence`      | 0-1 (fraction of doses taken on time)

### Outputs

| Name         | Shape                | dtype   | Meaning |
|--------------|----------------------|---------|---------|
| `logits`     | `(B, 2)`             | float32 | Raw class logits: `[inter_ictal, pre_ictal]`. Apply `softmax` for probabilities. The **risk score** for a seizure within ~30 min is `softmax(logits)[:, 1]`. |
| `embeddings` | `(B, 128)`           | float32 | KD-aligned feature embedding (only useful for retraining / analytics; Android can ignore). |

### Risk thresholding

Default emergency threshold from `KDConfig.risk_threshold = 0.75`. Apply a
moving average over the last 6 windows (`moving_avg_window = 6`, i.e. 30 s)
before triggering an alert.

---

## TFLite quantization mode

`train_and_export.py` tries the following in order and keeps the first that succeeds:

1. **INT8 dynamic-range** via `onnx2tf -oiqt` (smallest, ~30-60 KB).
2. **Float16** (~80-120 KB).
3. **Float32** (~150-250 KB).
4. **Stub CNN** placeholder if all of the above fail.

> **Caveat - GRU + INT8.** TFLite's INT8 quantizer doesn't always cleanly
> handle PyTorch GRU ops translated through ONNX. If your run lands on
> float16 or float32 instead of INT8, that's expected and the model will
> still work on Android (just slightly larger). Check the printed
> `mode=...` line at the end of the script to see which branch was used.
>
> **Caveat - stub fallback.** If the `mode=stub_cnn` line appears, the
> `.tflite` file is a tiny placeholder CNN (NOT the trained RGF-Net) that
> exists only so the Android demo has *some* loadable model. Re-run with
> a working onnx2tf / TF / GRU-quant toolchain before claiming real
> seizure-prediction performance. The stub keeps the same input/output
> *names and shapes* so the Android code does not change.

---

## Architecture summary (RGF-Net student)

- ~37K parameters (well under the 100K budget for 8-bit Android deployment).
- `EEGFeatureExtractor`: depthwise temporal Conv1d -> pointwise spatial Conv1d -> AvgPool.
- `RingBufferGRU`: 2-layer GRU, hidden=48; supports streaming O(1)-memory inference.
- `FiLMLayer`: biometric-conditioned feature modulation `(1+gamma) * x + beta`.
- `Classifier`: LayerNorm -> Linear -> ELU -> Dropout -> Linear (2 logits).
- Knowledge distilled from a 661K-param Transformer teacher
  (`SeizureTransformerTeacher`) using Hinton soft-label KD + SmoothL1 feature
  distillation (alpha=0.7, T=4.0, lambda_feat=0.3).

References: STAN (arXiv 2511.01275), FiLM (arXiv 1709.07871),
Hinton KD (arXiv 1503.02531).
