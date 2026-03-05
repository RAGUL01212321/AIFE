"""
AIFE - Advanced Interactive File Explorer
Main PyQt5 GUI Application

Demonstrates: User Interface, Event Handling, File Operations Coordination
This is the presentation layer that provides the user interface and
coordinates user interactions with the file manager.
"""

import sys
import os
from typing import Optional, List
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QLabel, QPushButton, QLineEdit,
    QMessageBox, QMenu, QDialog, QInputDialog, QTreeWidget, QTreeWidgetItem,
    QSplitter, QHeaderView, QAbstractItemView, QTableWidget, QTableWidgetItem,
    QStatusBar, QToolBar, QComboBox, QProgressBar, QDockWidget
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor
import stat

from file_manager import FileManager, OperationResult, FileOperationType
from filesystem import FileNode, FileSystemAbstraction
from chatbot import ChatbotWidget


class SignalEmitter(QObject):
    """Signal emitter for file operations"""
    operation_completed = pyqtSignal(OperationResult)
    current_directory_changed = pyqtSignal(str)


class FileExplorerWindow(QMainWindow):
    """
    Main window for AIFE file explorer
    
    Components:
    - Navigation toolbar (up, home, back, forward buttons)
    - Location bar (current path display)
    - Directory tree (left panel)
    - File list (center panel)
    - Details panel (right panel)
    - Status bar (operations feedback)
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AIFE - Advanced Interactive File Explorer")
        self.setGeometry(100, 100, 1200, 700)
        
        # Initialize file manager
        self.file_manager = FileManager()
        
        # File system abstraction for RAG file lookups
        self.fs = FileSystemAbstraction()
        
        # Signals
        self.signals = SignalEmitter()
        self.signals.operation_completed.connect(self.on_operation_completed)
        
        # Register file manager callback
        self.file_manager.register_operation_callback(
            self.signals.operation_completed.emit
        )
        
        # Navigation history
        self.history_back = []
        self.history_forward = []
        
        # Setup UI
        self.setup_ui()
        
        # Load initial directory
        self.navigate_to(self.file_manager.get_home_directory())
    
    def setup_ui(self):
        """Setup user interface"""
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Toolbar
        self.setup_toolbar()
        
        # Location bar
        location_layout = QHBoxLayout()
        location_layout.setSpacing(8)
        loc_label = QLabel("  📍 Location")
        loc_label.setObjectName("sectionTitle")
        location_layout.addWidget(loc_label)
        self.location_input = QLineEdit()
        self.location_input.setReadOnly(True)
        self.location_input.setFont(QFont("JetBrains Mono", 11))
        location_layout.addWidget(self.location_input)
        self.go_button = QPushButton("Go")
        self.go_button.setObjectName("accentButton")
        self.go_button.setFixedWidth(60)
        self.go_button.clicked.connect(self.on_go_clicked)
        location_layout.addWidget(self.go_button)
        main_layout.addLayout(location_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Quick Access only
        qa_widget = QWidget()
        qa_layout = QVBoxLayout(qa_widget)
        qa_layout.setContentsMargins(4, 4, 4, 4)
        qa_layout.setSpacing(4)
        qa_label = QLabel("⚡ Quick Access")
        qa_label.setObjectName("sectionTitle")
        qa_layout.addWidget(qa_label)
        self.quick_access_tree = QTreeWidget()
        self.quick_access_tree.setHeaderHidden(True)
        self.quick_access_tree.itemDoubleClicked.connect(self.on_quick_access_clicked)
        self.quick_access_tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.quick_access_tree.setDefaultDropAction(Qt.MoveAction)
        qa_layout.addWidget(self.quick_access_tree)
        splitter.addWidget(qa_widget)
        
        # Center panel: File list
        center_layout = QVBoxLayout()
        center_layout.setContentsMargins(4, 4, 4, 4)
        ff_label = QLabel("📂 Files and Folders")
        ff_label.setObjectName("sectionTitle")
        center_layout.addWidget(ff_label)
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(5)
        self.file_list.setHorizontalHeaderLabels([
            "Name", "Type", "Size", "Modified", "Permissions"
        ])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_list.setAlternatingRowColors(True)
        self.file_list.setShowGrid(False)
        self.file_list.verticalHeader().setVisible(False)
        self.file_list.verticalHeader().setDefaultSectionSize(36)
        self.file_list.itemDoubleClicked.connect(self.on_file_opened)
        self.file_list.itemRightClicked = lambda item: self.show_context_menu(item)
        self.file_list.customContextMenuRequested.connect(self.on_context_menu_requested)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        center_layout.addWidget(self.file_list)
        center_widget = QWidget()
        center_widget.setLayout(center_layout)
        splitter.addWidget(center_widget)
        
        splitter.setSizes([200, 700])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter)
        
        # Chatbot as a draggable dock widget (right side, can be moved/floated/resized)
        self.chatbot = ChatbotWidget()
        self.chatbot.search_results_ready.connect(self.on_chatbot_search_results)
        self.chatbot.files_retrieved.connect(self._on_files_retrieved)
        self.chatbot.navigate_to_dir.connect(self.navigate_to)
        
        self.chat_dock = QDockWidget("💬 Assistant", self)
        self.chat_dock.setObjectName("chatDock")
        self.chat_dock.setWidget(self.chatbot)
        self.chat_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        self.chat_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable |
            QDockWidget.DockWidgetClosable
        )
        self.chat_dock.setMinimumWidth(280)
        self.addDockWidget(Qt.RightDockWidgetArea, self.chat_dock)
        # Give right dock the full vertical span (both corners)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def setup_toolbar(self):
        """Setup navigation toolbar"""
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)
        
        # Back button
        self.back_button = QPushButton("  ←  Back  ")
        self.back_button.setToolTip("Go back")
        self.back_button.clicked.connect(self.on_back_clicked)
        toolbar.addWidget(self.back_button)
        
        # Forward button
        self.forward_button = QPushButton("  Forward  →  ")
        self.forward_button.setToolTip("Go forward")
        self.forward_button.clicked.connect(self.on_forward_clicked)
        toolbar.addWidget(self.forward_button)
        
        # Up button
        self.up_button = QPushButton("  ⬆  Parent  ")
        self.up_button.setToolTip("Go to parent directory")
        self.up_button.clicked.connect(self.on_up_clicked)
        toolbar.addWidget(self.up_button)
        
        # Home button
        self.home_button = QPushButton("  🏠  Home  ")
        self.home_button.setToolTip("Go to home directory")
        self.home_button.clicked.connect(self.on_home_clicked)
        toolbar.addWidget(self.home_button)
        
        toolbar.addSeparator()
        
        # Refresh button
        self.refresh_button = QPushButton("  🔄  Refresh  ")
        self.refresh_button.setToolTip("Refresh current directory")
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        toolbar.addWidget(self.refresh_button)
    
    def navigate_to(self, path: str):
        """Navigate to a directory"""
        # Save to history
        current = self.file_manager.get_current_directory()
        if current and current != path:
            self.history_back.append(current)
            self.history_forward.clear()
        
        # Browse directory
        result = self.file_manager.browse_directory(path)
        
        if result.success:
            self.location_input.setText(path)
            self.populate_file_list(result.data)
            self.populate_quick_access()
            # Update chatbot context with current directory
            try:
                if hasattr(self, 'chatbot') and self.chatbot:
                    self.chatbot.set_current_directory(path)
            except Exception:
                pass
            self.statusBar().showMessage(result.message)
        else:
            QMessageBox.warning(self, "Error", result.message)
    
    def populate_file_list(self, files: List[FileNode]):
        """Populate file list with FileNode objects"""
        self.file_list.setRowCount(len(files))
        
        for row, file_node in enumerate(files):
            # Name
            name_item = QTableWidgetItem(file_node.name)
            name_item.setData(Qt.UserRole, file_node.path)  # Store full path
            name_item.setData(Qt.UserRole + 1, file_node)  # Store FileNode object
            if file_node.is_dir:
                name_item.setText(f"📁 {file_node.name}")
            elif file_node.is_symlink:
                name_item.setText(f"🔗 {file_node.name}")
            else:
                name_item.setText(f"📄 {file_node.name}")
            self.file_list.setItem(row, 0, name_item)
            
            # Type
            if file_node.is_dir:
                file_type = "Folder"
            elif file_node.is_symlink:
                file_type = "Link"
            else:
                file_type = "File"
            self.file_list.setItem(row, 1, QTableWidgetItem(file_type))
            
            # Size
            size_str = f"{file_node.size} B" if not file_node.is_dir else "-"
            self.file_list.setItem(row, 2, QTableWidgetItem(size_str))
            
            # Modified time
            self.file_list.setItem(row, 3, QTableWidgetItem(file_node.get_modified_time_str()))
            
            # Permissions
            perm_octal = file_node.get_permission_octal()
            self.file_list.setItem(row, 4, QTableWidgetItem(perm_octal))
    
    def populate_quick_access(self):
        """Populate quick access tree"""
        self.quick_access_tree.clear()
        
        paths = {
            "🏠 Home": self.file_manager.get_home_directory(),
            "📁 Documents": os.path.expanduser("~/Documents"),
            "📁 Downloads": os.path.expanduser("~/Downloads"),
            "📁 Desktop": os.path.expanduser("~/Desktop"),
            "📁 Root": "/",
        }
        
        for label, path in paths.items():
            if os.path.exists(path):
                item = QTreeWidgetItem([label])
                item.setData(0, Qt.UserRole, path)
                self.quick_access_tree.addTopLevelItem(item)
    
    def on_file_opened(self, item):
        """Handle file/folder opened (double-click)"""
        file_node = item.data(Qt.UserRole + 1)
        
        if file_node.is_dir:
            # Navigate to directory
            self.navigate_to(file_node.path)
        else:
            # Open file
            result = self.file_manager.open_file(file_node.path)
            if result.success:
                self.statusBar().showMessage(result.message)
                # Track file open in chatbot activity
                if hasattr(self, 'chatbot') and self.chatbot:
                    self.chatbot.record_activity("file", file_node.path)
            else:
                QMessageBox.information(self, "Info", result.message)
    
    def on_context_menu_requested(self, pos):
        """Show context menu for file operations"""
        item = self.file_list.itemAt(pos)
        if not item:
            return
        
        file_node = item.data(Qt.UserRole + 1)
        if file_node is None:
            return
        
        menu = QMenu(self)
        
        if file_node.is_dir:
            open_action = menu.addAction("📁 Enter Folder")
            open_action.triggered.connect(lambda: self.navigate_to(file_node.path))
        else:
            open_action = menu.addAction("📄 Open")
            open_action.triggered.connect(lambda: self.file_manager.open_file(file_node.path))
        
        menu.addSeparator()
        
        # Show properties
        props_action = menu.addAction("ℹ️  Properties")
        props_action.triggered.connect(lambda: self.show_properties(file_node))
        
        menu.addSeparator()
        
        # Rename
        rename_action = menu.addAction("✏️  Rename")
        rename_action.triggered.connect(lambda: self.on_rename_clicked(file_node))
        
        # Delete
        delete_action = menu.addAction("🗑️  Delete")
        delete_action.triggered.connect(lambda: self.on_delete_clicked(file_node))
        
        menu.exec_(self.file_list.mapToGlobal(pos))
    
    def on_delete_clicked(self, file_node: FileNode):
        """Handle delete operation"""
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete '{file_node.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            result = self.file_manager.delete_file(file_node.path)
            if result.success:
                self.navigate_to(self.file_manager.get_current_directory())
            else:
                QMessageBox.warning(self, "Delete Failed", result.message)
    
    def on_rename_clicked(self, file_node: FileNode):
        """Handle rename operation"""
        new_name, ok = QInputDialog.getText(
            self,
            "Rename",
            f"Enter new name for '{file_node.name}':",
            text=file_node.name
        )
        
        if ok and new_name:
            result = self.file_manager.rename_file(file_node.path, new_name)
            if result.success:
                self.navigate_to(self.file_manager.get_current_directory())
            else:
                QMessageBox.warning(self, "Rename Failed", result.message)
    
    def show_properties(self, file_node: FileNode):
        """Show file properties dialog"""
        perm_str = file_node.get_permissions_string()
        perm_octal = file_node.get_permission_octal()
        
        file_type = "Directory" if file_node.is_dir else "File"
        if file_node.is_symlink:
            file_type = "Symbolic Link"
        
        details = f"""
