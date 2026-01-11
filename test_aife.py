#!/usr/bin/env python3
"""
AIFE Test Suite
Demonstrates file system operations and error handling

Usage:
    python3 test_aife.py

Tests:
    1. Basic directory listing
    2. File metadata extraction
    3. Permission checks
    4. Error handling
    5. File operations (rename, delete)
"""

import sys
import os
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from filesystem import FileSystemAbstraction, FileNode
from file_manager import FileManager, OperationResult


def test_setup():
    """Setup test environment"""
    test_dir = os.path.expanduser("~/AIFE_TEST")
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Create test files
    test_files = [
        ("test1.txt", "content1"),
        ("test2.txt", "content2"),
        ("document.md", "# Test Document"),
    ]
    
    for filename, content in test_files:
        path = os.path.join(test_dir, filename)
        with open(path, 'w') as f:
            f.write(content)
    
    # Create test subdirectory
    subdir = os.path.join(test_dir, "subfolder")
    if not os.path.exists(subdir):
        os.makedirs(subdir)
        with open(os.path.join(subdir, "subfile.txt"), 'w') as f:
            f.write("sub content")
    
    return test_dir


def test_cleanup(test_dir):
    """Clean up test environment"""
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"✓ Cleaned up test directory: {test_dir}")


def print_section(title):
    """Print test section header"""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")


