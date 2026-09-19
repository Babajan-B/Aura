"""
Aura-Agent Configuration
========================
Central configuration for the seizure prediction pipeline.
Based on literature consensus from:
  - STAN (arxiv 2511.01275): Spatio-Temporal Attention Networks
  - Spiking Conformer (arxiv 2402.09424)
  - Edge LSTM/CNN (arxiv 2012.00307)
  - FiLM (arxiv 1709.07871)
  - Hinton KD (arxiv 1503.02531)
"""
from dataclasses import dataclass, field
from typing import Tuple


@dataclass
class EEGConfig:
    """EEG signal configuration — 10-20 international system."""
    sample_rate: int = 256                    # Hz (CHB-MIT standard)
    n_channels: int = 19                      # 10-20 system (exclude P7-T7, T8-P8)
    window_sec: float = 5.0                   # seconds per segment
    window_samples: int = 1280                # sample_rate * window_sec
    preictal_minutes: int = 30                # 30-min pre-ictal warning target
    interictal_gap_minutes: int = 240         # ≥4h from any seizure
    overlap_ratio: float = 0.5               # 50% overlap for augmentation
    
    # Channel names (standard 10-20, 19 channels)
    channel_names: Tuple[str, ...] = (
        'FP1-F7', 'F7-T7', 'T7-P7', 'P7-O1',
        'FP1-F3', 'F3-C3', 'C3-P3', 'P3-O1',
        'FP2-F4', 'F4-C4', 'C4-P4', 'P4-O2',
        'FP2-F8', 'F8-T8', 'T8-P8', 'P8-O2',
        'FZ-CZ', 'CZ-PZ', 'P7-T7',
    )
    
    # Frequency bands for spectral features
    freq_bands: dict = field(default_factory=lambda: {
        'delta': (1, 4),
        'theta': (4, 8),
        'alpha': (8, 12),
        'beta': (12, 30),
        'gamma': (30, 100),
    })


@dataclass
class TeacherConfig:
    """Teacher model (Transformer) configuration — STAN-inspired."""
    n_attention_blocks: int = 3               # Cascaded attention blocks (M=3)
    spatial_dim: int = 64                     # Spatial attention hidden dim
    temporal_dim: int = 128                   # Temporal attention hidden dim
    n_heads: int = 4                          # Multi-head attention heads
    d_model: int = 128                        # Transformer embed dimension
    n_transformer_layers: int = 4             # Transformer encoder layers
    d_ff: int = 256                           # Feed-forward dimension
    dropout: float = 0.2                      # Dropout rate
    n_classes: int = 2                        # pre-ictal vs inter-ictal
    embed_dim: int = 128                      # Feature embedding for KD


@dataclass
class StudentConfig:
    """Student model (RGF-Net) configuration — must be <100K params."""
    # Input processing
    temporal_kernel: int = 25                 # Temporal conv kernel (≈100ms @ 256Hz)
    temporal_filters: int = 8                 # Temporal conv output channels
    spatial_filters: int = 8                  # Spatial conv output channels
    pool_kernel: int = 8                      # Pooling to reduce sequence length
    
    # Ring-Buffer GRU
    gru_hidden: int = 48                      # GRU hidden size (kept small)
    gru_layers: int = 2                       # Stacked GRU layers
    gru_dropout: float = 0.1                  # Inter-layer dropout
    
    # FiLM conditioning
    cond_dim: int = 6                         # Biometric features dimension
    film_hidden: int = 16                     # FiLM generator hidden dim
    
    # Output
    n_classes: int = 2
    dropout: float = 0.2
    
    # KD
    teacher_embed_dim: int = 128              # Must match TeacherConfig.embed_dim
    
    # Ring buffer
    ring_buffer_size: int = 60                # Number of windows in ring buffer
    
    # Target param budget
    max_params: int = 100_000


@dataclass
class KDConfig:
    """Knowledge Distillation training configuration."""
    # KD hyperparameters (Hinton 1503.02531)
    temperature: float = 4.0                  # Softmax temperature for soft labels
    alpha: float = 0.7                        # Weight for soft-label loss
    lambda_feat: float = 0.3                  # Weight for feature distillation loss
    
    # Training
    teacher_lr: float = 1e-3                  # Teacher learning rate (Adam)
    student_lr: float = 3e-4                  # Student learning rate (Adam)
    teacher_epochs: int = 100                 # Teacher training epochs
    student_epochs: int = 100                 # Student distillation epochs
    batch_size: int = 64                      # Batch size
    weight_decay: float = 1e-4               # AdamW weight decay
    
    # Scheduler
    warmup_steps: int = 500
    
    # Class imbalance
    pos_weight: float = 3.0                   # Positive (pre-ictal) class weight
    
    # Inference
    moving_avg_window: int = 6                # 30-second moving avg (6 × 5s windows)
    risk_threshold: float = 0.75              # Emergency response threshold


@dataclass
class AgentConfig:
    """smolagents CodeAgent configuration."""
    model_id: str = "meta-llama/Llama-3.3-70B-Instruct"
    max_steps: int = 8
    temperature: float = 0.1                  # Low temp for medical decisions
    risk_threshold: float = 0.75              # Same as KDConfig
