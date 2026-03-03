# AIFE - Operating Systems Perspective Workflow

## Project Overview from OS Perspective

AIFE (Advanced Interactive File Explorer) demonstrates core Operating System concepts through a practical file management application with LLM-powered assistance. This project bridges user-space applications with kernel-level file system operations.

---

## 1. System Architecture & Layers

```
┌─────────────────────────────────────────────┐
│         User Interface Layer (GUI)          │  ← PyQt5 Application
├─────────────────────────────────────────────┤
│      Application Logic (File Manager)       │  ← Business Logic
├─────────────────────────────────────────────┤
│   File System Abstraction (filesystem.py)   │  ← OS Interface
├─────────────────────────────────────────────┤
│       Python OS/System Call Wrapper         │  ← Standard Library
├─────────────────────────────────────────────┤
│         Linux Kernel (System Calls)         │  ← open(), stat(), etc.
├─────────────────────────────────────────────┤
│     VFS (Virtual File System) Layer         │  ← File System Abstraction
├─────────────────────────────────────────────┤
│   File System Implementation (ext4, etc.)   │  ← Actual FS
└─────────────────────────────────────────────┘
```

**OS Concepts Demonstrated:**
- **Layered Architecture**: User space → Kernel space separation
- **System Call Interface**: Application uses OS services via system calls
- **Virtual File System (VFS)**: Abstraction layer hiding FS implementation details

---

## 2. File System Operations Workflow

### A. Directory Listing (browse_directory)

**User Action:** Navigate to `/home/user/Documents`

**Workflow:**
```
1. User clicks folder in GUI
   └─> file_manager.browse_directory(path)
       └─> filesystem.list_directory(path)
           └─> os.listdir(path)              # System call: getdents64
               └─> KERNEL: VFS layer
                   └─> ext4_readdir()
                       └─> Read directory blocks from disk
                       └─> Return directory entries

2. For each entry:
   └─> filesystem.get_file_info(entry)
       └─> os.stat(entry)                    # System call: stat64/fstatat
           └─> KERNEL: VFS layer
               └─> ext4_getattr()
                   └─> Read inode metadata
                   └─> Return stat structure

3. Create FileNode objects with:
   - Inode number (unique file identifier)
   - Size (in bytes)
   - Permissions (mode bits)
   - Owner UID/GID
   - Timestamps (mtime, atime, ctime)
   - Link count (hard links)
```

**OS Concepts:**
- **Inodes**: Unique identifiers storing file metadata
- **Directory Structure**: Mapping filenames to inode numbers
- **stat() System Call**: Retrieving file metadata without opening file
- **File Descriptors**: OS-level handles for open files

---

### B. File Permissions & Access Control

**User Action:** View file properties or attempt operation

**Workflow:**
```
1. Check file permissions:
   └─> FileNode.get_permissions_string()
       └─> stat_info.st_mode                 # Mode bits from inode
           └─> Extract owner/group/other permissions
               Format: rwxr-xr-x (octal: 755)

2. Permission check before operation:
   └─> os.access(path, mode)                 # System call: access/faccessat
       └─> KERNEL: Check effective UID/GID
           └─> Compare with file's owner/group
           └─> Apply permission mask
           └─> Return allowed/denied

3. Attempt operation (e.g., delete):
   └─> file_manager.delete_file(path)
       └─> Check parent directory write permission
       └─> os.unlink(path)                   # System call: unlink
           └─> KERNEL: VFS layer
               ├─> Check permissions (EACCES)
               ├─> Decrement link count
               └─> If links=0, free inode & blocks
```

**OS Concepts:**
- **Permission Bits**: rwx for owner, group, others
- **Access Control**: Kernel enforces based on UID/GID
- **errno Values**: EACCES (permission denied), ENOENT (not found)
- **Hard Link Count**: Multiple names for same inode

---

### C. File Open & I/O Operations

**User Action:** Open a text file

