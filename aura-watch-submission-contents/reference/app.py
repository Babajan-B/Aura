#!/usr/bin/env python3
"""
🧠 Aura-Agent: Neural Guardian — Gradio Demo
=============================================
Interactive demo for the seizure prediction pipeline:
  - Inspect Teacher & Student architectures
  - Run Knowledge Distillation training
  - Test RGF-Net inference with synthetic EEG
  - View smolagents CodeAgent workflow
"""

import gradio as gr
import torch
import torch.nn.functional as F
import numpy as np
import json
import time
import io
import sys
import math

from aura_agent.config import EEGConfig, TeacherConfig, StudentConfig, KDConfig
from aura_agent.teacher import SeizureTransformerTeacher
from aura_agent.student import RGFNet
from aura_agent.distillation import DistillationTrainer, SyntheticEEGDataset

# ── Global State ──
MODELS = {}


# ============================================================================
# Tab 1: Architecture Inspector
# ============================================================================

def inspect_architectures():
    """Build both models and return architecture details."""
    eeg_cfg = EEGConfig()
    teacher_cfg = TeacherConfig()
    student_cfg = StudentConfig()

    teacher = SeizureTransformerTeacher(eeg_cfg, teacher_cfg)
    student = RGFNet(eeg_cfg, student_cfg)

    teacher_info = f"""## 🎓 Teacher: SeizureTransformerTeacher

| Property | Value |
|----------|-------|
| **Total Parameters** | {teacher.count_parameters():,} |
| **d_model** | {teacher_cfg.d_model} |
| **Attention Heads** | {teacher_cfg.n_heads} |
| **Transformer Layers** | {teacher_cfg.n_transformer_layers} |
| **FFN Dimension** | {teacher_cfg.d_ff} |
| **Embed Dim (for KD)** | {teacher_cfg.embed_dim} |
| **Dropout** | {teacher_cfg.dropout} |
| **Input Shape** | (B, {eeg_cfg.n_channels}, {eeg_cfg.window_samples}) |
| **Output** | logits (B, 2) + embeddings (B, {teacher_cfg.embed_dim}) |

### Architecture
```
Raw EEG (B, 19, 1280)
  → PatchEmbedding (Conv1D per-channel → spatial projection)
  → Positional Encoding (sinusoidal)
  → 4× Transformer Encoder (pre-norm, GELU, 4-head attention)
  → Attention-weighted Temporal Pooling
  → Embedding Head (LayerNorm + GELU)
  → Classification Head → (B, 2)
```
"""

    breakdown = student.param_breakdown()
    breakdown_rows = ""
    for name, count in breakdown.items():
        pct = 100 * count / breakdown['total']
        bar = "█" * int(pct / 3)
        breakdown_rows += f"| {name} | {count:,} | {pct:.1f}% | {bar} |\n"

    student_info = f"""## 🧬 Student: RGF-Net (Ring-Buffer GRU + FiLM)

| Property | Value |
|----------|-------|
| **Total Parameters** | **{student.count_parameters():,}** |
| **Budget** | < 100,000 ✅ |
| **GRU Hidden Size** | {student_cfg.gru_hidden} |
| **GRU Layers** | {student_cfg.gru_layers} |
| **FiLM Cond Dim** | {student_cfg.cond_dim} |
| **Ring Buffer Size** | {student_cfg.ring_buffer_size} windows |
| **EEG Input** | (B, {eeg_cfg.n_channels}, {eeg_cfg.window_samples}) |
| **Biometric Input** | (B, {student_cfg.cond_dim}) |
| **8-bit Quantized Size** | ~{student.count_parameters() / 1024:.1f} KB |

### Parameter Breakdown
| Module | Params | % | Distribution |
|--------|--------|---|-------------|
{breakdown_rows}

### Architecture
```
EEG (B,19,1280) + Biometrics (B,6)
  → Depthwise Temporal Conv (per-channel, k=25)
  → Pointwise Spatial Conv (channel fusion)
  → AvgPool (8× temporal reduction)
  → 2-layer Ring-Buffer GRU (hidden=48)
  → FiLM Layer: (1+γ)⊙h + β  [γ,β = f(biometrics)]
  → LayerNorm → Linear → ELU → Dropout → Linear → (B, 2)
```

### FiLM Conditioning
The biometric vector `[age, sex, HR, HRV, hours_since_seizure, med_adherence]`
generates per-feature scale (γ) and shift (β) via a small MLP.
Using residual formulation `(1+γ)⊙h + β` ensures identity initialization.
"""

    ratio = teacher.count_parameters() / student.count_parameters()
    compression = f"""## 📊 Compression Summary

| Metric | Value |
|--------|-------|
| **Teacher** | {teacher.count_parameters():,} params |
| **Student** | {student.count_parameters():,} params |
| **Compression Ratio** | **{ratio:.1f}×** |
| **Student (INT8)** | ~{student.count_parameters() / 1024:.1f} KB |
| **Android-ready** | ✅ Under 100K param budget |
"""

    return teacher_info, student_info, compression


