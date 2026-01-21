# OS Concepts Deep Dive - AIFE Implementation

## Table of Contents
1. User Space vs Kernel Space
2. Virtual File System (VFS)
3. System Calls
4. File Permissions and Access Control
5. Inodes and File Metadata
6. Error Handling and errno

---

## 1. User Space vs Kernel Space

### Concept
Modern operating systems use privilege separation:
- **Kernel Space**: Privileged mode with direct hardware access
- **User Space**: Unprivileged mode, restricted access

### AIFE Implementation

AIFE is entirely a **user space application**:
```
┌─────────────────────────────────────┐
│      User Space (AIFE)              │
│  ┌─────────────────────────────┐    │
│  │ GUI Layer (PyQt5)           │    │
│  │ File Manager Layer          │    │
│  │ File System Abstraction     │    │
│  └─────────────────────────────┘    │
└──────────────┬──────────────────────┘
               │ System Calls
┌──────────────▼──────────────────────┐
│  Kernel Space (Protected)           │
│  ├── VFS (Virtual File System)     │
│  ├── File System Drivers            │
│  ├── Inode Management               │
│  └── Permission Enforcement         │
└─────────────────────────────────────┘
```

### Key Characteristic: CANNOT Execute Privileged Operations
```python
# ✅ These work (unprivileged user space)
os.stat(path)           # Read file metadata
os.listdir(path)        # List directory
os.remove(path)         # Delete own file

# ❌ These would fail (need sudo)
os.mount(...)           # Mount filesystem
os.chmod(path, 0o644)   # Change file permissions
os.chown(path, uid, gid) # Change file owner
```

### Code Location
[src/filesystem.py](../src/filesystem.py) - All operations run as unprivileged user

### Demonstration in Viva
```
Run: /home/user/AIFE$ python3 main.py
- Application starts as normal user (no sudo)
- Navigate to protected directory (e.g., /root)
- Try to delete a file
- Result: PermissionError - boundary enforced by kernel
```

---

## 2. Virtual File System (VFS)

### Concept
The Linux VFS is an abstraction layer that:
- Presents unified interface for all file systems
- Hides implementation details of specific file systems
- Maps inode objects across different file systems (ext4, btrfs, nfs, etc.)
- Provides consistent operations (open, read, write, delete)

### AIFE's VFS Abstraction

Our `FileSystemAbstraction` class emulates VFS concepts:

```python
class FileSystemAbstraction:
    """
    Virtual File System Abstraction
    - Hides OS-specific implementation
    - Provides unified interface
    - Handles path resolution
    - Abstracts file types and metadata
    """
    
    def list_directory(self, path: str) -> List[FileNode]:
        """Returns standardized FileNode objects"""
        
    def get_file_info(self, path: str) -> FileNode:
        """Uniform metadata extraction"""
```

### FileNode: Inode-like Representation
The `FileNode` class mirrors the Linux inode structure:

```python
@dataclass
class FileNode:
    # From inode.st_ino
    inode_number: int
    
    # From inode.st_mode
    is_dir: bool              # S_ISDIR(mode)
    is_symlink: bool          # S_ISLNK(mode)
    permissions: int          # S_IMODE(mode)
    
    # From inode metadata
    size: int                 # st_size
    owner_uid: int            # st_uid
    owner_gid: int            # st_gid
    modified_time: float      # st_mtime
    hard_links: int           # st_nlink
```

### VFS Path Resolution

When you navigate `~/Documents/file.txt`:

1. Start at root inode (/)
2. Resolve "home" directory entry → inode of /home
3. Resolve "user" entry → inode of /home/user
4. Resolve "Documents" entry → inode of /home/user/Documents
5. Resolve "file.txt" entry → inode of /home/user/Documents/file.txt

**Our code does this:**
```python
def normalize_path(self, path: str) -> str:
    """VFS path resolution"""
    return os.path.realpath(os.path.expanduser(path))
```

### Unified Interface Over Different File Systems

```python
# Same code works for:
# - ext4 file system
# - btrfs file system
# - NFS (network)
# - tmpfs
# - Different mount points
files = self.fs.list_directory("/home")      # ext4
files = self.fs.list_directory("/tmp")       # tmpfs
files = self.fs.list_directory("/proc")      # procfs
```

The VFS abstraction means our code doesn't care which underlying file system is used.