File Properties
{'=' * 40}
Name: {file_node.name}
Full Path: {file_node.path}
Type: {file_type}
Size: {file_node.size} bytes
Inode: {file_node.inode_number}
Hard Links: {file_node.hard_links}

Permissions (Octal): {perm_octal}
Permissions (String): {perm_str}

Owner UID: {file_node.owner_uid}
Owner GID: {file_node.owner_gid}

Modified: {file_node.get_modified_time_str()}
Accessed: {file_node.accessed_time}
        """
        
        QMessageBox.information(self, "Properties", details)
    
    def on_back_clicked(self):
        """Navigate back in history"""
        if self.history_back:
            current = self.file_manager.get_current_directory()
            self.history_forward.append(current)
            path = self.history_back.pop()
            self.navigate_to(path)
    
    def on_forward_clicked(self):
        """Navigate forward in history"""
        if self.history_forward:
            current = self.file_manager.get_current_directory()
            self.history_back.append(current)
            path = self.history_forward.pop()
            self.navigate_to(path)
    
    def on_up_clicked(self):
        """Navigate to parent directory"""
        result = self.file_manager.navigate_parent()
        if result.success:
            self.populate_file_list(result.data)
    
    def on_home_clicked(self):
        """Navigate to home directory"""
        self.navigate_to(self.file_manager.get_home_directory())
    
    def on_refresh_clicked(self):
        """Refresh current directory"""
        self.navigate_to(self.file_manager.get_current_directory())
    
    def on_go_clicked(self):
        """Navigate to path entered in location bar"""
        path = self.location_input.text()
        if path:
            self.navigate_to(path)
    
    def on_quick_access_clicked(self, item, column):
        """Handle quick access item clicked"""
        path = item.data(0, Qt.UserRole)
        if path:
            self.navigate_to(path)
    
    def on_operation_completed(self, result: OperationResult):
        """Handle file operation completion"""
        if result.success:
            self.statusBar().showMessage(result.message)
        else:
            # Only show error for non-list operations
            if result.operation != FileOperationType.LIST:
                pass  # Error already shown in operation methods

    def on_chatbot_search_results(self, files: List[FileNode]):
        """Update file list with LLM-selected search results"""
        if files:
            self.populate_file_list(files)
            self.statusBar().showMessage(f"Showing {len(files)} matches from assistant")
        else:
            self.statusBar().showMessage("No matches returned by assistant")

    # ───────────── RAG File Retrieval → Main File List ─────────────

    def _on_files_retrieved(self, files: list):
        """Populate the main file list with RAG-retrieved files"""
        file_nodes = []
        for f in files:
            path = f.get("path", "")
            if not path or not os.path.exists(path):
                continue
            try:
                node = self.fs.get_file_info(path)
                file_nodes.append(node)
            except Exception:
                continue
        
        if file_nodes:
            self.populate_file_list(file_nodes)
            self.statusBar().showMessage(f"Showing {len(file_nodes)} retrieved file(s)")
        else:
            self.statusBar().showMessage("No matching files found")


LIGHT_THEME_QSS = """
/* ── Global ── */
* {
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 13px;
}

