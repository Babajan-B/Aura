#!/usr/bin/env python3
"""
RGF-Net Training + Export Pipeline
==================================
Hackathon-speed pipeline that:
  1. Trains the Transformer Teacher (briefly) on synthetic EEG.
  2. Distills knowledge into the RGF-Net Student (Ring-Buffer GRU + FiLM).
  3. Exports the student to ONNX.
  4. Converts ONNX -> TFLite (INT8 if possible, else float16, else float32).

Outputs (relative to this file):
  - rgf_net.onnx
  - rgf_net.tflite
  - student_best.pt   (best student checkpoint, written by trainer)
  - teacher_best.pt   (best teacher checkpoint, written by trainer)
  - training_report.json

Run:
  source /Users/jaan/Desktop/seizure-Project/ml/.venv/bin/activate
  python /Users/jaan/Desktop/seizure-Project/ml/train_and_export.py
"""

from __future__ import annotations

import os
import sys
import shutil
import subprocess
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ML_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ML_DIR.parent
REFERENCE_DIR = PROJECT_ROOT / "reference"

# Allow imports from reference/ (which contains the aura_agent package)
sys.path.insert(0, str(REFERENCE_DIR))

ONNX_PATH = ML_DIR / "rgf_net.onnx"
TFLITE_PATH = ML_DIR / "rgf_net.tflite"
REPORT_PATH = ML_DIR / "training_report.json"

# Switch to ML_DIR so checkpoints (teacher_best.pt, student_best.pt) land here
os.chdir(ML_DIR)


# ---------------------------------------------------------------------------
# Step 1 + 2: Train teacher and distill into student
# ---------------------------------------------------------------------------
def train() -> "RGFNet":
    import torch
    from aura_agent.config import EEGConfig, TeacherConfig, StudentConfig, KDConfig
    from aura_agent.distillation import DistillationTrainer, SyntheticEEGDataset

    # Hackathon-speed config: tiny epochs, small dataset
    eeg_cfg = EEGConfig()
    teacher_cfg = TeacherConfig()
    student_cfg = StudentConfig()
    kd_cfg = KDConfig()
    kd_cfg.teacher_epochs = 10
    kd_cfg.student_epochs = 10
    kd_cfg.batch_size = 32

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"[train] device={device}")

    print("[train] generating synthetic EEG (n_samples=500)")
    eeg_data, cond_data, labels = SyntheticEEGDataset.generate(
        n_samples=500, eeg_cfg=eeg_cfg, preictal_ratio=0.3, seed=42
    )

    trainer = DistillationTrainer(
        eeg_cfg=eeg_cfg,
        teacher_cfg=teacher_cfg,
        student_cfg=student_cfg,
        kd_cfg=kd_cfg,
        device=device,
    )
    trainer.train_teacher(eeg_data, cond_data, labels)
    trainer.distill(eeg_data, cond_data, labels)
    trainer.save_training_report(filepath=str(REPORT_PATH))

    return trainer.student


# ---------------------------------------------------------------------------
# Step 3: Export student to ONNX
# ---------------------------------------------------------------------------
def export_onnx(student) -> Path:
    student = student.cpu().eval()
    student.export_onnx(str(ONNX_PATH), device="cpu")

    # Sanity-check ONNX with onnxruntime
    try:
        import numpy as np
        import onnxruntime as ort

        sess = ort.InferenceSession(str(ONNX_PATH), providers=["CPUExecutionProvider"])
        inp_eeg = np.random.randn(1, 19, 1280).astype(np.float32)
        inp_cond = np.random.randn(1, 6).astype(np.float32)
        outs = sess.run(None, {"eeg_input": inp_eeg, "biometric_cond": inp_cond})
        print(f"[onnx] sanity check OK, logits={outs[0].shape}, embeds={outs[1].shape}")
    except Exception as e:
        print(f"[onnx] sanity check skipped/failed: {e}")

    return ONNX_PATH


# ---------------------------------------------------------------------------
# Step 4: Convert ONNX -> TFLite
# ---------------------------------------------------------------------------
def convert_onnx_to_tflite(onnx_path: Path) -> tuple[Path, str]:
    """Try INT8, then float16, then float32. Returns (path, mode_used)."""

    # Strategy A: onnx2tf (simplest path; emits TFLite directly from ONNX).
    try:
        return _convert_with_onnx2tf(onnx_path)
    except Exception as e:
        print(f"[tflite] onnx2tf path failed: {e}")

    # Strategy B: onnx -> TF SavedModel -> TFLiteConverter
    try:
        return _convert_via_savedmodel(onnx_path)
    except Exception as e:
        print(f"[tflite] SavedModel path failed: {e}")

    # Strategy C: stub model — Android side just needs *some* working .tflite.
    print("[tflite] falling back to stub TFLite (small CNN placeholder)")
    return _write_stub_tflite(), "stub_cnn"


