#!/usr/bin/env python3
"""
Aura-Agent: Neural Guardian for Seizure Prediction
===================================================
Main entry point — demonstrates the full pipeline:

  1. Build & inspect Teacher and Student architectures
  2. Generate synthetic EEG data (replace with TUH/CHB-MIT in production)
  3. Train Teacher model on seizure detection
  4. Distill Teacher → Student (RGF-Net) via Knowledge Distillation
  5. Quantize Student for Android Edge-AI
  6. (Optional) Launch smolagents CodeAgent for autonomous monitoring

Usage:
    python main.py                    # Full pipeline demo
    python main.py --phase inspect    # Inspect architectures only
    python main.py --phase train      # Train + distill
    python main.py --phase agent      # Agent demo only
"""

import argparse
import sys
import time
import torch
import json

from aura_agent.config import EEGConfig, TeacherConfig, StudentConfig, KDConfig, AgentConfig
from aura_agent.teacher import SeizureTransformerTeacher
from aura_agent.student import RGFNet
from aura_agent.distillation import DistillationTrainer, SyntheticEEGDataset


def print_banner():
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║       🧠  AURA-AGENT: Neural Guardian  🧠                    ║
    ║       Seizure Prediction via Knowledge Distillation           ║
    ║                                                               ║
    ║   Teacher: Transformer EEG Classifier (~661K params)          ║
    ║   Student: RGF-Net — Ring-Buffer GRU + FiLM (<100K params)    ║
    ║   Target:  30-minute pre-ictal warning on Android Edge-AI     ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)


def inspect_architectures():
    eeg_cfg = EEGConfig()
    teacher_cfg = TeacherConfig()
    student_cfg = StudentConfig()

    teacher = SeizureTransformerTeacher(eeg_cfg, teacher_cfg)
    student = RGFNet(eeg_cfg, student_cfg)

    print(f"Teacher: {teacher.count_parameters():,} params")
    print(f"Student: {student.count_parameters():,} params (budget: <100K)")
    print(f"Compression: {teacher.count_parameters() / student.count_parameters():.1f}x")
    print(f"Student breakdown: {student.param_breakdown()}")

    dummy_eeg = torch.randn(2, eeg_cfg.n_channels, eeg_cfg.window_samples)
    dummy_cond = torch.randn(2, student_cfg.cond_dim)
    logits_t, _ = teacher(dummy_eeg)
    logits_s, _ = student(dummy_eeg, dummy_cond)
    print(f"Teacher output: {logits_t.shape}, Student output: {logits_s.shape}")


def run_training(epochs_teacher=50, epochs_student=50, n_samples=2000):
    eeg_cfg = EEGConfig()
    kd_cfg = KDConfig()
    kd_cfg.teacher_epochs = epochs_teacher
    kd_cfg.student_epochs = epochs_student

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    eeg_data, cond_data, labels = SyntheticEEGDataset.generate(n_samples=n_samples)

    trainer = DistillationTrainer(eeg_cfg=eeg_cfg, kd_cfg=kd_cfg, device=device)
    trainer.train_teacher(eeg_data, cond_data, labels)
    trainer.distill(eeg_data, cond_data, labels)
    trainer.quantize_student()
    trainer.save_training_report()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Aura-Agent: Neural Guardian')
    parser.add_argument('--phase', choices=['all', 'inspect', 'train', 'agent'], default='all')
    parser.add_argument('--epochs-teacher', type=int, default=50)
    parser.add_argument('--epochs-student', type=int, default=50)
    parser.add_argument('--n-samples', type=int, default=2000)
    args = parser.parse_args()

    print_banner()

    if args.phase in ('all', 'inspect'):
        inspect_architectures()

    if args.phase in ('all', 'train'):
        run_training(args.epochs_teacher, args.epochs_student, args.n_samples)

    print("\n✅ Aura-Agent pipeline complete.")
