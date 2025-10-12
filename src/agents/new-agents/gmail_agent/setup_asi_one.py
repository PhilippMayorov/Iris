#!/usr/bin/env python3
"""
Setup script for ASI:One API key to enable context functionality in Gmail Agent

This script helps you set up the ASI:One API key to enable natural language
email processing and conversation context in the Gmail Agent.
"""

import os
import sys
from pathlib import Path

def setup_asi_one_key():
    """Setup ASI:One API key for the Gmail Agent"""
    
    print("🔧 ASI:One API Key Setup for Gmail Agent")
    print("=" * 50)
    
    print("\n📋 What is ASI:One?")
    print("ASI:One is an AI service that enables natural language processing")
    print("for the Gmail Agent. It allows you to send emails using casual,")
    print("conversational language instead of structured commands.")
    print("\n🎯 Benefits:")
    print("- Send emails using natural language")
    print("- Maintain conversation context across interactions")
    print("- Intelligent email content generation")
    print("- Better user experience")
    
    print("\n🔑 Getting Your API Key:")
    print("1. Visit: https://asi1.ai/dashboard/api-keys")
    print("2. Sign up or log in to your account")
    print("3. Create a new API key")
    print("4. Copy the API key")
    
    print("\n⚙️ Setup Options:")
    print("1. Set environment variable (recommended)")
    print("2. Create .env file")
    print("3. Test with temporary key")
    
    choice = input("\nChoose setup method (1-3): ").strip()
    
    if choice == "1":
        setup_environment_variable()
    elif choice == "2":
        setup_env_file()
    elif choice == "3":
        test_temporary_key()
    else:
        print("❌ Invalid choice. Please run the script again.")
        return False
    
    return True

def setup_environment_variable():
    """Setup ASI:One API key as environment variable"""
    
    print("\n🔧 Setting up environment variable...")
    
    api_key = input("Enter your ASI:One API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided.")
        return False
    
    # Get shell type
    shell = os.environ.get('SHELL', '').split('/')[-1]
    
    if 'zsh' in shell:
        config_file = os.path.expanduser('~/.zshrc')
    elif 'bash' in shell:
        config_file = os.path.expanduser('~/.bashrc')
    else:
        config_file = os.path.expanduser('~/.profile')
    
    print(f"\n📝 Adding to {config_file}...")
    
    export_line = f'export ASI_ONE_API_KEY="{api_key}"'
    
    try:
        # Check if already exists
        with open(config_file, 'r') as f:
            content = f.read()
            if 'ASI_ONE_API_KEY' in content:
                print("⚠️ ASI_ONE_API_KEY already exists in your shell config.")
                replace = input("Replace existing key? (y/n): ").strip().lower()
                if replace == 'y':
                    # Remove existing line
                    lines = content.split('\n')
                    lines = [line for line in lines if 'ASI_ONE_API_KEY' not in line]
                    content = '\n'.join(lines)
                else:
                    print("❌ Setup cancelled.")
                    return False
        
        # Add the export line
        with open(config_file, 'a') as f:
            f.write(f'\n# ASI:One API Key for Gmail Agent\n{export_line}\n')
        
        print(f"✅ Added ASI_ONE_API_KEY to {config_file}")
        print(f"\n🔄 To apply changes, run:")
        print(f"   source {config_file}")
        print(f"\nOr restart your terminal.")
        
        # Test the key
        test_api_key(api_key)
        
    except Exception as e:
        print(f"❌ Error writing to {config_file}: {e}")
        return False
    
    return True

def setup_env_file():
    """Setup ASI:One API key in .env file"""
    
    print("\n🔧 Setting up .env file...")
    
    api_key = input("Enter your ASI:One API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided.")
        return False
    
    env_file = Path(__file__).parent / '.env'
    
    try:
        # Check if .env already exists
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                if 'ASI_ONE_API_KEY' in content:
                    print("⚠️ ASI_ONE_API_KEY already exists in .env file.")
                    replace = input("Replace existing key? (y/n): ").strip().lower()
                    if replace != 'y':
                        print("❌ Setup cancelled.")
                        return False
        
        # Write or update .env file
        with open(env_file, 'w') as f:
            f.write(f'# ASI:One API Key for Gmail Agent\n')
            f.write(f'ASI_ONE_API_KEY={api_key}\n')
        
        print(f"✅ Created/updated {env_file}")
        print(f"\n📝 To use this .env file, you'll need to load it in your application.")
        print(f"   The Gmail Agent will automatically load it if using python-dotenv.")
        
        # Test the key
        test_api_key(api_key)
        
    except Exception as e:
        print(f"❌ Error writing to .env file: {e}")
        return False
    
    return True

def test_temporary_key():
    """Test with a temporary API key"""
    
    print("\n🧪 Testing with temporary API key...")
    
    api_key = input("Enter your ASI:One API key: ").strip()
    
    if not api_key:
        print("❌ No API key provided.")
        return False
    
    # Set environment variable for current session
    os.environ['ASI_ONE_API_KEY'] = api_key
    
    print("✅ API key set for current session")
    print("⚠️ This will only work for the current terminal session.")
    print("   For permanent setup, use option 1 or 2.")
    
    # Test the key
    test_api_key(api_key)
    
    return True

def test_api_key(api_key):
    """Test the API key with the Gmail Agent"""
    
    print(f"\n🧪 Testing API key...")
    
    try:
        # Import and test the Gmail agent
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from gmail_agent import process_email_request_with_asi_one
        
        # Test with a simple request
        test_input = "send an email to test@example.com about the meeting"
        result = process_email_request_with_asi_one(test_input, [])
        
        if result and result.get('is_valid_format'):
            print("✅ API key is working! Natural language processing is enabled.")
            print(f"   Test result: {result.get('to')} - {result.get('subject')}")
        else:
            print("⚠️ API key accepted but processing failed.")
            if result and result.get('error'):
                print(f"   Error: {result['error']}")
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        print("   The key might be invalid or there might be a network issue.")

def main():
    """Main setup function"""
    
    print("Gmail Agent - ASI:One Setup")
    print("=" * 50)
    
    # Check if already set
    if os.environ.get('ASI_ONE_API_KEY'):
        print("✅ ASI_ONE_API_KEY is already set!")
        print(f"   Current key: {os.environ['ASI_ONE_API_KEY'][:10]}...")
        
        test = input("\nTest current key? (y/n): ").strip().lower()
        if test == 'y':
            test_api_key(os.environ['ASI_ONE_API_KEY'])
        return
    
    # Run setup
    success = setup_asi_one_key()
    
    if success:
        print("\n🎉 Setup completed!")
        print("\n📋 Next steps:")
        print("1. Restart your terminal or run 'source ~/.zshrc' (or ~/.bashrc)")
        print("2. Start the Gmail Agent")
        print("3. Try sending emails using natural language!")
        print("\n💡 Example commands:")
        print("- 'send an email to john@example.com about the meeting'")
        print("- 'email the team about the project update'")
        print("- 'tell sarah we're running late'")
    else:
        print("\n❌ Setup failed. Please try again.")

if __name__ == "__main__":
    main()
