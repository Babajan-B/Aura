"""
Aura-Agent Teacher Model: EEG Seizure Transformer
==================================================
A high-capacity Transformer-based classifier for EEG seizure prediction.
Inspired by STAN (arxiv 2511.01275) with Temporal Fusion Transformer elements.

Architecture:
  Input: (B, C=19, T=1280) raw EEG segments (5s @ 256Hz)
  1. Patch Embedding: Conv1d per-channel → (B, C, D)
  2. Spatial-Temporal Positional Encoding
  3. N-layer Transformer Encoder with multi-head self-attention
  4. Temporal aggregation → classification head
  
Output: logits (B, 2), embeddings (B, embed_dim) for KD
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple

from .config import TeacherConfig, EEGConfig


class PatchEmbedding(nn.Module):
    """Convert raw EEG channels into patch embeddings.
    
    Each channel is independently processed by a shared 1D-CNN 
    to extract local temporal features, then projected to d_model.
    """
    
    def __init__(self, eeg_cfg: EEGConfig, d_model: int):
        super().__init__()
        self.n_channels = eeg_cfg.n_channels
        self.d_model = d_model
        
        # Temporal feature extractor (shared across channels)
        # kernel=25 ≈ 100ms at 256Hz, stride=8 for 8x downsampling
        self.temporal_conv = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=25, stride=1, padding=12),
            nn.BatchNorm1d(32),
            nn.GELU(),
            nn.Conv1d(32, 64, kernel_size=15, stride=8, padding=7),
            nn.BatchNorm1d(64),
            nn.GELU(),
            nn.Conv1d(64, d_model, kernel_size=9, stride=4, padding=4),
            nn.BatchNorm1d(d_model),
            nn.GELU(),
        )
        
        # Spatial aggregation: learn inter-channel relationships
        self.spatial_proj = nn.Linear(eeg_cfg.n_channels, 1)
        
        # Adaptive pooling to fixed sequence length
        self.adaptive_pool = nn.AdaptiveAvgPool1d(32)  # 32 time tokens
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, C, T) raw EEG — C=19 channels, T=1280 time steps
        Returns:
            tokens: (B, S, D) — S=32 time tokens, D=d_model
        """
        B, C, T = x.shape
        
        # Process each channel independently through shared convs
        # Reshape: (B, C, T) → (B*C, 1, T)
        x = x.reshape(B * C, 1, T)
        x = self.temporal_conv(x)  # (B*C, D, T')
        
        # Reshape back: (B*C, D, T') → (B, C, D, T')
        D = x.shape[1]
        T_prime = x.shape[2]
        x = x.reshape(B, C, D, T_prime)
        
        # Spatial aggregation: (B, C, D, T') → (B, D, T')
        x = x.permute(0, 2, 3, 1)  # (B, D, T', C)
        x = self.spatial_proj(x).squeeze(-1)  # (B, D, T')
        
        # Fixed sequence length
        x = self.adaptive_pool(x)  # (B, D, 32)
        x = x.permute(0, 2, 1)    # (B, 32, D) = (B, S, D)
        
        return x


class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for temporal sequence."""
    
    def __init__(self, d_model: int, max_len: int = 128, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # (1, max_len, d_model)
        self.register_buffer('pe', pe)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """x: (B, S, D)"""
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


class SeizureTransformerTeacher(nn.Module):
    """
    High-capacity Transformer teacher for EEG seizure prediction.
    
    Pipeline:
        Raw EEG → Patch Embedding → Positional Encoding → 
        Transformer Encoder → Temporal Aggregation → 
        Classification Head + Embedding Head (for KD)
    
    Typical param count: ~2-3M parameters.
    """
    
    def __init__(
        self,
        eeg_cfg: EEGConfig = None,
        teacher_cfg: TeacherConfig = None,
    ):
        super().__init__()
        if eeg_cfg is None:
            eeg_cfg = EEGConfig()
        if teacher_cfg is None:
            teacher_cfg = TeacherConfig()
            
        self.eeg_cfg = eeg_cfg
        self.cfg = teacher_cfg
        
        # 1. Patch embedding
        self.patch_embed = PatchEmbedding(eeg_cfg, teacher_cfg.d_model)
        
        # 2. Positional encoding
        self.pos_enc = PositionalEncoding(
            teacher_cfg.d_model, 
            max_len=128,
            dropout=teacher_cfg.dropout
        )
        
        # 3. Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=teacher_cfg.d_model,
            nhead=teacher_cfg.n_heads,
            dim_feedforward=teacher_cfg.d_ff,
            dropout=teacher_cfg.dropout,
            activation='gelu',
            batch_first=True,
            norm_first=True,  # Pre-norm for stability
        )
        self.transformer = nn.TransformerEncoder(
            encoder_layer,
            num_layers=teacher_cfg.n_transformer_layers,
            enable_nested_tensor=False,
        )
        
        # 4. Temporal aggregation (attention-weighted pooling)
        self.attn_pool = nn.Sequential(
            nn.Linear(teacher_cfg.d_model, 1),
            nn.Softmax(dim=1),
        )
        
        # 5. Embedding head (for KD feature distillation)
        self.embed_head = nn.Sequential(
            nn.Linear(teacher_cfg.d_model, teacher_cfg.embed_dim),
            nn.LayerNorm(teacher_cfg.embed_dim),
            nn.GELU(),
        )
        
        # 6. Classification head
        self.classifier = nn.Sequential(
            nn.Linear(teacher_cfg.embed_dim, teacher_cfg.embed_dim // 2),
            nn.GELU(),
            nn.Dropout(teacher_cfg.dropout),
            nn.Linear(teacher_cfg.embed_dim // 2, teacher_cfg.n_classes),
        )
        
        self._init_weights()
        
    def _init_weights(self):
        """Initialize weights with Xavier uniform."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.Conv1d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
        
    def forward(
        self, 
        x: torch.Tensor,
        return_embeddings: bool = True,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: (B, C, T) raw EEG — C=19 channels, T=1280 samples
            return_embeddings: if True, return intermediate embeddings for KD
            
        Returns:
            logits: (B, n_classes)
            embeddings: (B, embed_dim) — for knowledge distillation
        """
        # Patch embedding: (B, C, T) → (B, S, D)
        tokens = self.patch_embed(x)
        
        # Positional encoding
        tokens = self.pos_enc(tokens)
        
        # Transformer encoder: (B, S, D) → (B, S, D)
        encoded = self.transformer(tokens)
        
        # Attention-weighted temporal aggregation: (B, S, D) → (B, D)
        attn_weights = self.attn_pool(encoded)  # (B, S, 1)
        pooled = (encoded * attn_weights).sum(dim=1)  # (B, D)
        
        # Embedding (for KD)
        embeddings = self.embed_head(pooled)  # (B, embed_dim)
        
        # Classification
        logits = self.classifier(embeddings)  # (B, n_classes)
        
        if return_embeddings:
            return logits, embeddings
        return logits, None

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
