#!/usr/bin/env python3
"""
AIFE LLM Chatbot - Interactive Test Demo

This script demonstrates the LLM-powered chatbot backend working without GUI.
You can test queries and see the intelligent responses with file system context.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from filesystem import FileSystemAbstraction
from llm_chatbot_backend import LLMIntegrationManager, LLMProvider
from chatbot import ChatbotSettings


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_response(response_data):
    """Print formatted response"""
    print(f"💬 Response:")
    print(f"   {response_data['response']}")
    
    if response_data.get('suggested_actions'):
        print(f"\n📌 Suggested Actions: {', '.join(response_data['suggested_actions'])}")
    
    if response_data.get('action_type'):
        print(f"   Action Type: {response_data['action_type']}")
    
    if response_data.get('requires_confirmation'):
        print(f"   ⚠️  Requires Confirmation (destructive operation)")
    
    print(f"\n   Metadata Used: {', '.join(response_data['metadata_used'])}")
    print(f"   Timestamp: {response_data['timestamp']}")


def demo_interactive():
    """Interactive demo mode"""
    print_header("AIFE LLM Chatbot - Interactive Demo")
    
    print("📁 Setting up file system context...")
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    
    print("🤖 Initializing LLM backend with Ollama (local)...")
    print("   (Make sure Ollama is running: ollama serve)")
    print("   (You can also configure OpenAI in settings)")
    
    try:
        llm_manager = LLMIntegrationManager(
            fs_abstraction=fs,
            provider=LLMProvider.OLLAMA
        )
        print("✅ LLM Manager initialized successfully!\n")
    except Exception as e:
        print(f"⚠️  Could not initialize LLM: {e}")
        print("   Falling back to rule-based chatbot mode\n")
        return False
    
    current_dir = os.path.expanduser("~")
    
    print("=" * 70)
    print("💬 Interactive Chatbot - Type your queries (type 'quit' to exit)")
    print("=" * 70)
    print(f"\n📂 Current Directory: {current_dir}")
    print("\nExample queries:")
    print("  - 'Show me all files'")
    print("  - 'What Python files are here?'")
    print("  - 'How large is this directory?'")
    print("  - 'What are the permissions?'")
    print("  - 'Explain what an inode is'")
    print("\n")
    
    query_count = 0
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            query_count += 1
            print("\n⏳ Processing query...")
            
            response_data = llm_manager.process_user_message(
                user_input,
                current_dir
            )
            
            print_response(response_data)
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print()
    
    return True


def demo_predefined():
    """Demo with predefined queries"""
    print_header("AIFE LLM Chatbot - Predefined Demo")
    
    print("📁 Setting up file system context...")
    fs = FileSystemAbstraction(os.path.expanduser("~"))
    
    print("🤖 Initializing LLM backend...")
    llm_manager = LLMIntegrationManager(
        fs_abstraction=fs,
        provider=LLMProvider.OLLAMA
    )
    print("✅ LLM Manager initialized!\n")
    
    current_dir = os.path.expanduser("~")
    
    # Get context info first
    print("📊 Current Directory Context:")
    context = llm_manager.get_context_info(current_dir)
    print(f"   📂 Directory: {context['current_directory']}")
    print(f"   📄 Files: {context['total_files_count']}")
    print(f"   📁 Subdirectories: {context['directory_structure'].get('subdirs', 0)}")
    print(f"   💾 Total Size: {context['total_size_bytes'] / (1024*1024):.2f} MB")
    print()
    
    # Sample queries
    queries = [
        "Show me all the files in this directory",
        "What's the total size of this folder?",
        "How many Python files are there?",
        "What are permissions and why do they matter?",
    ]
    
    print("=" * 70)
    print("Running predefined queries...\n")
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*70}")
        print(f"Query {i}/{len(queries)}:")
        print(f"{'='*70}")
        print(f"\n❓ You: {query}")
        
        try:
            response_data = llm_manager.process_user_message(
                query,
                current_dir
            )
            print_response(response_data)
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("✅ Demo completed!")
    print("="*70)


def demo_settings():
    """Show settings configuration"""
    print_header("AIFE LLM Settings Configuration")
    
    settings = ChatbotSettings()
    
    print("📋 Current Settings:")
    print(f"   Use LLM Backend: {settings.get('use_llm_backend', True)}")
    print(f"   LLM Provider: {settings.get('llm_provider', 'ollama')}")
    print(f"   Ollama Model: {settings.get('ollama_model', 'llama2')}")
    print(f"   Temperature: {settings.get('temperature', 0.7)}")
    print(f"   Max History: {settings.get('max_history', 20)}")
    print(f"   API Key: {'*' * len(settings.get('api_key', '')) if settings.get('api_key') else '(not set)'}")
    
    print("\n📁 Settings File Location:")
    print(f"   {settings.CONFIG_FILE}")
    
    if os.path.exists(settings.CONFIG_FILE):
        print("   ✅ Settings file exists")
    else:
        print("   ⚠️  Settings file will be created on first save")


def main():
    """Main entry point"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*15 + "AIFE LLM Chatbot - Interactive Demo" + " "*19 + "║")
    print("╚" + "="*68 + "╝")
    
    print("\n🚀 Welcome to AIFE LLM Backend Demo!")
    print("\nThis demo shows the intelligent chatbot with:")
    print("  ✅ File system awareness")
    print("  ✅ LLM-powered responses")
    print("  ✅ Context-aware suggestions")
    print("  ✅ Multi-provider support (Ollama, OpenAI, etc.)")
    
    print("\n" + "="*70)
    print("Choose an option:")
    print("="*70)
    print("1. Interactive Demo (type queries manually)")
    print("2. Predefined Demo (see example queries)")
    print("3. View Settings Configuration")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        success = demo_interactive()
        if not success:
            print("\n💡 LLM backend not available.")
            print("   Make sure Ollama is running: ollama serve")
            return 1
    elif choice == "2":
        try:
            demo_predefined()
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            print("\n💡 To run demo with LLM responses:")
            print("   1. Install Ollama: https://ollama.ai")
            print("   2. Start Ollama: ollama serve")
            print("   3. Run this demo again")
            return 1
    elif choice == "3":
        demo_settings()
    elif choice == "4":
        print("\n👋 Goodbye!")
        return 0
    else:
        print("\n❌ Invalid choice")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