QMainWindow {
    background-color: #f8f9fa;
}

QWidget {
    background-color: #f8f9fa;
    color: #1e293b;
}

/* ── Toolbar ── */
QToolBar {
    background: #ffffff;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 8px;
    spacing: 6px;
}

QToolBar::separator {
    width: 1px;
    background: #e2e8f0;
    margin: 4px 8px;
}

QToolBar QPushButton {
    background: #f1f5f9;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 14px;
    font-weight: 600;
    font-size: 12px;
    min-width: 60px;
}

QToolBar QPushButton:hover {
    background: #e2e8f0;
    border-color: #6366f1;
    color: #1e293b;
}

QToolBar QPushButton:pressed {
    background: #6366f1;
    border-color: #6366f1;
    color: #ffffff;
}

/* ── Buttons (general) ── */
QPushButton {
    background-color: #f1f5f9;
    color: #334155;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 6px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #e2e8f0;
    border-color: #6366f1;
    color: #1e293b;
}

QPushButton:pressed {
    background-color: #6366f1;
    color: #ffffff;
}

QPushButton#accentButton {
    background-color: #6366f1;
    color: #ffffff;
    border: none;
    font-weight: 700;
}

QPushButton#accentButton:hover {
    background-color: #4f46e5;
}

/* ── Line Edits ── */
QLineEdit {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 7px 12px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

QLineEdit:focus {
    border-color: #6366f1;
}

QLineEdit:read-only {
    background-color: #f8f9fa;
    border: 1px solid #e2e8f0;
    color: #64748b;
}

/* ── Labels ── */
QLabel {
    color: #475569;
    font-weight: 500;
    background: transparent;
    padding: 2px 0px;
}

QLabel#sectionTitle {
    color: #1e293b;
    font-size: 14px;
    font-weight: 700;
    padding: 4px 0px;
}

