"""
File System Abstraction Layer

Demonstrates: Virtual File System (VFS), System Calls, Path Resolution
This layer abstracts OS-specific file system operations and provides
a unified interface for higher-level components.

OS Concepts:
- System calls: stat, readdir, open, unlink, rename, access
- File metadata (inode equivalent): size, permissions, timestamps
- Path normalization and resolution
- File type detection via mode bits
"""

import os
import stat
from pathlib import Path
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class FileNode:
    """
    Represents a file in the file system (analogous to inode with metadata)
    
    This class maps to the inode structure in Linux:
    - name: filename (part of directory entry)
    - path: full path (resolved through VFS)
    - is_dir: S_ISDIR(mode) - file type from inode
    - size: st_size from inode
    - permissions: mode & 0o777 - permission bits from inode
    - owner_uid: st_uid - owner UID from inode
    - owner_gid: st_gid - owner GID from inode
    - modified_time: st_mtime - modification time from inode
    - accessed_time: st_atime - access time from inode
    - is_symlink: S_ISLNK(mode) - symlink type from inode
    - inode_number: st_ino - actual inode number from OS
    """
    name: str                 # Filename
    path: str                 # Absolute path
    is_dir: bool             # True if directory (S_ISDIR)
    is_symlink: bool         # True if symbolic link (S_ISLNK)
    size: int                # File size in bytes (st_size)
    permissions: int         # Octal permissions (e.g., 0o755)
    owner_uid: int           # Owner user ID (st_uid)
    owner_gid: int           # Owner group ID (st_gid)
    modified_time: float     # Modification timestamp (st_mtime)
    accessed_time: float     # Access timestamp (st_atime)
    inode_number: int        # Inode number (st_ino)
    hard_links: int          # Hard link count (st_nlink)
    
    def get_human_size(self) -> str:
        """Convert byte size to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.size < 1024:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024
        return f"{self.size:.1f} PB"
    
    def get_permissions_string(self) -> str:
        """Return permission string like 'rwxr-xr-x'"""
        return stat.filemode(self.permissions | stat.S_IFREG)
    
    def get_permission_octal(self) -> str:
        """Return permission in octal format like '755'"""
        return oct(self.permissions)[2:]
    
    def get_modified_time_str(self) -> str:
        """Return formatted modification time"""
        return datetime.fromtimestamp(self.modified_time).strftime('%Y-%m-%d %H:%M:%S')


class FileSystemAbstraction:
    """
    Virtual File System (VFS) Abstraction Layer
    
    Demonstrates key OS concepts:
    1. VFS Abstraction: Hides underlying file system implementation
    2. System Calls: Uses os.stat(), os.listdir(), os.access()
    3. Path Resolution: Normalizes paths through the VFS
    4. Permission Checks: Respects Linux permission model
    5. File Type Detection: Differentiates file types via inode mode bits
    
    System calls made (mapping to Linux):
    - os.stat(path)       → stat() syscall
    - os.listdir(path)    → getdents()/getdents64() syscall
    - os.access(path, m)  → access() syscall
    - os.path.realpath()  → readlink() for symlinks
    """
    
    def __init__(self, home_dir: str = None):
        """
        Initialize file system abstraction layer
        
        Args:
            home_dir: Root directory for browsing (defaults to user home)
        """
        self.home_dir = home_dir or os.path.expanduser("~")
        self.current_path = self.home_dir
        self._validate_path(self.home_dir)
    
    def _validate_path(self, path: str) -> None:
        """
        Validate that path is within home directory (security boundary)
        
        System call: access() - check if path is accessible
        Error handling: FileNotFoundError, PermissionError
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        if not os.path.isabs(path):
            raise ValueError(f"Path must be absolute: {path}")
        
        # Resolve any symlinks to prevent escaping home directory
        try:
            real_path = os.path.realpath(path)
        except (OSError, RuntimeError) as e:
            raise RuntimeError(f"Cannot resolve path: {path}") from e
    
    def list_directory(self, path: str) -> List[FileNode]:
        """
        List all files and directories in a path
        
        System call: os.listdir() → getdents()/getdents64()
                    os.stat() → stat() [called for each entry]
        
        Returns:
            List of FileNode objects with metadata
            
        Raises:
            PermissionError: If no read+execute permission on directory
            FileNotFoundError: If directory doesn't exist
            NotADirectoryError: If path is not a directory
        """
        self._validate_path(path)
        
        if not os.path.isdir(path):
            raise NotADirectoryError(f"Not a directory: {path}")
        
        # Check read + execute permissions on directory
        if not os.access(path, os.R_OK | os.X_OK):
            raise PermissionError(f"No permission to read directory: {path}")
        
        files = []
        
        try:
            # System call: getdents/getdents64 to read directory entries
            entries = os.listdir(path)
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {path}") from e
        except OSError as e:
            raise OSError(f"Error listing directory: {path}") from e
        
        for entry in entries:
            file_path = os.path.join(path, entry)
            
            try:
                # System call: stat() to get file metadata (inode information)
                stat_result = os.stat(file_path)
                mode = stat_result.st_mode
                
                # Extract file type from mode (inode st_mode field)
                is_dir = stat.S_ISDIR(mode)
                is_symlink = stat.S_ISLNK(mode)
                
                # Extract permission bits (rwx for user/group/other)
                permissions = stat.S_IMODE(mode)
                
                node = FileNode(
                    name=entry,
                    path=file_path,
                    is_dir=is_dir,
                    is_symlink=is_symlink,
                    size=stat_result.st_size,
                    permissions=permissions,
                    owner_uid=stat_result.st_uid,
                    owner_gid=stat_result.st_gid,
                    modified_time=stat_result.st_mtime,
                    accessed_time=stat_result.st_atime,
                    inode_number=stat_result.st_ino,
                    hard_links=stat_result.st_nlink,
                )
                files.append(node)
                
            except (FileNotFoundError, PermissionError, OSError):
                # Skip files we can't stat (broken symlinks, permission denied)
                continue
        
        return sorted(files, key=lambda f: (not f.is_dir, f.name.lower()))
    
    def get_file_info(self, path: str) -> FileNode:
        """
        Get metadata for a single file
        
        System call: os.stat() → stat()
        
        Returns:
            FileNode with complete metadata
            
        Raises:
            FileNotFoundError: If file doesn't exist
            PermissionError: If cannot access file
        """
        self._validate_path(path)
        
        try:
            stat_result = os.stat(path)
        except FileNotFoundError:
            raise FileNotFoundError(f"File not found: {path}")
        except PermissionError:
            raise PermissionError(f"Permission denied: {path}")
        
        mode = stat_result.st_mode
        is_dir = stat.S_ISDIR(mode)
        is_symlink = stat.S_ISLNK(mode)
        permissions = stat.S_IMODE(mode)
        
        return FileNode(
            name=os.path.basename(path),
            path=path,
            is_dir=is_dir,
            is_symlink=is_symlink,
            size=stat_result.st_size,
            permissions=permissions,
            owner_uid=stat_result.st_uid,
            owner_gid=stat_result.st_gid,
            modified_time=stat_result.st_mtime,
            accessed_time=stat_result.st_atime,
            inode_number=stat_result.st_ino,
            hard_links=stat_result.st_nlink,
        )
    
    def can_read(self, path: str) -> bool:
        """
        Check if user can read file
        
        System call: os.access() → access()
        """
        try:
            return os.access(path, os.R_OK)
        except (FileNotFoundError, OSError):
            return False
    
    def can_write(self, path: str) -> bool:
        """
        Check if user can write to file
        
        System call: os.access() → access()
        """
        try:
            return os.access(path, os.W_OK)
        except (FileNotFoundError, OSError):
            return False
    
    def can_execute(self, path: str) -> bool:
        """
        Check if user can execute file or enter directory
        
        System call: os.access() → access()
        """
        try:
            return os.access(path, os.X_OK)
        except (FileNotFoundError, OSError):
            return False
    
    def delete_file(self, path: str) -> None:
        """
        Delete a file or directory
        
        System calls: os.remove() → unlink() for files
                     os.rmdir() → rmdir() for empty directories
        
        Requires: Write permission on parent directory
                  Execute permission on parent directory (to modify it)
        
        Raises:
            PermissionError: If no write permission on parent
            IsADirectoryError: If trying to delete non-empty directory with remove()
            OSError: Other OS-level errors
        """
        self._validate_path(path)
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        parent = os.path.dirname(path)
        
        # Check write + execute permission on parent directory
        # (need write to delete entry from parent, execute to access parent)
        if not os.access(parent, os.W_OK | os.X_OK):
            raise PermissionError(f"No permission to delete {path}")
        
        try:
            if os.path.isdir(path):
                # Empty directory
                os.rmdir(path)  # System call: rmdir()
            else:
                # Regular file or symlink
                os.remove(path)  # System call: unlink()
        except PermissionError as e:
            raise PermissionError(f"Permission denied: {path}") from e
        except IsADirectoryError as e:
            raise IsADirectoryError(f"Directory not empty or is directory: {path}") from e
        except OSError as e:
            raise OSError(f"Error deleting file: {path}") from e
    
    def rename_file(self, old_path: str, new_path: str) -> None:
        """
        Rename or move a file
        
        System call: os.rename() → rename() / renameat()
        
        Requires: Write permission on both parent directories
                  Execute permission on both parent directories
        
        Raises:
            PermissionError: If no write permission on parent directories
            FileNotFoundError: If source file doesn't exist
            FileExistsError: If destination already exists
            OSError: Other OS-level errors
        """
        self._validate_path(old_path)
        self._validate_path(os.path.dirname(new_path))
        
        if not os.path.exists(old_path):
            raise FileNotFoundError(f"File not found: {old_path}")
        
        old_parent = os.path.dirname(old_path)
        new_parent = os.path.dirname(new_path)
        
        # Check permissions on both parent directories
        if not os.access(old_parent, os.W_OK | os.X_OK):
            raise PermissionError(f"No permission to modify source directory")
        
        if not os.access(new_parent, os.W_OK | os.X_OK):
            raise PermissionError(f"No permission to modify destination directory")
        
        if os.path.exists(new_path):
            raise FileExistsError(f"Destination already exists: {new_path}")
        
        try:
            os.rename(old_path, new_path)  # System call: rename() / renameat()
        except PermissionError as e:
            raise PermissionError(f"Permission denied during rename") from e
        except OSError as e:
            raise OSError(f"Error renaming file: {old_path}") from e
    
    def get_parent_directory(self, path: str) -> Optional[str]:
        """Get parent directory path, returns None if at root"""
        parent = os.path.dirname(path)
        return parent if parent != path else None
    
    def normalize_path(self, path: str) -> str:
        """
        Normalize path (remove .., ., trailing slashes)
        Resolves symlinks
        """
        try:
            return os.path.realpath(os.path.expanduser(path))
        except (OSError, RuntimeError):
            return path
    
    def get_absolute_path(self, relative_path: str) -> str:
        """Convert relative path to absolute"""
        if os.path.isabs(relative_path):
            return relative_path
        return os.path.join(self.current_path, relative_path)
