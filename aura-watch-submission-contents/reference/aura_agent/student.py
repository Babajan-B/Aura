"""
Aura-Agent Student Model: RGF-Net (Ring-Buffer GRU with FiLM)
=============================================================
Lightweight edge-AI model for real-time seizure prediction on mobile devices.

Architecture:
  Input: (B, C=19, T=1280) raw EEG + (B, cond_dim) biometric features
  1. Temporal Conv1D → extract local temporal features per channel
  2. Spatial Conv1D → fuse cross-channel information
  3. Ring-Buffer GRU → sequential temporal modeling with O(1) memory
  4. FiLM Conditioning → biometric-adaptive feature modulation
  5. Classification head → pre-ictal probability
  
Constraints:
  - Total parameters < 100,000 (for 8-bit quantization on Android)
  - Supports ONNX export and INT8 quantization
  - Ring-buffer enables constant-memory streaming inference

FiLM Reference: arxiv 1709.07871
  FiLM(F | γ, β) = γ ⊙ F + β
  where γ, β = f(biometric_condition)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Tuple, Optional
from collections import deque

from .config import StudentConfig, EEGConfig


class FiLMLayer(nn.Module):
    """Feature-wise Linear Modulation (FiLM) layer.
    
    Generates per-feature scale (γ) and shift (β) from a conditioning
    vector, then applies element-wise affine transformation:
    
        output = (1 + γ) ⊙ input + β
    
    The (1 + γ) formulation ensures residual initialization:
    when γ=0, β=0, the layer is an identity transform.
    
    Reference: Perez et al., "FiLM: Visual Reasoning with a General 
    Conditioning Layer", AAAI 2018 (arxiv 1709.07871)
    """
    
    def __init__(self, cond_dim: int, feature_dim: int, hidden_dim: int = 16):
        super().__init__()
        self.film_generator = nn.Sequential(
            nn.Linear(cond_dim, hidden_dim),
            nn.ReLU(inplace=True),
            nn.Linear(hidden_dim, 2 * feature_dim),  # γ and β
        )
        # Initialize to identity: γ=0, β=0
        nn.init.zeros_(self.film_generator[-1].weight)
        nn.init.zeros_(self.film_generator[-1].bias)
        
    def forward(self, x: torch.Tensor, cond: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, D) feature tensor
            cond: (B, cond_dim) conditioning vector (biometric features)
        Returns:
            modulated: (B, D) FiLM-conditioned features
        """
        gamma_beta = self.film_generator(cond)  # (B, 2*D)
        gamma, beta = gamma_beta.chunk(2, dim=-1)  # each (B, D)
        return (1.0 + gamma) * x + beta  # Residual FiLM