/* ── Table ── */
QTableWidget {
    background-color: #ffffff;
    alternate-background-color: #f8fafc;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    gridline-color: transparent;
    selection-background-color: rgba(99, 102, 241, 0.18);
    selection-color: #1e293b;
    outline: 0;
    padding: 2px;
}

QTableWidget::item {
    padding: 6px 10px;
    border: none;
    border-bottom: 1px solid #f1f5f9;
}

QTableWidget::item:hover {
    background-color: rgba(99, 102, 241, 0.08);
}

QTableWidget::item:selected {
    background-color: rgba(99, 102, 241, 0.18);
    color: #1e293b;
}

QHeaderView {
    background-color: transparent;
}

QHeaderView::section {
    background: #f8f9fa;
    color: #64748b;
    border: none;
    border-bottom: 2px solid #6366f1;
    border-right: 1px solid #e2e8f0;
    padding: 8px 10px;
    font-weight: 700;
    font-size: 12px;
    text-transform: uppercase;
}

QHeaderView::section:last {
    border-right: none;
}

/* ── Tree Widget ── */
QTreeWidget {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    outline: 0;
    padding: 4px;
}

QTreeWidget::item {
    padding: 6px 8px;
    border-radius: 6px;
    margin: 1px 2px;
}

QTreeWidget::item:hover {
    background-color: rgba(99, 102, 241, 0.08);
}

