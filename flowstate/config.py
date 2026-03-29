"""FlowState configuration — all tunable constants in one place."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- Detection thresholds (tuned for fast demo) ---
STRESS_THRESHOLD: int = int(os.getenv("STRESS_THRESHOLD", "2"))       # consecutive stressed before handoff
STRESS_SCORE_CUTOFF: float = float(os.getenv("STRESS_SCORE_CUTOFF", "0.25"))
FATIGUE_SCORE_CUTOFF: float = float(os.getenv("FATIGUE_SCORE_CUTOFF", "0.10"))
RECOVERY_THRESHOLD: float = float(os.getenv("RECOVERY_THRESHOLD", "0.15"))

# --- Timing (fast capture — 1s per frame, 2 frames to analyse) ---
TICK_WEBCAM_SECONDS: int = int(os.getenv("TICK_WEBCAM_SECONDS", "1"))
TICK_SCREEN_SECONDS: int = int(os.getenv("TICK_SCREEN_SECONDS", "10"))
HANDOFF_TIMEOUT_SECONDS: int = int(os.getenv("HANDOFF_TIMEOUT_SECONDS", "60"))

# --- Buffer sizes ---
WEBCAM_BUFFER_SIZE: int = 2
SCREEN_BUFFER_SIZE: int = 10

# --- API keys ---
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
AUGMENT_API_KEY: str = os.getenv("AUGMENT_API_KEY", "")
UNKEY_ROOT_KEY: str = os.getenv("UNKEY_ROOT_KEY", "")
UNKEY_API_ID: str = os.getenv("UNKEY_API_ID", "")

# --- DigitalOcean ---
DO_GRADIENT_BASE_URL: str = os.getenv("DO_GRADIENT_BASE_URL", "https://inference.do-ai.run/v1")

# --- Server ---
API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
API_PORT: int = int(os.getenv("API_PORT", "8000"))

# --- Demo target ---
DEMO_GCP_PROJECT: str = os.getenv("DEMO_GCP_PROJECT", "")
DEMO_CLOUD_RUN_SERVICE: str = os.getenv("DEMO_CLOUD_RUN_SERVICE", "")
