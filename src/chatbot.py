"""
AIFE - Advanced Interactive File Explorer
Chatbot Module

Intelligent chatbot with LLM-powered file system assistance.
Supports both rule-based and LLM-based responses with file metadata context.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QLabel, QScrollArea, QDialog, QFormLayout,
    QSpinBox, QCheckBox, QMessageBox, QComboBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QColor, QTextCursor
import re
import random
import json
import os
from typing import Optional, Callable

from filesystem import FileSystemAbstraction
from llm_chatbot_backend import LLMIntegrationManager, LLMProvider
from rag_engine import RAGEngine


class ChatbotSignals(QObject):
    """Signals for chatbot"""
    response_generated = pyqtSignal(str)


class LLMWorker(QThread):
    """Background thread for LLM calls so the UI stays responsive"""
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, llm_manager, user_message: str, current_directory: str, is_retry: bool = False, is_final_summary: bool = False, parent=None):
        super().__init__(parent)
        self.llm_manager = llm_manager
        self.user_message = user_message
        self.current_directory = current_directory
        self.is_retry = is_retry
        self.is_final_summary = is_final_summary

    def run(self):
        try:
            result = self.llm_manager.process_user_message(
                self.user_message,
                self.current_directory
            )
            # Tag the result so we know it was a retry
            result["is_retry"] = self.is_retry
            result["is_final_summary"] = self.is_final_summary
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class ChatbotSettings:
    """Manage chatbot settings"""
    
    CONFIG_FILE = os.path.expanduser("~/.aife_chatbot_config.json")
    
    DEFAULT_SETTINGS = {
        "api_key": "",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "enable_ai": True,
        "max_history": 20,
        "llm_provider": "ollama",
        "ollama_model": "smollm",
        "use_llm_backend": True
    }
    
    def __init__(self):
        self.settings = self.load_settings()
    
    def load_settings(self) -> dict:
        """Load settings from file"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception:
                return self.DEFAULT_SETTINGS.copy()
        return self.DEFAULT_SETTINGS.copy()
    
    def save_settings(self, settings: dict) -> bool:
        """Save settings to file"""
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(settings, f, indent=2)
            self.settings = settings
            return True
        except Exception:
            return False
    
    def get(self, key: str, default=None):
        """Get a setting value"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value):
        """Set a setting value"""
        self.settings[key] = value


class Chatbot:
    """Simple rule-based chatbot for AIFE assistance"""
    
    def __init__(self):
        self.responses = {
            "hello": [
                "Hello! I'm AIFE's assistant. How can I help you explore your files?",
                "Hi there! Need help navigating your file system?",
                "Greetings! What would you like to do with your files?"
            ],
            "help": [
                "I can help you with:\n• File navigation tips\n• Explaining file properties\n• Suggesting file operations\n• Understanding permissions",
                "What do you need help with? I can assist with file operations, navigation, or explain file system concepts.",
            ],
            "permissions": [
                "File permissions use three digits:\n• First digit: Owner permissions\n• Second digit: Group permissions\n• Third digit: Other permissions\n\nEach can be 0-7 (sum of r=4, w=2, x=1)",
                "Permissions control who can read (r), write (w), or execute (x) a file. They're shown in octal (0-7) or as rwx notation.",
            ],
            "symlink": [
                "A symbolic link (shortcut) points to another file or directory without copying its contents.",
                "Symlinks are references to other files. They're shown with 🔗 in the file list.",
            ],
            "inode": [
                "An inode is a unique identifier for a file on the filesystem. Each file has exactly one inode number.",
                "Inodes store file metadata like size, permissions, and ownership. Hard links share the same inode.",
            ],
            "how do i": [
                "I can help! Be more specific about what you'd like to do with your files.",
                "Try right-clicking files for options, or use the toolbar buttons for navigation.",
            ],
            "default": [
                "That's interesting! I'm here to help with file operations and system concepts. What would you like to know?",
                "I can help with file management and filesystem concepts. What's your question?",
                "Feel free to ask about files, permissions, links, or how to navigate your system!",
            ]
        }
    
    def get_response(self, user_input: str) -> str:
        """Generate a response based on user input"""
        user_input = user_input.lower().strip()
        
        # Check for keyword matches
        for keyword, responses in self.responses.items():
            if keyword != "default" and keyword in user_input:
                return random.choice(responses)
        
        # Default response
        return random.choice(self.responses["default"])


class ChatbotSettingsDialog(QDialog):
    """Settings dialog for chatbot configuration"""
    
    def __init__(self, settings: ChatbotSettings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️  Chatbot Settings")
        self.setGeometry(200, 200, 440, 360)
        self.settings = settings
        self.setup_ui()
    
    def setup_ui(self):
        """Setup settings dialog UI"""
        layout = QFormLayout(self)
        
        # Use LLM Backend
        self.use_llm_checkbox = QCheckBox("Use LLM-powered Backend")
        self.use_llm_checkbox.setChecked(self.settings.get("use_llm_backend", True))
        layout.addRow(self.use_llm_checkbox)
        
        # LLM Provider selection
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["ollama", "openai", "anthropic", "huggingface"])
        self.provider_combo.setCurrentText(self.settings.get("llm_provider", "ollama"))
        layout.addRow("LLM Provider:", self.provider_combo)
        
        # Ollama Model
        self.ollama_model_input = QLineEdit()
        self.ollama_model_input.setText(self.settings.get("ollama_model", "smollm"))
        self.ollama_model_input.setPlaceholderText("e.g., smollm, mistral, neural-chat")
        layout.addRow("Ollama Model:", self.ollama_model_input)
        
        # API Key (for cloud providers)
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key (optional)...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(self.settings.get("api_key", ""))
        layout.addRow("API Key:", self.api_key_input)
        
        # Model selection
        self.model_input = QLineEdit()
        self.model_input.setText(self.settings.get("model", "gpt-4o-mini"))
        layout.addRow("Cloud Model:", self.model_input)
        
        # Temperature
        self.temperature_input = QSpinBox()
        self.temperature_input.setMinimum(0)
        self.temperature_input.setMaximum(100)
        self.temperature_input.setValue(int(self.settings.get("temperature", 0.7) * 100))
        self.temperature_input.setSuffix("%")
        layout.addRow("Temperature (Creativity):", self.temperature_input)
        
        # Max history
        self.max_history_input = QSpinBox()
        self.max_history_input.setMinimum(5)
        self.max_history_input.setMaximum(100)
        self.max_history_input.setValue(self.settings.get("max_history", 20))
        layout.addRow("Max Chat History:", self.max_history_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        save_button = QPushButton("  Save  ")
        save_button.setObjectName("accentButton")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("  Cancel  ")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addRow(button_layout)
    
    def save_settings(self):
        """Save settings and close dialog"""
        settings_dict = {
            "api_key": self.api_key_input.text().strip(),
            "model": self.model_input.text().strip(),
            "temperature": self.temperature_input.value() / 100,
            "use_llm_backend": self.use_llm_checkbox.isChecked(),
            "max_history": self.max_history_input.value(),
            "llm_provider": self.provider_combo.currentText().strip(),
            "ollama_model": self.ollama_model_input.text().strip()
        }
        
        if self.settings.save_settings(settings_dict):
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings.")


class ChatbotWidget(QWidget):
    """ChatBot UI Widget with LLM Integration"""
    
    # Signal to notify parent of current directory
    current_directory_changed = pyqtSignal(str)
    # Signal to notify parent of LLM search results
    search_results_ready = pyqtSignal(list)
    # RAG signals for preview panel
    files_retrieved = pyqtSignal(list)        # list of file dicts
    folder_stats_ready = pyqtSignal(dict)     # folder statistics
    file_properties_ready = pyqtSignal(dict)  # single-file properties
    # Navigation signal — tells GUI to open a directory
    navigate_to_dir = pyqtSignal(str)
    
    def __init__(self, fs_abstraction: Optional[FileSystemAbstraction] = None):
        super().__init__()
        self.chatbot = Chatbot()
        self.settings = ChatbotSettings()
        self.signals = ChatbotSignals()
        self.fs_abstraction = fs_abstraction or FileSystemAbstraction()
        self.current_directory = self.fs_abstraction.home_dir
        
        # Standalone RAG engine (works even without LLM)
        self.rag_engine = RAGEngine(self.fs_abstraction)
        
        # Activity history — tracks last opened files and navigated folders
        self.activity_history = []
        
        # Conversation context — tracks chat history for follow-up queries
        self.chat_history = []  # list of {"role": "user"|"assistant", "text": ..., "intent": ..., "query_used": ...}
        
        # Initialize LLM backend if available and enabled
        self.llm_manager: Optional[LLMIntegrationManager] = None
        self.use_llm = self.settings.get("use_llm_backend", True)
        self._init_llm_backend()
        
        # Keep track of active background threads to prevent garbage collection crashes
        self._active_workers = []
        
        self.setup_ui()
    
    def _init_llm_backend(self):
        """Initialize LLM backend based on settings"""
        try:
            if not self.use_llm:
                return
            
            provider_name = self.settings.get("llm_provider", "ollama").lower()
            provider_map = {
                "ollama": LLMProvider.OLLAMA,
                "openai": LLMProvider.OPENAI,
                "anthropic": LLMProvider.ANTHROPIC,
                "huggingface": LLMProvider.HUGGINGFACE
            }
            
            provider = provider_map.get(provider_name, LLMProvider.OLLAMA)

            if provider == LLMProvider.OLLAMA:
                model_name = self.settings.get("ollama_model", "smollm")
            else:
                model_name = self.settings.get("model", "gpt-4o-mini")
            
            self.llm_manager = LLMIntegrationManager(
                fs_abstraction=self.fs_abstraction,
                provider=provider,
                api_key=self.settings.get("api_key"),
                model_name=model_name
            )
        except Exception as e:
            print(f"Warning: Could not initialize LLM backend: {e}")
            self.llm_manager = None
    
    def set_current_directory(self, directory: str):
        """Set current directory for file system context"""
        self.current_directory = directory
        self.rag_engine.invalidate_cache()
        self.current_directory_changed.emit(directory)
        # Track folder navigation
        self.record_activity("folder", directory)
    
    def record_activity(self, activity_type: str, path: str):
        """Record a file/folder activity for 'last worked with' queries"""
        import os
        entry = {
            "type": activity_type,
            "path": path,
            "name": os.path.basename(path) or path,
        }
        self.activity_history.append(entry)
        # Keep last 50 entries
        if len(self.activity_history) > 50:
            self.activity_history = self.activity_history[-50:]
    
    def setup_ui(self):
        """Setup chatbot UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Title with settings button
        title_layout = QHBoxLayout()
        title_layout.setSpacing(6)
        title = QLabel("💬 Assistant")
        title.setObjectName("sectionTitle")
        title_layout.addWidget(title)
        title_layout.addStretch()
        
        # Settings button
        settings_button = QPushButton("⚙️")
        settings_button.setFixedSize(32, 32)
        settings_button.setToolTip("Chatbot Settings")
        settings_button.clicked.connect(self.show_settings)
        title_layout.addWidget(settings_button)
        
        layout.addLayout(title_layout)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Segoe UI", 10))
        
        # Initial greeting
        self._append_message("Assistant", "Hello! I'm AIFE's assistant. How can I help?")
        
        layout.addWidget(self.chat_display, 1)  # stretch factor 1 → fills all space
        
        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me anything about files...")
        self.input_field.returnPressed.connect(self.on_send_message)
        input_layout.addWidget(self.input_field)
        
        send_button = QPushButton("Send")
        send_button.setObjectName("accentButton")
        send_button.setFixedWidth(64)
        send_button.clicked.connect(self.on_send_message)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
    
    def _start_llm_worker(self, query: str, is_retry: bool = False, is_final: bool = False):
        """Helper to start an LLM worker thread safely"""
        worker = LLMWorker(
            self.llm_manager, query, self.current_directory, 
            is_retry=is_retry, is_final_summary=is_final
        )
        # Prevent garbage collection of active thread
        self._active_workers.append(worker)
        
        worker.finished.connect(self._on_llm_response)
        worker.error.connect(self._on_llm_error)
        
        # Cleanup when done
        worker.finished.connect(lambda: self._cleanup_worker(worker))
        worker.error.connect(lambda: self._cleanup_worker(worker))
        
        worker.start()
        return worker

    def _cleanup_worker(self, worker):
        """Remove worker from tracking list and allow it to be destroyed"""
        if worker in self._active_workers:
            self._active_workers.remove(worker)
            worker.deleteLater()

    def on_send_message(self):
        """Handle message send with LLM backend if available"""
        user_message = self.input_field.text().strip()
        if not user_message:
            return
        
        # Display user message
        self._append_message("You", user_message)
        
        # Track in chat history
        self.chat_history.append({"role": "user", "text": user_message, "intent": None, "query_used": None})
        if len(self.chat_history) > 30:
            self.chat_history = self.chat_history[-30:]
        
        # Clear input immediately
        self.input_field.clear()
        
        # Handle folder-open/navigate locally — skip LLM for navigation commands
        q = user_message.lower().strip()
        open_kws = ['open ', 'go to ', 'navigate to ', 'cd ', 'take me to ', 'switch to ']
        if any(q.startswith(kw) for kw in open_kws):
            self._handle_open_folder(user_message)
            self.input_field.setFocus()
            return
        
        # LLM handles all retrieval, counts, properties, general chat
        if self.llm_manager and self.use_llm:
            self.input_field.setEnabled(False)
            self._append_message("System", "⏳ Thinking...")
            self._start_llm_worker(user_message)
        else:
            # No LLM fallback
            answered = self._process_rag_standalone(user_message)
            if not answered:
                rule_response = self.chatbot.get_response(user_message)
                self._append_message("Assistant", rule_response)
            self.input_field.setFocus()
    
    def _on_llm_response(self, response_data: dict):
        """Handle LLM response from background thread"""
        self.input_field.setEnabled(True)
        
        response_text = (response_data.get("response") or "").strip()
        
        # Detect hard API / connection errors — retrying won't help
        ERROR_PREFIXES = [
            "error calling", "error from ollama", "error calling openai",
            "error calling anthropic", "error calling hugging",
            "openai client not initialized", "ollama is not available",
            "llm provider not configured",
        ]
        is_api_error = any(response_text.lower().startswith(p) for p in ERROR_PREFIXES)
        
        # Detect soft refusals where the LLM says it lacks context
        NO_CONTEXT_PHRASES = [
            "i don't have enough context",
            "i don't have context",
            "no context",
            "i can't answer",
            "cannot answer",
            "i don't have access",
            "i'm unable to",
            "unable to provide",
            "try being more specific",
        ]
        is_refusal = (not is_api_error) and any(p in response_text.lower() for p in NO_CONTEXT_PHRASES)
        is_retry = response_data.get("is_retry", False)
        
        if is_api_error:
            # API error — show it directly, don't retry
            self._append_message("System", f"\u26a0\ufe0f {response_text}")
            self.input_field.setFocus()
            return
        
        if response_text and not is_refusal:
            # Check if the LLM returned a command for user approval
            cmd_result = self._extract_command(response_text)
            if cmd_result:
                explanation, command = cmd_result
                self._show_command_approval(explanation, command)
            else:
                self._append_message("Assistant", response_text)
        elif not is_retry:
            original_query = response_data.get("_original_query", "")
            import os

            # Only trigger the RAG→LLM retry flow for summarise / directory-analysis queries
            if original_query and self._is_summarise_query(original_query) and os.path.isdir(self.current_directory):
                self._append_message("System", "⏳ Gathering file details via RAG and retrying AI...")
                rag_summary = self._build_rag_enriched_context(self.current_directory)
                dir_name = os.path.basename(self.current_directory) or self.current_directory
                forced_query = (
                    f"Here is a detailed summary of the folder '{dir_name}' ({self.current_directory}):\n"
                    f"{rag_summary}\n\n"
                    f"The user asked: '{original_query}'\n"
                    f"Using ONLY the information above, provide a clear explanation of what this directory "
                    f"is about and what each file/folder likely contains or does. "
                    f"Do NOT say you lack context — the summary above is all you need."
                )
                self.input_field.setEnabled(False)
                self._start_llm_worker(forced_query, is_retry=True)
                return
            else:
                # Non-summarise query failed — simple fallback, no directory analysis
                self._append_message("Assistant",
                    response_text if response_text else "I don't have enough information to answer that. Try rephrasing your question.")
        elif not response_data.get("is_final_summary", False):
            # Second attempt (summarise retry) also failed — try once more
            import os
            if os.path.isdir(self.current_directory):
                self._append_message("System", "⏳ Final AI summarization with full file details...")
                rag_summary = self._build_rag_enriched_context(self.current_directory)
                dir_name = os.path.basename(self.current_directory) or self.current_directory
                final_query = (
                    f"Folder: {dir_name}\n"
                    f"{rag_summary}\n\n"
                    f"What is this folder about? For each item listed, say what it likely is."
                )
                self.input_field.setEnabled(False)
                self._start_llm_worker(final_query, is_retry=True, is_final=True)
            else:
                self._append_message("Assistant", "I couldn't analyze this folder. Try checking the directory path.")
        else:
            # All LLM attempts exhausted — show the RAG summary as formatted HTML
            import os
            if os.path.isdir(self.current_directory):
                html_summary = self._build_rag_display_html(self.current_directory)
                self._append_message("Assistant", html_summary, html=True)
            else:
                self._append_message("Assistant", "Final attempt failed. Please try a different query.")
        
        # Populate the file list with paths the LLM mentioned in its response
        matched_paths = response_data.get("matched_files") or []
        if matched_paths:
            import os, stat as stat_mod
            file_dicts = []
            for p in matched_paths:
                try:
                    st = os.stat(p)
                    is_dir = os.path.isdir(p)
                    size = st.st_size
                    from datetime import datetime
                    mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
                    ext = "" if is_dir else os.path.splitext(p)[1].lower()
                    file_dicts.append({
                        "path": p,
                        "name": os.path.basename(p),
                        "extension": ext,
                        "size": size,
                        "readable_size": self.rag_engine._format_bytes(size),
                        "is_dir": is_dir,
                        "is_symlink": os.path.islink(p),
                        "modified": mtime,
                        "snippet": "",
                        "permissions": oct(stat_mod.S_IMODE(st.st_mode))[2:],
                    })
                except OSError:
                    continue
            if file_dicts:
                self.files_retrieved.emit(file_dicts)
                self._append_message("System", f"Showing {len(file_dicts)} item(s) in the file list.")
        
        # Show suggested actions if any
        if response_data.get("suggested_actions"):
            actions_text = "\n📌 Suggested actions: " + ", ".join(response_data["suggested_actions"])
            self._append_message("System", actions_text)
        
        self.input_field.setFocus()
    
    def _on_llm_error(self, error_msg: str):
        """Handle LLM error — fall back to rule-based chatbot + standalone RAG"""
        self.input_field.setEnabled(True)
        self._append_message("System", f"LLM unavailable, using local analysis.")
        # Try to get the original query from the worker
        original_query = getattr(self._llm_worker, 'user_message', '') if hasattr(self, '_llm_worker') else ''
        if original_query:
            # Give a rule-based response
            response = self.chatbot.get_response(original_query)
            self._append_message("Assistant", response)
            # Process RAG independently
            self._process_rag_standalone(original_query)
        self.input_field.setFocus()
    
    def _process_rag_standalone(self, user_message: str) -> bool:
        """
        Process RAG independently of the LLM.
        Detects intent, retrieves files, computes stats, and emits signals.
        Uses conversation history to resolve follow-up queries.
        Returns True if a meaningful answer was given.
        """
        if not user_message:
            return False
        
        try:
            # Check for "last file/folder" queries first
            q = user_message.lower()
            if any(kw in q for kw in ['last file', 'last folder', 'last worked', 'recently', 'recent file', 'recent folder', 'previous file', 'previous folder', 'what was i']):
                return self._handle_activity_query(q)
            
            # Check for open/navigate intent
            open_kws = ['open ', 'go to ', 'navigate to ', 'cd ', 'take me to ', 'show me ', 'switch to ']
            if any(q.startswith(kw) for kw in open_kws) or re.search(r'open\s+(?:the\s+)?\w', q):
                return self._handle_open_folder(user_message)
            
            # Resolve follow-ups using conversation context
            resolved_message = self._resolve_followup(user_message)
            
            intent = self.rag_engine.detect_intent(resolved_message)
            
            if intent in ("retrieve", "list_by_type", "preview"):
                # Try local directory first
                results = self.rag_engine.retrieve(resolved_message, self.current_directory, top_k=5)
                scope = "current folder"
                
                if not results:
                    # Fall back to global home-directory search
                    self._append_message("System", "🔍 Not found locally — searching everywhere...")
                    results = self.rag_engine.global_search(resolved_message, top_k=8)
                    scope = "home directory"
                
                if results:
                    file_dicts = [r.to_dict() for r in results]
                    for fd, r in zip(file_dicts, results):
                        fd["is_dir"] = r.is_dir
                        fd["is_symlink"] = r.is_symlink
                        fd["readable_size"] = self.rag_engine._format_bytes(r.size)
                    self.files_retrieved.emit(file_dicts)
                    
                    names = ", ".join(r.name for r in results[:3])
                    extra = f" and {len(results) - 3} more" if len(results) > 3 else ""
                    response = f"Found {len(results)} file(s) in {scope}: {names}{extra}. Showing in the file list."
                    self._append_message("Assistant", response)
                    self._track_assistant_response(response, intent, resolved_message)
                    return True
                else:
                    response = f"No matching files found anywhere in your home directory."
                    self._append_message("Assistant", response)
                    self._track_assistant_response(response, intent, resolved_message)
                    return True

            elif intent == "count":
                # Check if the user mentions a specific folder by name
                folder_name = self.rag_engine.extract_folder_from_query(resolved_message)
                target_dir = self.current_directory
                display_name = os.path.basename(self.current_directory) or self.current_directory
                
                if folder_name:
                    found_path = self.rag_engine.find_folder(folder_name, self.current_directory)
                    if found_path:
                        target_dir = found_path
                        display_name = folder_name
                    else:
                        self._append_message("Assistant", f"Couldn't find a folder named '{folder_name}'. Showing stats for the current folder instead.")
                
                stats = self.rag_engine.get_folder_stats(target_dir)

                parts = [f"In **{display_name}** ({target_dir}):"]
                parts.append(f"  • {stats.total_files} file(s)")
                parts.append(f"  • {stats.total_folders} folder(s)")
                if stats.total_symlinks:
                    parts.append(f"  • {stats.total_symlinks} symlink(s)")
                parts.append(f"  • Total size: {stats.readable_size}")
                if stats.hidden_count:
                    parts.append(f"  • {stats.hidden_count} hidden item(s)")

                # Type breakdown
                if stats.type_distribution:
                    top = list(stats.type_distribution.items())[:5]
                    type_str = ", ".join(f"{ext}: {cnt}" for ext, cnt in top)
                    parts.append(f"  • Types: {type_str}")

                # Notable files
                if stats.largest_file:
                    parts.append(f"  • Largest: {stats.largest_file['name']} ({stats.largest_file['size']})")
                if stats.newest_file:
                    parts.append(f"  • Newest: {stats.newest_file['name']} ({stats.newest_file['modified']})")

                response = "\n".join(parts)
                self._append_message("Assistant", response)
                self._track_assistant_response(response, intent, resolved_message)
                return True

            elif intent == "properties":
                filename = self.rag_engine.extract_filename_from_query(resolved_message)
                if filename:
                    idx = self.rag_engine.index_directory(self.current_directory)
                    match = next((f for f in idx if f.name.lower() == filename.lower()), None)
                    if match:
                        props = self.rag_engine.get_file_properties(match.path)
                        parts = [f"Properties for **{props.get('name', filename)}**:"]
                        parts.append(f"  • Type: {props.get('type')}")
                        parts.append(f"  • Size: {props.get('readable_size')}")
                        parts.append(f"  • Permissions: {props.get('permissions_octal')} ({props.get('permissions_string')})")
                        parts.append(f"  • Inode: {props.get('inode')}")
                        parts.append(f"  • Modified: {props.get('modified')}")
                        parts.append(f"  • Path: {props.get('path')}")
                        response = "\n".join(parts)
                        self._append_message("Assistant", response)
                        self._track_assistant_response(response, intent, resolved_message)
                        return True
                    else:
                        response = f"Couldn't find '{filename}' in the current folder."
                        self._append_message("Assistant", response)
                        self._track_assistant_response(response, intent, resolved_message)
                        return True

            return False
        except Exception as e:
            print(f"RAG standalone error: {e}")
            return False
    
    def _resolve_followup(self, user_message: str) -> str:
        """
        Resolve follow-up queries using conversation history.
        
        If the current message looks like a follow-up (short, has pronouns,
        ambiguous intent), enrich it with context from previous turns.
        
        Examples:
          - Previous: "how many files?" → Current: "what about python?" → "find python files"
          - Previous: "find text files" → Current: "and images?" → "find image files"
          - Previous: "show properties of main.py" → Current: "what about test.py?" → "show properties of test.py"
        """
        import re
        q = user_message.lower().strip()
        
        # If the query is self-contained (long enough, has clear intent), no resolution needed
        intent = self.rag_engine.detect_intent(user_message)
        if intent != "general" and len(q.split()) > 3:
            return user_message
        
        # Look for follow-up indicators
        followup_indicators = [
            'what about', 'how about', 'and ', 'also ', 'same for',
            'what of', 'now ', 'then ', 'okay ', 'ok ',
            'those', 'them', 'these', 'that', 'it', 'its',
        ]
        is_followup = (
            len(q.split()) <= 5
            or any(q.startswith(ind) for ind in followup_indicators)
            or q.endswith('?') and len(q.split()) <= 4
        )
        
        if not is_followup or not self.chat_history:
            return user_message
        
        # Find the last assistant response with a known intent
        prev_intents = [
            h for h in reversed(self.chat_history)
            if h["role"] == "assistant" and h.get("intent")
        ]
        
        if not prev_intents:
            return user_message
        
        prev = prev_intents[0]
        prev_intent = prev.get("intent", "")
        prev_query = prev.get("query_used", "")
        
        # Strip follow-up prefixes to extract the core new token
        core = q
        for prefix in followup_indicators:
            if core.startswith(prefix):
                core = core[len(prefix):].strip()
                break
        # Remove trailing ?
        core = core.rstrip('?').strip()
        
        if not core:
            return user_message
        
        # Remove trailing 'files'/'file' to avoid duplication like 'find text files files'
        core_stripped = re.sub(r'\s+files?\s*$', '', core).strip()
        if core_stripped:
            core = core_stripped
        
        # Rebuild the query based on previous intent
        if prev_intent in ("count",):
            # "what about python?" after count → search for python files
            return f"find {core} files"
        elif prev_intent in ("retrieve", "list_by_type"):
            return f"find {core} files"
        elif prev_intent in ("properties",):
            return f"show properties of {core}"
        elif prev_intent in ("preview",):
            return f"preview {core}"
        else:
            # General follow-up: just append to give more context
            return f"{core} {prev_query}" if prev_query else user_message
    
    def _track_assistant_response(self, response: str, intent: str, query_used: str):
        """Record an assistant response in chat history for follow-up resolution."""
        self.chat_history.append({
            "role": "assistant",
            "text": response,
            "intent": intent,
            "query_used": query_used,
        })
        if len(self.chat_history) > 30:
            self.chat_history = self.chat_history[-30:]
    
    def _handle_open_folder(self, user_message: str) -> bool:
        """
        Detect 'open X / go to X / navigate to X' intent and navigate to that folder.
        Searches common locations if not found in the current directory.
        """
        q = user_message.strip()
        
        # Extract the folder name — strip leading verb phrases
        verb_patterns = [
            r'^(?:open|go to|navigate to|cd|take me to|switch to|show me)\s+(?:the\s+)?',
        ]
        folder_name = q
        for pat in verb_patterns:
            folder_name = re.sub(pat, '', folder_name, flags=re.IGNORECASE).strip()
        folder_name = folder_name.strip('"\' ')
        
        if not folder_name:
            return False
        
        # Handle special aliases
        home = os.path.expanduser("~")
        aliases = {
            "home": home,
            "~": home,
            "desktop": os.path.join(home, "Desktop"),
            "documents": os.path.join(home, "Documents"),
            "downloads": os.path.join(home, "Downloads"),
            "root": "/",
        }
        
        target = aliases.get(folder_name.lower())
        
        if not target:
            # Try to find the folder by name
            target = self.rag_engine.find_folder(folder_name, self.current_directory)
        
        if target and os.path.isdir(target):
            self._append_message("Assistant", f"Opening **{folder_name}** ({target})...")
            self.navigate_to_dir.emit(target)
            return True
        else:
            self._append_message("Assistant", f"Couldn't find a folder named '{folder_name}'. Try checking the name or navigating manually.")
            return True
    
    def _handle_activity_query(self, query: str) -> bool:
        """Answer questions about the last file/folder the user worked with."""
        if not self.activity_history:
            resp = "You haven't opened any files or navigated to any folders yet in this session."
            self._append_message("Assistant", resp)
            self._track_assistant_response(resp, "activity", query)
            return True
        
        # Determine what they're asking about
        want_file = any(kw in query for kw in ['file', 'document'])
        want_folder = any(kw in query for kw in ['folder', 'directory', 'dir'])
        
        if want_file:
            # Find last file entry
            file_entries = [e for e in self.activity_history if e['type'] == 'file']
            if file_entries:
                last = file_entries[-1]
                self._append_message("Assistant", f"The last file you opened was **{last['name']}** ({last['path']}).")
            else:
                self._append_message("Assistant", "You haven't opened any files yet in this session.")
            return True
        
        if want_folder:
            # Find last folder entry
            folder_entries = [e for e in self.activity_history if e['type'] == 'folder']
            if folder_entries:
                last = folder_entries[-1]
                self._append_message("Assistant", f"The last folder you visited was **{last['name']}** ({last['path']}).")
            else:
                self._append_message("Assistant", "You haven't navigated to any folders yet.")
            return True
        
        # General "what was I last working with?"
        last = self.activity_history[-1]
        kind = "file" if last['type'] == 'file' else "folder"
        self._append_message("Assistant", f"The last {kind} you worked with was **{last['name']}** ({last['path']}).")
        
        # Also show a short recent history
        if len(self.activity_history) > 1:
            recent = self.activity_history[-5:]
            recent.reverse()
            history_lines = []
            for i, entry in enumerate(recent, 1):
                icon = "📄" if entry['type'] == 'file' else "📁"
                history_lines.append(f"  {i}. {icon} {entry['name']}")
            self._append_message("Assistant", "Recent activity:\n" + "\n".join(history_lines))
        return True
    
    def _append_message(self, sender: str, message: str, html: bool = False):
        """Append message to chat display.
        
        Args:
            sender: 'You', 'System', or 'Assistant'
            message: Plain text or HTML content
            html: If True, message is inserted as raw HTML
        """
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)

        if html:
            # Render formatted HTML block
            if sender == "You":
                prefix = '<span style="color:#4f46e5;font-weight:bold;">You:</span><br>'
            elif sender == "System":
                prefix = ''
            else:
                prefix = '<span style="color:#059669;font-weight:bold;">Assistant:</span><br>'
            self.chat_display.append('')  # spacing
            self.chat_display.insertHtml(prefix + message + '<br>')
            self.chat_display.append('')  # spacing after
        else:
            # Format message with light-theme-friendly colors
            if sender == "You":
                self.chat_display.setTextColor(QColor(79, 70, 229))   # Indigo
                self.chat_display.append(f"You: {message}")
            elif sender == "System":
                self.chat_display.setTextColor(QColor(100, 116, 139))  # Slate
                self.chat_display.append(message)
            else:
                self.chat_display.setTextColor(QColor(5, 150, 105))   # Emerald
                self.chat_display.append(f"Assistant: {self._format_response_text(message)}")
        
        self.chat_display.setTextColor(QColor(30, 41, 59))  # Default dark text
        self.chat_display.append("")

    @staticmethod
    def _format_response_text(text: str) -> str:
        """Light formatting for plain-text LLM responses:
        convert **bold** and bullet lines for readability."""
        import re
        # Convert **bold** markers to just the text (QTextEdit plain mode)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        return text

    # ── Command extraction & execution ──────────────────────────

    _CMD_PATTERN = re.compile(r'\[CMD\](.*?)\[/CMD\]', re.DOTALL)

    def _extract_command(self, text: str):
        """Return (explanation, command) if the response contains a [CMD] block, else None."""
        m = self._CMD_PATTERN.search(text)
        if not m:
            return None
        cmd = m.group(1).strip()
        explanation = self._CMD_PATTERN.sub('', text).strip()
        return explanation, cmd

    def _show_command_approval(self, explanation: str, command: str):
        """Display the command in the chat with Approve / Reject buttons."""
        # Show the explanation text
        if explanation:
            self._append_message("Assistant", explanation)

        # Build a styled HTML block for the command
        cmd_html = (
            '<div style="background:#f1f5f9; border:1px solid #e2e8f0; border-left:3px solid #6366f1;'
            ' border-radius:6px; padding:8px 12px; margin:4px 0; font-family:monospace; font-size:12px;'
            f' color:#1e293b;">{command}</div>'
        )
        self._append_message("System", cmd_html, html=True)

        # Create approve / reject buttons below the chat
        btn_frame = QFrame()
        btn_frame.setStyleSheet("background:transparent; border:none;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 2, 0, 2)
        btn_layout.setSpacing(8)

        approve_btn = QPushButton("✅ Run")
        approve_btn.setStyleSheet(
            "background:#059669; color:#fff; border:none; border-radius:6px;"
            " padding:5px 18px; font-weight:600; font-size:12px;"
        )
        reject_btn = QPushButton("❌ Cancel")
        reject_btn.setStyleSheet(
            "background:#ef4444; color:#fff; border:none; border-radius:6px;"
            " padding:5px 18px; font-weight:600; font-size:12px;"
        )

        btn_layout.addStretch()
        btn_layout.addWidget(approve_btn)
        btn_layout.addWidget(reject_btn)
        btn_layout.addStretch()

        # Insert the button frame into the chat layout (above the input bar)
        parent_layout = self.layout()
        # Insert just before the input row (last item in layout)
        parent_layout.insertWidget(parent_layout.count() - 1, btn_frame)

        def on_approve():
            btn_frame.setParent(None)
            btn_frame.deleteLater()
            self._execute_command(command)

        def on_reject():
            btn_frame.setParent(None)
            btn_frame.deleteLater()
            self._append_message("System", "Command cancelled.")

        approve_btn.clicked.connect(on_approve)
        reject_btn.clicked.connect(on_reject)

    def _execute_command(self, command: str):
        """Execute an approved shell command and report the result."""
        import subprocess
        self._append_message("System", "⏳ Running command...")
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=30, cwd=self.current_directory
            )
            if result.returncode == 0:
                output = result.stdout.strip()
                msg = "✅ Command executed successfully."
                if output:
                    msg += f"\n{output}"
                self._append_message("System", msg)
            else:
                err = result.stderr.strip() or result.stdout.strip()
                self._append_message("System", f"⚠️ Command failed (exit {result.returncode}):\n{err}")
        except subprocess.TimeoutExpired:
            self._append_message("System", "⚠️ Command timed out after 30 seconds.")
        except Exception as e:
            self._append_message("System", f"⚠️ Error running command: {e}")

        # Refresh the file explorer view
        self.navigate_to_dir.emit(self.current_directory)

    # ── Summarise detection ─────────────────────────────────────

    @staticmethod
    def _is_summarise_query(query: str) -> bool:
        """Return True only when the user is explicitly asking to summarise / analyse a folder."""
        q = query.lower()
        phrases = [
            'summarize', 'summarise', 'summary',
            'what is this folder', 'what is this directory',
            "what's this folder", "what's this directory",
            'what is in this', "what's in this",
            'tell me about this folder', 'tell me about this directory',
            'describe this folder', 'describe this directory',
            'analyze this', 'analyse this',
            'what does this folder', 'what does this directory',
            'about this folder', 'about this directory',
            'what are the files', 'what are these files',
            'what kind of project', 'what type of project',
            'what project is this', 'purpose of this',
            'overview of this', 'explain this folder',
            'what could these be',
        ]
        return any(phrase in q for phrase in phrases)

    def _build_rag_display_html(self, directory: str) -> str:
        """
        Build a nicely formatted HTML summary of a directory for display
        in the chat widget. Uses RAG engine data.
        """
        import os
        dir_name = os.path.basename(directory) or directory

        # Gather data
        try:
            index = self.rag_engine.index_directory(directory)
        except Exception:
            index = []

        try:
            stats = self.rag_engine.get_folder_stats(directory)
        except Exception:
            stats = None

        dirs_list = [f for f in index if f.is_dir]
        files_list = [f for f in index if not f.is_dir]

        html = []
        # Header
        html.append(
            f'<div style="margin:6px 0;">'
            f'<span style="color:#4f46e5;font-size:14px;font-weight:bold;">📂 {dir_name}</span>'
            f'</div>'
        )

        # Quick stats bar
        if stats:
            stat_items = []
            stat_items.append(f'<b>{stats.total_files}</b> files')
            stat_items.append(f'<b>{stats.total_folders}</b> folders')
            stat_items.append(f'<b>{stats.readable_size}</b> total')
            if stats.hidden_count:
                stat_items.append(f'{stats.hidden_count} hidden')
            html.append(
                f'<div style="color:#64748b;font-size:11px;margin:2px 0 8px 0;">'
                f'{"  •  ".join(stat_items)}'
                f'</div>'
            )

        # Folders section
        if dirs_list:
            html.append('<div style="color:#b45309;font-weight:bold;margin:6px 0 3px 0;">Folders</div>')
            html.append('<table cellpadding="2" cellspacing="0" style="margin-left:8px;">')
            for d in dirs_list:
                html.append(
                    f'<tr>'
                    f'<td style="color:#6366f1;">📁</td>'
                    f'<td style="color:#1e293b;">{d.name}</td>'
                    f'</tr>'
                )
            html.append('</table>')

        # Files section
        if files_list:
            html.append('<div style="color:#b45309;font-weight:bold;margin:8px 0 3px 0;">Files</div>')
            html.append('<table cellpadding="2" cellspacing="0" style="margin-left:8px;">')
            for f in files_list[:30]:
                ext_str = f.extension if f.extension else '—'
                size_str = self.rag_engine._format_bytes(f.size)
                snippet = ''
                if f.snippet:
                    snippet_text = f.snippet[:120].replace(chr(10), ' ').replace('<', '&lt;').replace('>', '&gt;')
                    snippet = f'<div style="color:#94a3b8;font-size:10px;margin:1px 0 3px 0;">{snippet_text}…</div>'
                html.append(
                    f'<tr>'
                    f'<td style="color:#6366f1;vertical-align:top;">📄</td>'
                    f'<td>'
                    f'<span style="color:#1e293b;">{f.name}</span> '
                    f'<span style="color:#94a3b8;font-size:10px;">{ext_str} · {size_str}</span>'
                    f'{snippet}'
                    f'</td>'
                    f'</tr>'
                )
            html.append('</table>')

        # Type distribution
        if stats and stats.type_distribution:
            top_types = list(stats.type_distribution.items())[:6]
            type_chips = []
            for ext, cnt in top_types:
                type_chips.append(
                    f'<span style="background:#e2e8f0;color:#334155;padding:1px 6px;'
                    f'border-radius:3px;font-size:10px;margin-right:4px;">{ext}: {cnt}</span>'
                )
            html.append(
                f'<div style="margin:8px 0 2px 0;">'
                f'<span style="color:#64748b;font-size:11px;">File types: </span>'
                f'{" ".join(type_chips)}'
                f'</div>'
            )

        # Notable files
        if stats:
            notes = []
            if stats.largest_file:
                notes.append(f'Largest: <b>{stats.largest_file["name"]}</b> ({stats.largest_file["size"]})')
            if stats.newest_file:
                notes.append(f'Newest: <b>{stats.newest_file["name"]}</b> ({stats.newest_file["modified"]})')
            if notes:
                html.append(
                    f'<div style="color:#64748b;font-size:11px;margin:4px 0;">'
                    f'{"  •  ".join(notes)}'
                    f'</div>'
                )

        # Note about AI
        html.append(
            '<div style="color:#94a3b8;font-size:10px;font-style:italic;margin-top:8px;">'
            '⚠ AI summary unavailable — showing indexed file data'
            '</div>'
        )

        return ''.join(html)

    def _build_rag_enriched_context(self, directory: str) -> str:
        """
        Use the RAG engine to build a rich text summary of a directory.
        Includes: file listing with types/sizes, folder stats, and
        content snippets for text files. This is sent to the LLM on retries.
        """
        import os
        parts = []
        dir_name = os.path.basename(directory) or directory

        # 1. Index the directory and build the file listing
        try:
            index = self.rag_engine.index_directory(directory)
        except Exception:
            index = []

        if index:
            dirs_list = [f for f in index if f.is_dir]
            files_list = [f for f in index if not f.is_dir]

            if dirs_list:
                folder_lines = []
                for d in dirs_list:
                    folder_lines.append(f"  📁 {d.name}")
                parts.append(f"Subfolders ({len(dirs_list)}):\n" + "\n".join(folder_lines))

            if files_list:
                file_lines = []
                for f in files_list[:30]:
                    ext_str = f.extension if f.extension else "(no ext)"
                    size_str = self.rag_engine._format_bytes(f.size)
                    snippet_preview = ""
                    if f.snippet:
                        snippet_preview = f" | Preview: {f.snippet[:200].replace(chr(10), ' ')}"
                    file_lines.append(f"  📄 {f.name} [{ext_str}, {size_str}]{snippet_preview}")
                parts.append(f"Files ({len(files_list)}):\n" + "\n".join(file_lines))
        else:
            # Fallback: raw os.listdir
            try:
                entries = sorted(os.listdir(directory))
                lines = []
                for entry in entries[:40]:
                    full = os.path.join(directory, entry)
                    icon = "📁" if os.path.isdir(full) else "📄"
                    lines.append(f"  {icon} {entry}")
                if lines:
                    parts.append("Directory listing:\n" + "\n".join(lines))
            except OSError:
                parts.append("(could not read directory)")

        # 2. Folder statistics from RAG
        try:
            stats = self.rag_engine.get_folder_stats(directory)
            stat_lines = [
                f"Total files: {stats.total_files}, Folders: {stats.total_folders}",
                f"Total size: {stats.readable_size}",
            ]
            if stats.total_symlinks:
                stat_lines.append(f"Symlinks: {stats.total_symlinks}")
            if stats.hidden_count:
                stat_lines.append(f"Hidden items: {stats.hidden_count}")
            if stats.type_distribution:
                top_types = list(stats.type_distribution.items())[:8]
                stat_lines.append("File types: " + ", ".join(f"{ext}: {cnt}" for ext, cnt in top_types))
            if stats.largest_file:
                stat_lines.append(f"Largest: {stats.largest_file['name']} ({stats.largest_file['size']})")
            if stats.newest_file:
                stat_lines.append(f"Newest: {stats.newest_file['name']} ({stats.newest_file['modified']})")
            parts.append("\nFolder statistics:\n  " + "\n  ".join(stat_lines))
        except Exception:
            pass

        return "\n".join(parts) if parts else f"(no files found in {dir_name})"

    def show_settings(self):
        """Show settings dialog"""
        dialog = ChatbotSettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            # Reinitialize LLM backend with new settings
            self.use_llm = self.settings.get("use_llm_backend", True)
            self._init_llm_backend()
            
            # Show confirmation
            status = "LLM backend enabled" if self.llm_manager else "Using rule-based chatbot"
            self._append_message("System", f"Settings updated. {status}")
