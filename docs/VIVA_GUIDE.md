# AIFE Viva Guide - Complete Preparation

## Pre-Viva Checklist

- [ ] Application runs without errors (`python3 main.py`)
- [ ] All features work (navigate, open, rename, delete)
- [ ] Documentation is printed/available
- [ ] Can explain architecture clearly
- [ ] Know the OS concepts demonstrated
- [ ] Understand system call mappings
- [ ] Can show code examples
- [ ] Have test scenarios ready

---

## Opening Statement (2-3 minutes)

**Use this or similar:**

"AIFE is a custom file explorer application for Ubuntu Linux built with Python and PyQt5. It demonstrates fundamental operating systems concepts through a modular, layered architecture.

The application is divided into four key layers:

1. **GUI Layer** - User interface with PyQt5 showing files and enabling operations
2. **File Manager** - Business logic that coordinates file operations and handles errors
3. **File System Abstraction** - A Virtual File System (VFS) abstraction layer that demonstrates how operating systems hide file system complexity
4. **System Call Wrappers** - Direct Python bindings to Linux system calls (stat, readdir, unlink, rename, access)

This design clearly demonstrates the boundary between user space (where AIFE runs) and kernel space (where actual file system operations happen). The application respects Unix permissions strictly, showing how the kernel enforces access control.

The VFS abstraction shows how the same code works with different file systems (ext4, tmpfs, procfs) without modification. The complete inode metadata extraction demonstrates how operating systems represent files internally.

Finally, comprehensive error handling shows how system call failures are translated into meaningful user messages."

---

## Detailed Component Explanation (3-5 minutes)

### Layer 1: GUI (src/gui.py)
**What it does:** User interface
**OS concepts:** Event handling, UI abstraction

```python
# Key components:
- MainWindow with toolbar navigation
- File list table with metadata
- Properties dialog showing inode information
- Context menus for operations
- Error dialogs for user feedback
```

**Key lines:**
- 95-115: File list population with metadata
- 198-240: Context menu with file operations
- 150-200: Properties dialog showing inode info

**Viva point:** "The GUI layer translates user actions into file manager calls. It doesn't directly manipulate files - it uses the abstraction layers below."

### Layer 2: File Manager (src/file_manager.py)
**What it does:** Coordinate operations and error handling
**OS concepts:** Error mapping, permission validation

```python
class FileManager:
    - browse_directory()      # List files
    - get_file_info()         # Get metadata
    - delete_file()           # Delete with confirmation
    - rename_file()           # Rename with validation
    - open_file()             # Open with xdg-open
```

**Key error handling:**
```python
except PermissionError:        # EACCES errno
    message = "Permission denied..."
except FileNotFoundError:      # ENOENT errno
    message = "File not found..."
except IsADirectoryError:      # EISDIR errno
    message = "Cannot operate on directory..."
```

**Viva point:** "The file manager translates low-level OS errors into user-friendly messages. It validates permissions before attempting operations."

### Layer 3: File System Abstraction (src/filesystem.py)
**What it does:** VFS abstraction and system call wrappers
**OS concepts:** VFS, system calls, inode representation

```python
class FileSystemAbstraction:
    def list_directory(path)
        # Calls os.listdir()  → getdents64() syscall
        # Calls os.stat()     → stat() syscall for each file
        
    def delete_file(path)
        # Calls os.remove()   → unlink() syscall
        
    def rename_file(old, new)
        # Calls os.rename()   → rename() syscall
        
    def can_read/write/execute(path)
        # Calls os.access()   → access() syscall

class FileNode:
    # Mirrors Linux inode structure
    inode_number          # st_ino
    size                  # st_size
    permissions           # st_mode (rwx bits)
    owner_uid/gid         # st_uid, st_gid
    modified_time         # st_mtime
    hard_links            # st_nlink
```

**Viva point:** "This layer demonstrates the Virtual File System concept. The same code works on ext4, tmpfs, procfs, or any other file system. The OS abstracts these differences."

### Layer 4: System Calls (Python os module → Linux Kernel)
**What it does:** Interface to kernel
**OS concepts:** System call interface, privilege boundary

