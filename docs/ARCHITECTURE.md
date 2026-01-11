# AIFE - Custom File Explorer Architecture

## Project Overview
AIFE (Advanced Interactive File Explorer) is a user-space desktop application demonstrating fundamental OS concepts through a custom file explorer for Ubuntu Linux.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│         PyQt5 GUI Layer (Presentation)              │
│  ┌─────────────────────────────────────────────┐   │
│  │ MainWindow | FileTreeView | DetailsPanel    │   │
│  │ ActionHandlers | ContextMenus              │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│      Business Logic Layer (File Operations)         │
│  ┌─────────────────────────────────────────────┐   │
│  │ FileManager | FileOperations | ErrorHandler │   │
│  │ PermissionValidator | MetadataExtractor     │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│    File System Abstraction Layer (VFS Emulation)    │
│  ┌─────────────────────────────────────────────┐   │
│  │ FileSystemAbstraction | PathResolver        │   │
│  │ VirtualFileSystem (VFS) Interface           │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│     System Call Wrapper Layer (os, stat modules)    │
│  ┌─────────────────────────────────────────────┐   │
│  │ os.stat() │ os.listdir() │ os.open()        │   │
│  │ os.remove() │ os.rename() (Python → Kernel) │   │
│  └─────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│  Linux Kernel (VFS, inode, filesystem drivers)      │
│  [NOT MODIFIED - Boundary of User Space]            │
└─────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### 1. **GUI Layer (PyQt5)**
- User interface components
- Event handling (button clicks, double-clicks, right-clicks)
- Display file lists, directory trees, metadata panels
- Context menus for file operations

### 2. **Business Logic Layer**
- File manager logic
- File operation coordination
- Error handling and validation
- Permission checks before operations
- Metadata extraction and formatting

### 3. **File System Abstraction Layer**
- Abstract representation of the file system
- Path resolution and normalization
- Emulates Virtual File System (VFS) concepts
- Provides unified interface to underlying OS calls

### 4. **System Call Wrapper Layer**
- Wraps Python's `os` and `stat` modules
- Maps to actual Linux system calls (stat, open, readdir, unlink, rename)
- Handles errno and exception translation

## OS Concepts Demonstrated

