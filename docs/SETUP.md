# AIFE - Advanced Interactive File Explorer
## Complete Setup and Running Guide

## Prerequisites

- **OS**: Ubuntu Linux (tested on 20.04 LTS and later)
- **Python**: 3.8 or higher
- **Desktop Environment**: Any (GNOME, KDE, XFCE, etc.)

## Installation & Setup

### Step 1: Install Python and pip

```bash
sudo apt update
sudo apt install python3 python3-pip
```

### Step 2: Clone or Download Project

```bash
cd ~/Desktop
# If not already in AIFE directory
cd AIFE
```

### Step 3: Install Dependencies

```bash
pip3 install -r requirements.txt
```

This installs:
- **PyQt5**: GUI framework for building desktop applications

### Step 4: Make main script executable (optional)

```bash
chmod +x main.py
```

## Running the Application

### Method 1: Direct Python Execution

```bash
cd ~/Desktop/AIFE
python3 main.py
```

### Method 2: Direct script execution (if made executable)

```bash
cd ~/Desktop/AIFE
./main.py
```

### Method 3: Install as command (optional)

```bash
# Copy to system path
sudo cp main.py /usr/local/bin/aife
sudo chmod +x /usr/local/bin/aife

# Now run from anywhere
aife
```

## Project Structure

```
AIFE/
├── main.py                 # Entry point
├── requirements.txt        # Python dependencies
├── src/
│   ├── filesystem.py      # File system abstraction layer
│   ├── file_manager.py    # File manager with error handling
│   └── gui.py             # PyQt5 GUI application
└── docs/
    ├── ARCHITECTURE.md    # Architecture and OS concepts
    ├── SETUP.md           # This file
    └── OS_CONCEPTS.md     # Detailed OS concepts explanation
```

## Features Implemented

### Phase 1 - Core Features

✅ **Directory Browsing**
- List files and folders
- Navigate through directory structure
- Show file metadata (name, size, type, permissions)

✅ **Navigation**
- Back/Forward history
- Parent directory (up)
- Home directory shortcut
- Quick access sidebar (Home, Documents, Downloads, Desktop, Root)
- Location bar navigation

✅ **File Metadata Display**
- File name and type (file, folder, symlink)
- File size in bytes
- Modification time
- Permission bits (octal format)
- Inode number
- Owner UID/GID
- Hard link count

✅ **File Operations**
- **Open**: Double-click files to open with default application
- **Rename**: Right-click → Rename (with validation)
- **Delete**: Right-click → Delete (with confirmation)
- **Properties**: Right-click → Properties (view full metadata)

✅ **Error Handling**
- Permission errors (EACCES, EPERM)
- File not found errors
- Invalid operation errors
- User-friendly error messages
- Graceful degradation

✅ **Permission Checks**
- Check read permission before listing directory
- Check write+execute permission before delete/rename
- Display permission bits in octal format
- Respect Unix permission model

## OS Concepts Demonstrated

### 1. User Space vs Kernel Space
The application runs in user space and makes system calls through Python's `os` module.

**Files to examine**:
- [src/filesystem.py](../src/filesystem.py) - Lines with `os.stat()`, `os.listdir()`, `os.remove()`

**Key demonstrations**:
- Line 178: `os.stat(path)` - System call for file metadata
- Line 166: `os.listdir(path)` - System call to list directory
- Line 249: `os.remove(path)` - System call to delete file
- Line 280: `os.rename()` - System call to rename file

### 2. Virtual File System (VFS)
The `FileSystemAbstraction` class demonstrates VFS concepts.

**Files to examine**:
- [src/filesystem.py](../src/filesystem.py) - FileSystemAbstraction class

**Key demonstrations**:
- Path normalization (realpath resolution)
- Unified file representation (FileNode class)
- File type detection via mode bits (S_ISDIR, S_ISLNK)
- Abstraction over underlying OS calls

### 3. File Permissions and Access Control
Strict permission validation following Unix permission model.

**Files to examine**:
- [src/filesystem.py](../src/filesystem.py) - Methods: `can_read()`, `can_write()`, `can_execute()`
- [src/filesystem.py](../src/filesystem.py) - `delete_file()` method checks W_OK | X_OK on parent

**Key demonstrations**:
- Line 340: `os.access(path, os.R_OK | os.X_OK)` - Read + execute permission check
- Line 361: `os.access(parent, os.W_OK | os.X_OK)` - Write + execute on parent
- Line 419: Permission octal format extraction

### 4. System Calls
Direct mapping to Linux system calls.

**Files to examine**:
- [src/filesystem.py](../src/filesystem.py) - Lines with comments "System call:"

**System calls used**:
1. `stat()` - Get file metadata
2. `getdents()/getdents64()` - List directory contents
3. `open()` - Used in open file operation
4. `unlink()` - Delete files
5. `rmdir()` - Delete directories
6. `rename()/renameat()` - Rename files
7. `access()` - Check file accessibility
8. `readlink()` - Resolve symbolic links

### 5. File Inodes and Metadata
Complete inode-like information extraction.

**Files to examine**:
- [src/filesystem.py](../src/filesystem.py) - FileNode class

**Inode information extracted**:
```python
st_ino         # Inode number
st_size        # File size
st_mode        # File type + permissions
st_uid/st_gid  # Owner information
st_mtime       # Modification time
st_atime       # Access time
st_nlink       # Hard link count
```

### 6. File Types
Differentiation of file types via mode bits.

**Files to examine**:
- [src/filesystem.py](../src/filesystem.py) - Line 181-182

**File types supported**:
- Regular files (S_IFREG)
- Directories (S_ISDIR)
- Symbolic links (S_ISLNK)
- Permission bits (rwx for user/group/other)