QTreeWidget::item:selected {
    background-color: rgba(99, 102, 241, 0.18);
    color: #1e293b;
}

QTreeWidget::branch {
    background: transparent;
}

/* ── Splitter ── */
QSplitter::handle {
    background-color: #e2e8f0;
    width: 2px;
    margin: 8px 2px;
    border-radius: 1px;
}

QSplitter::handle:hover {
    background-color: #6366f1;
}

/* ── Dock Widget ── */
QDockWidget {
    color: #1e293b;
    font-weight: 700;
    titlebar-close-icon: none;
}

QDockWidget::title {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-bottom: 2px solid #6366f1;
    padding: 8px 12px;
    text-align: left;
    font-size: 13px;
}

QDockWidget::close-button, QDockWidget::float-button {
    border: none;
    background: transparent;
    padding: 2px;
}

QDockWidget::close-button:hover, QDockWidget::float-button:hover {
    background: #e2e8f0;
    border-radius: 4px;
}

/* ── Status Bar ── */
QStatusBar {
    background: #ffffff;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    padding: 4px 12px;
    font-size: 12px;
}

/* ── Context Menus ── */
QMenu {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 6px 4px;
}

QMenu::item {
    padding: 8px 28px 8px 16px;
    border-radius: 6px;
    margin: 2px 4px;
}