### 1. **User Space vs Kernel Space**
- Application runs as unprivileged user process (user space)
- Makes system calls to kernel (via Python's os module)
- Cannot access kernel directly; respects permission boundaries
- Demonstrates separation of privilege levels

**Evidence in Code:**
```python
os.stat(path)           # System call: stat()
os.listdir(path)        # System call: getdents()/getdents64()
os.remove(path)         # System call: unlink()
```

### 2. **File Permissions and Access Control**
- Respects Unix permission model (rwx for owner/group/other)
- Checks permission bits before operations
- Handles EACCES and EPERM errors gracefully
- Displays permission octal notation (755, 644, etc.)

**Evidence in Code:**
```python
st = os.stat(path)
mode = oct(st.st_mode)[-3:]  # Extract rwx bits
# Cannot delete files without write+execute on parent
```

### 3. **Virtual File System (VFS) Abstraction**
- File system abstraction layer hides implementation details
- Supports abstracted file objects (name, size, type, permissions)
- Path resolution through multiple components
- Demonstrates VFS inode-like representation (metadata)

**Evidence in Code:**
```python
class FileNode:
    """Represents a file (like an inode with metadata)"""
    path: str
    name: str
    size: int
    mode: int
    uid: int
    gid: int
```

### 4. **System Calls**
- `stat()` - Get file metadata (size, permissions, timestamps)
- `open()` - Open file descriptor (used by open operation)
- `readdir()` - List directory contents
- `unlink()` - Delete file
- `rename()` - Rename file
- `access()` - Check permission accessibility

### 5. **File Types and Inodes**
- Regular files (S_IFREG)
- Directories (S_IFDIR)
- Symlinks (S_IFLNK)
- Special files (character/block devices)
- Mode bits indicating type and permissions

## Component Breakdown

### FileSystemAbstraction (`filesystem.py`)
```
Purpose: Abstract layer over OS file system operations
Responsibilities:
- List directory contents
- Get file metadata
- Validate paths
- Handle path normalization
- Encapsulate OS-specific calls
```

### FileManager (`file_manager.py`)
```
Purpose: Coordinate file operations
Responsibilities:
- Perform file operations (open, delete, rename)
- Validate permissions
- Handle errors gracefully
- Maintain operation history
- Emit signals for UI updates
```

### PyQt5 Application (`gui.py`)
```
Purpose: User interface
Responsibilities:
- Display file lists/tree
- Handle user interactions
- Show file metadata
- Provide context menus
- Update UI based on file manager signals
```

## Data Flow Examples

### Browsing a Directory
```
User clicks on folder
    ↓
GUI emit signal to FileManager
    ↓
FileManager.browse_directory(path)
    ↓
FileSystemAbstraction.list_directory(path)
    ↓
os.listdir() + os.stat() [System calls]
    ↓
GUI receives file list signal
    ↓
GUI displays files with metadata
```

### Deleting a File
```
User right-clicks → Delete
    ↓
GUI shows confirmation dialog
    ↓
User confirms
    ↓
FileManager.delete_file(path)
    ↓
Check permissions: os.access(parent, os.W_OK | os.X_OK)
    ↓
os.remove(path) [System call: unlink()]
    ↓
Update GUI
    ↓
Catch PermissionError, OSError exceptions
```

## Permission Model Implementation

### Read Directory
```python
def can_read_directory(path):
    # Need execute permission on directory to list contents
    return os.access(path, os.X_OK)
```

### Write File (Delete/Rename)
```python
def can_modify_file(path):
    parent = os.path.dirname(path)
    # Need write+execute on parent directory
    return os.access(parent, os.W_OK | os.X_OK)
```

### Access File
```python
def can_access_file(path):
    # Read permission check
    return os.access(path, os.R_OK)
```

## File Metadata Extracted

From `os.stat()` call (st_* fields):
- `st_ino` - Inode number
- `st_size` - Size in bytes
- `st_mode` - Permission bits + file type
- `st_uid` - Owner user ID
- `st_gid` - Owner group ID
- `st_mtime` - Modification time
- `st_atime` - Access time
- `st_ctime` - Change time
- `st_nlink` - Hard link count

## Error Handling Strategy

```
FileNotFoundError          → File/directory doesn't exist
PermissionError (EACCES)   → User lacks permission
PermissionError (EPERM)    → Operation not permitted (OS protection)
IsADirectoryError          → Operation invalid for directory type
NotADirectoryError         → Path component is not directory
OSError (generic)          → Other OS-level errors
```

## Key Design Decisions

1. **Modular Design**: Separate concerns into layers for testability
2. **System Call Transparency**: Show which OS concepts are being used
3. **Error Handling**: Graceful degradation with user-friendly messages
4. **VFS Abstraction**: Demonstrate how OS abstracts file system details
5. **Permission Awareness**: Respect Linux permission model strictly
6. **Single User Operation**: No need for privilege elevation (design constraint)

## Limitations & Scope

- Phase 1: No AI features
- No file content editing
- No batch operations
- No networking/remote files
- No advanced features (search, filter, sort)
- Runs as unprivileged user only
- Single-threaded GUI (can block on slow operations)

## Testing & Demo Scenarios

1. **List Home Directory**: Demonstrate os.listdir() and metadata extraction
2. **Navigate Subdirectories**: Show path resolution and VFS abstraction
3. **View File Permissions**: Display permission bits and octal notation
4. **Attempt Restricted Operation**: Try deleting file without permission → PermissionError
5. **Rename File**: Demonstrate file system modification via system call
6. **View File Types**: Show how VFS differentiates file types via mode bits

## OS Concepts Checklist

- [x] User space vs kernel space boundary
- [x] System calls (stat, open, readdir, unlink, rename, access)
- [x] File permissions (rwx bits, user/group/other)
- [x] File types (regular, directory, symlink)
- [x] Inodes and metadata
- [x] Virtual File System abstraction
- [x] Error handling (errno translation)
- [x] Path resolution
- [x] Access control enforcement
