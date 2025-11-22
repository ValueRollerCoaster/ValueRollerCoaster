# Value Rollercoaster: Complete Deployment Guide

<div align="center">

# 🚀 Deploying Value Rollercoaster in Your Organization

**Complete guide to deploying and running Value Rollercoaster in any environment**

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Next Steps](#next-steps)

---

## Overview

**Value Rollercoaster** is a Python-based Streamlit web application that can be deployed in various ways depending on your organization's needs, infrastructure, and security requirements.

### Application Architecture

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python application with async support
- **Database**: Qdrant (vector database) - cloud or self-hosted
- **AI Services**: Google Gemini, OpenAI ChatGPT, Perplexity Sonar (via APIs)
- **Embeddings**: Ollama (local) or cloud-based

### What Value Rollercoaster Does

Value Rollercoaster helps organizations transform company values into actionable tools by:
1. **Individual Input**: Each employee defines value components from their perspective
2. **AI Transformation**: Converts diverse inputs into customer-focused benefits
3. **Customer Value Visibility**: Everyone sees how their work creates customer value
4. **Practical Applications**: Use transformed values for persona generation, prospect alignment, and better customer conversations

---

## Prerequisites

### 1. Python Environment

**Required**: Python 3.8+ installed on the system

**Check Python version:**
```bash
python --version
# or
python3 --version
```

**Install Python** (if not installed):
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: `sudo apt-get install python3 python3-pip` (Ubuntu/Debian)
- **macOS**: `brew install python3` (with Homebrew)

### 2. API Keys (Required)

You need API keys for the AI services:

#### Google Gemini API Key (Required)
- **Get it from**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Cost**: Pay-as-you-go pricing
- **Usage**: Primary AI model for analysis

#### OpenAI API Key (Optional but Recommended)
- **Get it from**: [OpenAI Platform](https://platform.openai.com/api-keys)
- **Cost**: Pay-as-you-go pricing
- **Usage**: Secondary AI model for creative insights

#### Perplexity Sonar API Key (Optional but Recommended)
- **Get it from**: [Perplexity API](https://www.perplexity.ai/settings/api)
- **Cost**: Pay-as-you-go pricing
- **Usage**: Quality validation to prevent hallucinations

### 3. Qdrant Database

You need a Qdrant vector database instance. Two options:

#### Option A: Cloud Qdrant (Recommended for Production)
- **Service**: [Qdrant Cloud](https://cloud.qdrant.io/)
- **Cost**: Free tier available, paid plans for production
- **Benefits**: Managed service, automatic backups, scaling
- **What you need**: Qdrant Cloud account, API key, cluster URL

#### Option B: Self-Hosted Qdrant (For On-Premise)
- **Deployment**: Docker container or native installation
- **Cost**: Infrastructure costs only
- **Benefits**: Full control, data stays on-premise
- **What you need**: Server with Docker or Qdrant installed

### 4. Ollama (Optional but Recommended)

**For local embedding generation:**
- **What it is**: Local AI model server for embeddings
- **Get it from**: [Ollama.ai](https://ollama.ai/)
- **Installation**: Download and install Ollama
- **Model**: Pull "mistral" model: `ollama pull mistral`
- **Why**: Reduces API costs, faster embeddings, privacy

**If not using Ollama:**
- You can use cloud-based embeddings (higher cost)
- Some features may be slower

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ValueRollerCoaster/ValueRollerCoaster.git
cd ValueRollerCoaster
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Required
GOOGLE_API_KEY=your-gemini-api-key
QDRANT_HOST=localhost
QDRANT_PORT=6333
# OR for cloud Qdrant:
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-qdrant-api-key

OLLAMA_BASE_URL=http://localhost:11434

# Optional but Recommended
OPENAI_API_KEY=your-openai-api-key
SONAR_API_KEY=your-perplexity-api-key
```

### 4. Start Qdrant Database

**Option A: Local Qdrant (Docker)**
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Option B: Cloud Qdrant**
- Sign up at [Qdrant Cloud](https://cloud.qdrant.io/)
- Create a cluster and get your URL and API key
- Add to `.env` file

### 5. Start Ollama (Optional but Recommended)

```bash
# Install Ollama from https://ollama.ai/
# Pull the mistral model
ollama pull mistral
```

### 6. Run the Application

**Single-User Mode:**
```bash
streamlit run app/streamlit_app.py
```

**Multi-User Mode (with Authentication):**
```bash
streamlit run run_auth_app.py
```

Access the application at `http://localhost:8501`

---

## Next Steps

### Initial Setup

1. **Admin Setup (One-Time)**
   - Configure company profile
   - Set up AI framework
   - Configure company website (optional)

2. **Value Components Setup (All Users)**
   - Each employee defines value components from their perspective
   - AI transforms inputs into customer-focused benefits
   - Adjust importance and save (90% completion required for persona generation)

3. **Start Using**
   - Generate buyer personas for prospects
   - Review value alignment matrices
   - Use insights for better customer conversations

### Additional Resources

- **[Deployment Quick Reference](DEPLOYMENT_QUICK_REFERENCE.md)**: Quick decision guide and commands
- **[Technical Documentation](README_TECHNICAL.md)**: Detailed system architecture and configuration
- **[Token Limits Guide](TOKEN_LIMITS_GUIDE.md)**: Understanding API usage and costs

---

*For detailed deployment scenarios, configuration options, and troubleshooting, see the [Technical Documentation](README_TECHNICAL.md) and [Deployment Quick Reference](DEPLOYMENT_QUICK_REFERENCE.md).*

