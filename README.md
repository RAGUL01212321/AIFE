# AIFE - Advanced Interactive File Explorer

A custom file explorer for Ubuntu Linux demonstrating fundamental Operating Systems concepts through a PyQt5 desktop application.

**For Operating Systems Course Project | Suitable for Viva & Demo**

## 🎯 Quick Start

```bash
# Clone/navigate to project
cd ~/Desktop/AIFE

# Install dependencies
pip3 install -r requirements.txt

# Run the application
python3 main.py
```

## 📋 Project Overview

AIFE demonstrates:
- ✅ User space vs kernel space boundary
- ✅ Virtual File System (VFS) abstraction
- ✅ System calls (stat, readdir, open, unlink, rename, access)
- ✅ Unix file permissions and access control
- ✅ Inode metadata and file types
- ✅ Error handling and errno translation
- ✅ Modular, layered architecture

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│   PyQt5 GUI (User Interface)        │
├─────────────────────────────────────┤
│ File Manager (Business Logic)       │
├─────────────────────────────────────┤
│ File System Abstraction (VFS)       │
├─────────────────────────────────────┤
│ System Call Wrappers (os module)    │
├─────────────────────────────────────┤
│ Linux Kernel [NOT MODIFIED]         │
└─────────────────────────────────────┘
```

Each layer demonstrates specific OS concepts.

## 📁 Project Structure

```
AIFE/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies (PyQt5)
├── src/
│   ├── filesystem.py      # VFS abstraction layer
│   ├── file_manager.py    # File operations coordinator
│   └── gui.py             # PyQt5 GUI application
└── docs/
    ├── ARCHITECTURE.md    # Component & layer details
    ├── SETUP.md           # Installation & usage guide
    └── OS_CONCEPTS.md     # Deep dive into OS concepts
```

## ✨ Features (Phase 1)

### Navigation
- Browse directories and files
- Back/Forward history
- Parent directory navigation
- Home directory shortcut
- Quick access sidebar (Home, Documents, Downloads, Desktop, Root)
- Location bar for direct path input

### File Operations
- **Open**: Double-click to open with default application
- **Rename**: Right-click → Rename with validation
- **Delete**: Right-click → Delete with confirmation
- **Properties**: View complete metadata

### Metadata Display
- File name and type (file, folder, symlink)
- File size and timestamps
- Permission bits (octal and string format)
- Inode number and hard links
- Owner UID/GID
- Modification and access times

### Error Handling
- Permission errors (EACCES, EPERM)
- File not found errors
- Directory not empty errors
- User-friendly error messages
- Graceful degradation

## 🔑 Key OS Concepts Demonstrated

### 1. User Space vs Kernel Space
Application runs as unprivileged user - demonstrates privilege boundary through permission enforcement.

**Code**: [src/filesystem.py](src/filesystem.py) - All operations run without sudo

### 2. Virtual File System (VFS)
FileSystemAbstraction provides unified interface over different file systems (ext4, tmpfs, procfs, etc.).

**Code**: [src/filesystem.py](src/filesystem.py#L87) - FileSystemAbstraction class

### 3. System Calls
Direct mapping to Linux system calls:
- `stat()` - File metadata
- `getdents()/getdents64()` - List directory
- `rename()` - Rename file
- `unlink()` - Delete file
- `access()` - Check permissions
- `open()` - Open file descriptor

**Code**: [src/filesystem.py](src/filesystem.py) - Lines with os.* calls

### 4. File Permissions & Access Control
Strict Unix permission model enforcement (rwx bits for user/group/other).

**Code**: [src/filesystem.py](src/filesystem.py#L334) - can_read(), can_write(), can_execute()

### 5. Inodes and Metadata
Complete inode information extraction via stat() system call.

**Code**: [src/filesystem.py](src/filesystem.py#L35) - FileNode class

### 6. Error Handling
System error translation and user-friendly messages.

**Code**: [src/file_manager.py](src/file_manager.py#L60) - Error handling in FileManager

## 🚀 Installation

### Requirements
- Ubuntu Linux (20.04 LTS or later)
- Python 3.8+
- pip3

### Steps

```bash
# 1. Navigate to project directory
cd ~/Desktop/AIFE

# 2. Install Python dependencies
pip3 install -r requirements.txt

# 3. Make main script executable (optional)
chmod +x main.py
```

## 📖 Usage

### Run Application
```bash
# Method 1: Python
python3 main.py

# Method 2: Executable script
./main.py