QMenu::item:selected {
    background-color: #6366f1;
    color: #ffffff;
}

QMenu::separator {
    height: 1px;
    background: #e2e8f0;
    margin: 4px 12px;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: #f8f9fa;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #6366f1;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    height: 0;
    background: none;
}

QScrollBar:horizontal {
    background: #f8f9fa;
    height: 10px;
    border-radius: 5px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    border-radius: 5px;
    min-width: 30px;
}

QScrollBar::handle:horizontal:hover {
    background: #6366f1;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    width: 0;
    background: none;
}

/* ── Message Boxes / Dialogs ── */
QMessageBox {
    background-color: #ffffff;
    color: #1e293b;
}

QMessageBox QLabel {
    color: #1e293b;
    font-size: 13px;
}

QMessageBox QPushButton {
    min-width: 80px;
}

QDialog {
    background-color: #ffffff;
    color: #1e293b;
}

QInputDialog {
    background-color: #ffffff;
}

/* ── Form Layout Labels ── */
QFormLayout QLabel {
    color: #64748b;
}

/* ── Checkboxes ── */
QCheckBox {
    color: #1e293b;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 2px solid #cbd5e1;
    border-radius: 4px;
    background: #ffffff;
}

QCheckBox::indicator:checked {
    background: #6366f1;
    border-color: #6366f1;
}

QCheckBox::indicator:hover {
    border-color: #6366f1;
}

/* ── Combo Boxes ── */
QComboBox {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 6px 12px;
}

QComboBox:hover {
    border-color: #6366f1;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
    outline: 0;
}

/* ── Spin Boxes ── */
QSpinBox {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 6px 10px;
}

QSpinBox:focus {
    border-color: #6366f1;
}

/* ── Text Edits ── */
QTextEdit {
    background-color: #ffffff;
    color: #1e293b;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 8px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

/* ── Progress Bar ── */
QProgressBar {
    background-color: #e2e8f0;
    border: none;
    border-radius: 6px;
    text-align: center;
    color: #1e293b;
    height: 8px;
}

QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #6366f1, stop:1 #818cf8);
    border-radius: 6px;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #1e293b;
    color: #f8f9fa;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""


def main():
    """Main entry point"""
    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    # Apply light palette
    from PyQt5.QtGui import QPalette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(248, 249, 250))
    palette.setColor(QPalette.WindowText, QColor(30, 41, 59))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(248, 250, 252))
    palette.setColor(QPalette.ToolTipBase, QColor(30, 41, 59))
    palette.setColor(QPalette.ToolTipText, QColor(248, 249, 250))
    palette.setColor(QPalette.Text, QColor(30, 41, 59))
    palette.setColor(QPalette.Button, QColor(241, 245, 249))
    palette.setColor(QPalette.ButtonText, QColor(51, 65, 85))
    palette.setColor(QPalette.BrightText, QColor(255, 255, 255))
    palette.setColor(QPalette.Link, QColor(99, 102, 241))
    palette.setColor(QPalette.Highlight, QColor(99, 102, 241))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)

    # Apply stylesheet
    app.setStyleSheet(LIGHT_THEME_QSS)

    # Create and show window
    window = FileExplorerWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