```
User Space Code         Kernel Space
os.stat(path)       →   stat() syscall    →  Inode lookup
os.listdir(path)    →   getdents64()      →  Directory read
os.remove(path)     →   unlink()          →  File deletion
os.rename(old, new) →   rename()          →  File rename
os.access(path, m)  →   access()          →  Permission check
```

**Viva point:** "Each of these is a privilege boundary crossing. The kernel verifies permissions, manages inodes, and enforces access control."

---

## Key OS Concepts Explained (5 minutes)

### 1. User Space vs Kernel Space

**What the examiner wants to know:** Can you explain privilege levels?

**Your answer:**
"Modern OSes have two privilege levels:
- **Kernel space**: Privileged mode, direct hardware access, can execute any instruction
- **User space**: Restricted mode, limited instruction set, must use system calls for privileged operations

AIFE is entirely user space. It cannot:
- Mount file systems (would need mount() syscall as root)
- Change permissions (would need chmod() syscall as root)
- Access other users' files if permissions prevent it

When AIFE tries to delete a file without write permission on parent directory, the kernel refuses and returns EACCES (errno 13). Our code can't override this - the boundary is enforced by hardware and OS."

**Code to show:**
[src/filesystem.py](../src/filesystem.py#L360) - Permission check before delete:
```python
if not os.access(parent, os.W_OK | os.X_OK):
    raise PermissionError(f"No permission to delete {path}")
```

**Live demo:**
- Try navigating to /root (permission denied)
- Try deleting a system file (permission denied)
- Show error message reflecting kernel rejection

### 2. Virtual File System (VFS)

**What the examiner wants to know:** Can you explain abstraction?

**Your answer:**
"The Virtual File System is Linux's abstraction layer for file operations:

```
Different File Systems:    ext4 | btrfs | NFS | tmpfs | procfs
                             ↓      ↓      ↓     ↓       ↓
                          ┌─────────────────────────────────┐
                          │  VFS Abstraction Layer          │
                          │ (inode operations, dentry cache)│
                          └─────────────────────────────────┘
                             ↑
                    Application Code
```

The key benefit: **Same code works for all file systems**.

In AIFE, this FileSystemAbstraction class emulates VFS concepts:
- Same list_directory() works on ext4 (/home), tmpfs (/tmp), procfs (/proc)
- Same get_file_info() extracts metadata from any file system
- OS hides whether files are stored on disk, network, or kernel memory

This is crucial for operating systems because:
1. Single interface for all file systems
2. Can add new file systems without changing application code
3. Allows transparent network file systems (NFS)
4. Enables special file systems like procfs for kernel communication"

**Code to show:**
[src/filesystem.py](../src/filesystem.py#L87) - FileSystemAbstraction class
[src/filesystem.py](../src/filesystem.py#L35) - FileNode class (inode equivalent)

**Live demo:**
- Navigate to /home (ext4)
- Navigate to /tmp (tmpfs - volatile memory)
- Navigate to /proc (procfs - kernel info)
- Show same interface works for all

### 3. System Calls

**What the examiner wants to know:** Which system calls are used? Why?

**Your answer:**
"AIFE uses these system calls (via Python's os module):

**stat(2)** - Get file metadata (inode information)
```python
os.stat(path) → Returns: size, permissions, timestamps, inode number, etc.
```
Used when: Displaying file properties, checking file type

**getdents64(2)** - List directory contents
```python
os.listdir(path) → Returns list of directory entries
```
Used when: Browsing a folder

**unlink(2)** - Delete file
```python
os.remove(path) → Removes file from directory
```
Used when: Deleting a file

**rename(2)** - Rename/move file
```python
os.rename(old, new) → Atomically renames file
```
Used when: Renaming a file

**access(2)** - Check file permissions
```python
os.access(path, os.W_OK) → Checks if we have write permission
```
Used when: Validating operations before attempting them

**open(2)** - Used implicitly by xdg-open to open files
```python
subprocess.Popen(['xdg-open', path]) → Opens file with default app
```

Each system call switches from user space to kernel space, where:
- Kernel verifies permissions
- Kernel manages inodes
- Kernel reads/writes disk blocks
- Kernel maintains file system consistency"

**Code to show:**
[src/filesystem.py](../src/filesystem.py) - Search for comments "System call:"

**Live demo:**
Run with strace to see actual system calls:
```bash
strace -e trace=stat,getdents64,unlink,rename,access python3 main.py
```
- Navigate to folder → watch getdents64 calls
- View properties → watch stat calls
- Delete file → watch unlink call

### 4. File Permissions & Access Control

**What the examiner wants to know:** How do permissions work?

**Your answer:**
"Unix permissions use a 3-tier model stored in inode st_mode:

```
rwx rwx rwx
│││ │││ │││
│││ │││ └── Other (everyone else)
│││ └────── Group
└────────── Owner
```

Each tier has 3 bits:
- **r (read)**: Can read file contents / can list directory
- **w (write)**: Can modify file / can add/remove directory entries
- **x (execute)**: Can run file as program / can access directory

AIFE demonstrates this by:

1. **Checking permissions before operations:**
```python
# Before delete: Need write+execute on parent directory
if not os.access(parent, os.W_OK | os.X_OK):
    raise PermissionError()

# Before listing: Need read+execute on directory
if not os.access(path, os.R_OK | os.X_OK):
    raise PermissionError()
```

2. **Displaying permissions:**
```python
permissions = os.stat(path).st_mode
octal = oct(permissions & 0o777)    # e.g., '0o755'
string = stat.filemode(permissions) # e.g., 'rwxr-xr-x'
```

3. **Respecting kernel enforcement:**
When permission check fails, kernel returns errno 13 (EACCES).
Our code can't bypass this - it's enforced in hardware."

**Important distinction:**
- **Directory write permission**: Allows adding/removing entries (not modifying entries)
- **File write permission**: Allows modifying file content
- **Directory execute permission**: Allows accessing files in directory
- **File execute permission**: Allows running as program

**Code to show:**
[src/filesystem.py](../src/filesystem.py#L334) - can_read/write/execute()
[src/filesystem.py](../src/filesystem.py#L360) - Delete permission check

**Live demo:**
```bash
# Create test file
echo "test" > ~/test.txt
chmod 644 ~/test.txt  # rw-r--r--

# In AIFE:
# 1. View properties → Show "644" octal permission
# 2. Rename works → We own file
# 3. Delete works → We have write+execute on parent
```

### 5. Inodes and File Metadata

**What the examiner wants to know:** What information is in an inode?

**Your answer:**
"An inode is the kernel's internal data structure representing a file:

```python
FileNode(  # Our inode equivalent
    inode_number: 12345,            # st_ino - unique identifier
    size: 4096,                     # st_size - bytes
    permissions: 0o644,             # st_mode - rwx bits
    is_dir: False,                  # st_mode - file type
    is_symlink: False,              # st_mode - file type
    owner_uid: 1000,                # st_uid - owner's user ID
    owner_gid: 1000,                # st_gid - owner's group ID
    modified_time: 1704067200.5,   # st_mtime - last modified
    accessed_time: 1704067200.5,   # st_atime - last accessed
    hard_links: 1,                  # st_nlink - link count
)
```

**Key points:**
1. **Inode number**: Unique per file system. Like social security number for files.
2. **Multiple names, one inode**: Hard links point to same inode
3. **st_mode field**: Actually contains BOTH file type bits AND permission bits
4. **Timestamps**: Tracked in seconds since Unix epoch (1970-01-01)
5. **Link count**: If > 1, file has multiple names (hard links)

**File type detection:**
```python
# In st_mode:
# - Regular file: S_IFREG (0100000)
# - Directory: S_IFDIR (0040000)
# - Symlink: S_IFLNK (0120000)
# - Others: char/block devices, sockets, pipes

S_ISDIR(mode)   # Check if directory
S_ISREG(mode)   # Check if regular file
S_ISLNK(mode)   # Check if symlink
```

AIFE extracts and displays all this information in the properties dialog."

**Code to show:**
[src/filesystem.py](../src/filesystem.py#L35) - FileNode dataclass
[src/filesystem.py](../src/filesystem.py#L122-L135) - Inode extraction from stat()

**Live demo:**
```bash
# Show inode information
ls -i ~/test.txt        # Shows inode number
stat ~/test.txt         # Shows full inode info

# In AIFE:
# Right-click file → Properties
# Shows: Inode: 12345, Hard Links: 1, Permissions: 644
```

### 6. Error Handling and errno

**What the examiner wants to know:** How are OS errors handled?

**Your answer:**
"When a system call fails, Linux sets the global errno variable. Python translates this into exceptions:

```
System Call Failure  →  errno set  →  Python Exception
os.stat(path)            ENOENT          FileNotFoundError
os.listdir(path)         EACCES          PermissionError
os.remove(path)          EPERM           PermissionError
os.rmdir(path)           ENOTEMPTY       IsADirectoryError
```

AIFE demonstrates proper error handling:

1. **Catch exceptions at OS level:**
```python
try:
    os.stat(path)
except FileNotFoundError:
    # File doesn't exist
except PermissionError:
    # Access denied (EACCES or EPERM)
```

2. **Re-raise with context:**
```python
except PermissionError as e:
    raise PermissionError(f'No permission to delete: {path}') from e
```

3. **Translate to user message:**
```python
except PermissionError:
    result.message = 'Permission denied. You don\\'t have write access.'
```

4. **Display in GUI:**
```python
QMessageBox.warning(self, 'Error', result.message)
```

This layered error handling ensures:
- Low-level OS errors don't escape
- Users get meaningful messages
- Application doesn't crash
- Clear separation of concerns"

**Code to show:**
[src/file_manager.py](../src/file_manager.py#L60) - Error handling in FileManager
[src/filesystem.py](../src/filesystem.py#L162) - Error handling in FileSystemAbstraction
[src/gui.py](../src/gui.py#L259) - Error display in GUI

**Live demo:**
```bash
# Try operations that generate errors:
# 1. Navigate to /root (PermissionError)
# 2. Delete non-existent file (FileNotFoundError)
# 3. Delete directory with files (IsADirectoryError)
# All shown with friendly error messages
```

---

## Expected Viva Questions & Answers

### Q1: Why is this user space and not kernel space?

**A:** "AIFE is entirely user space because:
1. Written in Python (interpreted language)
2. Uses system calls (os module) to access file system
3. Cannot modify kernel code
4. Respects permission boundaries - cannot escalate privileges
5. Kernel enforces permission checks, not our code

The kernel space boundary is the system call interface. We can't cross it to modify the kernel or bypass permissions."

---

### Q2: How does AIFE use the Virtual File System?

**A:** "The VFS is an abstraction layer that:

1. **Hides file system differences**: Same code works for ext4, tmpfs, procfs, etc.
2. **Provides inode representation**: FileNode class mirrors inode structure
3. **Manages operations uniformly**: list, stat, rename, delete work the same for all file systems

Our FileSystemAbstraction class demonstrates this:
```python
def list_directory(path):
    os.listdir(path)  # Works on any file system
```

When you navigate /home, /tmp, /proc - same code works because VFS abstracts the differences. The kernel handles switching between file system drivers."

---

### Q3: What system calls does AIFE make?

**A:** "Six main system calls:

1. **stat(2)** - Get file metadata (inode)
   ```python
   os.stat(path) → size, permissions, timestamps, inode number
   ```

2. **getdents64(2)** - List directory entries
   ```python
   os.listdir(path) → list of files/folders
   ```

3. **unlink(2)** - Delete file
   ```python
   os.remove(path) → removes file from directory
   ```

4. **rename(2)** - Rename file
   ```python
   os.rename(old, new) → atomically renames
   ```

5. **access(2)** - Check permissions
   ```python
   os.access(path, os.W_OK) → check write permission
   ```

6. **open(2)** - Indirectly via xdg-open
   ```python
   subprocess.Popen(['xdg-open', path])
   ```

Each crosses the privilege boundary from user space to kernel space."

---

### Q4: How does AIFE enforce Unix permissions?

**A:** "AIFE enforces permissions at two levels:

1. **Application level**: Check before attempting operation
```python
# Before delete: Check write+execute on parent
if not os.access(parent, os.W_OK | os.X_OK):
    raise PermissionError('No permission')
```

2. **Kernel level**: Enforced during system call
```python
# Even if check passes, kernel verifies again
os.remove(path)  # Kernel re-checks before unlink()
```

The key permission rules:
- **To list directory**: Need read + execute on directory
- **To modify directory**: Need write + execute on directory
- **To delete file**: Need write + execute on parent directory
- **To read file**: Need read on file

When permission fails, kernel returns errno 13 (EACCES), Python raises PermissionError, and GUI shows user message."

---

### Q5: Can you explain the inode structure shown in properties?

**A:** "Yes. When you right-click a file and view Properties:

```
Inode: 12345           ← st_ino - unique identifier
Size: 4096             ← st_size - bytes
Permissions: 644       ← st_mode (rwx bits)
Owner UID: 1000        ← st_uid
Owner GID: 1000        ← st_gid
Hard Links: 1          ← st_nlink
Modified: 2024-01-01   ← st_mtime
```

These come from the OS-maintained inode structure:
- **Inode number**: Like a pointer to the actual inode
- **Size**: How many bytes the file is
- **Permissions**: Access control (644 = rw-r--r--)
- **Ownership**: UID/GID of the owner
- **Timestamps**: Track modification and access
- **Links**: How many directory entries point to this inode

The inode doesn't store the filename! The filename is in the parent directory's entry, which points to the inode number."

---

### Q6: Why did I get PermissionError when trying to delete a file in /root?

**A:** "/root directory has permissions 700 (drwx------):
- Owner: read, write, execute
- Group: none
- Other: none

You're running as your user (not root), so:
```
os.access(/root, os.R_OK | os.X_OK)  → Returns False
Raise PermissionError
```

Even if this check passed, the kernel would enforce it again:
```
os.listdir(/root)  → Kernel returns EACCES (errno 13)
```

This demonstrates the permission boundary. Your user cannot access /root because the kernel enforces the permission bits stored in /root's inode st_mode field."

---

### Q7: How does error handling work in AIFE?

**A:** "Three layers:

1. **FileSystem layer** catches OS errors and provides context
```python
try:
    os.stat(path)
except FileNotFoundError:
    raise FileNotFoundError(f'File not found: {path}') from e
```

2. **FileManager layer** translates to user messages
```python
except FileNotFoundError:
    result = OperationResult(
        success=False,
        message='File not found',
        error_type='NotFound'
    )
```

3. **GUI layer** displays error to user
```python
if not result.success:
    QMessageBox.warning(self, 'Error', result.message)
```

This prevents OS errors from crashing the app and ensures users see meaningful messages."

---

### Q8: What happens when you delete a file?

**A:** "When you right-click a file and select Delete:

1. **GUI asks for confirmation** (safety check)
2. **User clicks OK**
3. **FileManager.delete_file() is called**
4. **Check permissions on parent directory**
   ```python
   os.access(parent, os.W_OK | os.X_OK)
   ```
5. **Call FileSystem.delete_file()**
6. **Call os.remove(path)** → **unlink() system call**
7. **Kernel**:
   - Finds inode via path
   - Verifies permissions again
   - Decrements hard link count
   - If count = 0, frees inode and data blocks
   - Updates parent directory inode
8. **If successful**: GUI refreshes to show deleted file is gone
9. **If error**: GUI shows PermissionError message"

---

### Q9: How is the modular design beneficial?

**A:** "Four layers with clear separation:

1. **GUI layer**: Can be redesigned without changing logic
2. **FileManager layer**: Can be reused by CLI, web app, etc.
3. **FileSystem layer**: Encapsulates all OS interactions
4. **OS layer**: Can swap file system implementations

Benefits:
- **Testable**: Can test FileManager without GUI
- **Maintainable**: Changes isolated to one layer
- **Reusable**: FileManager layer can be used elsewhere
- **Clear responsibility**: Each layer has one job
- **Demonstrates architecture**: Shows how real file managers work"

---

### Q10: Can AIFE modify the Linux kernel?

**A:** "No, and it shouldn't. AIFE is user space application that:

1. Cannot execute privileged instructions
2. Cannot access kernel memory directly
3. Must use system calls to interact with file system
4. Must respect permission boundaries
5. Cannot install kernel modules

This is by design. The kernel protects itself to:
- Maintain system stability
- Enforce security boundaries
- Prevent malicious software from damaging OS
- Manage resource allocation fairly

AIFE demonstrates this boundary. When you try to access /root, the kernel enforcement prevents you - not our code."

---

## Viva Presentation Flow

### Total Time: ~15-20 minutes

**Timing breakdown:**
- **2 min**: Opening statement
- **3 min**: Architecture overview
- **5 min**: OS concepts explanation (pick 2-3 most relevant)
- **5 min**: Demo (navigate, check properties, try permission error)
- **3 min**: Q&A

**Start with:**
```
"I've built a file explorer that demonstrates key OS concepts.
Let me start with the architecture, then do a quick demo, and then
we can discuss the OS concepts in detail."
```

**End with:**
```
"The key takeaway is that AIFE demonstrates the user space / kernel space
boundary. Everything visible here is user space. The actual file system
operations, inode management, and permission enforcement happen in
the kernel. AIFE is just a well-designed interface to those kernel services."
```

---

## Quick Reference Card

Print this and keep with you during viva:

```
AIFE VIVA QUICK REFERENCE
═══════════════════════════════════════════════════════════════

ARCHITECTURE:
  GUI → FileManager → FileSystemAbstraction → OS → Kernel

KEY SYSTEM CALLS:
  stat(2)         - Get metadata
  getdents64(2)   - List directory
  unlink(2)       - Delete file
  rename(2)       - Rename file
  access(2)       - Check permissions
  open(2)         - Open file

KEY OS CONCEPTS:
  User Space vs Kernel Space
  Virtual File System (VFS)
  Inode Structure
  File Permissions (rwx)
  System Calls (privilege boundary)
  Error Handling (errno → exceptions)

PERMISSION RULES:
  Read Dir:    Need R+X on directory
  List Dir:    Need R+X on directory
  Delete File: Need W+X on parent directory
  Modify File: Need W on file

FILE PERMISSIONS (octal):
  755 = rwxr-xr-x (readable/executable by all)
  644 = rw-r--r-- (writable only by owner)
  700 = rwx------ (accessible only by owner)

INODE FIELDS:
  st_ino      - Inode number
  st_size     - File size
  st_mode     - Type + permissions
  st_uid/gid  - Owner
  st_mtime    - Modified time
  st_nlink    - Hard link count

DEMO SCENARIOS:
  1. Navigate /home, /tmp, /proc (same code, different FS)
  2. View properties (show inode info)
  3. Rename file (show rename() syscall)
  4. Try /root (show permission error)
  5. Delete file (show unlink() syscall)
```

---

## Final Tips

1. **Know your code**: Be ready to show specific lines when questioned
2. **Understand the concepts**: Don't memorize - explain the ideas
3. **Show confidence**: You built this from scratch, you understand it
4. **Connect to theory**: Show how AIFE demonstrates textbook concepts
5. **Handle "I don't know"**: "That's a good question. In the code at [line X]..." or "That would require kernel modification which AIFE doesn't do"
6. **Have examples ready**: /tmp, /proc, /root for permission demonstrations
7. **Know the limitations**: Be honest about what AIFE doesn't do (single-threaded, no caching, etc.)
8. **Practice the demo**: Run it multiple times before viva to avoid surprises

---

## Post-Viva Checklist

After viva, you can enhance further:
- [ ] Search functionality
- [ ] File sorting options
- [ ] Copy/move operations
- [ ] File compression
- [ ] Thumbnails preview
- [ ] Bookmark favorite locations
- [ ] Multi-threading for responsiveness

Good luck with your viva! 🚀