# Method 3: From anywhere (after system installation)
aife
```

### Basic Operations
1. **Browse**: Double-click folders to navigate
2. **View Metadata**: Right-click any file → Properties
3. **Rename**: Right-click → Rename (with validation)
4. **Delete**: Right-click → Delete (with confirmation)
5. **Navigate Back**: Click "← Back" button
6. **Go Home**: Click "🏠 Home" button

## 🧪 Testing Scenarios

### Test 1: Directory Browsing
Navigate through different directories, verify file listings and metadata.

### Test 2: Permission Errors
Try navigating to `/root` or deleting files you don't own.

**Expected**: PermissionError message explaining insufficient permissions.

### Test 3: File Operations
Create test files, rename them, delete them.

**Expected**: Operations succeed with ownership verification.

### Test 4: View Inode Information
Right-click any file → Properties → Shows inode number, permissions, etc.

### Test 5: Symlinks
Navigate to a directory with symlinks (e.g., `/etc`).

**Expected**: Symlinks displayed with 🔗 icon.

## 📚 Documentation

- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Component design, layer responsibilities, data flow
- **[SETUP.md](docs/SETUP.md)** - Detailed setup, testing scenarios, troubleshooting
- **[OS_CONCEPTS.md](docs/OS_CONCEPTS.md)** - Deep dive into each OS concept with code examples

## 🎓 Viva Preparation

### Opening Statement
"AIFE is a custom file explorer built with Python and PyQt5 that demonstrates key Operating Systems concepts: Virtual File System abstraction, system calls, Unix permissions, and inode-based file metadata. It's structured in layers, with clear separation between user space application and kernel space boundaries."

### Key Points to Highlight
1. ✅ **VFS Abstraction**: FileSystemAbstraction class hides OS details
2. ✅ **System Calls**: Direct mapping to Linux syscalls (stat, readdir, unlink, etc.)
3. ✅ **Permissions**: Enforces Unix permission model (rwx bits, user/group/other)
4. ✅ **Inode Metadata**: Complete metadata extraction and display
5. ✅ **Error Handling**: Proper exception handling with meaningful messages
6. ✅ **No Privilege Escalation**: Runs as regular user (respects boundaries)
7. ✅ **Modular Design**: Clear layer separation for maintainability

### Demo Script
```
1. Launch: python3 main.py
   → Shows application starts as regular user

2. Navigate home directory
   → Explain: Uses os.listdir() system call

3. Open file properties
   → Explain: Uses os.stat() to extract inode information

4. Attempt to access /root
   → Explain: Permission error shows kernel boundary

5. Create and rename a file
   → Explain: Uses os.rename() system call

6. Try deleting with insufficient permissions
   → Explain: PermissionError from access() check

7. Open filesystem.py
   → Walk through system call wrappers
   → Explain VFS abstraction layer
```

### Expected Questions

**Q: Why can't you delete files in /root?**
A: /root has permissions 700 (drwx------). We're not root, so kernel enforces PermissionError.

**Q: How is this different from the normal file manager?**
A: This demonstrates OS concepts. It's built from scratch using system calls, showing how file managers work internally.

**Q: What system calls are used?**
A: stat(), readdir(), rename(), unlink(), access(), open(). Each is a boundary crossing from user to kernel space.

**Q: Can you modify the Linux kernel?**
A: No. AIFE respects the kernel boundary. Permission enforcement happens in the kernel, not in our code.

## 🔒 Security Features

- ✅ No privilege escalation (no sudo)
- ✅ Respects Unix permissions strictly
- ✅ No path traversal vulnerabilities
- ✅ No shell injection risks
- ✅ Validates all paths
- ✅ Cannot bypass OS permission checks

## 🚧 Future Enhancements (Phase 2)

- [ ] Search and filter
- [ ] File sorting (by name, size, date)
- [ ] Batch operations
- [ ] File content preview
- [ ] Drag and drop support
- [ ] Bookmarks/favorites
- [ ] File compression
- [ ] Multi-threading for responsive UI
- [ ] Configuration/settings
- [ ] Theme support

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError: No module named 'PyQt5'
**Solution**: `pip3 install PyQt5`

### Issue: Cannot delete files
**Solution**: Check ownership and permissions. Run `ls -la` to verify write permission on parent directory.

### Issue: Application doesn't start
**Solution**: Ensure X11 display is available. If using SSH/WSL, configure display forwarding.

### Issue: Permission denied on certain directories
**Solution**: This is expected - the application respects kernel permission boundaries. Navigate only to directories where you have access.

## 📝 Notes

- Single-threaded GUI (may block on very large directories)
- No caching (always reads fresh from filesystem)
- Respects user permissions (no sudo needed)
- Suitable for typical desktop use (home directories, documents, etc.)
- Design optimized for clarity of OS concepts, not production features

## 📄 License

Educational project for Operating Systems course.

## ✅ Checklist for Submission

- [x] Architecture documentation
- [x] Source code with OS concept comments
- [x] System call documentation
- [x] Error handling implementation
- [x] Permission checks
- [x] Setup and running instructions
- [x] Test scenarios
- [x] Viva preparation guide
- [x] README with overview
- [x] Modular design

## 📞 Support

For issues or questions about implementation, refer to the documentation:
- Component questions → [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- Setup issues → [SETUP.md](docs/SETUP.md)
- OS concept questions → [OS_CONCEPTS.md](docs/OS_CONCEPTS.md)

---

**Built with Python 3.8+, PyQt5 5.15+, for Ubuntu Linux**