**Workflow:**
```
1. Open file request:
   └─> file_manager.open_file(path)
       └─> subprocess.run(['xdg-open', path]) # Launch external program
           └─> KERNEL: fork() + exec()
               ├─> Create new process (copy parent)
               ├─> Load program binary
               └─> Exec system call replaces process image

2. External program reads file:
   └─> open(path, O_RDONLY)                  # System call: openat
       └─> KERNEL: VFS layer
           ├─> Allocate file descriptor (int)
           ├─> Create file table entry
           ├─> Store file offset (0)
           └─> Return fd to user space

   └─> read(fd, buffer, size)                # System call: read
       └─> KERNEL: VFS layer
           ├─> Check fd in process table
           ├─> ext4_read()
           │   └─> Read data blocks via page cache
           ├─> Update file offset
           └─> Copy data to user buffer

   └─> close(fd)                             # System call: close
       └─> KERNEL: Release file descriptor
           └─> Decrement file table reference count
```

**OS Concepts:**
- **File Descriptors**: Per-process table mapping ints to files
- **File Table**: System-wide table of open files
- **Inode Table**: In-memory cache of active inodes
- **Page Cache**: Buffer cache for disk I/O
- **Process Creation**: fork() + exec() model

---

## 3. Advanced OS Concepts in AIFE

### A. Symbolic Links vs Hard Links

**Demonstration in GUI:**
```
1. Hard Link:
   └─> ln file1 file2                        # System call: link
       └─> KERNEL: Create new directory entry
           ├─> Points to SAME inode as file1
           ├─> Increment inode link count
           └─> Both names equal (no "original")

2. Symbolic Link:
   └─> ln -s target linkname                 # System call: symlink
       └─> KERNEL: Create NEW inode
           ├─> Store target path as data
           ├─> Mark as symlink (S_IFLNK)
           └─> Separate inode from target

3. FileNode detection:
   └─> stat_info.st_mode & S_IFLNK           # Check if symlink
       └─> Display 🔗 icon in GUI
       └─> Show target in properties
```

**OS Concepts:**
- **Inode Sharing**: Hard links share same inode
- **Path Resolution**: Kernel follows symlinks during path lookup
- **Link Count**: Tracks number of directory entries per inode

---

### B. LLM Backend Process Management

**User Action:** Ask chatbot a question

**Workflow:**
```
1. User sends message in GUI
   └─> ChatbotWidget.on_send_message()
       └─> LLMIntegrationManager.process_user_message()
           └─> LLMChatbotBackend._call_ollama()

2. HTTP request to local Ollama server:
   └─> requests.post('http://localhost:11434/api/chat')
       └─> socket.socket(AF_INET, SOCK_STREAM)  # System call: socket
           └─> connect(('127.0.0.1', 11434))    # System call: connect
               └─> KERNEL: TCP/IP stack
                   ├─> Create socket buffer
                   ├─> Establish TCP connection
                   └─> Loopback interface (no network)

   └─> send(data)                               # System call: sendto
       └─> KERNEL: Copy data to socket buffer
           └─> Local delivery to Ollama process

3. Ollama server (separate process):
   └─> Running as: ollama serve
       └─> KERNEL: Separate process context
           ├─> Own address space (memory isolation)
           ├─> Own file descriptor table
           ├─> Listening on port 11434
           └─> GPU access for model inference

4. Response back:
   └─> recv(buffer)                             # System call: recvfrom
       └─> KERNEL: Copy from socket buffer
           └─> Wake up blocked process (context switch)
```

**OS Concepts:**
- **Inter-Process Communication (IPC)**: HTTP over loopback
- **Socket API**: Network programming interface
- **Context Switching**: CPU switches between processes
- **Process Isolation**: Separate address spaces
- **Blocking I/O**: Process sleeps until data arrives

---

### C. File System Metadata & Context

**LLM receives file metadata:**
```
1. Gather metadata:
   └─> LLMChatbotBackend.gather_file_metadata(current_dir)
       └─> For each file:
           └─> os.stat(file)                    # System call: stat
               └─> KERNEL: Read inode
                   Return:
                   ├─> st_ino: Inode number
                   ├─> st_size: File size in bytes
                   ├─> st_mode: Permission bits + file type
                   ├─> st_uid/st_gid: Owner
                   ├─> st_mtime: Last modification time
                   └─> st_nlink: Hard link count

2. LLM analyzes metadata:
   └─> Build context with:
       ├─> Total files/directories (stat count)
       ├─> Total size (sum of st_size)
       ├─> File types (S_IFDIR, S_IFREG, S_IFLNK)
       └─> Recent modifications (st_mtime sorting)

3. File search ranking:
   └─> LLM returns top 5 file paths
       └─> GUI filters file list
           └─> Only display matching FileNode objects
```

