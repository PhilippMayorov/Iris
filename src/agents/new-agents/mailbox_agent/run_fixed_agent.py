#!/usr/bin/env python3
"""
Run the fixed mailbox agent that handles API errors gracefully
"""

import os
import sys
import subprocess
import time

def main():
    """Main function"""
    print("🧠 Running Fixed Mailbox Agent")
    print("=" * 50)
    
    # Check for ASI_ONE_API_KEY
    if not os.getenv('ASI_ONE_API_KEY'):
        print("⚠️ ASI_ONE_API_KEY not set - running in fallback mode")
        print("💡 For full functionality, set: export ASI_ONE_API_KEY='your_key_here'")
    else:
        print("✅ ASI_ONE_API_KEY is set")
    
    print("🚀 Starting fixed mailbox agent...")
    print("💡 This version handles API errors gracefully")
    print("=" * 50)
    
    try:
        # Run the fixed agent
        subprocess.run([sys.executable, "mailbox_agent_fixed.py"])
    except KeyboardInterrupt:
        print("\n👋 Agent stopped by user")
    except Exception as e:
        print(f"❌ Error running agent: {e}")

if __name__ == "__main__":
    main()