## Testing the Application

### Test 1: View Home Directory
```
1. Launch application
2. Should show files/folders in home directory
3. Check metadata (size, permissions, time)
4. Demonstrates: os.listdir(), os.stat(), VFS abstraction
```

### Test 2: Navigate to Subdirectory
```
1. Double-click on a folder
2. Should navigate to that folder
3. Breadcrumb shows current path
4. Demonstrates: path resolution, directory traversal
```

### Test 3: Check Permissions
```
1. Right-click file → Properties
2. View permission octal (e.g., 644, 755)
3. View as string (e.g., rw-r--r--)
4. Demonstrates: permission bit extraction, VFS metadata
```

### Test 4: Rename File (With Permission)
```
1. Create a test file in home directory
2. Right-click → Rename
3. Change name and confirm
4. Should succeed if you own file
5. Demonstrates: os.rename() system call
```

### Test 5: Delete File (With Permission)
```
1. Create a test file in home directory
2. Right-click → Delete → Confirm
3. Should succeed if you have write permission
4. Demonstrates: os.remove() system call, permission checks
```

### Test 6: Permission Denied Scenarios
```
1. Navigate to /root directory
2. Try to delete a file → Permission denied
3. Error message: "No permission to delete"
4. Demonstrates: Permission enforcement, PermissionError handling
```

### Test 7: Open File
```
1. Double-click on a .txt or image file
2. Should open with default application (xdg-open)
3. Demonstrates: os.open() concept, desktop integration
```

### Test 8: Navigate System Directories
```
1. Quick access: Click "Root"
2. Navigate to /etc, /home, /usr
3. View different file types and permissions
4. Some directories may show permission errors
5. Demonstrates: filesystem structure, permission boundaries
```

## Understanding the Code

### Layer 1: GUI (gui.py)
- User interface with PyQt5
- Handles all user interactions
- Calls file manager for operations
- Updates display based on results

```python
# GUI makes calls like:
result = self.file_manager.open_file(path)
result = self.file_manager.delete_file(path)
result = self.file_manager.rename_file(old_path, new_name)
```

### Layer 2: File Manager (file_manager.py)
- Business logic coordination
- Error handling and translation
- Permission validation
- Operation callbacks

```python
# File manager makes calls like:
self.fs.list_directory(path)
self.fs.delete_file(path)
self.fs.rename_file(old_path, new_path)
```

### Layer 3: File System Abstraction (filesystem.py)
- Direct OS system call wrappers
- Path validation and normalization
- Permission checks
- File metadata extraction

```python
# File system layer makes calls like:
os.stat(path)       # Get metadata
os.listdir(path)    # List contents
os.remove(path)     # Delete file
os.rename(...)      # Rename file
os.access(path, m)  # Check permissions
```

### Layer 4: Linux Kernel (not modified)
- Virtual File System implementation
- Inode management
- Permission enforcement
- File system drivers

## Troubleshooting

### Issue: "No module named PyQt5"
```bash
# Solution: Install PyQt5
pip3 install PyQt5
```

### Issue: "Permission denied" when running script
```bash
# Solution: Make executable
chmod +x main.py

# Or run with python3
python3 main.py
```

### Issue: Window doesn't appear
```bash
# Check for display server
echo $DISPLAY

# If using WSL2, ensure X11 is configured
# Or use: DISPLAY=:0 python3 main.py
```

### Issue: Cannot delete file in certain directories
```
This is expected behavior - the application respects Unix permissions.
Ensure you have write permission on the parent directory.

Check permissions with:
ls -la /path/to/parent/
```

## Performance Considerations

- The application runs single-threaded
- Large directory listings (10,000+ files) may lag
- No caching of directory contents (always fresh from OS)
- Suitable for typical use cases (home directories, documents, etc.)

## Security Considerations

1. **No Privilege Escalation**: Respects user permissions strictly
2. **No Path Traversal**: Validates all paths
3. **No Shell Injection**: Uses subprocess safely
4. **Runs as User**: No sudo required
5. **VFS Boundary**: Cannot bypass OS permission checks

## Next Steps (Phase 2 - Future)

- [ ] Search functionality
- [ ] File sorting and filtering
- [ ] Batch operations
- [ ] File content preview
- [ ] Drag and drop
- [ ] Bookmarks/favorites
- [ ] File compression
- [ ] Multi-threading for responsive UI

## Viva/Demo Script

### Opening Statement
"AIFE is a custom file explorer demonstrating key OS concepts: Virtual File System abstraction, system calls, permission checks, and error handling. It's built with a layered architecture separating presentation, business logic, and OS abstraction."

### Demo Flow
1. **Launch**: `python3 main.py`
2. **Show home directory**: "This uses os.listdir() and os.stat() system calls"
3. **Navigate folder**: "This demonstrates path resolution through VFS"
4. **Show properties**: "This is the inode metadata from stat() call"
5. **Try rename**: "This uses the rename() system call"
6. **Try permission error**: "Navigate to /root, try delete - shows permission enforcement"
7. **Show code**: Open filesystem.py and explain layers

### Key Points to Emphasize
- ✅ User space application (no kernel modification)
- ✅ Direct system calls via Python os module
- ✅ VFS abstraction hides complexity
- ✅ Respects Unix permission model
- ✅ Graceful error handling
- ✅ Modular, testable design
- ✅ Runs as unprivileged user

## Submission Checklist

- ✅ Architecture documentation
- ✅ Source code with OS concepts clearly marked
- ✅ Comments explaining system calls
- ✅ Error handling demonstration
- ✅ Permission checks implementation
- ✅ Setup and running instructions
- ✅ Test scenarios
- ✅ Viva preparation guide

## Additional Resources

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture information.
