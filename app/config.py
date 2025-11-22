import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Qdrant settings
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "YOUR_QDRANT_API_KEY")  # For cloud Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", "YOUR_QDRANT_URL")  # For cloud Qdrant (alternative to host/port)
COLLECTION_NAME = "value_waterfall_analyses"
GLOBAL_SETTINGS_COLLECTION = "global_settings"

# Vector settings
VECTOR_DIM = 4096  # Migrated from 1536 to use full Ollama Mistral embeddings
INDEX_PARAMS = {
    "distance": "Cosine"
}

# AI settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
if not OLLAMA_BASE_URL:
    raise RuntimeError("OLLAMA_BASE_URL environment variable is not set. Please set it to the correct Ollama address.")

MODEL = "mistral"
AI_TIMEOUT = 30  # seconds
AI_MAX_RETRIES = 3

# OpenAI/ChatGPT settings
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_TIMEOUT = 60  # seconds
OPENAI_MAX_RETRIES = 3

# Enhanced persona generation settings
ENABLE_DUAL_MODEL_PERSONA = os.getenv("ENABLE_DUAL_MODEL_PERSONA", "true").lower() == "true"
ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"

# Demo mode settings
# Option 1: Set via environment variable (ENABLE_DEMO_MODE=true)
# Option 2: Set directly in this file by changing the value below
DEMO_MODE_ENABLED = True  # Change to True to enable demo mode

ENABLE_DEMO_MODE = os.getenv("ENABLE_DEMO_MODE", "false").lower() == "true" or DEMO_MODE_ENABLED

# Company website settings
COMPANY_WEBSITE_URL = os.getenv("COMPANY_WEBSITE_URL", "")
ENABLE_COMPANY_WEBSITE_SCRAPING = os.getenv("ENABLE_COMPANY_WEBSITE_SCRAPING", "true").lower() == "true"

# --- DETERMINISTIC AI CONFIGURATION ---
# These parameters ensure consistent, reproducible results across all AI calls
AI_TEMPERATURE = 0.0  # Set to 0.0 for most deterministic output
AI_SEED = 42  # Fixed seed for reproducible randomness
AI_TOP_P = 1.0  # Use all tokens (most deterministic)
AI_TOP_K = 1  # Use only the most likely token
AI_MAX_TOKENS = 6000  # Recommended balance of quality and cost

# --- SONAR INTEGRATION CONFIGURATION ---
# Sonar API configuration for customer focus validation
SONAR_API_KEY = os.environ.get("SONAR_API_KEY")  # Set SONAR_API_KEY environment variable
SONAR_MODEL = "sonar-pro"  # Correct Perplexity Sonar model
SONAR_TEMPERATURE = 0.0  # Deterministic output
SONAR_MAX_TOKENS = 4000  # Token limit for Sonar
SONAR_SEED = 42  # Fixed seed for reproducibility

# Sonar feature flags
ENABLE_SONAR_VALIDATION = True
ENABLE_COMPANY_PROFILE_VALIDATION = True
ENABLE_CUSTOMER_FOCUS_QUALITY_GATES = True

# Model-specific deterministic settings
GEMINI_TEMPERATURE = AI_TEMPERATURE
GEMINI_SEED = AI_SEED
GEMINI_TOP_P = AI_TOP_P
GEMINI_TOP_K = AI_TOP_K
GEMINI_MAX_TOKENS = 8000  # Use Gemini's full capacity for maximum quality

CHATGPT_TEMPERATURE = AI_TEMPERATURE
CHATGPT_SEED = AI_SEED
CHATGPT_TOP_P = AI_TOP_P
# Note: ChatGPT doesn't support top_k parameter
CHATGPT_MAX_TOKENS = 4000  # ChatGPT's maximum limit

# Cache settings
CACHE_TTL = 3600  # 1 hour
MAX_CACHE_SIZE = 1000

# Data validation
MAX_URL_LENGTH = 500
MAX_ANALYSIS_SIZE = 1024 * 1024  # 1MB
MAX_VALUE_BRICKS = 100

# Retry settings
RETRY_DELAY = 1  # seconds
MAX_RETRIES = 3

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Debug settings
# Set these to "true" to enable debug output for different components
# DEBUG_MODE: Master switch for all debug output
# DEBUG_WIDGET_KEYS: Show widget key generation and collision detection
# DEBUG_AI_PROCESSING: Show AI processing steps and results
# DEBUG_DATABASE_OPERATIONS: Show database save/delete operations
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "false"

DEBUG_WIDGET_KEYS = os.getenv("DEBUG_WIDGET_KEYS", "false").lower() == "true"
DEBUG_AI_PROCESSING = os.getenv("DEBUG_AI_PROCESSING", "false").lower() == "true"
DEBUG_DATABASE_OPERATIONS = os.getenv("DEBUG_DATABASE_OPERATIONS", "false").lower() == "true"

# Version settings
APP_VERSION = "1.0.0"
ANALYSIS_VERSION = "1.0.0" 