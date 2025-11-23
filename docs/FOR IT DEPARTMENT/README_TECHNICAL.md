# Value Rollercoaster: Technical Documentation

<div align="center">

# 🛠️ IT Implementation Guide

**Complete technical documentation for system administrators, developers, and IT teams**

</div>

---

## 📋 Table of Contents

- [System Architecture](#system-architecture)
- [Technology Stack](#technology-stack)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Deployment Options](#deployment-options)
- [API Integration](#api-integration)
- [Development Guide](#development-guide)
- [Security Considerations](#security-considerations)
- [Performance Optimization](#performance-optimization)
- [Troubleshooting](#troubleshooting)
- [Maintenance & Updates](#maintenance--updates)

---

## 🏗️ System Architecture

### Core Transformation Process

**The heart of Value Rollercoaster** is the transformation of individual employee inputs into customer-focused benefits:

```
Individual Employee Input (Value Components)
    ↓
Company Context (from Admin Settings)
    ↓
AI Transformation (Gemini + ChatGPT + Sonar)
    ├── Context Gathering (Business Intelligence, Value Delivery, Capabilities)
    ├── Field-Specific Processing (Technical/Business/Strategic/After Sales)
    └── Customer Benefit Generation
    ↓
Customer-Focused Benefits (Visible to All Employees)
    ↓
Practical Applications (Persona Generation, Prospect Alignment)
```

**Key Technical Components:**
- **Value Components System**: Captures diverse employee perspectives
- **AI Processing Pipeline**: Transforms inputs using company context
- **Customer Benefit Generation**: Converts technical/internal language to customer value
- **Value Alignment Workflow**: Matches transformed values with prospect needs

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                       │
│  (UI Components, User Interface, Authentication)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│              Application Layer                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Company    │  │    Value     │  │   Persona    │       │
│  │   Context    │  │ Components   │  │  Generator   │       │
│  │   Manager    │  │   System     │  │   (Dual AI)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    AI Services Layer                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Gemini     │  │   ChatGPT    │  │   Market     │       │
│  │   Client     │  │   Client     │  │ Intelligence │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    Data Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Qdrant     │  │   Eurostat   │  │   Web        │       │
│  │  Database    │  │     API      │  │   Search     │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### Core Components

1. **Company Context Manager** (`app/core/company_context_manager.py`)
   - Manages company profile loading and access
   - Provides company-specific context to all AI operations
   - Handles profile validation and caching

2. **Value Components System** (`app/components/value_components/`)
   - Structured framework for value propositions
   - 4 main categories with subcategories
   - **Core Function**: Captures individual employee perspectives and transforms them into customer-focused benefits
   - AI-powered customer benefit generation using company context
   - Database persistence and synchronization

3. **Persona Generator** (`app/ai/personas.py`, `app/ai/enhanced_persona_generator.py`)
   - Dual-model AI analysis (Gemini + ChatGPT)
   - 7-step enhanced generation process
   - Value alignment workflow integration

4. **Value Alignment Workflow** (`app/ai/workflow_orchestrator.py`)
   - 3-step matching process (Profiler → Hypothesizer → Final Aligner)
   - Evidence-based alignment matrix generation

5. **Market Intelligence Service** (`app/ai/market_intelligence/`)
   - Dynamic industry framework generation
   - NACE system integration
   - Eurostat API integration

6. **Sonar Validation System** (`app/ai/sonar/`)
   - Quality gates at every step
   - Relevance validation (pre-analysis)
   - Customer focus validation
   - Accuracy verification
   - Perplexity Sonar API integration

7. **Authentication System** (`app/auth/`)
   - User management and session handling
   - Data isolation per user
   - Secure authentication flow

### Data Flow

#### Core Value Transformation Flow

```
Individual Employee Input (Value Component)
    ↓
Company Context Manager (Business Intelligence, Value Delivery, Capabilities)
    ↓
AI Processing Pipeline (app/utils/enhanced_ai_processor.py)
    ├── Context Selection (Field-specific: Technical/Business/Strategic/After Sales)
    ├── Customer Benefit Generation (Gemini with low temperature)
    └── Quality Validation (Similarity check, banned phrase detection)
    ↓
Customer-Focused Benefit (Stored in Database)
    ↓
Visible to All Employees (Everyone sees their value contribution)
```

#### Persona Generation Flow (Application of Transformed Values)

```
User Input (Website URL)
    ↓
Company Profile (from Company Context Manager)
    ↓
Transformed Value Components (Customer-Focused Benefits from Database)
    ↓
Dual AI Analysis (Gemini + ChatGPT)
    ├── Website Content Extraction
    ├── Business Analysis
    └── Market Intelligence (Eurostat + Web Search)
    ↓
Value Alignment Workflow
    ├── Profiler Agent (identify prospect needs)
    ├── Hypothesizer Agent (match needs with transformed values)
    └── Final Aligner (create alignment matrix with evidence)
    ↓
Buyer Persona + Alignment Matrix
    ↓
Storage (Qdrant Database)
```

---

## 💻 Technology Stack

### Core Technologies

- **Python**: 3.8+
- **Streamlit**: 1.47+ (Web framework)
- **Qdrant**: Vector database (cloud or local)
- **Google Gemini API**: Primary AI model
- **OpenAI ChatGPT API**: Secondary AI model
- **Ollama**: Local embedding generation (optional)

### Key Dependencies

```python
# Core Framework
streamlit>=1.47.0
plotly>=5.19.0
qdrant-client>=1.7.0

# AI Services
google-generativeai>=0.8.0
google-genai>=0.2.0  # Web search grounding
openai>=1.0.0
ollama==0.1.6

# Data Processing
pandas>=2.2.0
numpy>=1.26.3
beautifulsoup4>=4.9.3
aiohttp>=3.8.0

# Utilities
python-dotenv==1.0.1
requests==2.32.3
eurostat  # Eurostat API integration
nltk
langdetect
```

### External Services

- **Qdrant**: Vector database (cloud or self-hosted)
- **Google Gemini API**: Primary AI analysis
- **OpenAI API**: Secondary AI analysis (optional)
- **Perplexity Sonar API**: Quality validation system (optional but recommended)
- **Eurostat API**: Economic data and industry statistics
- **Web Search**: Live data gathering (via Gemini)

---

## 📦 Installation & Setup

### Prerequisites

1. **Python 3.8+**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Qdrant Database**
   - Option A: Cloud Qdrant (recommended for production)
   - Option B: Local Qdrant instance
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. **Ollama** (for local embeddings, optional)
   ```bash
   # Install Ollama
   curl https://ollama.ai/install.sh | sh
   
   # Pull required model
   ollama pull mistral
   ```

4. **API Keys**
   - Google Gemini API key
   - OpenAI API key (optional but recommended)
   - Qdrant API key (if using cloud)

### Installation Steps

#### 1. Clone Repository

```bash
git clone https://github.com/ValueRollerCoaster/ValueRollerCoaster.git
cd ValueRollerCoaster
```

#### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4. Environment Configuration

Create `.env` file in project root:

```bash
# AI API Keys
GOOGLE_API_KEY=your-gemini-api-key
OPENAI_API_KEY=your-openai-api-key
SONAR_API_KEY=your-perplexity-sonar-api-key  # Optional but recommended for quality validation

# Qdrant Configuration
QDRANT_HOST=localhost  # or cloud URL
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key  # if using cloud
QDRANT_URL=https://your-qdrant-url.cloud.qdrant.io  # if using cloud

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434

# Optional Features
ENABLE_DEMO_MODE=false
ENABLE_DUAL_MODEL_PERSONA=true
ENABLE_WEB_SEARCH=true
COMPANY_WEBSITE_URL=https://your-company-website.com

# Logging
LOG_LEVEL=INFO
```

#### 5. Initialize Database

```bash
# Run database initialization (creates collections)
python -c "from app.database import ensure_collections_exist; ensure_collections_exist()"
```

#### 6. Run Application

**Single-User Mode:**
```bash
streamlit run app/streamlit_app.py
```

**Multi-User Mode (Authentication):**
```bash
streamlit run run_auth_app.py
```

Default credentials: `default_user` / `default`

---

## ⚙️ Configuration

### Configuration File: `app/config.py`

Main configuration file contains all system settings:

#### AI Configuration

```python
# Gemini Settings
GEMINI_TEMPERATURE = 0.0  # Deterministic output
GEMINI_SEED = 42
GEMINI_MAX_TOKENS = 8000

# ChatGPT Settings
CHATGPT_TEMPERATURE = 0.0
CHATGPT_SEED = 42
CHATGPT_MAX_TOKENS = 4000

# Sonar/Perplexity Settings
SONAR_API_KEY = os.environ.get("SONAR_API_KEY")
SONAR_MODEL = "sonar-pro"
SONAR_TEMPERATURE = 0.0
SONAR_MAX_TOKENS = 4000
SONAR_SEED = 42

# Feature Flags
ENABLE_DUAL_MODEL_PERSONA = True
ENABLE_WEB_SEARCH = True
ENABLE_SONAR_VALIDATION = True
ENABLE_COMPANY_PROFILE_VALIDATION = True
ENABLE_CUSTOMER_FOCUS_QUALITY_GATES = True
```

#### Database Configuration

```python
# Qdrant Settings
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
VECTOR_DIM = 1536
INDEX_PARAMS = {"distance": "Cosine"}
```

#### Collection Names

```python
COLLECTIONS = {
    "value_waterfall_analyses": {...},
    "value_components": {...},
    "personas": {...},
    "background_tasks": {...},
    "users": {...},
    "company_profiles": {...},
    # ... more collections
}
```

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_API_KEY` | Gemini API key | Yes | - |
| `OPENAI_API_KEY` | ChatGPT API key | No | - |
| `QDRANT_HOST` | Qdrant host | Yes | localhost |
| `QDRANT_PORT` | Qdrant port | Yes | 6333 |
| `QDRANT_API_KEY` | Qdrant API key (cloud) | No | - |
| `QDRANT_URL` | Qdrant URL (cloud) | No | - |
| `OLLAMA_BASE_URL` | Ollama server URL | Yes | - |
| `SONAR_API_KEY` | Perplexity Sonar API key | No | - (recommended) |
| `ENABLE_DEMO_MODE` | Enable demo mode | No | false |
| `LOG_LEVEL` | Logging level | No | INFO |

---

## 🗄️ Database Setup

### Qdrant Collections

The application uses the following Qdrant collections:

#### Core Collections

1. **`value_components`**
   - Stores individual employee value inputs and AI-transformed customer benefits
   - Vector dimension: 4096 (updated to match Ollama Mistral embeddings)
   - **Core Function**: Stores both `original_value` (employee input) and `ai_processed_value` (customer-focused benefit)
   - Used for: Value alignment matching in persona generation

2. **`personas`**
   - Stores generated buyer personas
   - Vector dimension: 1536
   - Used for: Persona search and retrieval

3. **`background_tasks`**
   - Tracks background persona generation tasks
   - Vector dimension: 1536
   - Used for: Progress tracking

4. **`company_profiles`**
   - Stores company configuration
   - Vector dimension: 128
   - Used for: Company context

5. **`users`**
   - User accounts (authenticated mode)
   - Vector dimension: 128
   - Used for: Authentication

6. **`user_sessions`**
   - Active user sessions
   - Vector dimension: 128
   - Used for: Session management

#### Collection Initialization

Collections are automatically created on first use. To manually initialize:

```python
from app.database import ensure_collections_exist
ensure_collections_exist()
```

### Database Schema

#### Value Components Schema

```python
{
    "main_category": str,      # e.g., "Technical Value"
    "category": str,           # e.g., "Quality"
    "name": str,              # e.g., "Certificates and Skills"
    "original_value": str,     # Employee's individual input/perspective
    "ai_processed_value": str, # AI-transformed customer-focused benefit
    "user_id": str,           # User identifier (for multi-user, data isolation)
    "weight": int,            # Component importance weight
    "user_rating": int,       # User rating (1-5)
    "created_at": str         # Timestamp for versioning
}
```

**Transformation Process:**
- `original_value`: What the employee enters (e.g., "We have ISO 9001 certification")
- `ai_processed_value`: Customer benefit generated by AI (e.g., "Products meet international quality standards, reducing risk and ensuring compliance")
- Transformation uses company context (Business Intelligence, Value Delivery, Capabilities frameworks)
- Field-specific processing based on category (Technical/Business/Strategic/After Sales)

#### Persona Schema

```python
{
    "company": {...},          # Company information
    "pain_points": [...],      # Identified pain points
    "goals": [...],           # Company goals
    "value_drivers": [...],   # Value drivers
    "value_signals": [...],   # Value signals from website
    "alignment_matrix": {...}, # Value alignment matrix
    "chain_of_thought": str,  # AI reasoning
    "generator_version": str,  # Generator version
    "user_id": str,           # User identifier
    "created_at": str         # Timestamp
}
```

### Database Maintenance

#### Sync Value Components with Template

```bash
python -m tests.sync_value_components_with_template
```

This ensures the database matches the template structure defined in `app/categories.py`.

---

## 🚀 Deployment Options

### Option 1: Local Development

**Best for:** Development, testing, single-user scenarios

```bash
# Install and run locally
streamlit run app/streamlit_app.py
```

**Access:** `http://localhost:8501`

### Option 2: Docker Deployment

**Best for:** Production, easy deployment, containerization

```dockerfile
# Dockerfile example
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# Build and run
docker build -t value-rollercoaster .
docker run -p 8501:8501 --env-file .env value-rollercoaster
```

### Option 3: Cloud Deployment

#### Streamlit Cloud

1. Connect repository to Streamlit Cloud
2. Set environment variables in dashboard
3. Deploy automatically

#### AWS/GCP/Azure

1. Deploy Streamlit app on cloud platform
2. Use managed Qdrant (cloud) or self-hosted
3. Configure API keys and environment variables
4. Set up load balancing for multi-user scenarios

### Option 4: Multi-User Production

**Requirements:**
- Authentication enabled (`run_auth_app.py`)
- User management system
- Data isolation per user
- Session management

**Configuration:**
- Set up user accounts
- Configure data migration (if migrating from single-user)
- Set up monitoring and logging
- Configure backup strategy

---

## 🔌 API Integration

### Google Gemini API

**Configuration:**
```python
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
```

**Usage:**
```python
from app.ai.gemini_client import gemini_client

response = await gemini_client(
    prompt="Analyze this company...",
    temperature=0.0,
    max_tokens=8000
)
```

**Rate Limits:**
- 10 requests per minute (RPM)
- Rate-limited client handles throttling automatically

### OpenAI ChatGPT API

**Configuration:**
```python
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = "gpt-4o-mini"
```

**Usage:**
```python
from app.ai.chatgpt_client import ChatGPTClient

client = ChatGPTClient()
response = await client.chat_completion(
    messages=[{"role": "user", "content": "..."}],
    temperature=0.0
)
```

### Perplexity Sonar API

**Configuration:**
```python
SONAR_API_KEY = os.getenv("SONAR_API_KEY")
SONAR_MODEL = "sonar-pro"
```

**Usage:**
```python
from app.ai.sonar.sonar_client import sonar_client

# Check if Sonar is available
is_available = await sonar_client.is_available()

# Generate validation response
response = await sonar_client.generate_response(
    prompt="Validate this company analysis...",
    temperature=0.0,
    max_tokens=4000
)
```

**Purpose:**
- Quality validation at every step of persona generation
- Relevance validation (pre-analysis check)
- Customer focus validation (ensures correct company)
- Accuracy verification throughout the process
- Quality gates at 8 different checkpoints

### Eurostat API

**Integration:**
- Automatic NACE code detection
- Economic indicator data
- Industry statistics

**Usage:**
```python
from app.nace_system import NACE_System

nace = NACE_System()
insights = nace.get_industry_insights("Manufacturing")
```

### Qdrant API

**Connection:**
```python
from app.database import get_qdrant_client

client = get_qdrant_client()
# Use client for database operations
```

---

## 💻 Development Guide

### Project Structure

```
ValueRollerCoaster/
├── app/
│   ├── admin/              # Admin tools (company setup wizard)
│   ├── ai/                 # AI services and models
│   │   ├── market_intelligence/
│   │   └── sonar/          # Validation system
│   ├── auth/               # Authentication system
│   ├── charts/              # Visualization components
│   ├── components/          # UI components
│   │   ├── value_components/
│   │   └── demo_companies/
│   ├── core/                # Core functionality
│   ├── utils/               # Utility functions
│   ├── config.py            # Configuration
│   ├── database.py          # Database operations
│   └── streamlit_app.py     # Main application entry
├── README/                  # Documentation
├── requirements.txt         # Dependencies
└── run_auth_app.py         # Authenticated app entry
```

### Development Workflow

1. **Setup Development Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Run in Development Mode**
   ```bash
   streamlit run app/streamlit_app.py
   ```

3. **Enable Debug Mode**
   ```bash
   export DEBUG_MODE=true
   export DEBUG_AI_PROCESSING=true
   export DEBUG_DATABASE_OPERATIONS=true
   ```

4. **Run Tests**
   ```bash
   pytest tests/
   ```

### Code Standards

- **Imports**: Use absolute imports (`from app.utils import ...`)
- **Type Hints**: Use type hints for all functions
- **Logging**: Use structured logging with appropriate levels
- **Error Handling**: Comprehensive error handling with user-friendly messages

### Adding New Features

1. **Value Components**: Modify `app/categories.py`
2. **AI Prompts**: Update prompts in `app/ai/prompts.py`
3. **UI Components**: Add components in `app/components/`
4. **Database**: Add collections in `app/database.py`

---

## 🔒 Security Considerations

### API Key Security

- **Never commit API keys** to version control
- Use environment variables or secure secret management
- Rotate keys regularly
- Use different keys for development/production

### Authentication Security

- **Password Hashing**: SHA-256 hashing for passwords
- **Session Management**: Secure session tokens
- **Data Isolation**: User data completely isolated
- **Input Validation**: Comprehensive input validation

### Database Security

- **Connection Security**: Use TLS for Qdrant connections (cloud)
- **Access Control**: Limit database access
- **Data Encryption**: Encrypt sensitive data at rest
- **Backup Strategy**: Regular backups with encryption

### Application Security

- **Input Sanitization**: Sanitize all user inputs
- **Rate Limiting**: Implement rate limiting for API calls
- **Error Handling**: Don't expose sensitive information in errors
- **Logging**: Don't log sensitive data (API keys, passwords)

---

## ⚡ Performance Optimization

### AI API Optimization

- **Rate Limiting**: Automatic rate limiting (10 RPM for Gemini)
- **Parallelization**: Parallel execution of independent AI calls
- **Caching**: Cache responses where appropriate
- **Batch Processing**: Batch operations where possible

### Database Optimization

- **Vector Indexing**: Proper vector indexing for Qdrant
- **Collection Management**: Regular cleanup of old data
- **Connection Pooling**: Reuse database connections
- **Query Optimization**: Efficient queries with filters

### Application Optimization

- **Streamlit Caching**: Use `@st.cache_data` for expensive operations
- **Async Operations**: Use async/await for I/O operations
- **Background Tasks**: Use background tasks for long operations
- **Progress Tracking**: Show progress for long operations

### Monitoring

- **Logging**: Comprehensive logging for debugging
- **Performance Metrics**: Track API call times, database query times
- **Error Tracking**: Monitor and alert on errors
- **Usage Analytics**: Track feature usage and performance

---

## 🐛 Troubleshooting

### Common Issues

#### 1. API Key Errors

**Problem**: "Invalid API key" errors

**Solution**:
- Verify API keys in `.env` file
- Check environment variable names
- Ensure API keys are not expired
- Verify API quotas are not exceeded

#### 2. Database Connection Errors

**Problem**: Cannot connect to Qdrant

**Solution**:
- Verify Qdrant is running (if local)
- Check connection URL/credentials
- Verify network connectivity
- Check firewall settings

#### 3. Persona Generation Failures

**Problem**: Persona generation fails or times out

**Solution**:
- Check value components completion (90% required)
- Verify API quotas are not exceeded
- Check network connectivity
- Review logs for specific errors

#### 4. Import Errors

**Problem**: Module import errors

**Solution**:
- Verify PYTHONPATH is set correctly
- Ensure all dependencies are installed
- Check virtual environment is activated
- Verify file structure matches imports

### Debug Mode

Enable debug mode for detailed logging:

```bash
export DEBUG_MODE=true
export DEBUG_AI_PROCESSING=true
export DEBUG_DATABASE_OPERATIONS=true
```

### Log Files

- **Application Logs**: `logs/log.log`
- **Value Alignment Logs**: `logs/value_alignment.log`
- **ChatGPT Logs**: `app/logs/chatgpt_model.log`

---

## 🔄 Maintenance & Updates

### Regular Maintenance Tasks

1. **Database Cleanup**
   - Remove old personas (optional)
   - Clean up expired sessions
   - Archive old data if needed

2. **Log Rotation**
   - Rotate log files regularly
   - Archive old logs
   - Monitor disk space

3. **API Key Rotation**
   - Rotate API keys periodically
   - Update environment variables
   - Test after rotation

4. **Dependency Updates**
   - Update dependencies regularly
   - Test after updates
   - Monitor for breaking changes

### Update Procedure

1. **Backup Database**
   ```bash
   # Export Qdrant data
   # (Use Qdrant snapshot/backup tools)
   ```

2. **Update Code**
   ```bash
   git pull origin main
   pip install -r requirements.txt --upgrade
   ```

3. **Run Migrations** (if needed)
   ```bash
   python -m app.auth.migration_runner
   ```

4. **Test Application**
   - Verify all features work
   - Check database connections
   - Test AI integrations

5. **Deploy**
   - Deploy to production
   - Monitor for errors
   - Rollback if needed

### Version Management

- **APP_VERSION**: Application version (`app/config.py`)
- **GENERATOR_VERSION**: Persona generator version (incremented when generator changes)
- **ANALYSIS_VERSION**: Analysis version

### Backup Strategy

1. **Database Backups**
   - Regular Qdrant snapshots
   - Export critical collections
   - Store backups securely

2. **Configuration Backups**
   - Backup `.env` files
   - Backup company profiles
   - Document configuration changes

3. **Code Backups**
   - Version control (Git)
   - Tag releases
   - Document changes

---

## 📚 Additional Resources

### Documentation

- **Main README**: [README.md](../../README.md)
- **Persona Generation Prompts**: [ALL_PERSONA_GENERATION_PROMPTS.md](../Usage/ALL_PERSONA_GENERATION_PROMPTS.md)
- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Token Limits Guide**: [TOKEN_LIMITS_GUIDE.md](TOKEN_LIMITS_GUIDE.md)

### External Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Google Gemini API](https://ai.google.dev/)
- [OpenAI API](https://platform.openai.com/docs)
- [Eurostat API](https://ec.europa.eu/eurostat/web/main/data/database)

---


<div align="center">

**Technical Documentation for Value Rollercoaster**

[Back to Main README](../../README.md)

</div>

