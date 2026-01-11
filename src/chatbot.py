"""
AIFE - Advanced Interactive File Explorer
Chatbot Module

A simple themed chatbot that provides helpful guidance and file system assistance.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QLabel, QScrollArea, QDialog, QFormLayout,
    QSpinBox, QCheckBox, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QColor, QTextCursor
import random
import json
import os


class ChatbotSignals(QObject):
    """Signals for chatbot"""
    response_generated = pyqtSignal(str)


class ChatbotSettings:
    """Manage chatbot settings"""
    
    CONFIG_FILE = os.path.expanduser("~/.aife_chatbot_config.json")
    
    DEFAULT_SETTINGS = {
        "api_key": "",
        "model": "gpt-3.5-turbo",
        "temperature": 0.7,
        "enable_ai": False,
        "max_history": 20
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
        self.setWindowTitle("Chatbot Settings")
        self.setGeometry(200, 200, 400, 300)
        self.settings = settings
        self.setup_ui()
    
    def setup_ui(self):
        """Setup settings dialog UI"""
        layout = QFormLayout(self)
        
        # API Key
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setText(self.settings.get("api_key", ""))
        layout.addRow("OpenAI API Key:", self.api_key_input)
        
        # Model selection
        self.model_input = QLineEdit()
        self.model_input.setText(self.settings.get("model", "gpt-3.5-turbo"))
        layout.addRow("Model:", self.model_input)
        
        # Temperature
        self.temperature_input = QSpinBox()
        self.temperature_input.setMinimum(0)
        self.temperature_input.setMaximum(100)
        self.temperature_input.setValue(int(self.settings.get("temperature", 0.7) * 100))
        self.temperature_input.setSuffix("%")
        layout.addRow("Temperature (Creativity):", self.temperature_input)
        
        # Enable AI
        self.enable_ai_checkbox = QCheckBox("Enable AI responses")
        self.enable_ai_checkbox.setChecked(self.settings.get("enable_ai", False))
        layout.addRow(self.enable_ai_checkbox)
        
        # Max history
        self.max_history_input = QSpinBox()
        self.max_history_input.setMinimum(5)
        self.max_history_input.setMaximum(100)
        self.max_history_input.setValue(self.settings.get("max_history", 20))
        layout.addRow("Max Chat History:", self.max_history_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addRow(button_layout)
    
    def save_settings(self):
        """Save settings and close dialog"""
        settings_dict = {
            "api_key": self.api_key_input.text(),
            "model": self.model_input.text(),
            "temperature": self.temperature_input.value() / 100,
            "enable_ai": self.enable_ai_checkbox.isChecked(),
            "max_history": self.max_history_input.value()
        }
        
        if self.settings.save_settings(settings_dict):
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Failed to save settings.")


class ChatbotWidget(QWidget):
    """ChatBot UI Widget"""
    
    def __init__(self):
        super().__init__()
        self.chatbot = Chatbot()
        self.settings = ChatbotSettings()
        self.signals = ChatbotSignals()
        self.setup_ui()
    
    def setup_ui(self):
        """Setup chatbot UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Title with settings button
        title_layout = QHBoxLayout()
        title = QLabel("💬 Assistant")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title.setFont(title_font)
        title_layout.addWidget(title)
        
        # Settings button
        settings_button = QPushButton("⚙️")
        settings_button.setMaximumWidth(35)
        settings_button.setToolTip("Chatbot Settings")
        settings_button.clicked.connect(self.show_settings)
        title_layout.addWidget(settings_button)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setFont(QFont("Courier", 8))
        self.chat_display.setMaximumHeight(500)
        
        # Initial greeting
        self._append_message("Assistant", "Hello! I'm AIFE's assistant. How can I help?")
        
        layout.addWidget(self.chat_display)
        
        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask me anything about files...")
        self.input_field.returnPressed.connect(self.on_send_message)
        input_layout.addWidget(self.input_field)
        
        send_button = QPushButton("Send")
        send_button.setMaximumWidth(60)
        send_button.clicked.connect(self.on_send_message)
        input_layout.addWidget(send_button)
        
        layout.addLayout(input_layout)
        layout.addStretch()
    
    def on_send_message(self):
        """Handle message send"""
        user_message = self.input_field.text().strip()
        if not user_message:
            return
        
        # Display user message
        self._append_message("You", user_message)
        
        # Get and display bot response
        response = self.chatbot.get_response(user_message)
        self._append_message("Assistant", response)
        
        # Clear input
        self.input_field.clear()
        self.input_field.setFocus()
    
    def _append_message(self, sender: str, message: str):
        """Append message to chat display"""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_display.setTextCursor(cursor)
        
        # Format message
        if sender == "You":
            self.chat_display.setTextColor(QColor(0, 100, 200))
            self.chat_display.append(f"You: {message}")
        else:
            self.chat_display.setTextColor(QColor(50, 150, 50))
            self.chat_display.append(f"Assistant: {message}")
        
        self.chat_display.setTextColor(QColor(0, 0, 0))
        self.chat_display.append("")
    
    def show_settings(self):
        """Show settings dialog"""
        dialog = ChatbotSettingsDialog(self.settings, self)
        dialog.exec_()
