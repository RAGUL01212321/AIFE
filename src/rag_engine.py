"""
AIFE - RAG (Retrieval-Augmented Generation) Engine

Lightweight RAG engine that indexes files in the current directory,
retrieves relevant ones based on user queries, and provides folder
statistics and file property inspection.

Features:
- In-memory file indexing with content snippets for text files
- Keyword + extension + recency scoring for retrieval
- Folder statistics (counts, size breakdown, type distribution)
- Intent detection to classify user queries
"""

import os
import re
import stat
import mimetypes
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from filesystem import FileSystemAbstraction, FileNode


# Text file extensions we can safely read for content indexing
TEXT_EXTENSIONS = {
    '.txt', '.md', '.py', '.js', '.ts', '.html', '.css', '.json', '.xml',
    '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.sh', '.bash',
    '.zsh', '.fish', '.c', '.cpp', '.h', '.hpp', '.java', '.rs', '.go',
    '.rb', '.php', '.pl', '.lua', '.r', '.sql', '.csv', '.tsv', '.log',
    '.env', '.gitignore', '.dockerfile', '.makefile', '.cmake',
    '.tex', '.rst', '.org', '.vim', '.el', '.lisp', '.hs', '.scala',
    '.kt', '.swift', '.m', '.mm', '.dart', '.vue', '.svelte', '.jsx',
    '.tsx', '.scss', '.sass', '.less', '.bat', '.ps1', '.psm1',
}

# Known binary extensions to skip reading
BINARY_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg', '.webp',
    '.mp3', '.wav', '.flac', '.ogg', '.aac', '.mp4', '.avi', '.mkv',
    '.mov', '.wmv', '.flv', '.webm', '.zip', '.tar', '.gz', '.bz2',
    '.xz', '.7z', '.rar', '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.ppt', '.pptx', '.exe', '.dll', '.so', '.dylib', '.o', '.a',
    '.pyc', '.pyo', '.class', '.jar', '.war', '.ear', '.whl',
    '.iso', '.img', '.bin', '.dat', '.db', '.sqlite', '.sqlite3',
}


@dataclass
class FileIndex:
    """Indexed file entry for RAG retrieval"""
    path: str
    name: str
    extension: str
    size: int
    is_dir: bool
    is_symlink: bool
    modified_time: float
    snippet: str = ""           # First N chars of text files
    inode: int = 0
    permissions: str = ""
    owner_uid: int = 0
    owner_gid: int = 0
    hard_links: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "name": self.name,
            "extension": self.extension,
            "size": self.size,
            "is_dir": self.is_dir,
            "is_symlink": self.is_symlink,
            "modified": datetime.fromtimestamp(self.modified_time).strftime("%Y-%m-%d %H:%M"),
            "snippet": self.snippet[:200] if self.snippet else "",
            "permissions": self.permissions,
        }


