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
    QStatusBar, QToolBar, QComboBox, QProgressBar
)
from PyQt5.QtCore import Qt, QSize, pyqtSignal, QObject, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor
import stat

from file_manager import FileManager, OperationResult, FileOperationType
from filesystem import FileNode
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
        location_layout.addWidget(QLabel("Location:"))
        self.location_input = QLineEdit()
        self.location_input.setReadOnly(True)
        location_layout.addWidget(self.location_input)
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.on_go_clicked)
        location_layout.addWidget(self.go_button)
        main_layout.addLayout(location_layout)
        
        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel: Directory tree and Chatbot
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)
        
        left_layout.addWidget(QLabel("Quick Access"))
        self.quick_access_tree = QTreeWidget()
        self.quick_access_tree.setHeaderHidden(True)
        self.quick_access_tree.itemDoubleClicked.connect(self.on_quick_access_clicked)
        # Enable drag-drop for vertical reordering
        self.quick_access_tree.setDragDropMode(QAbstractItemView.InternalMove)
        self.quick_access_tree.setDefaultDropAction(Qt.MoveAction)
        left_layout.addWidget(self.quick_access_tree, 10)
        
        # Add chatbot with stretch
        self.chatbot = ChatbotWidget()
        left_layout.addWidget(self.chatbot, 3)
        
        left_widget = QWidget()
        left_widget.setLayout(left_layout)
        splitter.addWidget(left_widget)
        
        # Center panel: File list
        center_layout = QVBoxLayout()
        center_layout.addWidget(QLabel("Files and Folders"))
        self.file_list = QTableWidget()
        self.file_list.setColumnCount(5)
        self.file_list.setHorizontalHeaderLabels([
            "Name", "Type", "Size", "Modified", "Permissions"
        ])
        self.file_list.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.file_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.file_list.itemDoubleClicked.connect(self.on_file_opened)
        self.file_list.itemRightClicked = lambda item: self.show_context_menu(item)
        self.file_list.customContextMenuRequested.connect(self.on_context_menu_requested)
        self.file_list.setContextMenuPolicy(Qt.CustomContextMenu)
        center_layout.addWidget(self.file_list)
        center_widget = QWidget()
        center_widget.setLayout(center_layout)
        splitter.addWidget(center_widget)
        
        splitter.setSizes([250, 650])
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def setup_toolbar(self):
        """Setup navigation toolbar"""
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)
        
        # Back button
        self.back_button = QPushButton("← Back")
        self.back_button.clicked.connect(self.on_back_clicked)
        toolbar.addWidget(self.back_button)
        
        # Forward button
        self.forward_button = QPushButton("Forward →")
        self.forward_button.clicked.connect(self.on_forward_clicked)
        toolbar.addWidget(self.forward_button)
        
        # Up button
        self.up_button = QPushButton("⬆ Parent")
        self.up_button.clicked.connect(self.on_up_clicked)
        toolbar.addWidget(self.up_button)
        
        # Home button
        self.home_button = QPushButton("🏠 Home")
        self.home_button.clicked.connect(self.on_home_clicked)
        toolbar.addWidget(self.home_button)
        
        toolbar.addSeparator()
        
        # Refresh button
        self.refresh_button = QPushButton("🔄 Refresh")
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
            else:
                QMessageBox.information(self, "Info", result.message)
    
    def on_context_menu_requested(self, pos):
        """Show context menu for file operations"""
        item = self.file_list.itemAt(pos)
        if not item:
            return
        
        file_node = item.data(Qt.UserRole + 1)
        
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


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show window
    window = FileExplorerWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