### Code Location
[src/filesystem.py](../src/filesystem.py#L87) - FileSystemAbstraction class

### Demonstration in Viva
```
1. Launch AIFE and navigate to different mount points:
   - /home (ext4)
   - /tmp (tmpfs)
   - /proc (procfs)
   - /sys (sysfs)
2. Same code works for all
3. Explain: "VFS abstraction hides file system differences"
```

---

## 3. System Calls

### Concept
System calls are the interface between user space and kernel space.
Made via machine instructions that switch to kernel mode.

### AIFE's System Calls

Our application uses these system calls (via Python's `os` module):

#### 3.1 stat() - Get File Metadata
```python
# Code in filesystem.py, line 178
stat_result = os.stat(file_path)

# Maps to Linux system call: stat(2)
# Returns inode information:
mode = stat_result.st_mode      # File type + permissions
size = stat_result.st_size      # File size in bytes
uid = stat_result.st_uid        # Owner user ID
gid = stat_result.st_gid        # Owner group ID
mtime = stat_result.st_mtime    # Modification timestamp
ino = stat_result.st_ino        # Inode number
nlink = stat_result.st_nlink    # Hard link count
```

**In kernel**: Locates inode, reads metadata

#### 3.2 readdir() / getdents() - List Directory
```python
# Code in filesystem.py, line 166
entries = os.listdir(path)

# Maps to Linux system call: getdents64(2)
# Returns list of directory entries:
# [
#   {"name": "file1.txt", "inode": 123456},
#   {"name": "folder", "inode": 123457},
#   ...
# ]
```

**In kernel**: Reads directory block, parses entries

#### 3.3 rename() - Rename File
```python
# Code in filesystem.py, line 277
os.rename(old_path, new_path)

# Maps to Linux system call: renameat2(2)
# Atomically updates directory entry
# Requires write permission on parent directory
```

**In kernel**: Updates parent directory inode, atomic operation

#### 3.4 unlink() - Delete File
```python
# Code in filesystem.py, line 269
os.remove(path)

# Maps to Linux system call: unlink(2)
# Removes directory entry, decrements link count
# If link count = 0 and no open file descriptors, frees blocks
```

**In kernel**: Updates parent directory, decrements inode link count

#### 3.5 access() - Check Permissions
```python
# Code in filesystem.py, line 334
os.access(path, os.R_OK | os.X_OK)

# Maps to Linux system call: access(2)
# Checks if calling process can access file
# Respects UID, GID, and permission bits
```

**In kernel**: Reads inode permissions, checks effective UID

#### 3.6 open() - Open File Descriptor
```python
# Code in file_manager.py, line 131
subprocess.Popen(['xdg-open', path])

# Uses open(2) system call under the hood
# Returns file descriptor for I/O operations
```

**In kernel**: Allocates file descriptor, initializes inode reference

### System Call Trace

To see actual system calls made:
```bash
# Trace all system calls
strace -e trace=stat,openat,getdents64,unlink,rename,access python3 main.py

# Output shows:
# stat("/home/user", ...) = 0
# getdents64(3, ...) = 1234
# unlink("/home/user/oldfile") = 0
# rename("/home/user/a", "/home/user/b") = 0
```

### Code Locations
- **stat**: [src/filesystem.py](../src/filesystem.py#L178)
- **listdir**: [src/filesystem.py](../src/filesystem.py#L166)
- **rename**: [src/filesystem.py](../src/filesystem.py#L277)
- **remove**: [src/filesystem.py](../src/filesystem.py#L269)
- **access**: [src/filesystem.py](../src/filesystem.py#L334)
- **open**: [src/file_manager.py](../src/file_manager.py#L131)

### Demonstration in Viva
```bash
# Terminal 1: Run strace on AIFE
strace -f -e trace=stat,openat,getdents64 python3 main.py

# Terminal 2: Use AIFE
# - Double-click folder: watch getdents64 calls
# - Right-click Properties: watch stat calls
# - Delete file: watch unlink call
```

---

## 4. File Permissions and Access Control

### Concept
Unix permissions protect files through:
- **Owner permissions**: Read, Write, Execute for file owner
- **Group permissions**: Read, Write, Execute for group
- **Other permissions**: Read, Write, Execute for others

Permission bits in inode `st_mode`:
```
rwxrwxrwx
│││││││└─ Other-Execute
││││││└── Other-Write
│││││└─── Other-Read
││││└──── Group-Execute
│││└───── Group-Write
││└────── Group-Read
│└─────── Owner-Execute
└──────── Owner-Write
└──────── Owner-Read
```

### AIFE Implementation

#### 4.1 Permission Validation Before Operations

**Before deleting a file:**
```python
# filesystem.py, line 363
parent = os.path.dirname(path)
if not os.access(parent, os.W_OK | os.X_OK):
    raise PermissionError(f"No permission to delete {path}")
```

Why W_OK | X_OK on parent?
- **W_OK (Write)**: Can modify directory entries (add/remove files)
- **X_OK (Execute)**: Can access files in directory

**Before listing a directory:**
```python
# filesystem.py, line 162
if not os.access(path, os.R_OK | os.X_OK):
    raise PermissionError(f"No permission to read directory: {path}")
```

#### 4.2 Permission Extraction and Display

```python
# filesystem.py, line 135
permissions = stat.S_IMODE(mode)  # Extract rwx bits

# Display as octal (755, 644, etc.)
oct_perms = oct(permissions)[2:]  # "755"

# Display as string (rwxr-xr-x)
perm_str = stat.filemode(mode)    # "drwxr-xr-x"
```

#### 4.3 File Type Detection

File type is part of `st_mode`, not separate permission bits:

```python
# filesystem.py, line 125
is_dir = stat.S_ISDIR(mode)        # Directory?
is_symlink = stat.S_ISLNK(mode)    # Symbolic link?
is_file = stat.S_ISREG(mode)       # Regular file?
```

### Permission Examples

#### Example 1: Deleting Your Own File
```
File: /home/alice/myfile.txt
Mode: -rw-r--r-- (644)

Parent directory: /home/alice
Mode: drwxr-xr-x (755)

Result: ✅ Alice can delete (owns parent, has write)
```

#### Example 2: Deleting Another User's File (same directory)
```
File: /home/alice/bob_file.txt (owned by bob)
Parent: /home/alice (owned by alice)

Result: ✅ Alice CAN delete (has write on parent)
Note: Ownership of file doesn't matter, parent does!
```

#### Example 3: Permission Denied
```
Directory: /root
Mode: drwx------ (700) - only root can access

User alice tries to browse:
Result: ❌ PermissionError (no read, no execute)
```

### Code Locations
- **Permission checks**: [src/filesystem.py](../src/filesystem.py#L334-L345)
- **Delete validation**: [src/filesystem.py](../src/filesystem.py#L360-L369)
- **Rename validation**: [src/filesystem.py](../src/filesystem.py#L406-L412)
- **Display**: [src/gui.py](../src/gui.py#L258)

### Demonstration in Viva
```bash
# Create test scenario
cd ~/Desktop/AIFE
mkdir test_perms
echo "content" > test_perms/file.txt

# Full permissions
chmod 755 test_perms
# Result: AIFE can delete files

# Remove write permission
chmod 555 test_perms
# Result: AIFE shows PermissionError when trying to delete
```

---

## 5. Inodes and File Metadata

### Concept
An **inode** (index node) is the data structure that stores file metadata:
- Size, permissions, ownership
- Timestamps (modified, accessed, changed)
- Link count, file type
- Pointers to data blocks (not fully exposed in our app)

### AIFE's Inode Extraction

Our `FileNode` class maps to inode fields:

```python
stat_result = os.stat(path)

FileNode(
    name=entry,
    path=file_path,
    
    # From inode.st_mode (file type bits)
    is_dir=stat.S_ISDIR(mode),
    is_symlink=stat.S_ISLNK(mode),
    
    # From inode.st_mode (permission bits)
    permissions=stat.S_IMODE(mode),
    
    # Direct inode fields
    size=stat_result.st_size,           # st_size
    owner_uid=stat_result.st_uid,       # st_uid
    owner_gid=stat_result.st_gid,       # st_gid
    modified_time=stat_result.st_mtime, # st_mtime
    accessed_time=stat_result.st_atime, # st_atime
    inode_number=stat_result.st_ino,    # st_ino
    hard_links=stat_result.st_nlink,    # st_nlink
)
```

### Inode Fields Explained

| Field | Value | Meaning |
|-------|-------|---------|
| `st_ino` | 12345 | Unique inode number for this file |
| `st_size` | 4096 | File size in bytes |
| `st_mode` | 33188 | File type (regular=0100000) + permissions (644) |
| `st_uid` | 1000 | User ID of owner |
| `st_gid` | 1000 | Group ID of owner |
| `st_mtime` | 1704067200.5 | Last modification (Unix timestamp) |
| `st_atime` | 1704067200.5 | Last access time |
| `st_ctime` | 1704067200.5 | Last status change |
| `st_nlink` | 1 | Number of hard links |

### Why `st_ctime` is not included
`st_ctime` (change time) is NOT the creation time. It's when the inode metadata last changed. Most file systems don't store creation time (btime), so we skip it.

### Symbolic Links

Symlinks have special behavior:
```python
# os.stat() follows symlinks
stat_result = os.stat("/path/to/symlink")  # Stats target file

# os.lstat() does NOT follow symlinks
stat_result = os.lstat("/path/to/symlink")  # Stats symlink itself
```

AIFE uses `os.stat()` which is appropriate for most operations.

### Hard Links

When `st_nlink > 1`, the file has multiple directory entries pointing to the same inode:

```bash
$ ls -i
12345 file1.txt
12345 file2.txt  # Same inode number!

$ rm file1.txt   # Deletes entry, unlink() decrements nlink
$ # File content still exists via file2.txt
```

### Code Location
[src/filesystem.py](../src/filesystem.py#L35-L76) - FileNode class with all inode fields

### Demonstration in Viva
```python
# In AIFE properties dialog:
# Inode: 12345
# Hard Links: 2 (means multiple names for same file)
# Size: 4096
# Modified: 2024-01-01 12:00:00
# Permissions: 644 (rw-r--r--)
```

---

## 6. Error Handling and errno

### Concept
System calls set the `errno` global variable on failure.
Python translates errno into exceptions.

### AIFE's Error Mapping

```python
try:
    os.stat(path)
except FileNotFoundError:           # errno = ENOENT (2)
    # File doesn't exist
except PermissionError:             # errno = EACCES (13)
    # No permission to access
except IsADirectoryError:           # errno = EISDIR (21)
    # Operation invalid on directory
except NotADirectoryError:          # errno = ENOTDIR (20)
    # Path component is not directory
except OSError as e:
    # Generic OS error, e.errno contains actual errno
```

### Specific Error Scenarios in AIFE

#### 1. File Not Found (ENOENT)
```python
# filesystem.py, line 333
try:
    stat_result = os.stat(path)
except FileNotFoundError:
    raise FileNotFoundError(f"File not found: {path}")
```

#### 2. Permission Denied (EACCES)
```python
# filesystem.py, line 162
if not os.access(path, os.R_OK | os.X_OK):
    raise PermissionError(f"No permission to read directory: {path}")
```

#### 3. Directory Not Empty (ENOTEMPTY)
```python
# Raised by os.rmdir() when directory not empty
try:
    os.rmdir(path)
except IsADirectoryError:
    raise IsADirectoryError(f"Directory not empty: {path}")
```

#### 4. File Exists (EEXIST)
```python
# filesystem.py, line 426
if os.path.exists(new_path):
    raise FileExistsError(f"Destination already exists: {new_path}")
```

### User-Friendly Error Messages

AIFE translates low-level OS errors to user messages:

```python
# file_manager.py, line 74
except PermissionError as e:
    result = OperationResult(
        success=False,
        message=f"Permission denied. You don't have read access to this folder."
        # This is clearer than: "OSError: [Errno 13] Permission denied"
    )
```

### Error Handling Layers

```
Layer 1 (GUI):          Show dialog to user
    ↓
Layer 2 (FileManager):  Translate OS error to message
    ↓
Layer 3 (FileSystem):   Catch and re-raise with context
    ↓
Layer 4 (OS):           System call returns errno
```

### Code Location
- **FileSystem errors**: [src/filesystem.py](../src/filesystem.py#L155-L200)
- **FileManager errors**: [src/file_manager.py](../src/file_manager.py#L60-L120)
- **GUI errors**: [src/gui.py](../src/gui.py#L259-L274)

### Demonstration in Viva
```
1. Try to navigate to /root
   Error shown: "Permission denied. You don't have read access"
   
2. Explain: "System call access() returned EACCES (errno 13)"
   
3. Show code mapping:
   - OS errno 13
   - Python PermissionError exception
   - User-friendly message in GUI
```

---

## Summary: OS Concepts in AIFE

| Concept | Implementation | Code Location |
|---------|----------------|----------------|
| User space | Python application, no kernel code | main.py, src/*.py |
| Kernel space boundary | Respect permission checks, cannot escalate | file_manager.py |
| VFS abstraction | FileSystemAbstraction class | filesystem.py #87 |
| FileNode (inode) | @dataclass FileNode with metadata | filesystem.py #35 |
| System calls | os.stat, os.listdir, os.remove, etc. | filesystem.py #178+ |
| Permissions | os.access() checks, rwx validation | filesystem.py #334+ |
| Errors & errno | Exception mapping and handling | filesystem.py #155+ |

---

## Interview Questions & Answers

**Q: How does AIFE demonstrate the VFS?**
A: The FileSystemAbstraction class provides a unified interface over different file systems. The same list_directory() method works on ext4 (/home), tmpfs (/tmp), procfs (/proc), etc. The VFS hides these differences.

**Q: What system calls does AIFE make?**
A: stat(), readdir(), rename(), unlink(), access(), open(). Each is wrapped by Python's os module and involves switching to kernel mode.

**Q: Why does delete require write+execute on parent directory?**
A: Write permission allows modifying directory entries. Execute permission allows accessing the directory itself. Both are needed to remove an entry.

**Q: What happens when you try to access /root?**
A: os.access() returns False, raising PermissionError. The kernel enforces this via permission bits (700 = drwx------).

**Q: How does AIFE handle errors?**
A: System calls raise OS exceptions (FileNotFoundError, PermissionError). FileManager catches these and generates user messages. GUI displays the messages in dialogs.

---

## Further Reading

See [ARCHITECTURE.md](ARCHITECTURE.md) for component diagrams and layered design.