@dataclass
class FolderStats:
    """Statistics about a folder"""
    path: str
    total_files: int = 0
    total_folders: int = 0
    total_symlinks: int = 0
    total_size: int = 0
    type_distribution: Dict[str, int] = field(default_factory=dict)
    largest_file: Optional[Dict[str, Any]] = None
    smallest_file: Optional[Dict[str, Any]] = None
    newest_file: Optional[Dict[str, Any]] = None
    oldest_file: Optional[Dict[str, Any]] = None
    hidden_count: int = 0
    readable_size: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "total_files": self.total_files,
            "total_folders": self.total_folders,
            "total_symlinks": self.total_symlinks,
            "total_size": self.total_size,
            "readable_size": self.readable_size,
            "type_distribution": self.type_distribution,
            "largest_file": self.largest_file,
            "smallest_file": self.smallest_file,
            "newest_file": self.newest_file,
            "oldest_file": self.oldest_file,
            "hidden_count": self.hidden_count,
        }


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for AIFE.

    Indexes files in the current directory, scores them against user
    queries, and provides folder-level analytics.
    """

    SNIPPET_MAX_CHARS = 500

    def __init__(self, fs: Optional[FileSystemAbstraction] = None):
        self.fs = fs or FileSystemAbstraction()
        self._index: List[FileIndex] = []
        self._indexed_dir: Optional[str] = None

    # ──────────────────────── Indexing ────────────────────────

    def index_directory(self, path: str) -> List[FileIndex]:
        """
        Index all files in *path*. Reads a content snippet for text files.
        Results are cached until the directory changes.
        """
        path = os.path.realpath(path)

        # Re-use cache if same directory
        if path == self._indexed_dir and self._index:
            return self._index

        try:
            file_nodes: List[FileNode] = self.fs.list_directory(path)
        except Exception:
            self._index = []
            self._indexed_dir = path
            return self._index

        index: List[FileIndex] = []
        for node in file_nodes:
            ext = os.path.splitext(node.name)[1].lower()
            snippet = ""
            if not node.is_dir and ext in TEXT_EXTENSIONS:
                snippet = self._read_snippet(node.path)

            index.append(FileIndex(
                path=node.path,
                name=node.name,
                extension=ext,
                size=node.size,
                is_dir=node.is_dir,
                is_symlink=node.is_symlink,
                modified_time=node.modified_time,
                snippet=snippet,
                inode=node.inode_number,
                permissions=node.get_permission_octal(),
                owner_uid=node.owner_uid,
                owner_gid=node.owner_gid,
                hard_links=node.hard_links,
            ))

        self._index = index
        self._indexed_dir = path
        return index

    def invalidate_cache(self):
        """Force re-index on next call"""
        self._indexed_dir = None
        self._index = []

    # ──────────────────────── Retrieval ────────────────────────

    def retrieve(self, query: str, directory: str, top_k: int = 5) -> List[FileIndex]:
        """
        Score indexed files against *query* and return top-k matches.

        Scoring factors:
        - Keyword overlap with file name
        - Extension mentioned in query
        - Content snippet keyword overlap
        - Recency boost
        """
        index = self.index_directory(directory)
        if not index:
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        scored: List[Tuple[float, FileIndex]] = []

        # Detect extension requests in query (e.g. "python" → .py)
        requested_exts = self._extract_extensions(query)

        now = datetime.now().timestamp()

        for entry in index:
            score = 0.0
            name_lower = entry.name.lower()
            name_tokens = set(re.split(r'[\W_]+', name_lower))

            # 1. File name keyword match (strongest signal)
            for t in tokens:
                if t in name_lower:
                    score += 3.0
                if t in name_tokens:
                    score += 2.0

            # 2. Extension match
            if requested_exts and entry.extension in requested_exts:
                score += 4.0

            # 3. Content snippet keyword match
            if entry.snippet:
                snippet_lower = entry.snippet.lower()
                for t in tokens:
                    if t in snippet_lower:
                        score += 1.5

            # 4. Directory boost (folders often relevant for navigation)
            if entry.is_dir and any(t in name_lower for t in tokens):
                score += 1.0

            # 5. Recency boost (files modified within last 24h)
            age_hours = (now - entry.modified_time) / 3600
            if age_hours < 24:
                score += 0.5
            elif age_hours < 168:  # 1 week
                score += 0.2

            if score >= 2.0:  # Must have at least one keyword/extension match
                scored.append((score, entry))

        scored.sort(key=lambda x: -x[0])
        return [entry for _, entry in scored[:top_k]]

    def global_search(self, query: str, top_k: int = 8) -> List['FileIndex']:
        """
        Search for files matching *query* across the user's home directory tree.
        Skips hidden directories and common noise folders (.git, __pycache__, etc.).
        Returns ranked FileIndex results.
        """
        home = os.path.expanduser("~")
        tokens = self._tokenize(query)
        requested_exts = self._extract_extensions(query)

        if not tokens and not requested_exts:
            return []

        # Directories to skip
        SKIP_DIRS = {
            '.git', '__pycache__', '.cache', '.local', '.config',
            'node_modules', '.npm', '.pip', 'venv', 'env', '.env',
            '.venv', 'site-packages', '.mozilla', '.thunderbird',
            '.gnome', '.dbus', 'proc', 'sys', 'dev',
        }

        now = datetime.now().timestamp()
        scored: List[tuple] = []

        for root, dirs, files in os.walk(home):
            # Prune skip dirs in-place so os.walk doesn't descend into them
            dirs[:] = [
                d for d in dirs
                if d not in SKIP_DIRS and not d.startswith('.')
            ]

            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                name_lower = fname.lower()
                name_tokens = set(re.split(r'[\W_]+', name_lower))
                score = 0.0

                # Keyword match against file name
                for t in tokens:
                    if t in name_lower:
                        score += 3.0
                    if t in name_tokens:
                        score += 2.0

                # Extension match
                if requested_exts and ext in requested_exts:
                    score += 4.0

                if score == 0:
                    continue

                fpath = os.path.join(root, fname)
                try:
                    st = os.stat(fpath)
                    size = st.st_size
                    mtime = st.st_mtime
                except OSError:
                    continue

                # Recency boost
                age_hours = (now - mtime) / 3600
                if age_hours < 24:
                    score += 0.5
                elif age_hours < 168:
                    score += 0.2

                # Bonus: path contains a query token (e.g. folder name matches)
                dir_lower = root.lower()
                for t in tokens:
                    if t in dir_lower:
                        score += 0.5
                        break

                scored.append((score, FileIndex(
                    path=fpath,
                    name=fname,
                    extension=ext,
                    size=size,
                    is_dir=False,
                    is_symlink=os.path.islink(fpath),
                    modified_time=mtime,
                    snippet="",
                    inode=st.st_ino,
                    permissions=oct(stat.S_IMODE(st.st_mode))[2:],
                )))

        scored.sort(key=lambda x: -x[0])
        return [entry for _, entry in scored[:top_k]]



    # ──────────────────────── Folder Stats ────────────────────────

    def get_folder_stats(self, path: str) -> FolderStats:
        """
        Compute statistics for the folder at *path*.
        """
        index = self.index_directory(path)
        stats = FolderStats(path=path)

        if not index:
            stats.readable_size = "0 B"
            return stats

        files_only = [f for f in index if not f.is_dir]
        dirs_only = [f for f in index if f.is_dir]

        stats.total_files = len(files_only)
        stats.total_folders = len(dirs_only)
        stats.total_symlinks = sum(1 for f in index if f.is_symlink)
        stats.total_size = sum(f.size for f in files_only)
        stats.readable_size = self._format_bytes(stats.total_size)
        stats.hidden_count = sum(1 for f in index if f.name.startswith('.'))

        # Type distribution
        ext_counts: Dict[str, int] = {}
        for f in files_only:
            ext = f.extension if f.extension else "(no ext)"
            ext_counts[ext] = ext_counts.get(ext, 0) + 1
        stats.type_distribution = dict(sorted(ext_counts.items(), key=lambda x: -x[1]))

        # Extremes
        if files_only:
            largest = max(files_only, key=lambda f: f.size)
            smallest = min(files_only, key=lambda f: f.size)
            newest = max(files_only, key=lambda f: f.modified_time)
            oldest = min(files_only, key=lambda f: f.modified_time)

            stats.largest_file = {"name": largest.name, "size": self._format_bytes(largest.size)}
            stats.smallest_file = {"name": smallest.name, "size": self._format_bytes(smallest.size)}
            stats.newest_file = {
                "name": newest.name,
                "modified": datetime.fromtimestamp(newest.modified_time).strftime("%Y-%m-%d %H:%M")
            }
            stats.oldest_file = {
                "name": oldest.name,
                "modified": datetime.fromtimestamp(oldest.modified_time).strftime("%Y-%m-%d %H:%M")
            }

        return stats

    # ──────────────────────── File Properties ────────────────────────

    def get_file_properties(self, path: str) -> Dict[str, Any]:
        """
        Return detailed properties for a single file.
        """
        try:
            node = self.fs.get_file_info(path)
        except Exception as e:
            return {"error": str(e)}

        ext = os.path.splitext(node.name)[1].lower()
        file_type = "Directory" if node.is_dir else ("Symbolic Link" if node.is_symlink else "File")

        props = {
            "name": node.name,
            "path": node.path,
            "type": file_type,
            "size": node.size,
            "readable_size": self._format_bytes(node.size),
            "inode": node.inode_number,
            "hard_links": node.hard_links,
            "permissions_octal": node.get_permission_octal(),
            "permissions_string": node.get_permissions_string(),
            "owner_uid": node.owner_uid,
            "owner_gid": node.owner_gid,
            "modified": node.get_modified_time_str(),
            "accessed": str(node.accessed_time),
            "extension": ext,
        }

        # Content preview for text files
        if not node.is_dir and ext in TEXT_EXTENSIONS:
            props["content_preview"] = self.read_file_content(path, max_chars=2000)

        return props

    # ──────────────────────── File Content ────────────────────────

    def read_file_content(self, path: str, max_chars: int = 2000) -> str:
        """Safely read text file content, returning at most *max_chars*."""
        try:
            with open(path, 'r', errors='replace') as f:
                content = f.read(max_chars)
            if len(content) == max_chars:
                content += "\n... (truncated)"
            return content
        except Exception:
            return ""

    # ──────────────────────── Intent Detection ────────────────────────

    INTENT_PATTERNS = {
        "summarize": [
            r"summar", r"overview", r"what.s in", r"what is in",
            r"describe.*folder", r"tell me about.*folder",
            r"what does.*contain", r"contents of", r"what.s here",
        ],
        "count": [
            r"how many", r"count", r"number of", r"total files",
            r"total folders", r"how much space", r"folder size",
            r"disk usage", r"storage",
        ],
        "properties": [
            r"properties of", r"details of", r"info about",
            r"information about", r"show.*properties",
            r"permission[s]? of", r"size of", r"when was.*modified",
            r"owner of", r"inode",
        ],
        "retrieve": [
            r"find", r"search", r"locate", r"look for", r"looking for",
            r"where is", r"show me.*files", r"list.*files",
            r"get.*files", r"which files",
        ],
        "list_by_type": [
            r"show.*python", r"show.*text", r"show.*images",
            r"list.*by type", r"filter.*by", r"all.*files",
            r"\.py\b", r"\.txt\b", r"\.md\b", r"\.js\b",
        ],
        "preview": [
            r"preview", r"show content", r"read file",
            r"open file", r"what.s inside", r"cat ",
            r"display.*content",
        ],
    }

    def detect_intent(self, query: str) -> str:
        """
        Classify user intent into one of:
        retrieve, count, properties, list_by_type, preview, general
        """
        q = query.lower().strip()

        best_intent = "general"
        best_score = 0

        for intent_name, patterns in self.INTENT_PATTERNS.items():
            score = sum(1 for p in patterns if re.search(p, q))
            if score > best_score:
                best_score = score
                best_intent = intent_name

        return best_intent

    def extract_filename_from_query(self, query: str) -> Optional[str]:
        """Try to extract a specific filename from the user's query."""
        q = query.strip()

        # Look for quoted filenames
        quoted = re.findall(r'["\']([^"\']+)["\']', q)
        if quoted:
            return quoted[0]

        # Look for filename-like tokens (with extensions)
        tokens = q.split()
        for token in tokens:
            if '.' in token and not token.startswith('.'):
                clean = token.strip('.,!?;:')
                if os.path.splitext(clean)[1]:
                    return clean

        return None

    def extract_folder_from_query(self, query: str) -> Optional[str]:
        """Extract a folder name from a query like 'how many files in FPGA folder'."""
        q = query.strip()
        
        # Patterns like "in FPGA folder", "in the FPGA directory", "FPGA folder"
        patterns = [
            r'(?:in|inside|within|of)\s+(?:the\s+)?["\']?(\w[\w\s.-]*?)["\']?\s+(?:folder|directory|dir)\b',
            r'(?:folder|directory|dir)\s+["\']?(\w[\w\s.-]*?)["\']?(?:\s|$|\?)',
            r'(?:in|inside|within)\s+["\']?(\w[\w\s.-]*?)["\']?(?:\s*\??\s*$)',
        ]
        for pat in patterns:
            m = re.search(pat, q, re.IGNORECASE)
            if m:
                name = m.group(1).strip()
                # Filter out stopwords that shouldn't be folder names
                if name.lower() not in ('the', 'this', 'that', 'a', 'an', 'my', 'our', 'here', 'there', 'current'):
                    return name
        
        return None

    def find_folder(self, name: str, current_dir: str) -> Optional[str]:
        """
        Search for a folder by name across common locations.
        Returns the absolute path if found, None otherwise.
        """
        home = os.path.expanduser("~")
        search_roots = [
            current_dir,
            os.path.dirname(current_dir),  # parent
            home,
            os.path.join(home, "Desktop"),
            os.path.join(home, "Documents"),
            os.path.join(home, "Downloads"),
            os.path.join(home, "Projects"),
        ]
        
        name_lower = name.lower()
        
        for root in search_roots:
            if not os.path.isdir(root):
                continue
            try:
                candidate = os.path.join(root, name)
                if os.path.isdir(candidate):
                    return os.path.realpath(candidate)
                # Case-insensitive fallback
                for entry in os.listdir(root):
                    if entry.lower() == name_lower and os.path.isdir(os.path.join(root, entry)):
                        return os.path.realpath(os.path.join(root, entry))
            except PermissionError:
                continue
        
        return None

    # ──────────────────────── Helpers (private) ────────────────────────

    def _read_snippet(self, path: str) -> str:
        """Read the first N characters of a text file for indexing."""
        try:
            with open(path, 'r', errors='replace') as f:
                return f.read(self.SNIPPET_MAX_CHARS)
        except Exception:
            return ""

    def _tokenize(self, text: str) -> List[str]:
        """Split text into lowercase tokens, filtering stopwords."""
        stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'can', 'shall',
            'to', 'of', 'in', 'for', 'on', 'with', 'at', 'by', 'from',
            'as', 'into', 'through', 'during', 'before', 'after', 'above',
            'below', 'between', 'and', 'but', 'or', 'nor', 'not', 'so',
            'if', 'then', 'than', 'too', 'very', 'just', 'about', 'up',
            'out', 'that', 'this', 'it', 'its', 'my', 'me', 'we', 'us',
            'i', 'you', 'he', 'she', 'they', 'them', 'what', 'which',
            'who', 'whom', 'where', 'when', 'how', 'all', 'each', 'every',
            'show', 'display', 'give', 'tell', 'get', 'find', 'search',
            'list', 'many', 'much', 'there', 'here',
        }
        tokens = re.split(r'\W+', text.lower())
        return [t for t in tokens if t and t not in stopwords and len(t) > 1]

    def _extract_extensions(self, query: str) -> set:
        """Map natural language to file extensions."""
        ext_map = {
            'python': {'.py'}, 'javascript': {'.js'}, 'typescript': {'.ts'},
            'java': {'.java'}, 'rust': {'.rs'}, 'go': {'.go'},
            'ruby': {'.rb'}, 'php': {'.php'}, 'c++': {'.cpp', '.hpp'},
            'cpp': {'.cpp', '.hpp'}, 'c ': {'.c', '.h'},
            'html': {'.html', '.htm'}, 'css': {'.css', '.scss', '.sass'},
            'json': {'.json'}, 'yaml': {'.yaml', '.yml'},
            'xml': {'.xml'}, 'sql': {'.sql'},
            'markdown': {'.md'}, 'text': {'.txt'}, 'log': {'.log'},
            'shell': {'.sh', '.bash'}, 'bash': {'.sh', '.bash'},
            'config': {'.cfg', '.conf', '.ini', '.toml'},
            'image': {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'},
            'video': {'.mp4', '.avi', '.mkv', '.mov', '.webm'},
            'audio': {'.mp3', '.wav', '.flac', '.ogg', '.aac'},
            'pdf': {'.pdf'}, 'document': {'.doc', '.docx', '.pdf'},
        }

        q = query.lower()
        found = set()

        # Check explicit extensions like ".py"
        explicit = re.findall(r'\.\w+', q)
        for ext in explicit:
            found.add(ext)

        # Check natural language
        for keyword, exts in ext_map.items():
            if keyword in q:
                found.update(exts)

        return found

    @staticmethod
    def _format_bytes(size: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB"
