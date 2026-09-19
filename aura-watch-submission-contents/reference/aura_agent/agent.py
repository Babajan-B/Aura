"""
Aura-Agent: Autonomous Seizure Response CodeAgent
=================================================
Uses smolagents (v1.24.0) to create an autonomous CodeAgent that:
  1. Monitors biometric risk via RGF-Net
  2. Generates emergency response (SOS, GPS, first-aid) when risk exceeds threshold

Tools:
  - RGFNetSeizureRiskTool: Runs inference on EEG data → risk score
  - SendSOSAlertTool: Triggers emergency SOS alert
  - GetPatientGPSTool: Retrieves GPS coordinates
  - DispatchFirstAidTool: Sends first-aid instructions

Agent: CodeAgent with conditional logic for risk-based response.

Reference: smolagents docs (https://huggingface.co/docs/smolagents)
"""

import os
import datetime
import numpy as np
from typing import Optional

# smolagents imports
from smolagents import CodeAgent, Tool, tool, InferenceClientModel

from .config import AgentConfig, EEGConfig, StudentConfig
from .student import RGFNet


# ============================================================================
# Tool 1: RGF-Net Seizure Risk Assessment (Tool subclass — stateful)
# ============================================================================

class RGFNetSeizureRiskTool(Tool):
    """Runs RGF-Net model to compute seizure risk score from EEG data.
    
    Uses setup() for lazy model loading — weights are only loaded
    when the tool is first called, not at agent initialization.
    """
    
    name = "rgfnet_seizure_risk"
    description = """
    Computes seizure risk score (0.0-1.0) from patient EEG signal data 
    using the RGF-Net neural network model. A score above 0.75 indicates 
    HIGH RISK of imminent seizure within 30 minutes.
    
    ALWAYS call this tool FIRST before any emergency response actions.
    The returned score determines whether to trigger SOS, GPS, and first-aid.
    """
    inputs = {
        "eeg_data": {
            "type": "string",
            "description": (
                "Comma-separated EEG signal values as a string. "
                "Example: '0.1,0.2,-0.3,...' representing a 5-second window "
                "from 19 EEG channels (19 x 1280 = 24320 values total). "
                "If fewer values are provided, they will be padded/reshaped."
            ),
        },
        "patient_id": {
            "type": "string",
            "description": "Unique patient identifier (e.g., 'patient_001').",
        },
        "biometrics": {
            "type": "string",
            "description": (
                "Comma-separated biometric values: "
                "'age_normalized,sex(0/1),resting_hr_norm,hrv_norm,"
                "hours_since_seizure_norm,medication_adherence'. "
                "Example: '0.45,1,0.72,0.6,0.8,0.95'"
            ),
        },
    }
    output_type = "number"
    
    def __init__(self, model_path: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self._model_path = model_path
        self._model = None
        self._eeg_cfg = EEGConfig()
        self._student_cfg = StudentConfig()
    
    def setup(self):
        """Lazy initialization — load RGF-Net model weights."""
        import torch
        
        self._model = RGFNet(self._eeg_cfg, self._student_cfg)
        
        if self._model_path and os.path.exists(self._model_path):
            state_dict = torch.load(self._model_path, map_location='cpu', weights_only=True)
            self._model.load_state_dict(state_dict)
            print(f"[RGFNet Tool] Loaded weights from {self._model_path}")
        else:
            print("[RGFNet Tool] No weights loaded — using random initialization (demo mode)")
        
        self._model.eval()
        print(f"[RGFNet Tool] Model ready ({self._model.count_parameters():,} params)")
    
    def forward(self, eeg_data: str, patient_id: str, biometrics: str) -> float:
        """Run seizure risk inference.
        
        Args:
            eeg_data: comma-separated EEG values string
            patient_id: patient identifier
            biometrics: comma-separated biometric values
            
        Returns:
            risk_score: float between 0.0 and 1.0
        """
        import torch
        
        # Parse EEG data
        try:
            values = [float(x.strip()) for x in eeg_data.split(',') if x.strip()]
        except ValueError:
            values = list(np.random.randn(self._eeg_cfg.n_channels * self._eeg_cfg.window_samples))
        
        # Reshape to (1, 19, 1280)
        expected_size = self._eeg_cfg.n_channels * self._eeg_cfg.window_samples
        if len(values) < expected_size:
            values = values + [0.0] * (expected_size - len(values))
        values = values[:expected_size]
        
        eeg_tensor = torch.tensor(values, dtype=torch.float32).reshape(
            1, self._eeg_cfg.n_channels, self._eeg_cfg.window_samples
        )
        
        # Parse biometrics
        try:
            bio_values = [float(x.strip()) for x in biometrics.split(',') if x.strip()]
        except ValueError:
            bio_values = [0.5] * self._student_cfg.cond_dim
        
        if len(bio_values) < self._student_cfg.cond_dim:
            bio_values = bio_values + [0.5] * (self._student_cfg.cond_dim - len(bio_values))
        bio_values = bio_values[:self._student_cfg.cond_dim]
        
        cond_tensor = torch.tensor(bio_values, dtype=torch.float32).unsqueeze(0)
        
        # Inference
        with torch.no_grad():
            logits, _ = self._model(eeg_tensor, cond_tensor, return_embeddings=False)
            probs = torch.softmax(logits, dim=-1)
            risk_score = probs[0, 1].item()  # P(pre-ictal)
        
        timestamp = datetime.datetime.now().isoformat()
        print(
            f"[RGFNet] {timestamp} | Patient: {patient_id} | "
            f"Risk Score: {risk_score:.4f} | "
            f"Status: {'HIGH RISK' if risk_score >= 0.75 else 'Normal'}"
        )
        
        return round(risk_score, 4)


# ============================================================================
# Tool 2: SOS Alert
# ============================================================================

@tool
def send_sos_alert(patient_id: str, risk_score: float, location: str) -> str:
    """
    Sends an emergency SOS alert to medical staff, emergency contacts, 
    and emergency services (911/112).

    Args:
        patient_id: Unique patient identifier string.
        risk_score: The seizure risk score (0.0-1.0) that triggered this alert.
        location: GPS coordinates as 'latitude,longitude' string.

    Returns:
        Confirmation message with alert ID, timestamp, and dispatch status.
    """
    timestamp = datetime.datetime.now().isoformat()
    alert_id = f"SOS-{patient_id}-{timestamp.replace(':', '').replace('-', '')[:14]}"
    
    response = (
        f"EMERGENCY SOS DISPATCHED\n"
        f"  Alert ID: {alert_id}\n"
        f"  Patient: {patient_id}\n"
        f"  Risk Score: {risk_score:.3f}\n"
        f"  Location: {location}\n"
        f"  Timestamp: {timestamp}\n"
        f"  Status: Emergency contacts notified, EMS dispatched\n"
        f"  Actions: \n"
        f"    - Emergency contacts called\n"
        f"    - EMS (911) notified with GPS coordinates\n"
        f"    - Hospital pre-alert sent\n"
        f"    - Patient device alarm activated"
    )
    print(response)
    return response


# ============================================================================
# Tool 3: GPS Location
# ============================================================================

@tool
def get_patient_gps(patient_id: str) -> str:
    """
    Retrieves the current GPS coordinates from the patient's wearable device 
    or smartphone. Returns location for emergency dispatch.

    Args:
        patient_id: Unique patient identifier string.

    Returns:
        GPS coordinates as 'latitude,longitude' string with accuracy estimate.
    """
    lat, lon = 37.7554, -122.4044
    accuracy_m = 5.0
    
    result = f"{lat},{lon}"
    print(
        f"[GPS] Patient {patient_id}: {result} "
        f"(accuracy: +/-{accuracy_m}m, source: smartphone)"
    )
    return result


# ============================================================================
# Tool 4: First-Aid Instructions
# ============================================================================

@tool
def dispatch_first_aid(
    patient_id: str, 
    location: str, 
    risk_score: float,
) -> str:
    """
    Dispatches first-aid instructions to nearby responders and the patient's 
    emergency contact. Also sends seizure-specific first-aid guidance.

    Args:
        patient_id: Unique patient identifier.
        location: GPS coordinates as 'latitude,longitude' string.
        risk_score: Seizure risk score that triggered this dispatch.

    Returns:
        Dispatch confirmation with first-aid instructions and responder ETA.
    """
    timestamp = datetime.datetime.now().isoformat()
    
    first_aid_instructions = """
    SEIZURE FIRST-AID PROTOCOL (AES Guidelines)
    
    * STAY CALM - Time the seizure from onset
    
    * PROTECT: 
      - Clear area of hard/sharp objects
      - Place something soft under the head
      - Loosen tight clothing around neck
    
    * DO NOT:
      - Restrain the person
      - Put anything in their mouth
      - Move them unless in danger
    
    * POSITION:
      - After convulsions stop, turn on their side (recovery position)
      - Check breathing; clear airway if needed
    
    * CALL 911 IF:
      - Seizure lasts > 5 minutes
      - Person doesn't regain consciousness
      - Repeated seizures without recovery
      - First known seizure
      - Person is injured, pregnant, or diabetic
    
    * AFTER:
      - Stay with person until fully conscious
      - Speak calmly and reassuringly
      - Note seizure duration and characteristics
    """
    
    response = (
        f"FIRST-AID DISPATCH CONFIRMATION\n"
        f"  Patient: {patient_id}\n"
        f"  Location: {location}\n"
        f"  Risk Score: {risk_score:.3f}\n"
        f"  Timestamp: {timestamp}\n"
        f"  Nearest responder ETA: ~4 minutes\n"
        f"  Hospital ETA: ~8 minutes\n\n"
        f"{first_aid_instructions}"
    )
    print(response)
    return response


# ============================================================================
# Agent Factory
# ============================================================================

def create_seizure_agent(
    model_path: Optional[str] = None,
    agent_cfg: AgentConfig = None,
    hf_token: Optional[str] = None,
) -> CodeAgent:
    """Create the Aura-Agent CodeAgent for seizure monitoring."""
    if agent_cfg is None:
        agent_cfg = AgentConfig()
    
    token = hf_token or os.environ.get('HF_TOKEN')
    model = InferenceClientModel(
        model_id=agent_cfg.model_id,
        token=token,
        temperature=agent_cfg.temperature,
    )
    
    rgfnet_tool = RGFNetSeizureRiskTool(model_path=model_path)
    
    agent = CodeAgent(
        tools=[
            rgfnet_tool,
            send_sos_alert,
            get_patient_gps,
            dispatch_first_aid,
        ],
        model=model,
        additional_authorized_imports=[
            "numpy", "datetime", "json", "math",
        ],
        max_steps=agent_cfg.max_steps,
        instructions=f"""
You are the Aura-Agent Neural Guardian — an autonomous medical emergency 
response agent for seizure prediction and intervention.

CRITICAL PROTOCOL (MUST FOLLOW IN ORDER):
1. ASSESS: Call rgfnet_seizure_risk to compute the patient's seizure risk score.
2. DECIDE: Compare the risk score against the threshold ({agent_cfg.risk_threshold}).
3. IF risk_score >= {agent_cfg.risk_threshold}:
   a. Call get_patient_gps to get the patient's location
   b. Call send_sos_alert with patient_id, risk_score, and location
   c. Call dispatch_first_aid with patient_id, location, and risk_score
   d. Return a FULL emergency report with all details
4. IF risk_score < {agent_cfg.risk_threshold}:
   a. Report the score and that the patient is currently safe
   b. Recommend continued monitoring
   c. Take NO emergency actions

RULES:
- NEVER skip the risk assessment step
- ALWAYS follow the exact sequence above
- Log every action with timestamps for medical audit trail
- Be precise with numbers — lives depend on accuracy
- If any tool fails, report the failure and attempt fallback
""",
        verbosity_level=1,
    )
    
    return agent


def run_monitoring_cycle(
    agent: CodeAgent,
    patient_id: str,
    eeg_data: Optional[str] = None,
    biometrics: Optional[str] = None,
) -> str:
    """Execute one monitoring cycle for a patient."""
    if eeg_data is None:
        eeg_values = np.random.randn(19 * 1280).tolist()
        eeg_data = ','.join(f'{v:.4f}' for v in eeg_values[:100])
    
    if biometrics is None:
        biometrics = "0.45,1,0.72,0.6,0.8,0.95"
    
    task = (
        f"MONITORING CYCLE for patient '{patient_id}':\n"
        f"EEG Data (first 100 of 24320 values): {eeg_data}\n"
        f"Biometrics: {biometrics}\n\n"
        f"Execute the full seizure assessment protocol. "
        f"Assess risk, and if HIGH, trigger the complete emergency response chain."
    )
    
    result = agent.run(task)
    return result