**OS Concepts:**
- **File Metadata**: Stored in inode, accessed via stat()
- **File Types**: Regular, directory, symlink, device, etc.
- **Timestamps**: Access time, modify time, change time
- **Space Accounting**: Block allocation and size tracking

---

## 4. Error Handling & OS Error Codes

**Error propagation from kernel to user:**
```
Operation: Delete read-only file

1. User clicks delete in GUI
   └─> file_manager.delete_file(path)
       └─> os.unlink(path)
           └─> KERNEL: VFS layer
               └─> Check parent directory write permission
                   └─> If denied: return -EACCES (errno=13)

2. Python exception translation:
   └─> System call returns -1
       └─> errno set to EACCES
           └─> Python raises PermissionError
               └─> file_manager catches exception
                   └─> Create OperationResult(
                       success=False,
                       error_type="PermissionDenied",
                       message="You don't have permission..."
                   )

3. GUI displays user-friendly error:
   └─> QMessageBox.warning("Permission denied")
```

**Common errno values in AIFE:**
- **ENOENT (2)**: File not found
- **EACCES (13)**: Permission denied
- **EISDIR (21)**: Is a directory (can't unlink)
- **ENOTDIR (20)**: Not a directory
- **EEXIST (17)**: File already exists
- **ENOTEMPTY (39)**: Directory not empty

**OS Concepts:**
- **Error Codes**: Standardized errno values
- **Exception Handling**: Kernel errors → Python exceptions
- **User-Friendly Errors**: Translate technical errors for users

---

## 5. Virtual File System (VFS) Abstraction

**AIFE's FileSystemAbstraction mirrors VFS:**
```
┌──────────────────────────────────────────┐
│  Application (file_manager.py)           │
│  ↓ (calls)                                │
│  FileSystemAbstraction (filesystem.py)   │  ← Abstraction Layer
│  ↓ (maps to)                              │
│  os.stat, os.listdir, os.unlink          │  ← Python stdlib
│  ↓ (system calls)                         │
│  stat(), getdents64(), unlink()          │  ← System Call Interface
│  ↓ (enters kernel)                        │
│  Linux VFS Layer                          │  ← Kernel VFS
│  ↓ (dispatches to)                        │
│  ext4, btrfs, nfs, etc.                  │  ← Actual FS
└──────────────────────────────────────────┘
```

**Benefits of Abstraction:**
- Application code doesn't care about underlying FS (ext4, XFS, etc.)
- Same code works on different file systems
- Can add LLM intelligence layer above VFS
- Easy to mock for testing

**OS Concepts:**
- **Virtual File System**: Uniform interface for diverse file systems
- **Pluggable Architecture**: FS implementations register with VFS
- **Operation Dispatch**: VFS routes calls to correct FS driver

---

## 6. Complete User Workflow Example

**Scenario:** User searches for a Python file using LLM assistant

```
Step 1: User Input
   GUI: "find python files larger than 1KB"
   ↓

Step 2: ChatBot Processes Query
   chatbot.py → llm_chatbot_backend.py
   ↓
   LLM detects search intent
   ↓

Step 3: Gather File System Metadata
   filesystem.list_directory(current_dir)
   ↓
   For each file:
      os.stat(file) → [System Call: fstatat]
      ↓
      KERNEL: Read inode from disk/cache
      ↓
      Return: size, type, permissions, timestamps
   ↓

Step 4: LLM Ranks Files
   Filter: .py extension, size > 1024 bytes
   Rank by relevance (name match + size)
   Return top 5 file paths
   ↓

Step 5: Update GUI
   emit search_results_ready signal
   ↓
   GUI.populate_file_list(matched_files)
   ↓
   Display filtered FileNode objects
   ↓
   Status bar: "Showing 5 matches"

Step 6: User Opens File
   Double-click → file_manager.open_file()
   ↓
   subprocess.run(['xdg-open', path])
   ↓
   [System Call: fork()]
   ↓
   KERNEL: Create child process
   ↓
   [System Call: execve('/usr/bin/xdg-open')]
   ↓
   KERNEL: Load program, replace process image
   ↓
   xdg-open determines MIME type
   ↓
   [System Call: open(file, O_RDONLY)]
   ↓
   KERNEL: Allocate fd, create file table entry
   ↓
   Editor reads file via read() system calls
```

---

## 7. Key OS Concepts Summary

### File System Layer
- **Inodes**: Unique file identifiers with metadata
- **Directory Entries**: Name → Inode mappings
- **Hard Links**: Multiple names, same inode
- **Symbolic Links**: Separate inode storing path

### System Calls Demonstrated
- `stat()/fstatat()`: Get file metadata
- `open()/openat()`: Open file, get descriptor
- `read()/write()`: I/O operations
- `unlink()`: Delete file (decrement link count)
- `rename()`: Atomic rename operation
- `listdir()/getdents64()`: Read directory entries
- `access()`: Check permissions

### Process & Memory
- **Process Isolation**: Separate address spaces
- **Context Switching**: CPU time-sharing
- **fork() + exec()**: Process creation model
- **File Descriptor Table**: Per-process open files

### Security & Permissions
- **UID/GID**: User and group identifiers
- **Permission Bits**: rwx for owner/group/other
- **Access Control**: Kernel enforces permissions
- **Effective vs Real UID**: Privilege management

### I/O & Communication
- **Blocking I/O**: Process waits for data
- **Socket API**: Network/IPC interface
- **Loopback**: Local inter-process communication
- **Buffer Cache**: Kernel-space I/O buffering

---

## 8. Learning Outcomes (OS Course Perspective)

### What Students Learn:
1. **System Call Interface**: How applications interact with kernel
2. **File System Internals**: Inodes, directories, metadata
3. **Permission Model**: Unix permission bits and access control
4. **Error Handling**: errno codes and exception translation
5. **Process Management**: fork, exec, file descriptors
6. **IPC Mechanisms**: Sockets for process communication
7. **Virtual File System**: Abstraction layer benefits
8. **Real-World Application**: Theory applied in practical GUI app

### Hands-On Demonstrations:
- View inode numbers in file properties
- See permission bits (octal and rwx)
- Observe hard link counts
- Distinguish symlinks from regular files
- Experience permission denied errors
- Understand process isolation (Ollama separate)
- See VFS abstraction in filesystem.py

---

## 9. Connection to OS Course Topics

| OS Topic | AIFE Implementation | File/Module |
|----------|---------------------|-------------|
| File Systems | Inode metadata, directory listing | `filesystem.py` |
| System Calls | stat, open, unlink, etc. | All file operations |
| Process Management | fork/exec for external programs | `file_manager.py::open_file()` |
| IPC | HTTP over loopback to Ollama | `llm_chatbot_backend.py` |
| Permissions | Check before operations | `file_manager.py` |
| Error Handling | errno → Python exceptions | `file_manager.py` |
| Virtual FS | Abstraction layer pattern | `filesystem.py` |
| Memory Management | Process isolation | Ollama separate process |

---

## 10. Running the Project (OS Perspective)

**Setup:**
```bash
# 1. Environment isolation (virtual environment)
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (package management)
pip install -r requirements.txt

# 3. Start Ollama server (separate process)
ollama serve &  # Background process

# 4. Pull LLM model (network I/O)
ollama pull smollm

# 5. Run AIFE application (main process)
python3 main.py
```

**Process Tree:**
```
systemd (PID 1)
├── ollama serve (PID 1234)          ← GPU access, model inference
│   └── ollama runner (PID 1235)
└── python3 main.py (PID 5678)       ← GUI application
    └── xdg-open file.txt (PID 5679) ← Child process for file open
```

---

## Conclusion

AIFE demonstrates fundamental Operating System concepts through a practical, interactive application. Students can see how:
- User-space applications interact with the kernel
- System calls bridge applications and OS
- File systems manage data and metadata
- Processes communicate and share resources
- Security and permissions protect the system
- Abstractions simplify complex operations

This project bridges theory (OS textbook) and practice (real Linux system).
