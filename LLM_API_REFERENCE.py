"""
AIFE LLM Backend - Developer API Reference

Quick reference for developers integrating the LLM backend.
"""

# =============================================================================
# 1. BASIC USAGE
# =============================================================================

from filesystem import FileSystemAbstraction
from llm_chatbot_backend import LLMIntegrationManager, LLMProvider

# Initialize file system
fs = FileSystemAbstraction("/home/user")

# Initialize LLM manager with Ollama
llm_manager = LLMIntegrationManager(
    fs_abstraction=fs,
    provider=LLMProvider.OLLAMA
)

# Process a query
response = llm_manager.process_user_message(
    "Show me Python files",
    current_directory="/home/user/projects"
)

# Access response data
print(response["response"])           # Main response text
print(response["suggested_actions"])  # List of suggested actions
print(response["action_type"])        # Primary action type


# =============================================================================
# 2. PROVIDER SELECTION
# =============================================================================

# Ollama (Local, Free, Recommended)
manager = LLMIntegrationManager(
    fs_abstraction=fs,
    provider=LLMProvider.OLLAMA
)

# OpenAI (Cloud, Requires API Key)
manager = LLMIntegrationManager(
    fs_abstraction=fs,
    provider=LLMProvider.OPENAI,
    api_key="sk-..."
)

# Anthropic (Cloud, Requires API Key)
manager = LLMIntegrationManager(
    fs_abstraction=fs,
    provider=LLMProvider.ANTHROPIC,
    api_key="sk-ant-..."
)

# Hugging Face (Cloud, Requires API Key)
manager = LLMIntegrationManager(
    fs_abstraction=fs,
    provider=LLMProvider.HUGGINGFACE,
    api_key="hf_..."
)


# =============================================================================
# 3. ADVANCED BACKEND USAGE
# =============================================================================

from llm_chatbot_backend import LLMChatbotBackend

# Create backend with custom model
backend = LLMChatbotBackend(
    fs_abstraction=fs,
    provider=LLMProvider.OLLAMA,
    model_name="mistral"  # Faster than llama2
)

# Process query
response = backend.process_query(
    user_input="Find all config files",
    current_dir="/home/user/projects"
)

# Access detailed response
print(f"Answer: {response.response_text}")
print(f"Actions: {response.suggested_actions}")
print(f"Confidence: {response.confidence}")
print(f"Requires confirmation: {response.requires_confirmation}")
print(f"Metadata used: {response.metadata_used}")


# =============================================================================
# 4. METADATA GATHERING
# =============================================================================

# Get file system context for a directory
context = backend.gather_file_metadata("/home/user/projects")

# Access context information
print(f"Current dir: {context.current_directory}")
print(f"Total files: {context.total_files_count}")
print(f"Total size: {context.total_size_bytes} bytes")
print(f"Structure: {context.directory_structure}")
print(f"Recent files: {context.recent_files}")

# Convert to dictionary for JSON serialization
context_dict = context.to_dict()


# =============================================================================
# 5. CONVERSATION HISTORY
# =============================================================================

# Conversation is automatically maintained
backend.conversation_history  # List of {"role": "...", "content": "..."}

# Get history size
history_size = len(backend.conversation_history)

# Clear history for new conversation
backend.clear_history()

# Configure max history size
backend.max_history = 50  # Default is 20


# =============================================================================
# 6. CUSTOM SYSTEM PROMPT
# =============================================================================

class CustomChatbot(LLMChatbotBackend):
    """Custom chatbot with specialized behavior"""
    
    def _build_system_prompt(self) -> str:
        return """You are a developer-focused file system assistant.
        Focus on:
        - Code file organization
        - Build artifacts and ignoring them
        - Source control implications
        - Performance implications of file operations
        """

# Use custom chatbot
custom_backend = CustomChatbot(
    fs_abstraction=fs,
    provider=LLMProvider.OLLAMA
)


# =============================================================================
# 7. ERROR HANDLING
# =============================================================================

try:
    response = llm_manager.process_user_message(
        "Show files",
        "/nonexistent/path"
    )
except Exception as e:
    print(f"Error: {e}")
    # Backend gracefully handles errors and returns fallback response


# =============================================================================
# 8. INTEGRATION WITH GUI
# =============================================================================

from PyQt5.QtWidgets import QWidget
from chatbot import ChatbotWidget

# Create chatbot widget with file system context
widget = ChatbotWidget(fs_abstraction=fs)

# Update current directory (syncs with file explorer)
widget.set_current_directory("/home/user/projects")

# Access LLM manager from widget
if widget.llm_manager:
    context = widget.llm_manager.get_context_info("/home/user")


# =============================================================================
# 9. ACTION EXTRACTION
# =============================================================================

# Extract suggested actions from response text
actions = backend._extract_suggested_actions(
    "I suggest opening this file",
    context
)
# Returns: ["open"]

# Determine action type from user input
action_type = backend._determine_action_type("Delete the old file")
# Returns: "delete"


# =============================================================================
# 10. FORMATTING UTILITIES
# =============================================================================

# Format bytes to human-readable
size_str = backend._format_bytes(1073741824)  # Returns: "1.0 GB"

# Format timestamp
from filesystem import FileNode
timestamp_str = FileNode.get_modified_time_str()  # Returns: "2024-01-20 10:30:45"

