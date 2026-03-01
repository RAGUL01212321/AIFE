# AIFE LLM Backend - Quick Start Guide

## What's New?

Your AIFE chatbot now has **intelligent LLM-powered file system assistance**! The chatbot can:

✅ Analyze user queries with context-awareness  
✅ Access live file system metadata  
✅ Suggest intelligent file operations  
✅ Understand your intent and provide relevant help  
✅ Maintain conversation history  

## Quick Setup (5 minutes)

### Option 1: Ollama (Easiest - Recommended)

**Step 1: Install Ollama**
```bash
# Download from https://ollama.ai
# Choose your OS and install
```

**Step 2: Download a Model**
```bash
# Open terminal and run:
ollama pull llama2
# Or try mistral (faster):
ollama pull mistral
```

**Step 3: Start Ollama Server**
```bash
ollama serve
# Server runs on http://localhost:11434
```

**Step 4: Configure AIFE**
1. Run AIFE: `python3 main.py`
2. Click the ⚙️ button in the chatbot panel
3. Enable "Use LLM-powered Backend"
4. Select "ollama" as LLM Provider
5. Enter model name: `llama2` (or `mistral`)
6. Click Save

### Option 2: OpenAI (If You Have a Key)

```bash
# Install OpenAI package
pip install openai

# In AIFE Settings:
# 1. Select "openai" as LLM Provider
# 2. Enter your API key
# 3. Model: gpt-3.5-turbo
```

Get free API credits or buy at: https://platform.openai.com

## How to Use

### In the Chatbot

Simply ask natural questions about your files:

```
User: "Show me all Python files"
Assistant: "I found 5 Python files in your current directory:
  - main.py (4.0 KB)
  - utils.py (2.0 KB)
  ..."

User: "What are the permissions on main.py?"
Assistant: "main.py has permissions 755 (rwxr-xr-x), 
which means the owner can read/write/execute..."

User: "How large is this directory?"
Assistant: "Total size: 125 MB across 234 files..."

User: "Explain inodes"
Assistant: "An inode is a data structure in Unix file systems..."
```

## Features Explained

### 1. File System Context
The LLM knows about:
- Current directory and its contents
- File sizes and permissions
- Directory structure
- Subdirectories and file counts

### 2. Smart Analysis
The LLM:
- Understands what you're asking
- Matches it to relevant files
- Suggests appropriate actions
- Explains file system concepts

### 3. Action Suggestions
After answering, it suggests:
- "📌 Suggested actions: open, rename"
- If you say "delete", it asks for confirmation
- Shows what file operations are available

### 4. Conversation Context
The chatbot:
- Remembers previous questions
- Understands follow-up queries
- Maintains context across messages

## Configuration

### Settings File

Settings are saved to: `~/.aife_chatbot_config.json`

Example:
```json
{
  "use_llm_backend": true,
  "llm_provider": "ollama",
  "ollama_model": "mistral",
  "temperature": 0.7,
  "max_history": 20
}
```

### Environment Variables

```bash
# For Ollama
export OLLAMA_URL=http://localhost:11434

# For OpenAI
export OPENAI_API_KEY=sk-...

# For Anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

## Troubleshooting

### "Could not reach Ollama server"
```bash
# Make sure Ollama is running
ollama serve

# Check if it's accessible
curl http://localhost:11434/api/tags
```

### "Model not found"
```bash
# List available models
ollama list

# Download a model
ollama pull mistral
```

### "Error: openai package not installed"
```bash
# Install it
pip install openai

# Then restart AIFE
```

### Responses are Slow
- Using Ollama? Try `mistral` model (faster than llama2)
- Switch to OpenAI for instant responses
- Close other applications to free up memory

## Model Recommendations

| Use Case | Best Model | Installation |
|----------|-----------|--------------|
| Balance (Recommended) | Mistral (Ollama) | `ollama pull mistral` |
| Best Quality | GPT-4 (OpenAI) | Paid API key needed |
| Privacy-First | Llama2 (Ollama) | `ollama pull llama2` |
| Fastest Response | GPT-3.5 (OpenAI) | Paid API key needed |

## Example Conversations

### Example 1: File Discovery
```
You: "Find large files"
Assistant: "I found 3 large files:
- video.mp4 (245 MB)
- archive.tar.gz (156 MB)
- backup.zip (98 MB)

📌 Suggested actions: properties, rename, delete
```

### Example 2: Permission Questions
```
You: "Who can execute main.py?"
Assistant: "main.py has permissions 755 (rwxr-xr-x):
- Owner: can read, write, execute
- Group: can read, execute
- Others: can read, execute

The execution bit (x) is set for all users."
```

### Example 3: Directory Size
```
You: "How much space does this use?"
Assistant: "Total directory size: 2.3 GB across 156 files
- Largest file: video.mp4 (1.2 GB)
- Average file: 14.7 MB
- Smallest file: config.txt (2 KB)

📌 Suggested actions: open, properties, delete
```

## Advanced Usage

### Disable LLM Backend (Use Rule-Based)
1. Open Chatbot Settings (⚙️)
2. Uncheck "Use LLM-powered Backend"
3. Click Save

### Switch Providers
1. Settings → Change LLM Provider
2. Re-enter API key if needed
3. Click Save and restart AIFE

### Change Model
1. Settings → Change model name
2. For Ollama: list available with `ollama list`
3. Click Save

## Files Modified/Created

- ✅ `src/llm_chatbot_backend.py` - New LLM integration
- ✅ `src/chatbot.py` - Enhanced with LLM support
- ✅ `docs/LLM_CHATBOT_GUIDE.md` - Complete documentation
- ✅ `requirements.txt` - Added `requests` for Ollama
- ✅ `THIS_FILE` - Quick start guide

## Next Steps

1. **Install Ollama or get API key**
2. **Configure in AIFE Settings**
3. **Start asking questions!**
4. **Read full guide** in `docs/LLM_CHATBOT_GUIDE.md`

---

**Questions?** Check the full documentation at `docs/LLM_CHATBOT_GUIDE.md`