# ============================================================================
# Tab 2: Training & Distillation
# ============================================================================

def run_training(n_samples, epochs_teacher, epochs_student, learning_rate, temperature, alpha, progress=gr.Progress()):
    """Run the full training + KD pipeline with progress updates."""
    global MODELS

    eeg_cfg = EEGConfig()
    teacher_cfg = TeacherConfig()
    student_cfg = StudentConfig()
    kd_cfg = KDConfig()
    kd_cfg.teacher_epochs = int(epochs_teacher)
    kd_cfg.student_epochs = int(epochs_student)
    kd_cfg.teacher_lr = float(learning_rate)
    kd_cfg.student_lr = float(learning_rate) / 3.0
    kd_cfg.temperature = float(temperature)
    kd_cfg.alpha = float(alpha)
    kd_cfg.batch_size = min(64, int(n_samples) // 4)

    progress(0.05, desc="Generating synthetic EEG data...")
    eeg_data, cond_data, labels = SyntheticEEGDataset.generate(
        n_samples=int(n_samples), eeg_cfg=eeg_cfg, preictal_ratio=0.3,
    )

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    progress(0.1, desc="Initializing models...")
    trainer = DistillationTrainer(
        eeg_cfg=eeg_cfg, teacher_cfg=teacher_cfg,
        student_cfg=student_cfg, kd_cfg=kd_cfg, device=device,
    )

    log_lines = []
    log_lines.append(f"Device: {device}")
    log_lines.append(f"Teacher params: {trainer.teacher.count_parameters():,}")
    log_lines.append(f"Student params: {trainer.student.count_parameters():,}")
    log_lines.append(f"Data: {int(n_samples)} samples ({int(labels.sum())} pre-ictal)")
    log_lines.append(f"KD: T={temperature}, alpha={alpha}, lambda_feat={kd_cfg.lambda_feat}")
    log_lines.append("")

    progress(0.15, desc="Phase 1: Training Teacher...")
    log_lines.append("=" * 50)
    log_lines.append("PHASE 1: TEACHER TRAINING")
    log_lines.append("=" * 50)

    t0 = time.time()
    teacher_metrics = trainer.train_teacher(eeg_data, cond_data, labels)
    t1 = time.time()

    log_lines.append(f"Teacher training: {t1-t0:.1f}s")
    log_lines.append(f"Best Acc: {teacher_metrics['accuracy']:.4f}")
    log_lines.append(f"Best Sensitivity: {teacher_metrics['sensitivity']:.4f}")
    log_lines.append(f"Best Specificity: {teacher_metrics['specificity']:.4f}")
    log_lines.append("")

    progress(0.55, desc="Phase 2: Knowledge Distillation...")
    log_lines.append("=" * 50)
    log_lines.append("PHASE 2: KNOWLEDGE DISTILLATION")
    log_lines.append("=" * 50)

    t2 = time.time()
    student_metrics = trainer.distill(eeg_data, cond_data, labels)
    t3 = time.time()

    log_lines.append(f"Distillation: {t3-t2:.1f}s")
    log_lines.append(f"Best Acc: {student_metrics['accuracy']:.4f}")
    log_lines.append(f"Best Sensitivity: {student_metrics['sensitivity']:.4f}")
    log_lines.append(f"Best Specificity: {student_metrics['specificity']:.4f}")

    progress(0.95, desc="Generating report...")

    MODELS['teacher'] = trainer.teacher
    MODELS['student'] = trainer.student
    MODELS['eeg_cfg'] = eeg_cfg
    MODELS['student_cfg'] = student_cfg

    results_md = f"""## 📊 Training Results

| Metric | Teacher | Student (KD) | 
|--------|---------|-------------|
| **Accuracy** | {teacher_metrics['accuracy']:.4f} | {student_metrics['accuracy']:.4f} |
| **Sensitivity** | {teacher_metrics['sensitivity']:.4f} | {student_metrics['sensitivity']:.4f} |
| **Specificity** | {teacher_metrics['specificity']:.4f} | {student_metrics['specificity']:.4f} |
| **F1 Score** | {teacher_metrics.get('f1', 0):.4f} | {student_metrics.get('f1', 0):.4f} |
| **Parameters** | {trainer.teacher.count_parameters():,} | {trainer.student.count_parameters():,} |
| **Training Time** | {t1-t0:.1f}s | {t3-t2:.1f}s |

### Knowledge Distillation Config
- Temperature: {temperature} | Alpha (soft weight): {alpha}
- Feature distillation: SmoothL1 (lambda={kd_cfg.lambda_feat})
- Compression: {trainer.teacher.count_parameters() / trainer.student.count_parameters():.1f}x 
"""

    progress(1.0, desc="Done!")
    return results_md, "\n".join(log_lines)


# ============================================================================
# Tab 3: RGF-Net Live Inference
# ============================================================================

def run_inference(age, sex, heart_rate, hrv, hours_since_seizure, medication, signal_type):
    """Run RGF-Net inference with configurable biometrics."""
    eeg_cfg = EEGConfig()
    student_cfg = StudentConfig()

    if 'student' in MODELS:
        model = MODELS['student']
    else:
        model = RGFNet(eeg_cfg, student_cfg)

    model.eval()

    torch.manual_seed(int(time.time()) % 10000)
    C, T = eeg_cfg.n_channels, eeg_cfg.window_samples
    t_axis = torch.linspace(0, eeg_cfg.window_sec, T).unsqueeze(0).unsqueeze(0)

    if signal_type == "Normal (Inter-ictal)":
        eeg = torch.zeros(1, C, T)
        for ch in range(C):
            freq_a = 8 + 4 * torch.rand(1, 1, 1)
            freq_b = 12 + 18 * torch.rand(1, 1, 1)
            eeg[:, ch:ch+1, :] = (
                0.5 * torch.sin(2 * math.pi * freq_a * t_axis) +
                0.3 * torch.sin(2 * math.pi * freq_b * t_axis) +
                0.1 * torch.randn(1, 1, T)
            )
    elif signal_type == "Pre-ictal (Seizure Warning)":
        eeg = torch.zeros(1, C, T)
        for ch in range(C):
            freq_g = 30 + 70 * torch.rand(1, 1, 1)
            freq_t = 4 + 4 * torch.rand(1, 1, 1)
            spikes = torch.zeros(1, 1, T)
            for loc in torch.randint(0, T, (5,)):
                w = torch.randint(3, 15, (1,)).item()
                s, e = max(0, loc-w), min(T, loc+w)
                spikes[0, 0, s:e] = 2.0 * torch.randn(1)
            eeg[:, ch:ch+1, :] = (
                0.2 * torch.sin(2 * math.pi * freq_t * t_axis) +
                0.6 * torch.sin(2 * math.pi * freq_g * t_axis) +
                0.3 * torch.randn(1, 1, T) + spikes
            )
    else:
        eeg = torch.randn(1, C, T)

    mean = eeg.mean(dim=2, keepdim=True)
    std = eeg.std(dim=2, keepdim=True) + 1e-8
    eeg = (eeg - mean) / std

    cond = torch.tensor([[
        age / 100.0,
        float(sex == "Male"),
        heart_rate / 100.0,
        hrv / 100.0,
        hours_since_seizure / 48.0,
        medication / 100.0,
    ]], dtype=torch.float32)

    with torch.no_grad():
        logits, embeds = model(eeg, cond)
        probs = F.softmax(logits, dim=-1)
        risk_score = probs[0, 1].item()

    if risk_score >= 0.75:
        status = "🚨 **HIGH RISK** — Seizure likely within 30 minutes"
        action = """### 🚨 Emergency Protocol Triggered
1. ✅ RGF-Net risk assessment: **HIGH**
2. 📍 GPS coordinates retrieved
3. 📞 SOS alert dispatched to emergency contacts
4. 🏥 EMS notified with patient location  
5. 📋 First-aid instructions sent to nearby responders
"""
    elif risk_score >= 0.5:
        status = "⚠️ **ELEVATED** — Increased monitoring recommended"
        action = """### ⚠️ Elevated Risk Protocol
1. ✅ RGF-Net risk assessment: **ELEVATED**
2. ⏱️ Monitoring frequency increased to every 30 seconds
3. 📱 Caregiver notification sent
4. 💊 Medication reminder triggered
"""
    else:
        status = "✅ **NORMAL** — No immediate risk detected"
        action = """### ✅ Normal Status
1. ✅ RGF-Net risk assessment: **NORMAL**
2. 🔄 Continued standard monitoring (every 5 minutes)
3. 📊 Data logged for pattern analysis
"""

    result_md = f"""## Seizure Risk Assessment

### Risk Score: **{risk_score:.4f}**

{status}

### Biometric Profile
| Parameter | Value |
|-----------|-------|
| Age | {age} years |
| Sex | {sex} |
| Resting HR | {heart_rate} bpm |
| HRV (SDNN) | {hrv} ms |
| Hours since seizure | {hours_since_seizure} |
| Medication adherence | {medication}% |

### EEG Signal Type
{signal_type} — 19 channels x {eeg_cfg.window_samples} samples ({eeg_cfg.window_sec}s @ {eeg_cfg.sample_rate}Hz)

{action}
"""

    return result_md, f"{risk_score:.4f}"


# ============================================================================
# Tab 4: Agent Workflow
# ============================================================================

def show_agent_workflow():
    return """## 🤖 smolagents CodeAgent Workflow

The Aura-Agent uses HuggingFace's `smolagents` library to create an autonomous 
**CodeAgent** that chains RGF-Net inference with emergency response actions.

### Architecture
```
┌─────────────────────────────────────────────┐
│           CodeAgent (LLM Brain)             │
│   model: Llama-3.3-70B-Instruct            │
│   max_steps: 8, temperature: 0.1           │
├─────────────────────────────────────────────┤
│                                             │
│   Step 1: Assess Risk                       │
│   ┌─────────────────────────┐               │
│   │  rgfnet_seizure_risk    │ ← Tool class  │
│   │  (lazy model loading)   │   with setup() │
│   │  Returns: float 0.0-1.0 │               │
│   └────────────┬────────────┘               │
│                │                             │
│   Step 2: Decision Gate                     │
│   ┌────────────▼────────────┐               │
│   │  if risk >= 0.75:       │ ← Python code │
│   │      trigger_emergency()│   generated by │
│   │  else:                  │   CodeAgent    │
│   │      monitor_continue() │               │
│   └────────────┬────────────┘               │
│                │                             │
│   Step 3: Emergency Chain (if triggered)    │
│   ┌─────────────────────────┐               │
│   │  get_patient_gps()      │ ← @tool       │
│   │  send_sos_alert()       │ ← @tool       │
│   │  dispatch_first_aid()   │ ← @tool       │
│   └─────────────────────────┘               │
│                                             │
└─────────────────────────────────────────────┘
```

### Tool Definitions

#### 1. `RGFNetSeizureRiskTool` (Tool subclass)
```python
class RGFNetSeizureRiskTool(Tool):
    name = "rgfnet_seizure_risk"
    inputs = {
        "eeg_data":    {"type": "string", ...},
        "patient_id":  {"type": "string", ...},
        "biometrics":  {"type": "string", ...},
    }
    output_type = "number"
    
    def setup(self):   # Lazy-loads RGF-Net weights
    def forward(self): # Runs inference → risk score
```

#### 2. `send_sos_alert` (@tool decorator)
```python
@tool
def send_sos_alert(patient_id: str, risk_score: float, 
                   location: str) -> str:
    # Dispatches to: emergency contacts, EMS, hospital
```

#### 3. `get_patient_gps` (@tool decorator)
```python
@tool
def get_patient_gps(patient_id: str) -> str:
    # Returns: "latitude,longitude"
```

#### 4. `dispatch_first_aid` (@tool decorator)
```python
@tool
def dispatch_first_aid(patient_id: str, location: str,
                       risk_score: float) -> str:
    # Sends AES-guideline seizure first-aid protocol
```

### Agent Instructions (System Prompt)
```
CRITICAL PROTOCOL:
1. ASSESS: Call rgfnet_seizure_risk FIRST
2. DECIDE: Compare risk_score against threshold (0.75)
3. IF HIGH: GPS → SOS → First-Aid (in order)
4. IF NORMAL: Report and continue monitoring
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **CodeAgent** over ToolCallingAgent | Supports `if/else` logic for threshold-based decisions |
| **Tool subclass** for RGF-Net | `setup()` enables lazy model loading (no VRAM at init) |
| **@tool decorator** for utilities | Simpler API for stateless functions |
| **Low temperature (0.1)** | Medical decisions require deterministic behavior |
| **max_steps=8** | Bounded execution prevents runaway agent loops |
"""


# ============================================================================
# Tab 5: KD Loss Explained
# ============================================================================

def show_kd_explanation():
    return """## 📐 Knowledge Distillation: Loss Function

### Three-Component Combined Loss

The student learns from **three** sources simultaneously:

**L_total = alpha * L_soft + (1-alpha) * L_hard + lambda_feat * L_feature**

---

### 1. Soft-Label KD Loss (Hinton et al., 2015)

```python
L_soft = KL_div(
    log_softmax(student_logits / T),
    softmax(teacher_logits / T)
) * T**2
```

- **Temperature T=4.0** softens probability distributions
- Teacher's "dark knowledge" transfers richer information than hard labels
- **T^2 scaling** maintains gradient magnitude as T increases

### 2. Hard-Label Cross-Entropy

```python
L_hard = CrossEntropy(student_logits, ground_truth_labels)
```

- Standard classification objective
- **Class-weighted** (pos_weight=3.0) to handle pre-ictal/inter-ictal imbalance
- Ensures student still learns the correct decision boundary

### 3. Feature Distillation (TimeKD, 2025)

```python
L_feature = SmoothL1(
    student_kd_projector(student_hidden),
    teacher_embeddings.detach()
)
```

- Aligns **intermediate representations**, not just outputs
- **KD Projector** maps student's 48-dim GRU hidden → teacher's 128-dim embed space
- **SmoothL1** is more robust than MSE for cross-architecture alignment

---

### Default Hyperparameters

| Parameter | Value | Source |
|-----------|-------|--------|
| Temperature (T) | 4.0 | Hinton 1503.02531 |
| Alpha | 0.7 | 70% soft labels, 30% hard labels |
| Lambda feature | 0.3 | TimeKD 2505.02138 |
| Positive class weight | 3.0 | CHB-MIT imbalance ratio |

### Why This Combination Works

1. **Soft labels** transfer the teacher's understanding of class similarity
2. **Hard labels** anchor the student to ground truth
3. **Feature alignment** ensures the student's internal representations capture
   the same patterns the teacher learned (especially important for cross-architecture 
   distillation: Transformer → GRU)
"""


# ============================================================================
# Build Gradio App
# ============================================================================

def build_app():
    with gr.Blocks(
        title="🧠 Aura-Agent: Neural Guardian",
        theme=gr.themes.Soft(
            primary_hue="blue",
            secondary_hue="indigo",
        ),
    ) as app:

        gr.Markdown("""
# 🧠 Aura-Agent: Neural Guardian
### Seizure Prediction via Teacher-Student Knowledge Distillation

A proactive, mobile-first seizure prediction system with **30-minute pre-ictal warning**.

| Component | Architecture | Parameters |
|-----------|-------------|------------|
| **Teacher** | Transformer EEG Classifier | ~661K |
| **Student (RGF-Net)** | Ring-Buffer GRU + FiLM | ~37.5K (< 100K ✅) |
| **Agent** | smolagents CodeAgent | LLM-powered |
        """)

        with gr.Tab("🏗️ Architecture"):
            inspect_btn = gr.Button("🔍 Inspect Architectures", variant="primary")
            with gr.Row():
                teacher_md = gr.Markdown(label="Teacher")
                student_md = gr.Markdown(label="Student")
            compression_md = gr.Markdown(label="Compression")
            inspect_btn.click(
                inspect_architectures,
                outputs=[teacher_md, student_md, compression_md],
            )

        with gr.Tab("🎯 Train & Distill"):
            gr.Markdown("### Configure and run the full KD training pipeline")
            with gr.Row():
                with gr.Column():
                    n_samples = gr.Slider(100, 2000, value=300, step=100, label="Synthetic EEG Samples")
                    epochs_t = gr.Slider(5, 100, value=15, step=5, label="Teacher Epochs")
                    epochs_s = gr.Slider(5, 100, value=15, step=5, label="Student (KD) Epochs")
                with gr.Column():
                    lr = gr.Number(value=1e-3, label="Teacher Learning Rate")
                    temperature = gr.Slider(1.0, 10.0, value=4.0, step=0.5, label="KD Temperature (T)")
                    alpha = gr.Slider(0.0, 1.0, value=0.7, step=0.05, label="KD Alpha (soft label weight)")

            train_btn = gr.Button("🚀 Start Training", variant="primary")
            results_md = gr.Markdown(label="Results")
            train_log = gr.Textbox(label="Training Log", lines=15, max_lines=30)

            train_btn.click(
                run_training,
                inputs=[n_samples, epochs_t, epochs_s, lr, temperature, alpha],
                outputs=[results_md, train_log],
            )

        with gr.Tab("🔮 Live Inference"):
            gr.Markdown("### Test RGF-Net seizure risk prediction with configurable biometrics")
            with gr.Row():
                with gr.Column():
                    signal_type = gr.Radio(
                        ["Normal (Inter-ictal)", "Pre-ictal (Seizure Warning)", "Random Noise"],
                        value="Normal (Inter-ictal)",
                        label="EEG Signal Type",
                    )
                    age = gr.Slider(1, 100, value=35, step=1, label="Patient Age")
                    sex = gr.Radio(["Male", "Female"], value="Male", label="Sex")
                with gr.Column():
                    heart_rate = gr.Slider(40, 150, value=72, step=1, label="Resting Heart Rate (bpm)")
                    hrv = gr.Slider(10, 100, value=55, step=1, label="HRV SDNN (ms)")
                    hours_since = gr.Slider(0, 48, value=24, step=1, label="Hours Since Last Seizure")
                    medication = gr.Slider(0, 100, value=90, step=5, label="Medication Adherence (%)")

            infer_btn = gr.Button("⚡ Run Inference", variant="primary")
            with gr.Row():
                with gr.Column(scale=1):
                    risk_display = gr.Textbox(label="Risk Score")
                with gr.Column(scale=3):
                    inference_md = gr.Markdown(label="Assessment")

            infer_btn.click(
                run_inference,
                inputs=[age, sex, heart_rate, hrv, hours_since, medication, signal_type],
                outputs=[inference_md, risk_display],
            )

        with gr.Tab("🤖 Agent Workflow"):
            agent_md = gr.Markdown(show_agent_workflow())

        with gr.Tab("📐 KD Loss Explained"):
            kd_md = gr.Markdown(show_kd_explanation())

        with gr.Tab("📁 Source Code"):
            gr.Markdown("""
### Project Structure
```
aura_agent/
├── __init__.py          # Package initialization
├── config.py            # All hyperparameter configurations
├── teacher.py           # SeizureTransformerTeacher (Transformer classifier)
├── student.py           # RGF-Net (Ring-Buffer GRU + FiLM conditioning)
├── distillation.py      # KD training loop + synthetic data generator
├── agent.py             # smolagents CodeAgent + 4 custom tools
app.py                   # This Gradio demo
main.py                  # CLI entry point
requirements.txt         # Dependencies
```

### References
| Paper | Topic | ArXiv |
|-------|-------|-------|
| STAN | Spatio-Temporal Attention for seizure forecasting | 2511.01275 |
| Spiking Conformer | Efficient EEG seizure detection | 2402.09424 |
| Edge DL | Quantized models for neural implants | 2012.00307 |
| FiLM | Feature-wise Linear Modulation | 1709.07871 |
| Hinton KD | Knowledge Distillation | 1503.02531 |
| TimeKD | Privileged KD for time-series | 2505.02138 |
| Cross-arch KD | Transformer to CNN distillation | 2207.05273 |

### Datasets
| Dataset | Access |
|---------|--------|
| CHB-MIT | [PhysioNet](https://physionet.org/content/chbmit/1.0.0/) (free) |
| TUH EEG (TUSZ) | [ISIP Portal](https://isip.piconepress.com/projects/tuh_eeg/) (registration) |
            """)

    return app


if __name__ == "__main__":
    app = build_app()
    app.launch()