class EEGFeatureExtractor(nn.Module):
    """Lightweight temporal+spatial feature extraction from raw EEG.
    
    Uses depthwise-separable convolution pattern (EEGNet-inspired):
    1. Temporal Conv: per-channel temporal feature extraction
    2. Spatial Conv: cross-channel fusion (depthwise)
    3. Pooling: reduce sequence length for GRU
    """
    
    def __init__(self, eeg_cfg: EEGConfig, student_cfg: StudentConfig):
        super().__init__()
        
        # Temporal convolution (shared across channels)
        # kernel=25 ≈ 100ms @ 256Hz
        self.temporal_conv = nn.Sequential(
            nn.Conv1d(
                in_channels=eeg_cfg.n_channels,
                out_channels=student_cfg.temporal_filters * eeg_cfg.n_channels,
                kernel_size=student_cfg.temporal_kernel,
                stride=1,
                padding=student_cfg.temporal_kernel // 2,
                groups=eeg_cfg.n_channels,  # Depthwise: per-channel
            ),
            nn.BatchNorm1d(student_cfg.temporal_filters * eeg_cfg.n_channels),
            nn.ELU(inplace=True),
        )
        
        # Spatial convolution (cross-channel fusion)
        self.spatial_conv = nn.Sequential(
            nn.Conv1d(
                in_channels=student_cfg.temporal_filters * eeg_cfg.n_channels,
                out_channels=student_cfg.spatial_filters,
                kernel_size=1,  # Pointwise: channel mixing only
            ),
            nn.BatchNorm1d(student_cfg.spatial_filters),
            nn.ELU(inplace=True),
        )
        
        # Average pooling to reduce temporal dimension
        self.pool = nn.AvgPool1d(
            kernel_size=student_cfg.pool_kernel,
            stride=student_cfg.pool_kernel,
        )
        
        self.dropout = nn.Dropout(student_cfg.dropout)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, C=19, T=1280) raw EEG
        Returns:
            features: (B, T', spatial_filters) — reduced temporal sequence
        """
        x = self.temporal_conv(x)   # (B, temp_filters*C, T)
        x = self.spatial_conv(x)    # (B, spatial_filters, T)
        x = self.pool(x)            # (B, spatial_filters, T//pool_kernel)
        x = self.dropout(x)
        x = x.permute(0, 2, 1)     # (B, T', spatial_filters) for GRU
        return x


class RingBufferGRU(nn.Module):
    """GRU with ring-buffer support for constant-memory streaming.
    
    In training mode: processes the full sequence normally.
    In streaming mode: maintains a ring buffer of hidden states
    and processes one window at a time with O(1) memory.
    """
    
    def __init__(self, input_dim: int, hidden_dim: int, n_layers: int, 
                 dropout: float = 0.1, buffer_size: int = 60):
        super().__init__()
        self.hidden_dim = hidden_dim
        self.n_layers = n_layers
        self.buffer_size = buffer_size
        
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=n_layers,
            batch_first=True,
            dropout=dropout if n_layers > 1 else 0.0,
        )
        
        # Ring buffer for streaming inference (not used in training)
        self._hidden_buffer = None
        self._output_ring = None
        self._ring_idx = 0
        
    def reset_buffer(self, batch_size: int = 1, device: torch.device = None):
        """Initialize ring buffer for streaming inference."""
        if device is None:
            device = next(self.parameters()).device
        self._hidden_buffer = torch.zeros(
            self.n_layers, batch_size, self.hidden_dim, device=device
        )
        self._output_ring = deque(maxlen=self.buffer_size)
        self._ring_idx = 0
        
    def forward_stream(self, x: torch.Tensor) -> torch.Tensor:
        """Process a single time step in streaming mode.
        
        Args:
            x: (B, 1, input_dim) single-step input
        Returns:
            h: (B, hidden_dim) updated hidden state
        """
        output, self._hidden_buffer = self.gru(x, self._hidden_buffer)
        h = output[:, -1, :]  # (B, hidden_dim)
        self._output_ring.append(h.detach())
        self._ring_idx += 1
        return h
        
    def forward(self, x: torch.Tensor, h0: torch.Tensor = None) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: (B, T', input_dim) feature sequence
            h0: optional initial hidden state
        Returns:
            output: (B, T', hidden_dim) all hidden states
            h_last: (B, hidden_dim) final hidden state
        """
        output, hn = self.gru(x, h0)  # output: (B, T', H), hn: (n_layers, B, H)
        h_last = output[:, -1, :]      # (B, H) — final time step
        return output, h_last


class RGFNet(nn.Module):
    """Ring-Buffer GRU with FiLM — Lightweight Seizure Prediction Network.
    
    Complete pipeline:
        EEG (B, 19, 1280) + Biometrics (B, 6)
            → EEGFeatureExtractor → (B, T', 8)
            → RingBufferGRU → (B, hidden_dim)
            → FiLM conditioning with biometrics
            → Classifier → (B, 2) logits
    
    Target: <100K parameters for 8-bit Android deployment.
    
    Biometric conditioning vector (cond_dim=6):
        [age_normalized, sex, resting_hr, hrv_sdnn, 
         hours_since_last_seizure, medication_adherence]
    """
    
    def __init__(
        self,
        eeg_cfg: EEGConfig = None,
        student_cfg: StudentConfig = None,
    ):
        super().__init__()
        if eeg_cfg is None:
            eeg_cfg = EEGConfig()
        if student_cfg is None:
            student_cfg = StudentConfig()
            
        self.eeg_cfg = eeg_cfg
        self.cfg = student_cfg
        
        # 1. Feature extraction
        self.feature_extractor = EEGFeatureExtractor(eeg_cfg, student_cfg)
        
        # 2. Ring-Buffer GRU
        self.gru = RingBufferGRU(
            input_dim=student_cfg.spatial_filters,
            hidden_dim=student_cfg.gru_hidden,
            n_layers=student_cfg.gru_layers,
            dropout=student_cfg.gru_dropout,
            buffer_size=student_cfg.ring_buffer_size,
        )
        
        # 3. FiLM conditioning layer
        self.film = FiLMLayer(
            cond_dim=student_cfg.cond_dim,
            feature_dim=student_cfg.gru_hidden,
            hidden_dim=student_cfg.film_hidden,
        )
        
        # 4. KD projection head (aligns student hidden → teacher embed space)
        self.kd_projector = nn.Sequential(
            nn.Linear(student_cfg.gru_hidden, student_cfg.teacher_embed_dim),
            nn.LayerNorm(student_cfg.teacher_embed_dim),
        )
        
        # 5. Classification head
        self.classifier = nn.Sequential(
            nn.LayerNorm(student_cfg.gru_hidden),
            nn.Linear(student_cfg.gru_hidden, student_cfg.gru_hidden // 2),
            nn.ELU(inplace=True),
            nn.Dropout(student_cfg.dropout),
            nn.Linear(student_cfg.gru_hidden // 2, student_cfg.n_classes),
        )
        
        self._init_weights()
        self._validate_param_count()
        
    def _init_weights(self):
        """Initialize weights — Kaiming for convs, Xavier for linears."""
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    nn.init.zeros_(m.bias)
            elif isinstance(m, nn.GRU):
                for name, param in m.named_parameters():
                    if 'weight' in name:
                        nn.init.orthogonal_(param)
                    elif 'bias' in name:
                        nn.init.zeros_(param)
        # FiLM generator already initialized to identity in FiLMLayer.__init__
        
    def _validate_param_count(self):
        """Ensure model stays under param budget."""
        n_params = self.count_parameters()
        max_params = self.cfg.max_params
        if n_params > max_params:
            raise ValueError(
                f"RGF-Net has {n_params:,} params, exceeding budget of "
                f"{max_params:,}. Reduce gru_hidden or spatial_filters."
            )
            
    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
    
    def param_breakdown(self) -> dict:
        """Detailed parameter count per module."""
        breakdown = {}
        for name, module in self.named_children():
            count = sum(p.numel() for p in module.parameters() if p.requires_grad)
            breakdown[name] = count
        breakdown['total'] = sum(breakdown.values())
        return breakdown
        
    def forward(
        self,
        x: torch.Tensor,
        cond: torch.Tensor,
        return_embeddings: bool = True,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.
        
        Args:
            x: (B, C=19, T=1280) raw EEG segment
            cond: (B, cond_dim=6) biometric conditioning vector
                  [age_norm, sex, resting_hr, hrv_sdnn, 
                   hours_since_last_seizure, medication_adherence]
            return_embeddings: if True, return KD-projected embeddings
            
        Returns:
            logits: (B, n_classes=2) — [inter-ictal, pre-ictal]
            embeddings: (B, teacher_embed_dim) — projected for KD alignment
        """
        # Feature extraction: (B, 19, 1280) → (B, T', 8)
        features = self.feature_extractor(x)
        
        # GRU: (B, T', 8) → (B, gru_hidden)
        _, h_last = self.gru(features)
        
        # FiLM conditioning: (B, gru_hidden) → (B, gru_hidden)
        h_conditioned = self.film(h_last, cond)
        
        # Classification: (B, gru_hidden) → (B, n_classes)
        logits = self.classifier(h_conditioned)
        
        # KD projection: (B, gru_hidden) → (B, teacher_embed_dim)
        embeddings = None
        if return_embeddings:
            embeddings = self.kd_projector(h_conditioned)
        
        return logits, embeddings
    
    def forward_stream(
        self,
        x: torch.Tensor,
        cond: torch.Tensor,
    ) -> torch.Tensor:
        """Single-window streaming inference with ring buffer.
        
        Args:
            x: (1, C=19, T=1280) single EEG window
            cond: (1, cond_dim) biometric features
        Returns:
            risk_score: scalar float — P(pre-ictal)
        """
        features = self.feature_extractor(x)  # (1, T', 8)
        
        # Process each time step through streaming GRU
        for t in range(features.shape[1]):
            step = features[:, t:t+1, :]  # (1, 1, 8)
            h = self.gru.forward_stream(step)
        
        # FiLM + classify on final hidden
        h_conditioned = self.film(h, cond)
        logits = self.classifier(h_conditioned)
        risk_score = F.softmax(logits, dim=-1)[:, 1]  # P(pre-ictal)
        
        return risk_score.item()
    
    def export_onnx(self, filepath: str, device: str = 'cpu'):
        """Export to ONNX for Android deployment.
        
        Args:
            filepath: output .onnx path
            device: 'cpu' or 'cuda'
        """
        self.eval()
        dummy_eeg = torch.randn(1, self.eeg_cfg.n_channels, 
                                self.eeg_cfg.window_samples, device=device)
        dummy_cond = torch.randn(1, self.cfg.cond_dim, device=device)
        
        torch.onnx.export(
            self,
            (dummy_eeg, dummy_cond),
            filepath,
            input_names=['eeg_input', 'biometric_cond'],
            output_names=['logits', 'embeddings'],
            dynamic_axes={
                'eeg_input': {0: 'batch_size'},
                'biometric_cond': {0: 'batch_size'},
                'logits': {0: 'batch_size'},
                'embeddings': {0: 'batch_size'},
            },
            opset_version=13,
        )
        print(f"[RGF-Net] Exported to {filepath}")
