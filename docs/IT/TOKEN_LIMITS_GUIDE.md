# Token Limits Adjustment Guide

## 🎯 Quick Token Limit Settings

### **Production (High Quality) - Current Setting**
```python
# In app/config.py
AI_MAX_TOKENS = 6000      # Global default
GEMINI_MAX_TOKENS = 8000  # Gemini's full capacity
CHATGPT_MAX_TOKENS = 4000 # ChatGPT's maximum
```

### **Fast Testing (Quick Iteration)**
```python
# In app/config.py
AI_MAX_TOKENS = 2000      # Fast responses
GEMINI_MAX_TOKENS = 2000  # Quick Gemini responses
CHATGPT_MAX_TOKENS = 2000 # Quick ChatGPT responses
```

### **Development (Balanced)**
```python
# In app/config.py
AI_MAX_TOKENS = 4000      # Balanced speed/quality
GEMINI_MAX_TOKENS = 4000  # Balanced Gemini
CHATGPT_MAX_TOKENS = 4000 # Balanced ChatGPT
```

### **Maximum Quality (Comprehensive)**
```python
# In app/config.py
AI_MAX_TOKENS = 8000      # Maximum quality
GEMINI_MAX_TOKENS = 8000  # Gemini's full capacity
CHATGPT_MAX_TOKENS = 4000 # ChatGPT's maximum
```

## 🔧 How to Adjust

### **Method 1: Edit config.py**
1. Open `app/config.py`
2. Find the token limit settings
3. Change the values
4. Restart the application

### **Method 2: Environment Variables**
```bash
# Set environment variables (if supported)
export AI_MAX_TOKENS=2000
export GEMINI_MAX_TOKENS=2000
export CHATGPT_MAX_TOKENS=2000
```

### **Method 3: Per-Call Override**
```python
# Override for specific calls
response = await gemini_client(prompt, max_tokens=2000)  # Fast testing
response = await chatgpt_generate(prompt, max_tokens=2000)  # Fast testing
```

## 📊 Impact Comparison

| Setting | Speed | Quality | Cost | Use Case |
|---------|-------|---------|------|----------|
| **2000** | ⚡⚡⚡ | ⭐⭐ | 💰 | Fast testing |
| **4000** | ⚡⚡ | ⭐⭐⭐ | 💰💰 | Development |
| **6000** | ⚡ | ⭐⭐⭐⭐ | 💰💰💰 | Production |
| **8000** | 🐌 | ⭐⭐⭐⭐⭐ | 💰💰💰💰 | Maximum quality |

## 🎯 Recommended Workflow

### **1. Development Phase**
```python
AI_MAX_TOKENS = 2000  # Fast iteration
```

### **2. Testing Phase**
```python
AI_MAX_TOKENS = 4000  # Balanced testing
```

### **3. Production Phase**
```python
AI_MAX_TOKENS = 6000  # High quality
GEMINI_MAX_TOKENS = 8000  # Maximum Gemini quality
```

### **4. Special Analysis**
```python
# Override for specific comprehensive analysis
response = await gemini_client(prompt, max_tokens=8000)
```

## ⚡ Quick Commands

### **Switch to Fast Testing**
```python
# In app/config.py - change these lines:
AI_MAX_TOKENS = 2000
GEMINI_MAX_TOKENS = 2000
CHATGPT_MAX_TOKENS = 2000
```

### **Switch to Production**
```python
# In app/config.py - change these lines:
AI_MAX_TOKENS = 6000
GEMINI_MAX_TOKENS = 8000
CHATGPT_MAX_TOKENS = 4000
```

## 🔍 Verification

### **Check Current Settings**
```python
from app.config import AI_MAX_TOKENS, GEMINI_MAX_TOKENS, CHATGPT_MAX_TOKENS
print(f"AI: {AI_MAX_TOKENS}, Gemini: {GEMINI_MAX_TOKENS}, ChatGPT: {CHATGPT_MAX_TOKENS}")
```

### **Test Response Length**
```python
# Generate a persona and check token usage in logs
# Look for: "MaxTokens: XXXX" in the log output
```

## 💡 Tips

1. **Start Low**: Begin with 2000 for fast testing
2. **Increase Gradually**: Move to 4000, then 6000 as needed
3. **Monitor Costs**: Higher tokens = higher costs
4. **Check Quality**: Compare persona quality at different limits
5. **Use Overrides**: For specific cases, override per-call
6. **Model Compatibility**: ChatGPT doesn't support `top_k` parameter (OpenAI limitation)

## 🚀 Performance Impact

- **2000 tokens**: ~30-50% faster than 6000
- **4000 tokens**: ~15-25% faster than 6000
- **6000 tokens**: Production speed
- **8000 tokens**: Maximum quality, slower response

This configuration gives you the flexibility to easily adjust between fast testing and high-quality production use! 