# Format permissions
permission_string = FileNode.get_permissions_string()  # Returns: "-rwxr-xr-x"
permission_octal = FileNode.get_permission_octal()     # Returns: "755"


# =============================================================================
# 11. SETTINGS MANAGEMENT
# =============================================================================

from chatbot import ChatbotSettings

# Load settings
settings = ChatbotSettings()

# Get setting
provider = settings.get("llm_provider", "ollama")
api_key = settings.get("api_key", "")

# Set and save
settings.set("llm_provider", "openai")
settings.set("api_key", "sk-...")
settings.save_settings(settings.settings)


# =============================================================================
# 12. RESPONSE DATA STRUCTURE
# =============================================================================

# Response dictionary from process_user_message:
response_data = {
    "response": str,                    # Main response text
    "suggested_actions": List[str],     # ["open", "rename", "delete"]
    "action_type": Optional[str],       # "open", "rename", "delete", etc.
    "requires_confirmation": bool,      # True for destructive operations
    "metadata_used": List[str],         # ["current_directory", "file_list"]
    "timestamp": str                    # ISO format timestamp
}

# LLMResponse dataclass fields:
# - response_text: str
# - suggested_actions: List[str]
# - confidence: float (0-1)
# - metadata_used: List[str]
# - requires_confirmation: bool
# - action_type: Optional[str]


# =============================================================================
# 13. PROVIDERS DETAILS
# =============================================================================

# Ollama
# - URL: http://localhost:11434
# - Models: llama2, mistral, neural-chat, etc.
# - Start: ollama serve
# - Cost: Free
# - Speed: 5-10 seconds per query

# OpenAI
# - Endpoint: https://api.openai.com/v1/chat/completions
# - Models: gpt-3.5-turbo, gpt-4
# - Key: Get from https://platform.openai.com/api-keys
# - Cost: ~$0.001-0.02 per query
# - Speed: 1-2 seconds per query

# Anthropic (Claude)
# - Endpoint: https://api.anthropic.com
# - Models: claude-3-sonnet-20240229
# - Key: Get from https://console.anthropic.com
# - Cost: ~$0.01 per query
# - Speed: 2-3 seconds per query

# Hugging Face
# - Endpoint: https://api-inference.huggingface.co/models
# - Models: Various (meta-llama/Llama-2-7b, etc.)
# - Key: Get from https://huggingface.co/settings/tokens
# - Cost: Free tier available
# - Speed: 3-5 seconds per query


# =============================================================================
# 14. ENVIRONMENT SETUP
# =============================================================================

import os

# Ollama
os.environ["OLLAMA_URL"] = "http://localhost:11434"

# OpenAI
os.environ["OPENAI_API_KEY"] = "sk-..."

# Anthropic
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

# Hugging Face
os.environ["HF_API_KEY"] = "hf_..."


# =============================================================================
# 15. COMPLETE EXAMPLE
# =============================================================================

def main():
    # Setup
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    
    # Initialize with Ollama
    backend = LLMChatbotBackend(
        fs_abstraction=fs,
        provider=LLMProvider.OLLAMA,
        model_name="mistral"
    )
    
    # Get metadata
    context = backend.gather_file_metadata(os.path.expanduser("~"))
    print(f"Directory: {context.current_directory}")
    print(f"Files: {context.total_files_count}")
    
    # Process queries
    queries = [
        "Show me Python files",
        "What's the total size?",
        "Which files are largest?"
    ]
    
    for query in queries:
        response = backend.process_query(
            query,
            os.path.expanduser("~")
        )
        print(f"\nQ: {query}")
        print(f"A: {response.response_text}")
        if response.suggested_actions:
            print(f"Actions: {response.suggested_actions}")
    
    # Get conversation history
    print(f"\nTotal messages: {len(backend.conversation_history)}")


if __name__ == "__main__":
    main()


# =============================================================================
# 16. CLASS HIERARCHY
# =============================================================================

"""
LLMProvider (Enum)
├── OLLAMA
├── OPENAI
├── ANTHROPIC
└── HUGGINGFACE

FileMetadataContext (Dataclass)
├── current_directory: str
├── recent_files: List[Dict]
├── directory_structure: Dict
├── total_files_count: int
└── total_size_bytes: int

LLMQuery (Dataclass)
├── user_input: str
├── file_metadata_context: FileMetadataContext
├── conversation_history: List[Dict]
└── timestamp: str

LLMResponse (Dataclass)
├── response_text: str
├── suggested_actions: List[str]
├── confidence: float
├── metadata_used: List[str]
├── requires_confirmation: bool
└── action_type: Optional[str]

LLMChatbotBackend
├── __init__()
├── gather_file_metadata()
├── process_query()
├── _build_system_prompt()
├── _build_user_prompt()
├── _call_llm()
├── _call_ollama()
├── _call_openai()
├── _call_anthropic()
├── _call_huggingface()
├── _extract_suggested_actions()
├── _determine_action_type()
├── _format_bytes()
└── clear_history()

LLMIntegrationManager
├── __init__()
├── process_user_message()
└── get_context_info()

ChatbotWidget (Enhanced)
├── llm_manager: LLMIntegrationManager
├── set_current_directory()
└── on_send_message()  # Now calls LLM
"""

# =============================================================================
# END OF REFERENCE
# =============================================================================
