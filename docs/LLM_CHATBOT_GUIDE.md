# AIFE LLM Chatbot Backend Documentation

## Overview

The AIFE chatbot has been enhanced with an intelligent **LLM-powered backend** that provides context-aware file system assistance. The LLM has access to:

- **Current directory metadata** (files, folders, sizes)
- **File properties** (permissions, ownership, timestamps)
- **Directory structure** (subdirectories, file counts)
- **Conversation history** (previous messages)

## Architecture

```
User Query
    ↓
ChatbotWidget (GUI)
    ↓
LLMIntegrationManager
    ↓
LLMChatbotBackend
    ├─ Metadata Gathering
    │  └─ FileSystemAbstraction (gathers file context)
    │
    ├─ Prompt Construction
    │  ├─ System Prompt (role & instructions)
    │  └─ User Prompt (query + file context)
    │
    └─ LLM Processing
       ├─ Ollama (local, no API key needed) ✓ Recommended
       ├─ OpenAI (GPT-3.5, GPT-4)
       ├─ Anthropic (Claude)
       └─ Hugging Face (open models)

       ↓
    LLMResponse
       ├─ response_text (answer to query)
       ├─ suggested_actions (file operations)
       ├─ confidence (0-1 score)
       ├─ requires_confirmation (for destructive ops)
       └─ metadata_used (which context was used)

       ↓
    GUI Display
```

## Features

### 1. **File System Context Awareness**
The LLM receives metadata about the current directory:
- List of files with sizes and permissions
- Directory structure (count of subdirs, files, symlinks)
- Total directory size
- Recent file timestamps

### 2. **Query Analysis**
The LLM analyzes user queries to:
- Understand the user's intent (list files, open, delete, etc.)
- Identify relevant files to the query
- Determine required file operations
- Extract action types (rename, delete, properties, etc.)

### 3. **Action Suggestion**
Based on analysis, the LLM suggests:
- File operations (open, rename, delete, move)
- Display relevant file properties
- Confirmation requests for dangerous operations

### 4. **Conversation Context**
- Maintains conversation history (default: 20 messages)
- Uses history to understand follow-up queries
- Provides consistent responses

## Setup & Configuration

### Option 1: Ollama (Recommended - Free, Local, No API Key)

**Installation:**
```bash
# Install Ollama from https://ollama.ai
# Then pull a model:
ollama pull llama2      # 4GB
ollama pull mistral     # 4GB
ollama pull neural-chat # 5GB
```

**Run Ollama:**
```bash
ollama serve
# Ollama starts on http://localhost:11434
```

**In AIFE:**
1. Open Chatbot Settings (⚙️ button)
2. Enable "Use LLM-powered Backend"
3. Select "ollama" as LLM Provider
4. Enter model name (e.g., "llama2", "mistral")
5. Click Save

### Option 2: OpenAI (GPT-3.5, GPT-4)

**Requirements:**
```bash
pip install openai
```

**Setup:**
1. Get API key from https://platform.openai.com/api-keys
2. Open AIFE Chatbot Settings
3. Select "openai" as LLM Provider
4. Enter your API key
5. Set model (e.g., "gpt-3.5-turbo")

### Option 3: Anthropic (Claude)

**Requirements:**
```bash
pip install anthropic
```

**Setup:**
1. Get API key from https://console.anthropic.com
2. Open AIFE Chatbot Settings
3. Select "anthropic" as LLM Provider
4. Enter your API key

### Option 4: Hugging Face

**Requirements:**
```bash
pip install huggingface_hub
```

**Setup:**
1. Get API key from https://huggingface.co/settings/tokens
2. Open AIFE Chatbot Settings
3. Select "huggingface" as LLM Provider
4. Enter your API key

## How It Works

### 1. User Sends Query

```
User: "Show me all Python files in this folder"
```

### 2. Metadata Gathering

```python
FileMetadataContext(
    current_directory="/home/user/projects",
    recent_files=[
        {"name": "main.py", "size": 4096, "permissions": "755"},
        {"name": "utils.py", "size": 2048, "permissions": "644"},
        ...
    ],
    directory_structure={
        "current": "/home/user/projects",
        "files_count": 25,
        "subdirs": 3,
        "regular_files": 22,
        "symlinks": 0
    }
)
```

### 3. Prompt Construction

**System Prompt:**
```
You are AIFE Assistant - an intelligent file system helper.
Your role:
1. Understand user file system queries
2. Analyze provided file system metadata
3. Provide helpful, context-aware responses
4. Suggest relevant file operations
...
```

**User Prompt:**
```
Current File System Context:
- Current Directory: /home/user/projects
- Total Files: 25
- Subdirectories: 3
- Regular Files: 22

Recent Files in Current Directory:
- main.py (file, 4.0 KB, 2024-01-20 10:30:45)
- utils.py (file, 2.0 KB, 2024-01-19 15:20:30)
...

User Query: Show me all Python files in this folder
```

### 4. LLM Processing

The LLM (e.g., Llama2 via Ollama):
- Understands "Python files" means `.py` files
- Analyzes the provided file list
- Identifies: main.py, utils.py, etc.
- Suggests: listing them, opening one, etc.

### 5. Response

```
Response: "I found 5 Python files in your current directory:
1. main.py (4.0 KB) - Modified: Jan 20, 10:30
2. utils.py (2.0 KB) - Modified: Jan 19, 15:20
...

📌 Suggested actions: open, properties
```

## Example Queries

### File Discovery
```
"Show me all large files"
"Find PDF documents in this folder"
"What files were modified today?"
"List all symlinks"
```

