# Value Rollercoaster: Complete Deployment Guide

<div align="center">

# 🚀 Deploying Value Rollercoaster in Your Organization

**Complete guide to deploying and running Value Rollercoaster in any environment**

</div>

---

## 📋 Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Prerequisites](#prerequisites)
- [Deployment Options](#deployment-options)
- [Step-by-Step Deployment Guides](#step-by-step-deployment-guides)
- [Configuration](#configuration)
- [Security Considerations](#security-considerations)
- [Scaling & Performance](#scaling--performance)
- [Troubleshooting](#troubleshooting)

---

## Overview

**Value Rollercoaster** is a Python-based Streamlit web application that can be deployed in various ways depending on your organization's needs, infrastructure, and security requirements.

### Application Architecture

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Python application with async support
- **Database**: Qdrant (vector database) - cloud or self-hosted
- **AI Services**: Google Gemini, OpenAI ChatGPT, Perplexity Sonar (via APIs)
- **Embeddings**: Ollama (local) or cloud-based



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


*This guide covers all major deployment scenarios. Choose the option that best fits your organization's needs, infrastructure, and security requirements.*