def print_result(test_name, passed, message=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {test_name}")
    if message:
        print(f"  → {message}")


def test_filesystem_abstraction():
    """Test FileSystemAbstraction layer"""
    print_section("1. File System Abstraction Layer Tests")
    
    test_dir = test_setup()
    fs = FileSystemAbstraction(test_dir)
    
    # Test 1.1: List directory
    try:
        files = fs.list_directory(test_dir)
        passed = len(files) > 0
        print_result("List directory", passed, f"Found {len(files)} items")
        for f in files:
            print(f"  - {f.name} (inode: {f.inode_number}, size: {f.size})")
    except Exception as e:
        print_result("List directory", False, str(e))
    
    # Test 1.2: Get file info
    try:
        test_file = os.path.join(test_dir, "test1.txt")
        info = fs.get_file_info(test_file)
        passed = info.name == "test1.txt"
        print_result("Get file info", passed, f"File: {info.name}, Size: {info.size}")
    except Exception as e:
        print_result("Get file info", False, str(e))
    
    # Test 1.3: Permission checks
    try:
        can_read = fs.can_read(test_dir)
        can_write = fs.can_write(test_dir)
        can_exec = fs.can_execute(test_dir)
        passed = can_read and can_write and can_exec
        print_result(
            "Permission checks",
            passed,
            f"R:{can_read} W:{can_write} X:{can_exec}"
        )
    except Exception as e:
        print_result("Permission checks", False, str(e))
    
    # Test 1.4: Path validation
    try:
        invalid_path = "/nonexistent/path/to/file"
        try:
            fs._validate_path(invalid_path)
            print_result("Path validation", False, "Should have raised FileNotFoundError")
        except FileNotFoundError:
            print_result("Path validation", True, "Correctly rejected invalid path")
    except Exception as e:
        print_result("Path validation", False, str(e))
    
    test_cleanup(test_dir)


def test_file_operations():
    """Test file operations"""
    print_section("2. File Operations Tests")
    
    test_dir = test_setup()
    fm = FileManager(test_dir)
    
    # Test 2.1: Browse directory
    try:
        result = fm.browse_directory(test_dir)
        passed = result.success and result.data is not None
        print_result("Browse directory", passed, f"{len(result.data)} files found")
    except Exception as e:
        print_result("Browse directory", False, str(e))
    
    # Test 2.2: Get file info
    try:
        test_file = os.path.join(test_dir, "test1.txt")
        result = fm.get_file_info(test_file)
        passed = result.success and result.data.name == "test1.txt"
        print_result("Get file info", passed, result.message)
    except Exception as e:
        print_result("Get file info", False, str(e))
    
    # Test 2.3: Rename file
    try:
        test_file = os.path.join(test_dir, "test1.txt")
        result = fm.rename_file(test_file, "renamed.txt")
        passed = result.success
        print_result("Rename file", passed, result.message)
        
        # Verify rename
        if passed:
            renamed_path = os.path.join(test_dir, "renamed.txt")
            exists = os.path.exists(renamed_path)
            print_result("  Verify rename", exists, f"File exists: {exists}")
    except Exception as e:
        print_result("Rename file", False, str(e))
    
    # Test 2.4: Delete file
    try:
        test_file = os.path.join(test_dir, "test2.txt")
        result = fm.delete_file(test_file)
        passed = result.success and not os.path.exists(test_file)
        print_result("Delete file", passed, result.message)
    except Exception as e:
        print_result("Delete file", False, str(e))
    
    test_cleanup(test_dir)


def test_error_handling():
    """Test error handling"""
    print_section("3. Error Handling Tests")
    
    test_dir = test_setup()
    fm = FileManager(test_dir)
    
    # Test 3.1: File not found
    try:
        nonexistent = os.path.join(test_dir, "does_not_exist.txt")
        result = fm.get_file_info(nonexistent)
        passed = not result.success and "NotFound" in result.error_type
        print_result("File not found error", passed, result.message)
    except Exception as e:
        print_result("File not found error", False, str(e))
    
    # Test 3.2: Not a directory
    try:
        test_file = os.path.join(test_dir, "test1.txt")
        result = fm.browse_directory(test_file)
        passed = not result.success and "NotADirectory" in result.error_type
        print_result("Not a directory error", passed, result.message)
    except Exception as e:
        print_result("Not a directory error", False, str(e))
    
    # Test 3.3: Invalid filename in rename
    try:
        test_file = os.path.join(test_dir, "test1.txt")
        result = fm.rename_file(test_file, "bad/name.txt")
        passed = not result.success
        print_result("Invalid filename error", passed, result.message)
    except Exception as e:
        print_result("Invalid filename error", False, str(e))
    
    test_cleanup(test_dir)


def test_permission_scenarios():
    """Test permission-related scenarios"""
    print_section("4. Permission Scenarios")
    
    test_dir = test_setup()
    fm = FileManager(test_dir)
    
    # Test 4.1: Can read own directory
    try:
        result = fm.browse_directory(test_dir)
        passed = result.success
        print_result("Read own directory", passed, "Can list own files")
    except Exception as e:
        print_result("Read own directory", False, str(e))
    
    # Test 4.2: Cannot read /root (if not root)
    try:
        result = fm.browse_directory("/root")
        if os.getuid() != 0:
            passed = not result.success and "PermissionDenied" in result.error_type
            print_result(
                "Permission denied on /root",
                passed,
                f"Correctly rejected: {result.message}"
            )
        else:
            print_result("Permission denied on /root", True, "Running as root, skipped")
    except Exception as e:
        print_result("Permission denied on /root", False, str(e))
    
    test_cleanup(test_dir)


def test_inode_information():
    """Test inode information extraction"""
    print_section("5. Inode Information Tests")
    
    test_dir = test_setup()
    fm = FileManager(test_dir)
    
    try:
        test_file = os.path.join(test_dir, "test1.txt")
        result = fm.get_file_info(test_file)
        
        if result.success:
            node = result.data
            print_result("Extract inode info", True, "")
            print(f"  Inode number: {node.inode_number}")
            print(f"  Size: {node.size} bytes")
            print(f"  Permissions (octal): {node.get_permission_octal()}")
            print(f"  Permissions (string): {node.get_permissions_string()}")
            print(f"  Owner UID: {node.owner_uid}")
            print(f"  Owner GID: {node.owner_gid}")
            print(f"  Modified: {node.get_modified_time_str()}")
            print(f"  Hard links: {node.hard_links}")
            print(f"  Type: {'Directory' if node.is_dir else 'File'}")
        else:
            print_result("Extract inode info", False, result.message)
    except Exception as e:
        print_result("Extract inode info", False, str(e))
    
    test_cleanup(test_dir)


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print(" AIFE Test Suite - OS Concepts Demonstration")
    print("="*60)
    
    try:
        test_filesystem_abstraction()
        test_file_operations()
        test_error_handling()
        test_permission_scenarios()
        test_inode_information()
        
        print_section("Test Suite Complete")
        print("\n✓ All tests completed. Check results above.")
        print("\nOs Concepts Demonstrated:")
        print("  ✓ VFS Abstraction (FileSystemAbstraction layer)")
        print("  ✓ System Calls (os.stat, os.listdir, os.remove, etc.)")
        print("  ✓ File Permissions (rwx checks, EACCES errors)")
        print("  ✓ Inode Metadata (st_ino, st_mode, st_size, etc.)")
        print("  ✓ Error Handling (errno mapping to exceptions)")
        print("  ✓ Path Resolution (realpath normalization)")
        
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