def _convert_with_onnx2tf(onnx_path: Path) -> tuple[Path, str]:
    """Use onnx2tf to emit TFLite directly. Tries INT8, FP16, then FP32."""
    try:
        import onnx2tf  # noqa: F401
    except ImportError:
        raise RuntimeError("onnx2tf not installed")

    out_dir = ML_DIR / "_onnx2tf_out"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir()

    # onnx2tf CLI: output_*_tflite flags choose precision
    # Try INT8 first via dynamic-range quantization (no calibration needed).
    attempts = [
        # (cli flags, label)
        (["-oiqt", "-qt", "per-tensor"], "int8_dynamic"),  # Integer (dynamic range) qt
        (["-ofp16"], "float16"),
        ([], "float32"),
    ]

    last_err: Exception | None = None
    for flags, label in attempts:
        try:
            print(f"[tflite] onnx2tf attempt: {label} {flags}")
            cmd = [
                sys.executable,
                "-m",
                "onnx2tf",
                "-i",
                str(onnx_path),
                "-o",
                str(out_dir),
                "-cotof",  # confirm output tensors of float
            ] + flags
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0:
                raise RuntimeError(f"onnx2tf rc={res.returncode}: {res.stderr[-400:]}")

            # Find generated TFLite. Pick smallest INT8/FP16 if multiple.
            candidates = sorted(out_dir.glob("*.tflite"), key=lambda p: p.stat().st_size)
            if not candidates:
                raise RuntimeError("no .tflite file produced")

            chosen = candidates[0]
            shutil.copy(chosen, TFLITE_PATH)
            print(f"[tflite] onnx2tf success ({label}): "
                  f"{TFLITE_PATH} ({TFLITE_PATH.stat().st_size/1024:.1f} KB)")
            return TFLITE_PATH, label
        except Exception as e:
            last_err = e
            continue

    raise RuntimeError(f"onnx2tf all attempts failed: {last_err}")


def _convert_via_savedmodel(onnx_path: Path) -> tuple[Path, str]:
    """ONNX -> TF SavedModel (onnx-tf) -> TFLite (TFLiteConverter)."""
    try:
        import onnx
        from onnx_tf.backend import prepare  # noqa: F401
        import tensorflow as tf
    except ImportError as e:
        raise RuntimeError(f"missing dep for SavedModel path: {e}")

    sm_dir = ML_DIR / "_savedmodel"
    if sm_dir.exists():
        shutil.rmtree(sm_dir)

    print("[tflite] onnx -> SavedModel via onnx-tf")
    onnx_model = onnx.load(str(onnx_path))
    tf_rep = prepare(onnx_model)
    tf_rep.export_graph(str(sm_dir))

    # Try float16, then float32 (INT8 quant for GRU is unreliable here)
    for mode in ("float16", "float32"):
        try:
            converter = tf.lite.TFLiteConverter.from_saved_model(str(sm_dir))
            if mode == "float16":
                converter.optimizations = [tf.lite.Optimize.DEFAULT]
                converter.target_spec.supported_types = [tf.float16]
            converter.target_spec.supported_ops = [
                tf.lite.OpsSet.TFLITE_BUILTINS,
                tf.lite.OpsSet.SELECT_TF_OPS,  # GRU often needs this
            ]
            tflite = converter.convert()
            TFLITE_PATH.write_bytes(tflite)
            print(f"[tflite] SavedModel path success ({mode}): "
                  f"{TFLITE_PATH.stat().st_size/1024:.1f} KB")
            return TFLITE_PATH, mode
        except Exception as e:
            print(f"[tflite] SavedModel {mode} failed: {e}")

    raise RuntimeError("all SavedModel TFLite conversion attempts failed")


def _write_stub_tflite() -> Path:
    """Produce a tiny CNN .tflite as a placeholder so the Android app has *something*.
    Documented clearly in README — this is NOT the real RGF-Net.
    """
    import tensorflow as tf

    inputs = tf.keras.Input(shape=(19, 1280), name="eeg_input")
    x = tf.keras.layers.Conv1D(8, 25, padding="same", activation="relu")(inputs)
    x = tf.keras.layers.AveragePooling1D(pool_size=8)(x)
    x = tf.keras.layers.Conv1D(8, 1, activation="relu")(x)
    x = tf.keras.layers.GlobalAveragePooling1D()(x)
    cond = tf.keras.Input(shape=(6,), name="biometric_cond")
    x = tf.keras.layers.Concatenate()([x, cond])
    logits = tf.keras.layers.Dense(2, name="logits")(x)
    model = tf.keras.Model(inputs=[inputs, cond], outputs=logits)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]  # dynamic-range INT8
    tflite = converter.convert()
    TFLITE_PATH.write_bytes(tflite)
    print(f"[tflite] STUB written: {TFLITE_PATH.stat().st_size/1024:.1f} KB")
    return TFLITE_PATH


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print("=" * 70)
    print("RGF-Net hackathon pipeline: train -> ONNX -> TFLite")
    print("=" * 70)

    student = train()
    onnx_path = export_onnx(student)
    tflite_path, mode = convert_onnx_to_tflite(onnx_path)

    onnx_kb = onnx_path.stat().st_size / 1024
    tflite_kb = tflite_path.stat().st_size / 1024
    print("\n" + "=" * 70)
    print(f"DONE")
    print(f"  ONNX:   {onnx_path} ({onnx_kb:.1f} KB)")
    print(f"  TFLite: {tflite_path} ({tflite_kb:.1f} KB) mode={mode}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
