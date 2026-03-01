#!/usr/bin/env python3
"""
Test script for LLM Chatbot Backend

This script tests the LLM backend without GUI to verify it works correctly.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from filesystem import FileSystemAbstraction
from llm_chatbot_backend import LLMChatbotBackend, LLMProvider, LLMIntegrationManager


def test_metadata_gathering():
    """Test file system metadata gathering"""
    print("\n" + "="*60)
    print("TEST 1: Metadata Gathering")
    print("="*60)
    
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    backend = LLMChatbotBackend(fs)
    
    home_dir = os.path.expanduser("~")
    context = backend.gather_file_metadata(home_dir)
    
    print(f"✓ Current Directory: {context.current_directory}")
    print(f"✓ Total Files: {context.total_files_count}")
    print(f"✓ Total Size: {context.total_size_bytes / (1024*1024):.2f} MB")
    print(f"✓ Subdirectories: {context.directory_structure.get('subdirs', 0)}")
    print(f"✓ Regular Files: {context.directory_structure.get('regular_files', 0)}")
    print(f"✓ Symlinks: {context.directory_structure.get('symlinks', 0)}")
    print(f"✓ Recent files shown: {len(context.recent_files)}")


def test_prompt_building():
    """Test prompt building"""
    print("\n" + "="*60)
    print("TEST 2: Prompt Building")
    print("="*60)
    
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    backend = LLMChatbotBackend(fs)
    
    # Test system prompt
    system_prompt = backend._build_system_prompt()
    print(f"✓ System Prompt Length: {len(system_prompt)} chars")
    print(f"✓ Contains instructions: {'file system helper' in system_prompt}")
    
    # Test user prompt
    home_dir = os.path.expanduser("~")
    context = backend.gather_file_metadata(home_dir)
    user_prompt = backend._build_user_prompt("Show me Python files", context)
    print(f"✓ User Prompt Length: {len(user_prompt)} chars")
    print(f"✓ Contains context: {'Recent Files' in user_prompt}")
    print(f"✓ Contains query: {'Python files' in user_prompt}")


def test_action_extraction():
    """Test action extraction from responses"""
    print("\n" + "="*60)
    print("TEST 3: Action Extraction")
    print("="*60)
    
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    backend = LLMChatbotBackend(fs)
    
    test_responses = [
        "I suggest you open this file or rename it",
        "You should delete this file with caution",
        "Here are the file properties",
        "Try moving this to another directory"
    ]
    
    context = backend.gather_file_metadata(os.path.expanduser("~"))
    
    for response in test_responses:
        actions = backend._extract_suggested_actions(response, context)
        print(f"✓ Response: '{response[:40]}...'")
        print(f"  Actions: {actions}")


def test_action_type_determination():
    """Test action type determination"""
    print("\n" + "="*60)
    print("TEST 4: Action Type Determination")
    print("="*60)
    
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    backend = LLMChatbotBackend(fs)
    
    test_queries = [
        ("Open the config file", "open"),
        ("Rename this to backup.txt", "rename"),
        ("Delete the old file", "delete"),
        ("Show me file properties", "properties")
    ]
    
    for query, expected_action in test_queries:
        action = backend._determine_action_type(query)
        status = "✓" if action == expected_action else "✗"
        print(f"{status} Query: '{query}'")
        print(f"   Expected: {expected_action}, Got: {action}")


def test_ollama_connection():
    """Test Ollama connection (if available)"""
    print("\n" + "="*60)
    print("TEST 5: Ollama Connection")
    print("="*60)
    
    try:
        import requests
        
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        response = requests.get(f"{ollama_url}/api/tags", timeout=2)
        
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✓ Ollama is running at {ollama_url}")
            print(f"✓ Available models: {len(models)}")
            for model in models[:3]:
                print(f"  - {model.get('name', 'Unknown')}")
        else:
            print(f"✗ Ollama returned status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("⚠ Ollama is not running")
        print("  Start it with: ollama serve")
    except Exception as e:
        print(f"⚠ Error checking Ollama: {e}")


def test_integration_manager():
    """Test LLM Integration Manager"""
    print("\n" + "="*60)
    print("TEST 6: LLM Integration Manager")
    print("="*60)
    
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    
    try:
        manager = LLMIntegrationManager(
            fs_abstraction=fs,
            provider=LLMProvider.OLLAMA
        )
        
        print("✓ Manager initialized successfully")
        
        # Get context info
        context_info = manager.get_context_info(os.path.expanduser("~"))
        print(f"✓ Context gathered: {len(context_info['recent_files'])} files")
        print(f"✓ Directory structure: {context_info['directory_structure']}")
        
    except Exception as e:
        print(f"✗ Error initializing manager: {e}")


def test_conversation_history():
    """Test conversation history management"""
    print("\n" + "="*60)
    print("TEST 7: Conversation History")
    print("="*60)
    
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    backend = LLMChatbotBackend(fs)
    
    print(f"✓ Initial history size: {len(backend.conversation_history)}")
    
    # Simulate conversation
    backend.conversation_history.append({"role": "user", "content": "Hello"})
    backend.conversation_history.append({"role": "assistant", "content": "Hi there"})
    
    print(f"✓ After adding messages: {len(backend.conversation_history)}")
    
    # Test history trimming
    for i in range(30):
        backend.conversation_history.append({"role": "user", "content": f"Message {i}"})
    
    print(f"✓ After adding 30 messages: {len(backend.conversation_history)}")
    print(f"✓ Max history limit: {backend.max_history}")
    
    backend.clear_history()
    print(f"✓ After clearing: {len(backend.conversation_history)}")


def test_error_handling():
    """Test error handling"""
    print("\n" + "="*60)
    print("TEST 8: Error Handling")
    print("="*60)
    
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    backend = LLMChatbotBackend(fs)
    
    # Test with invalid directory
    try:
        context = backend.gather_file_metadata("/nonexistent/path")
        print(f"✓ Handled invalid directory gracefully")
        print(f"  Files count: {context.total_files_count}")
    except Exception as e:
        print(f"✗ Error handling invalid directory: {e}")
    
    # Test byte formatting
    test_sizes = [100, 1024, 1024*1024, 1024*1024*1024]
    for size in test_sizes:
        formatted = backend._format_bytes(size)
        print(f"✓ {size} bytes → {formatted}")


def main():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*15 + "AIFE LLM Backend Test Suite" + " "*15 + "║")
    print("╚" + "="*58 + "╝")
    
    try:
        test_metadata_gathering()
        test_prompt_building()
        test_action_extraction()
        test_action_type_determination()
        test_ollama_connection()
        test_integration_manager()
        test_conversation_history()
        test_error_handling()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS COMPLETED")
        print("="*60 + "\n")
        
        return 0
    except Exception as e:
        print(f"\n✗ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
