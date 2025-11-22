# Value Rollercoaster: Deployment Quick Reference

## 🚀 Quick Decision Guide

### Which Deployment Option Should You Choose?

| Scenario | Recommended Option | Why |
|----------|-------------------|-----|
| **Development/Testing** | Local Development | Easy setup, full control |
| **Small Team (< 10 users)** | Local or Docker | Simple, cost-effective |
| **Production, Cloud-First** | Streamlit Cloud or AWS | Managed, scalable |
| **Security-Critical, On-Premise** | On-Premise Server | Full control, data sovereignty |
| **Containerized Infrastructure** | Docker | Consistent, portable |
| **Multiple Organizations** | Multi-User Mode + Cloud | User isolation, scalability |

---

## 📦 What You Need

### Essential Requirements

1. **Python 3.8+** - Application runtime
2. **Google Gemini API Key** - Required AI service
3. **Qdrant Database** - Cloud or self-hosted
4. **Ollama** - For local embeddings (optional but recommended)

### Optional but Recommended

5. **OpenAI API Key** - Secondary AI model
6. **Perplexity Sonar API Key** - Quality validation
7. **Domain & SSL** - For production HTTPS

---

## 🎯 Deployment Options Summary

### 1. Local Development
**Command**: `streamlit run app/streamlit_app.py`  

### 2. Docker
**Command**: `docker-compose up -d`  


### 3. Streamlit Cloud
**Platform**: [share.streamlit.io](https://share.streamlit.io/)  

---

## ⚙️ Configuration Quick Start

### Minimal .env File

```bash
# Required
GOOGLE_API_KEY=your-key
QDRANT_URL=https://your-cluster.cloud.qdrant.io
QDRANT_API_KEY=your-key
OLLAMA_BASE_URL=http://localhost:11434

# Optional but Recommended
OPENAI_API_KEY=your-key
SONAR_API_KEY=your-key
```

### Application Modes

**Multi-User**: `streamlit run run_auth_app.py`



### Local Development
```bash
# 1. Clone and setup
git clone https://github.com/ValueRollerCoaster/ValueRollerCoaster.git && cd ValueRollerCoaster
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run
streamlit run app/streamlit_app.py
```

### Docker
```bash
# 1. Build and run
docker-compose up -d

# 2. View logs
docker-compose logs -f

# 3. Stop
docker-compose down
```

### Streamlit Cloud
1. Push to GitHub
2. Connect at share.streamlit.io
3. Add secrets (API keys)
4. Deploy

---