### File Properties
```
"What are the permissions on main.py?"
"Who owns this file?"
"How big is the entire directory?"
"Show me file metadata"
```

### File Operations
```
"Can I delete this file?"
"Rename config.txt to settings.txt"
"What's the inode number of this file?"
"Change permissions to 755"
```

### OS Concepts
```
"Explain inodes"
"What are symlinks?"
"How do Unix permissions work?"
"What's the difference between hard and soft links?"
```

## Configuration Options

### Chatbot Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `use_llm_backend` | `true` | Enable/disable LLM backend |
| `llm_provider` | `ollama` | LLM provider (ollama, openai, anthropic, huggingface) |
| `ollama_model` | `llama2` | Model for Ollama |
| `api_key` | (empty) | API key for cloud providers |
| `temperature` | `0.7` | Creativity level (0-1) |
| `max_history` | `20` | Conversation history size |

### Environment Variables

```bash
# Ollama
export OLLAMA_URL=http://localhost:11434

# OpenAI
export OPENAI_API_KEY=your_key_here

# Anthropic
export ANTHROPIC_API_KEY=your_key_here

# Hugging Face
export HF_API_KEY=your_key_here
```

## Code Examples

### Basic Usage

```python
from filesystem import FileSystemAbstraction
from llm_chatbot_backend import LLMIntegrationManager, LLMProvider

# Initialize file system
fs = FileSystemAbstraction("/home/user")

# Initialize LLM manager with Ollama
llm_manager = LLMIntegrationManager(
    fs_abstraction=fs,
    provider=LLMProvider.OLLAMA
)

# Process user query
response = llm_manager.process_user_message(
    "Show me Python files",
    current_directory="/home/user/projects"
)

print(response["response"])
print(response["suggested_actions"])
```

### Advanced Configuration

```python
from llm_chatbot_backend import LLMChatbotBackend, LLMProvider

# Custom configuration
backend = LLMChatbotBackend(
    fs_abstraction=fs,
    provider=LLMProvider.OPENAI,
    api_key="sk-...",
    model_name="gpt-4"
)

# Process query
response = backend.process_query(
    user_input="Show me all config files",
    current_dir="/home/user/projects"
)

# Access detailed response data
print(f"Response: {response.response_text}")
print(f"Actions: {response.suggested_actions}")
print(f"Action Type: {response.action_type}")
print(f"Requires Confirmation: {response.requires_confirmation}")
```

### Custom System Prompt

```python
# Extend the backend for custom behavior
class CustomChatbot(LLMChatbotBackend):
    def _build_system_prompt(self):
        return """You are a specialized file manager for developers.
        Focus on:
        - Code file organization
        - Build artifacts
        - Source control implications
        """
```

## Performance Considerations

### Ollama (Recommended for Development)
- **Speed**: ~5-10 seconds per query (depends on model)
- **Memory**: 4-8 GB RAM needed
- **Cost**: Free
- **Privacy**: All processing local

### OpenAI
- **Speed**: ~1-2 seconds per query
- **Memory**: Minimal (API calls)
- **Cost**: ~$0.001-0.02 per query
- **Privacy**: Data sent to OpenAI servers

### Model Performance

| Model | Size | Speed | Quality | RAM |
|-------|------|-------|---------|-----|
| Ollama Llama2 | 4GB | 5-10s | Good | 6GB |
| Ollama Mistral | 4GB | 3-5s | Excellent | 6GB |
| Ollama Neural-Chat | 5GB | 4-7s | Very Good | 7GB |
| OpenAI GPT-3.5 | - | 1-2s | Excellent | ~50MB |
| OpenAI GPT-4 | - | 2-5s | Outstanding | ~50MB |

## Troubleshooting

### Issue: "Could not reach Ollama server"
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Issue: "Error calling OpenAI"
```bash
# Verify API key
echo $OPENAI_API_KEY

# Check key format (should start with sk-)
# Regenerate at https://platform.openai.com/api-keys
```

### Issue: "LLM responses are slow"
1. Try a smaller model (Mistral < Llama2)
2. Reduce metadata context (fewer recent files)
3. Switch to faster provider (OpenAI vs Ollama)

### Issue: "Memory error when using Ollama"
1. Close other applications
2. Use smaller model: `ollama pull mistral`
3. Switch to cloud provider (OpenAI/Anthropic)

## Advanced Features

### Context Management

```python
# Gather specific metadata
context = backend.gather_file_metadata("/path/to/dir")

# Access context details
print(f"Files: {context.total_files_count}")
print(f"Size: {context.total_size_bytes} bytes")
print(f"Structure: {context.directory_structure}")
```

### Conversation History

```python
# Access conversation history
print(backend.conversation_history)

# Clear history
backend.clear_history()

# Configure history size
backend.max_history = 50
```

### Action Extraction

```python
# Get suggested actions from response
actions = backend._extract_suggested_actions(
    response_text="I suggest you open or rename this file",
    context=context
)
# Returns: ["open", "rename"]
```

## Future Enhancements

- [ ] Multi-file operations (batch rename, delete)
- [ ] Integration with file manager operations
- [ ] Learning from user actions
- [ ] Custom prompt templates per use case
- [ ] Streaming responses for long outputs
- [ ] Voice input support
- [ ] GUI integration for suggested actions
- [ ] Multi-language support

## References

- [Ollama Documentation](https://ollama.ai)
- [OpenAI API Reference](https://platform.openai.com/docs)
- [Anthropic Claude API](https://docs.anthropic.com)
- [Hugging Face Inference](https://huggingface.co/docs)
