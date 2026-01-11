"""
File Manager Layer

Demonstrates: Error handling, permission validation, operation coordination
This layer coordinates file operations and provides error handling for
user interactions with the file system.

OS Concepts:
- Error mapping (errno → Python exceptions)
- Permission validation before operations
- User space operations (no privilege escalation)
- File operation atomicity considerations
"""

import os
import subprocess
from typing import Optional, List, Callable
from enum import Enum
from dataclasses import dataclass

from filesystem import FileSystemAbstraction, FileNode


class FileOperationType(Enum):
    """Types of file operations"""
    LIST = "list_directory"
    DELETE = "delete"
    RENAME = "rename"
    OPEN = "open"
    GET_INFO = "get_info"


@dataclass
class OperationResult:
    """Result of a file operation"""
    success: bool
    operation: FileOperationType
    message: str
    data: any = None
    error_type: str = None


class PermissionError_Custom(Exception):
    """Custom permission error with OS context"""
    def __init__(self, message: str, errno: int = None):
        self.message = message
        self.errno = errno  # errno from OS
        super().__init__(message)


class FileManager:
    """
    File Manager - coordinates file system operations
    
    Responsibilities:
    - Coordinate file operations through FileSystemAbstraction
    - Validate permissions before operations
    - Handle errors and provide user-friendly messages
    - Map OS errors to application errors
    - Maintain operation history
    """
    
    def __init__(self, home_dir: str = None):
        """Initialize file manager with file system abstraction"""
        self.fs = FileSystemAbstraction(home_dir)
        self.current_directory = self.fs.home_dir
        self.operation_callbacks: List[Callable] = []
        self.operation_history: List[OperationResult] = []
    
    def register_operation_callback(self, callback: Callable) -> None:
        """Register callback for operation completion"""
        self.operation_callbacks.append(callback)
    
    def _notify_operation(self, result: OperationResult) -> None:
        """Notify all registered callbacks of operation result"""
        self.operation_history.append(result)
        for callback in self.operation_callbacks:
            try:
                callback(result)
            except Exception as e:
                print(f"Error in operation callback: {e}")
    
    def browse_directory(self, path: str) -> OperationResult:
        """
        Browse a directory and get its contents
        
        Error handling:
        - FileNotFoundError: Path doesn't exist
        - PermissionError: No read permission
        - NotADirectoryError: Path is not a directory
        - OSError: Other OS errors
        """
        try:
            # Validate and normalize path
            path = self.fs.normalize_path(path)
            
            # List directory contents
            files = self.fs.list_directory(path)
            
            # Update current directory
            self.current_directory = path
            
            result = OperationResult(
                success=True,
                operation=FileOperationType.LIST,
                message=f"Listed {len(files)} items in {path}",
                data=files
            )
            
        except NotADirectoryError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.LIST,
                message=f"Not a directory: {path}",
                error_type="NotADirectory"
            )
        
        except PermissionError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.LIST,
                message=f"Permission denied. You don't have read access to this folder.",
                error_type="PermissionDenied"
            )
        
        except FileNotFoundError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.LIST,
                message=f"Directory not found: {path}",
                error_type="NotFound"
            )
        
        except OSError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.LIST,
                message=f"Error reading directory: {e.strerror}",
                error_type="OSError"
            )
        
        self._notify_operation(result)
        return result
    
    def get_file_info(self, path: str) -> OperationResult:
        """
        Get metadata for a file
        
        Returns inode-like information from os.stat()
        """
        try:
            file_info = self.fs.get_file_info(path)
            
            result = OperationResult(
                success=True,
                operation=FileOperationType.GET_INFO,
                message=f"Retrieved info for {path}",
                data=file_info
            )
        
        except FileNotFoundError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.GET_INFO,
                message=f"File not found: {path}",
                error_type="NotFound"
            )
        
        except PermissionError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.GET_INFO,
                message=f"Permission denied: {path}",
                error_type="PermissionDenied"
            )
        
        except OSError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.GET_INFO,
                message=f"Error getting file info: {e.strerror}",
                error_type="OSError"
            )
        
        self._notify_operation(result)
        return result
    
    def delete_file(self, path: str) -> OperationResult:
        """
        Delete a file with confirmation
        
        Error handling:
        - PermissionError (EACCES): No write permission on parent
        - PermissionError (EPERM): Operation not permitted by OS
        - FileNotFoundError: File doesn't exist
        - IsADirectoryError: Directory not empty
        """
        try:
            self.fs.delete_file(path)
            
            result = OperationResult(
                success=True,
                operation=FileOperationType.DELETE,
                message=f"Successfully deleted {os.path.basename(path)}"
            )
        
        except PermissionError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.DELETE,
                message=f"Permission denied: You don't have permission to delete this file. "
                        f"Check write permission on the folder containing this file.",
                error_type="PermissionDenied"
            )
        
        except FileNotFoundError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.DELETE,
                message=f"File not found: {path}",
                error_type="NotFound"
            )
        
        except IsADirectoryError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.DELETE,
                message=f"Cannot delete non-empty directory: {path}",
                error_type="DirectoryNotEmpty"
            )
        
        except OSError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.DELETE,
                message=f"Error deleting file: {e.strerror}",
                error_type="OSError"
            )
        
        self._notify_operation(result)
        return result
    
    def rename_file(self, old_path: str, new_name: str) -> OperationResult:
        """
        Rename a file
        
        Error handling:
        - PermissionError: No write permission on parent directory
        - FileNotFoundError: Source file doesn't exist
        - FileExistsError: Destination already exists
        """
        try:
            # Construct new path (same directory, new name)
            parent = os.path.dirname(old_path)
            new_path = os.path.join(parent, new_name)
            
            # Check if new name is valid (not empty, no path separators)
            if not new_name or '/' in new_name or '\\' in new_name:
                result = OperationResult(
                    success=False,
                    operation=FileOperationType.RENAME,
                    message=f"Invalid filename: {new_name}",
                    error_type="InvalidFilename"
                )
                self._notify_operation(result)
                return result
            
            # Perform rename
            self.fs.rename_file(old_path, new_path)
            
            result = OperationResult(
                success=True,
                operation=FileOperationType.RENAME,
                message=f"Successfully renamed to {new_name}"
            )
        
        except PermissionError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.RENAME,
                message=f"Permission denied: You don't have permission to rename this file.",
                error_type="PermissionDenied"
            )
        
        except FileNotFoundError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.RENAME,
                message=f"File not found: {old_path}",
                error_type="NotFound"
            )
        
        except FileExistsError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.RENAME,
                message=f"A file with that name already exists.",
                error_type="FileExists"
            )
        
        except OSError as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.RENAME,
                message=f"Error renaming file: {e.strerror}",
                error_type="OSError"
            )
        
        self._notify_operation(result)
        return result
    
    def open_file(self, path: str) -> OperationResult:
        """
        Open a file with default application
        
        Uses xdg-open on Linux (respects desktop environment defaults)
        """
        try:
            if not os.path.exists(path):
                result = OperationResult(
                    success=False,
                    operation=FileOperationType.OPEN,
                    message=f"File not found: {path}",
                    error_type="NotFound"
                )
            elif not os.path.isfile(path):
                result = OperationResult(
                    success=False,
                    operation=FileOperationType.OPEN,
                    message=f"Cannot open directory as file",
                    error_type="IsDirectory"
                )
            else:
                # Use xdg-open on Linux (desktop environment agnostic)
                subprocess.Popen(['xdg-open', path])
                result = OperationResult(
                    success=True,
                    operation=FileOperationType.OPEN,
                    message=f"Opening {os.path.basename(path)}..."
                )
        
        except FileNotFoundError:
            result = OperationResult(
                success=False,
                operation=FileOperationType.OPEN,
                message=f"xdg-open not found. Cannot open file.",
                error_type="NotFound"
            )
        
        except Exception as e:
            result = OperationResult(
                success=False,
                operation=FileOperationType.OPEN,
                message=f"Error opening file: {str(e)}",
                error_type="Error"
            )
        
        self._notify_operation(result)
        return result
    
    def navigate_parent(self) -> OperationResult:
        """Navigate to parent directory"""
        parent = self.fs.get_parent_directory(self.current_directory)
        
        if parent is None:
            return OperationResult(
                success=False,
                operation=FileOperationType.LIST,
                message=f"Already at root directory",
                error_type="AlreadyAtRoot"
            )
        
        return self.browse_directory(parent)
    
    def get_current_directory(self) -> str:
        """Get current working directory"""
        return self.current_directory
    
    def get_home_directory(self) -> str:
        """Get home directory"""
        return self.fs.home_dir
    
    def get_operation_history(self) -> List[OperationResult]:
        """Get history of operations"""
        return self.operation_history.copy()
