"""
Aura-Agent Knowledge Distillation Training Loop
================================================
Implements Teacher→Student knowledge distillation for EEG seizure prediction.

Three-component loss (Hinton 1503.02531 + TimeKD 2505.02138):
  1. Soft-label KD loss: KL-divergence between temperature-scaled logits
  2. Hard-label CE loss: Standard cross-entropy with ground truth
  3. Feature distillation: SmoothL1 between projected student/teacher embeddings

Training protocol:
  Phase 1: Train teacher on labeled EEG data (CE + class-weighted sampling)
  Phase 2: Distill teacher → student with combined KD loss
  
Reference implementations:
  - Hinton et al., "Distilling the Knowledge in a Neural Network" (1503.02531)
  - TimeKD feature distillation (2505.02138)
  - Cross-architecture KD with projection heads (2207.05273)
"""

import os
import time
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset, WeightedRandomSampler
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts, OneCycleLR
from typing import Dict, Tuple, Optional
import json

from .config import EEGConfig, TeacherConfig, StudentConfig, KDConfig
from .teacher import SeizureTransformerTeacher
from .student import RGFNet


# ============================================================================
# Synthetic Data Generator (for development/testing)
# Replace with real TUH/CHB-MIT data loader in production
# ============================================================================

class SyntheticEEGDataset:
    """Generate synthetic EEG data mimicking CHB-MIT characteristics.
    
    Creates realistic-looking EEG segments with:
    - Inter-ictal: normal alpha/beta rhythms
    - Pre-ictal: increased gamma, decreased alpha, spike patterns
    
    For development/testing only — replace with real data pipeline.
    """
    
    @staticmethod
    def generate(
        n_samples: int = 2000,
        eeg_cfg: EEGConfig = None,
        preictal_ratio: float = 0.3,
        seed: int = 42,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Generate synthetic EEG data with labels.
        
        Args:
            n_samples: total number of 5-second windows
            eeg_cfg: EEG configuration
            preictal_ratio: fraction of pre-ictal samples
            seed: random seed
            
        Returns:
            eeg_data: (N, C, T) — synthetic EEG signals
            cond_data: (N, cond_dim) — biometric features
            labels: (N,) — 0=inter-ictal, 1=pre-ictal
        """
        if eeg_cfg is None:
            eeg_cfg = EEGConfig()
            
        torch.manual_seed(seed)
        C, T = eeg_cfg.n_channels, eeg_cfg.window_samples
        n_preictal = int(n_samples * preictal_ratio)
        n_interictal = n_samples - n_preictal
        
        # Time axis
        t = torch.linspace(0, eeg_cfg.window_sec, T).unsqueeze(0).unsqueeze(0)
        
        # === Inter-ictal: dominant alpha (8-12Hz) + beta (12-30Hz) ===
        interictal = torch.zeros(n_interictal, C, T)
        for ch in range(C):
            freq_alpha = 8 + 4 * torch.rand(n_interictal, 1, 1)
            freq_beta = 12 + 18 * torch.rand(n_interictal, 1, 1)
            interictal[:, ch:ch+1, :] = (
                0.5 * torch.sin(2 * math.pi * freq_alpha * t) +  # Alpha
                0.3 * torch.sin(2 * math.pi * freq_beta * t) +   # Beta
                0.1 * torch.randn(n_interictal, 1, T)            # Noise
            )
            
        # === Pre-ictal: increased gamma, decreased alpha, spikes ===
        preictal = torch.zeros(n_preictal, C, T)
        for ch in range(C):
            freq_gamma = 30 + 70 * torch.rand(n_preictal, 1, 1)
            freq_theta = 4 + 4 * torch.rand(n_preictal, 1, 1)
            # Spike artifacts (sharp transients)
            spike_locs = torch.randint(0, T, (n_preictal, 5))
            spikes = torch.zeros(n_preictal, 1, T)
            for i in range(n_preictal):
                for loc in spike_locs[i]:
                    width = torch.randint(3, 15, (1,)).item()
                    start = max(0, loc - width)
                    end = min(T, loc + width)
                    spikes[i, 0, start:end] = 2.0 * torch.randn(1)
                    
            preictal[:, ch:ch+1, :] = (
                0.2 * torch.sin(2 * math.pi * freq_theta * t) +   # Theta
                0.6 * torch.sin(2 * math.pi * freq_gamma * t) +   # Gamma
                0.3 * torch.randn(n_preictal, 1, T) +             # Noise
                spikes                                              # Spikes
            )
        
        # Concatenate and shuffle
        eeg_data = torch.cat([interictal, preictal], dim=0)
        labels = torch.cat([
            torch.zeros(n_interictal, dtype=torch.long),
            torch.ones(n_preictal, dtype=torch.long),
        ])
        
        # Biometric conditioning vectors
        # [age_norm, sex, resting_hr, hrv_sdnn, hours_since_seizure, med_adherence]
        cond_data = torch.zeros(n_samples, 6)
        cond_data[:, 0] = torch.rand(n_samples)                    # age: 0-1 normalized
        cond_data[:, 1] = (torch.rand(n_samples) > 0.5).float()   # sex: 0/1
        cond_data[:, 2] = 60 + 40 * torch.rand(n_samples)         # resting HR: 60-100 bpm
        cond_data[:, 2] = cond_data[:, 2] / 100.0                 # normalize
        cond_data[:, 3] = torch.rand(n_samples)                    # HRV SDNN normalized
        cond_data[:, 4] = torch.rand(n_samples)                    # hours since seizure (norm)
        cond_data[:, 5] = torch.rand(n_samples)                    # medication adherence
        
        # Shuffle
        perm = torch.randperm(n_samples)
        eeg_data = eeg_data[perm]
        cond_data = cond_data[perm]
        labels = labels[perm]
        
        # Normalize EEG: z-score per channel
        mean = eeg_data.mean(dim=2, keepdim=True)
        std = eeg_data.std(dim=2, keepdim=True) + 1e-8
        eeg_data = (eeg_data - mean) / std
        
        return eeg_data, cond_data, labels


# ============================================================================
# Loss Functions
# ============================================================================

class KnowledgeDistillationLoss(nn.Module):
    """Combined KD loss for Teacher→Student distillation.
    
    L_total = α * L_soft + (1 - α) * L_hard + λ_feat * L_feature
    
    Components:
    1. L_soft: KL-divergence between soft labels (temperature-scaled)
       - Teacher and student logits are divided by T before softmax
       - Multiplied by T² to maintain gradient magnitude
       
    2. L_hard: Cross-entropy with ground-truth labels
       - Weighted by class frequency for imbalance handling
       
    3. L_feature: SmoothL1 between projected embeddings
       - Student's KD projector maps to teacher's embed space
       - SmoothL1 is more robust than MSE for feature alignment
    """
    
    def __init__(self, kd_cfg: KDConfig = None):
        super().__init__()
        if kd_cfg is None:
            kd_cfg = KDConfig()
        self.T = kd_cfg.temperature
        self.alpha = kd_cfg.alpha
        self.lambda_feat = kd_cfg.lambda_feat
        
        # Weighted CE for class imbalance
        self.ce_loss = nn.CrossEntropyLoss(
            weight=torch.tensor([1.0, kd_cfg.pos_weight])
        )
        
    def forward(
        self,
        teacher_logits: torch.Tensor,
        student_logits: torch.Tensor,
        teacher_embeddings: torch.Tensor,
        student_embeddings: torch.Tensor,
        labels: torch.Tensor,
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Compute combined KD loss.
        
        Args:
            teacher_logits: (B, n_classes) — teacher's raw logits
            student_logits: (B, n_classes) — student's raw logits
            teacher_embeddings: (B, embed_dim) — teacher's embeddings
            student_embeddings: (B, embed_dim) — student's projected embeddings
            labels: (B,) — ground truth labels
            
        Returns:
            loss: scalar total loss
            loss_dict: breakdown of individual loss components
        """
        device = student_logits.device
        self.ce_loss = self.ce_loss.to(device)
        
        # 1. Soft-label distillation loss (Hinton KD)
        soft_teacher = F.softmax(teacher_logits.detach() / self.T, dim=-1)
        soft_student = F.log_softmax(student_logits / self.T, dim=-1)
        L_soft = F.kl_div(
            soft_student, 
            soft_teacher, 
            reduction='batchmean'
        ) * (self.T ** 2)  # Scale by T² to maintain gradient magnitude
        
        # 2. Hard-label cross-entropy loss
        L_hard = self.ce_loss(student_logits, labels)
        
        # 3. Feature distillation loss (SmoothL1 — more robust than MSE)
        L_feat = F.smooth_l1_loss(
            student_embeddings, 
            teacher_embeddings.detach()
        )
        
        # Combined loss
        loss = self.alpha * L_soft + (1 - self.alpha) * L_hard + self.lambda_feat * L_feat
        
        loss_dict = {
            'total': loss.item(),
            'soft_kd': L_soft.item(),
            'hard_ce': L_hard.item(),
            'feature': L_feat.item(),
        }
        
        return loss, loss_dict


# ============================================================================
# Training Engine
# ============================================================================

class DistillationTrainer:
    """Full training pipeline for Teacher-Student Knowledge Distillation.
    
    Usage:
        trainer = DistillationTrainer(device='cuda')
        
        # Phase 1: Train teacher
        trainer.train_teacher(train_loader, val_loader)
        
        # Phase 2: Distill to student
        trainer.distill(train_loader, val_loader)
        
        # Export student for edge deployment
        trainer.export_student('rgfnet_quantized.onnx')
    """
    
    def __init__(
        self,
        eeg_cfg: EEGConfig = None,
        teacher_cfg: TeacherConfig = None,
        student_cfg: StudentConfig = None,
        kd_cfg: KDConfig = None,
        device: str = 'cpu',
    ):
        self.eeg_cfg = eeg_cfg or EEGConfig()
        self.teacher_cfg = teacher_cfg or TeacherConfig()
        self.student_cfg = student_cfg or StudentConfig()
        self.kd_cfg = kd_cfg or KDConfig()
        self.device = torch.device(device)
        
        # Initialize models
        self.teacher = SeizureTransformerTeacher(
            self.eeg_cfg, self.teacher_cfg
        ).to(self.device)
        
        self.student = RGFNet(
            self.eeg_cfg, self.student_cfg
        ).to(self.device)
        
        # KD loss
        self.kd_loss_fn = KnowledgeDistillationLoss(self.kd_cfg).to(self.device)
        
        # Metrics tracking
        self.history = {
            'teacher': {'train_loss': [], 'val_loss': [], 'val_acc': [], 'val_sensitivity': [], 'val_specificity': []},
            'student': {'train_loss': [], 'val_loss': [], 'val_acc': [], 'val_sensitivity': [], 'val_specificity': [],
                       'kd_soft': [], 'kd_feat': []},
        }
        
        print(f"[Aura-Agent] Teacher params: {self.teacher.count_parameters():,}")
        print(f"[Aura-Agent] Student params: {self.student.count_parameters():,}")
        print(f"[Aura-Agent] Student param breakdown: {self.student.param_breakdown()}")
        print(f"[Aura-Agent] Device: {self.device}")
        
    def _create_dataloaders(
        self,
        eeg_data: torch.Tensor,
        cond_data: torch.Tensor,
        labels: torch.Tensor,
        val_split: float = 0.2,
    ) -> Tuple[DataLoader, DataLoader]:
        """Create train/val dataloaders with class-balanced sampling."""
        n = len(labels)
        n_val = int(n * val_split)
        n_train = n - n_val
        
        # Split
        train_eeg, val_eeg = eeg_data[:n_train], eeg_data[n_train:]
        train_cond, val_cond = cond_data[:n_train], cond_data[n_train:]
        train_labels, val_labels = labels[:n_train], labels[n_train:]
        
        # Weighted sampler for class imbalance
        class_counts = torch.bincount(train_labels)
        weights = 1.0 / class_counts.float()
        sample_weights = weights[train_labels]
        sampler = WeightedRandomSampler(
            sample_weights, 
            num_samples=len(sample_weights),
            replacement=True,
        )
        
        train_dataset = TensorDataset(train_eeg, train_cond, train_labels)
        val_dataset = TensorDataset(val_eeg, val_cond, val_labels)
        
        train_loader = DataLoader(
            train_dataset, 
            batch_size=self.kd_cfg.batch_size,
            sampler=sampler,
            drop_last=True,
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=self.kd_cfg.batch_size,
            shuffle=False,
        )
        
        print(f"[Data] Train: {n_train} samples ({train_labels.sum().item()} pre-ictal)")
        print(f"[Data] Val: {n_val} samples ({val_labels.sum().item()} pre-ictal)")
        
        return train_loader, val_loader
    
    @staticmethod
    def _compute_metrics(logits: torch.Tensor, labels: torch.Tensor) -> Dict[str, float]:
        """Compute accuracy, sensitivity, specificity, F1."""
        preds = logits.argmax(dim=-1)
        correct = (preds == labels).float()
        
        tp = ((preds == 1) & (labels == 1)).float().sum()
        tn = ((preds == 0) & (labels == 0)).float().sum()
        fp = ((preds == 1) & (labels == 0)).float().sum()
        fn = ((preds == 0) & (labels == 1)).float().sum()
        
        accuracy = correct.mean().item()
        sensitivity = (tp / (tp + fn + 1e-8)).item()  # Recall for pre-ictal
        specificity = (tn / (tn + fp + 1e-8)).item()
        precision = (tp / (tp + fp + 1e-8)).item()
        f1 = (2 * precision * sensitivity / (precision + sensitivity + 1e-8))
        
        return {
            'accuracy': accuracy,
            'sensitivity': sensitivity,
            'specificity': specificity,
            'precision': precision,
            'f1': f1,
        }
    
    # ========================================================================
    # Phase 1: Teacher Training
    # ========================================================================
    
    def train_teacher(
        self,
        eeg_data: torch.Tensor,
        cond_data: torch.Tensor,
        labels: torch.Tensor,
        epochs: int = None,
    ) -> Dict:
        """Train the teacher model with standard cross-entropy."""
        epochs = epochs or self.kd_cfg.teacher_epochs
        train_loader, val_loader = self._create_dataloaders(
            eeg_data, cond_data, labels
        )
        
        optimizer = torch.optim.AdamW(
            self.teacher.parameters(),
            lr=self.kd_cfg.teacher_lr,
            weight_decay=self.kd_cfg.weight_decay,
        )
        
        scheduler = OneCycleLR(
            optimizer,
            max_lr=self.kd_cfg.teacher_lr,
            epochs=epochs,
            steps_per_epoch=len(train_loader),
        )
        
        ce_loss_fn = nn.CrossEntropyLoss(
            weight=torch.tensor([1.0, self.kd_cfg.pos_weight]).to(self.device)
        )
        
        best_val_acc = 0.0
        best_metrics = {}
        
        print("\n" + "=" * 70)
        print("PHASE 1: TEACHER TRAINING")
        print("=" * 70)
        
        for epoch in range(epochs):
            # --- Training ---
            self.teacher.train()
            epoch_loss = 0.0
            n_batches = 0
            
            for batch_eeg, batch_cond, batch_labels in train_loader:
                batch_eeg = batch_eeg.to(self.device)
                batch_labels = batch_labels.to(self.device)
                
                optimizer.zero_grad()
                logits, _ = self.teacher(batch_eeg)
                loss = ce_loss_fn(logits, batch_labels)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.teacher.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                
                epoch_loss += loss.item()
                n_batches += 1
            
            avg_train_loss = epoch_loss / max(n_batches, 1)
            self.history['teacher']['train_loss'].append(avg_train_loss)
            
            # --- Validation ---
            val_metrics = self._validate_teacher(val_loader)
            self.history['teacher']['val_loss'].append(val_metrics['loss'])
            self.history['teacher']['val_acc'].append(val_metrics['accuracy'])
            self.history['teacher']['val_sensitivity'].append(val_metrics['sensitivity'])
            self.history['teacher']['val_specificity'].append(val_metrics['specificity'])
            
            if val_metrics['accuracy'] > best_val_acc:
                best_val_acc = val_metrics['accuracy']
                best_metrics = val_metrics.copy()
                best_metrics['epoch'] = epoch + 1
                torch.save(self.teacher.state_dict(), 'teacher_best.pt')
            
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(
                    f"  [Teacher] Epoch {epoch+1:3d}/{epochs} | "
                    f"Train Loss: {avg_train_loss:.4f} | "
                    f"Val Loss: {val_metrics['loss']:.4f} | "
                    f"Val Acc: {val_metrics['accuracy']:.4f} | "
                    f"Sens: {val_metrics['sensitivity']:.4f} | "
                    f"Spec: {val_metrics['specificity']:.4f}"
                )
        
        # Load best teacher
        self.teacher.load_state_dict(torch.load('teacher_best.pt', weights_only=True))
        print(f"\n  [Teacher] Best @ epoch {best_metrics.get('epoch', '?')}: "
              f"Acc={best_metrics['accuracy']:.4f}, "
              f"Sens={best_metrics['sensitivity']:.4f}, "
              f"Spec={best_metrics['specificity']:.4f}")
        
        return best_metrics
    
    @torch.no_grad()
    def _validate_teacher(self, val_loader: DataLoader) -> Dict:
        """Validate teacher model."""
        self.teacher.eval()
        all_logits, all_labels = [], []
        total_loss = 0.0
        n_batches = 0
        
        ce_loss_fn = nn.CrossEntropyLoss(
            weight=torch.tensor([1.0, self.kd_cfg.pos_weight]).to(self.device)
        )
        
        for batch_eeg, batch_cond, batch_labels in val_loader:
            batch_eeg = batch_eeg.to(self.device)
            batch_labels = batch_labels.to(self.device)
            
            logits, _ = self.teacher(batch_eeg)
            loss = ce_loss_fn(logits, batch_labels)
            
            all_logits.append(logits.cpu())
            all_labels.append(batch_labels.cpu())
            total_loss += loss.item()
            n_batches += 1
        
        all_logits = torch.cat(all_logits, dim=0)
        all_labels = torch.cat(all_labels, dim=0)
        
        metrics = self._compute_metrics(all_logits, all_labels)
        metrics['loss'] = total_loss / max(n_batches, 1)
        return metrics
    
    # ========================================================================
    # Phase 2: Knowledge Distillation
    # ========================================================================
    
    def distill(
        self,
        eeg_data: torch.Tensor,
        cond_data: torch.Tensor,
        labels: torch.Tensor,
        epochs: int = None,
    ) -> Dict:
        """Distill teacher knowledge into student (RGF-Net)."""
        epochs = epochs or self.kd_cfg.student_epochs
        train_loader, val_loader = self._create_dataloaders(
            eeg_data, cond_data, labels
        )
        
        # Freeze teacher
        self.teacher.eval()
        for p in self.teacher.parameters():
            p.requires_grad = False
            
        optimizer = torch.optim.AdamW(
            self.student.parameters(),
            lr=self.kd_cfg.student_lr,
            weight_decay=self.kd_cfg.weight_decay,
        )
        
        scheduler = CosineAnnealingWarmRestarts(
            optimizer, T_0=20, T_mult=2, eta_min=1e-6
        )
        
        best_val_acc = 0.0
        best_metrics = {}
        
        print("\n" + "=" * 70)
        print("PHASE 2: KNOWLEDGE DISTILLATION (Teacher → Student)")
        print("=" * 70)
        print(f"  Temperature={self.kd_cfg.temperature}, "
              f"α={self.kd_cfg.alpha}, λ_feat={self.kd_cfg.lambda_feat}")
        
        for epoch in range(epochs):
            # --- Training ---
            self.student.train()
            epoch_losses = {'total': 0, 'soft_kd': 0, 'hard_ce': 0, 'feature': 0}
            n_batches = 0
            
            for batch_eeg, batch_cond, batch_labels in train_loader:
                batch_eeg = batch_eeg.to(self.device)
                batch_cond = batch_cond.to(self.device)
                batch_labels = batch_labels.to(self.device)
                
                # Teacher forward (frozen)
                with torch.no_grad():
                    teacher_logits, teacher_embeds = self.teacher(
                        batch_eeg, return_embeddings=True
                    )
                
                # Student forward
                student_logits, student_embeds = self.student(
                    batch_eeg, batch_cond, return_embeddings=True
                )
                
                # KD loss
                loss, loss_dict = self.kd_loss_fn(
                    teacher_logits, student_logits,
                    teacher_embeds, student_embeds,
                    batch_labels,
                )
                
                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.student.parameters(), 1.0)
                optimizer.step()
                
                for k, v in loss_dict.items():
                    epoch_losses[k] += v
                n_batches += 1
            
            scheduler.step()
            
            avg_losses = {k: v / max(n_batches, 1) for k, v in epoch_losses.items()}
            self.history['student']['train_loss'].append(avg_losses['total'])
            self.history['student']['kd_soft'].append(avg_losses['soft_kd'])
            self.history['student']['kd_feat'].append(avg_losses['feature'])
            
            # --- Validation ---
            val_metrics = self._validate_student(val_loader)
            self.history['student']['val_loss'].append(val_metrics['loss'])
            self.history['student']['val_acc'].append(val_metrics['accuracy'])
            self.history['student']['val_sensitivity'].append(val_metrics['sensitivity'])
            self.history['student']['val_specificity'].append(val_metrics['specificity'])
            
            if val_metrics['accuracy'] > best_val_acc:
                best_val_acc = val_metrics['accuracy']
                best_metrics = val_metrics.copy()
                best_metrics['epoch'] = epoch + 1
                torch.save(self.student.state_dict(), 'student_best.pt')
            
            if (epoch + 1) % 10 == 0 or epoch == 0:
                print(
                    f"  [Student] Epoch {epoch+1:3d}/{epochs} | "
                    f"Loss: {avg_losses['total']:.4f} "
                    f"(KD:{avg_losses['soft_kd']:.3f} "
                    f"CE:{avg_losses['hard_ce']:.3f} "
                    f"Feat:{avg_losses['feature']:.3f}) | "
                    f"Val Acc: {val_metrics['accuracy']:.4f} | "
                    f"Sens: {val_metrics['sensitivity']:.4f} | "
                    f"Spec: {val_metrics['specificity']:.4f}"
                )
        
        # Load best student
        self.student.load_state_dict(torch.load('student_best.pt', weights_only=True))
        print(f"\n  [Student] Best @ epoch {best_metrics.get('epoch', '?')}: "
              f"Acc={best_metrics['accuracy']:.4f}, "
              f"Sens={best_metrics['sensitivity']:.4f}, "
              f"Spec={best_metrics['specificity']:.4f}")
        
        return best_metrics
    
    @torch.no_grad()
    def _validate_student(self, val_loader: DataLoader) -> Dict:
        """Validate student model with KD loss."""
        self.student.eval()
        self.teacher.eval()
        
        all_logits, all_labels = [], []
        total_loss = 0.0
        n_batches = 0
        
        for batch_eeg, batch_cond, batch_labels in val_loader:
            batch_eeg = batch_eeg.to(self.device)
            batch_cond = batch_cond.to(self.device)
            batch_labels = batch_labels.to(self.device)
            
            teacher_logits, teacher_embeds = self.teacher(batch_eeg)
            student_logits, student_embeds = self.student(batch_eeg, batch_cond)
            
            loss, _ = self.kd_loss_fn(
                teacher_logits, student_logits,
                teacher_embeds, student_embeds,
                batch_labels,
            )
            
            all_logits.append(student_logits.cpu())
            all_labels.append(batch_labels.cpu())
            total_loss += loss.item()
            n_batches += 1
        
        all_logits = torch.cat(all_logits, dim=0)
        all_labels = torch.cat(all_labels, dim=0)
        
        metrics = self._compute_metrics(all_logits, all_labels)
        metrics['loss'] = total_loss / max(n_batches, 1)
        return metrics
    
    # ========================================================================
    # Quantization & Export
    # ========================================================================
    
    def quantize_student(self) -> nn.Module:
        """Apply dynamic INT8 quantization to the student model."""
        self.student.eval()
        self.student = self.student.cpu()
        
        quantized = torch.quantization.quantize_dynamic(
            self.student,
            {nn.Linear, nn.GRU},
            dtype=torch.qint8,
        )
        
        orig_size = sum(p.nelement() * p.element_size() for p in self.student.parameters())
        quant_size = orig_size // 4
        
        print(f"[Quantization] Original: {orig_size / 1024:.1f} KB")
        print(f"[Quantization] Quantized (est.): {quant_size / 1024:.1f} KB")
        
        return quantized
    
    def save_training_report(self, filepath: str = 'training_report.json'):
        """Save complete training history and model info."""
        report = {
            'teacher': {
                'params': self.teacher.count_parameters(),
                'architecture': 'SeizureTransformerTeacher',
                'config': {
                    'd_model': self.teacher_cfg.d_model,
                    'n_heads': self.teacher_cfg.n_heads,
                    'n_layers': self.teacher_cfg.n_transformer_layers,
                },
                'history': self.history['teacher'],
            },
            'student': {
                'params': self.student.count_parameters(),
                'architecture': 'RGFNet (Ring-Buffer GRU + FiLM)',
                'config': {
                    'gru_hidden': self.student_cfg.gru_hidden,
                    'gru_layers': self.student_cfg.gru_layers,
                    'cond_dim': self.student_cfg.cond_dim,
                    'film_hidden': self.student_cfg.film_hidden,
                },
                'param_breakdown': self.student.param_breakdown(),
                'history': self.history['student'],
            },
            'distillation': {
                'temperature': self.kd_cfg.temperature,
                'alpha': self.kd_cfg.alpha,
                'lambda_feat': self.kd_cfg.lambda_feat,
            },
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"[Report] Saved to {filepath}")
        
        return report
