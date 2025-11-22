# Value Rollercoaster: AI-Powered B2B Persona & Value Alignment Platform

<div align="center">

![Value Rollercoaster](https://img.shields.io/badge/Value-Rollercoaster-4CAF50?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-1.47+-red?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Transform company websites into actionable strategic sales playbooks**

[Features](#-core-features) • [Quick Start](#-quick-start-guide) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## 📖 What is Value Rollercoaster?

**Value Rollercoaster** is an AI-powered B2B platform that transforms a potential customer's website into a comprehensive **Strategic Sales Playbook**. By analyzing company websites using advanced AI models (Google Gemini + ChatGPT), the platform generates detailed buyer personas, identifies value alignment opportunities, and provides evidence-based insights that empower sales and marketing teams to have more intelligent, effective conversations.

### 🎯 Core Purpose

The platform addresses a critical challenge in B2B sales: **understanding your prospect's needs and aligning your value propositions accordingly**. Instead of generic pitches, sales teams get:

- **Deep customer insights** extracted from company websites
- **Personalized value alignment** matching your offerings to their needs
- **Evidence-based rationale** for every recommendation
- **Market intelligence** powered by real economic data
- **Actionable playbooks** ready for sales conversations

---

## ✨ Core Features

### 🤖 **Dual-Model AI Architecture**
- **Google Gemini**: Structured analysis, web search, data validation
- **OpenAI ChatGPT**: Creative insights, alternative perspectives, emotional factors
- **Cross-Model Validation**: Compares insights from both models for higher confidence

### 🛡️ **Sonar AI Quality Validation System**
- **Quality Gates**: Validation checkpoints at every step of persona generation
- **Relevance Validation**: Pre-analysis check to ensure company is relevant before processing
- **Accuracy Verification**: Validates that AI models correctly identified the company
- **Customer Focus Validation**: Ensures analysis focuses on the correct company (not competitors or related entities)
- **Perplexity Sonar Integration**: Uses Perplexity's Sonar API for advanced validation
- **Quality Assurance**: Acts as a proofreader throughout the entire process

### 🌐 **Live Web Search Integration**
- Real-time data gathering for current market information
- Up-to-date company insights and industry trends
- Dynamic market intelligence powered by web search

### ⚡ **Optimized Performance**
- **25-40% faster** persona generation (5-8 minutes vs 8-12 minutes)
- Intelligent parallelization while maintaining quality
- Rate-limited API management for reliable operation

### 🏢 **Company-Agnostic Platform**
- Works for **ANY company type** and industry
- One-time company profile configuration
- Dynamic AI prompts that adapt to your business
- Multi-tenant ready architecture

### 📊 **Comprehensive Value Components System**
- **4 Main Categories**: Technical, Business, Strategic, After Sales
- **Structured Framework**: Organized by subcategories and components
- **AI-Powered Benefits**: Automatic customer benefit generation
- **Visual Analytics**: Interactive sunburst charts for value distribution

### 🎯 **7-Step Enhanced Persona Generation with Sonar Validation**
1. 🔍 Dual-Model Website Analysis
   - **Sonar Step 0**: Pre-analysis relevance validation (is company relevant?)
   - **Sonar Step 1.5**: Website analysis validation (correct company identified?)
2. ✅ Cross-Model Validation
   - **Sonar Step 2.5**: Cross-validation quality check
3. 🏭 Enhanced Market Intelligence
   - **Sonar Step 3.5**: Market intelligence validation
4. 🎯 Dual-Model Value Alignment
   - **Sonar Step 4.5**: Value alignment validation
5. 🎨 Creative Persona Elements
   - **Sonar Step 5.5**: Creative elements validation
6. 🧠 Final Persona Synthesis
   - **Sonar Step 6.5**: Final synthesis validation
7. 🔍 Quality Assurance
   - **Sonar Step 8**: Final quality check before completion

### 📈 **Eurostat API Integration**
- Real-time economic indicator data
- Industry classification via NACE system
- Market intelligence with EU benchmark comparisons
- Country-level economic trend analysis

### 🔐 **Flexible Authentication**
- **Single-user mode**: No authentication required
- **Multi-user mode**: Full user management and data isolation
- Automatic data migration support

---

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.8+**
- **API Keys**:
  - Google Gemini API key (`GOOGLE_API_KEY`)
  - OpenAI API key (`OPENAI_API_KEY`) - Optional but recommended
- **Qdrant Database**: Cloud or local instance
- **Ollama** (optional): For local embedding generation

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ValueRollerCoaster/ValueRollerCoaster.git
   cd ValueRollerCoaster
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**
   ```bash
   # Create .env file
   export GOOGLE_API_KEY="your-gemini-api-key"
   export OPENAI_API_KEY="your-openai-api-key"  # Optional
   export QDRANT_API_KEY="your-qdrant-api-key"  # If using cloud Qdrant
   export QDRANT_URL="your-qdrant-url"          # If using cloud Qdrant
   ```

4. **Choose your entry point**

   **Option A: Single-User Mode (No Authentication)**
   ```bash
   streamlit run app/streamlit_app.py
   ```

   **Option B: Multi-User Mode (Authentication Required)**
   ```bash
   streamlit run run_auth_app.py
   ```
   Default credentials: `default_user` / `default`

### First-Time Setup

1. **Company Setup Wizard** (First Run)
   - Enter company information (name, business description, location)
   - Select target customers and industries served
   - Describe products, services, and value propositions
   - Configure business intelligence settings
   - Optional: Add branding (colors, logo)

2. **Value Components Setup** (Critical Step)
   - Navigate to **Value Components** tab
   - Fill out value components across 4 categories:
     - **Technical Value**: Quality, Performance, Innovation, Sustainability
     - **Business Value**: Cost Savings, Revenue Growth, Efficiency Gains
     - **Strategic Value**: Competitive Advantage, Risk Mitigation, Partnership Development
     - **After Sales Value**: Customer Support, Maintenance, User Experience
   - **Option**: Click "Generate Initial Value Components" to auto-populate based on company profile
   - **Requirement**: At least 90% completion required for persona generation

3. **Generate Your First Persona**
   - Navigate to **Buyer Persona** tab
   - Enter a target company website URL
   - Click **"Generate Buyer Persona"**
   - Wait 5-8 minutes for analysis (progress tracked in sidebar)
   - Review the generated persona with value alignment matrix



## 🎯 How It Works

### Complete Workflow

```
1. Company Setup
   └──> Configure company profile (one-time)
   └──> Set target market and business model

2. Value Components Setup (Critical Entry Point)
   └──> Define value propositions across 4 categories
   └──> Populate technical, business, strategic, and after-sales values
   └──> AI generates customer benefits automatically
   └──> Visualize value distribution with sunburst charts

3. Persona Generation
   └──> Enter target company website
   └──> Dual AI models analyze website content
   └──> Market intelligence integration (Eurostat API)
   └──> Value alignment workflow matches needs to your offerings
   └──> Generate comprehensive buyer persona

4. Analysis & Insights
   └──> Review value alignment matrix
   └──> Explore AI reasoning (chain of thought)
   └──> Access cross-model validation insights
   └──> Save persona for future reference
```

### Value Components: The Foundation

**Value Components** are the critical entry point for everything else. They define:
- What your company offers (Technical, Business, Strategic, After Sales value)
- How you deliver value to customers
- Unique differentiators and competitive advantages

During persona generation, the system:
1. Analyzes the target company's website
2. Identifies their needs, pain points, and goals
3. **Matches their needs to your value components**
4. Creates an alignment matrix showing where you fit
5. Provides evidence-based rationale for each match

**Without value components, persona generation cannot work effectively.**



## 🏗️ System Architecture

### Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **AI Models**: Google Gemini, OpenAI ChatGPT
- **Database**: Qdrant (vector database)
- **APIs**: Eurostat (economic data), Web Search (live data)
- **Embeddings**: Ollama/Mistral (local) or cloud-based

### Key Components

- **Company Context Manager**: Manages company profile and configuration
- **Value Components System**: Structured value proposition framework
- **Persona Generator**: Dual-model AI analysis engine
- **Value Alignment Workflow**: 3-step matching process (Profiler → Hypothesizer → Final Aligner)
- **Market Intelligence Service**: Eurostat integration and industry insights
- **NACE System**: European industry classification integration

---

## 📊 Data Flow

```
Company Profile
    ↓
Value Components (Critical Entry Point)
    ↓
Target Website URL
    ↓
Dual AI Analysis (Gemini + ChatGPT)
    ↓
Market Intelligence (Eurostat + Web Search)
    ↓
Value Alignment Workflow
    ↓
Buyer Persona + Alignment Matrix
```

---

## 🔧 Configuration

### Required Settings

- **Company Profile**: Configured via Company Setup Wizard
- **Value Components**: Must be 90%+ complete for persona generation
- **API Keys**: 
  - Gemini (required)
  - ChatGPT (required)
  - Sonar/Perplexity (required)
- **Database**: Qdrant connection (cloud or local)

### Optional Features

- **Demo Mode**: Enable for development/testing (`ENABLE_DEMO_MODE=true`)
- **Website Enhancement**: Use company website data for value component generation
- **Branding**: Custom colors and logo in company profile





