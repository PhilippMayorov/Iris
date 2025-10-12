#!/usr/bin/env python3
"""
Setup and run script for Spotify Playlist Agent
Following Fetch.ai uAgents framework documentation
"""

import subprocess
import sys
import os

def check_python_version():
    """Check if Python 3.8+ is installed"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

def setup_virtual_environment():
    """Create and activate virtual environment"""
    print("🔧 Setting up virtual environment...")
    
    if not os.path.exists("venv"):
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("✅ Virtual environment created")
    else:
        print("✅ Virtual environment already exists")

def install_dependencies():
    """Install required packages"""
    print("📦 Installing dependencies...")
    
    # Activate venv and install packages
    if os.name == 'nt':  # Windows
        pip_path = "venv\\Scripts\\pip"
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        pip_path = "venv/bin/pip"
        python_path = "venv/bin/python"
    
    try:
        # Install uagents first
        subprocess.run([pip_path, "install", "uagents"], check=True)
        print("✅ uAgents framework installed")
        
        # Install other requirements
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print("✅ All dependencies installed")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

def run_agent():
    """Run the Spotify agent"""
    print("🎵 Starting Spotify Playlist Agent...")
    
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        python_path = "venv/bin/python"
    
    try:
        subprocess.run([python_path, "spotify_agent.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Agent stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running agent: {e}")

def run_tests():
    """Run the test script"""
    print("🧪 Running tests...")
    
    if os.name == 'nt':  # Windows
        python_path = "venv\\Scripts\\python"
    else:  # Unix/Linux/MacOS
        python_path = "venv/bin/python"
    
    try:
        subprocess.run([python_path, "test_spotify_agent.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests: {e}")

def main():
    """Main setup and run function"""
    print("🎼 Spotify Playlist Agent Setup")
    print("=" * 50)
    
    # Check requirements
    check_python_version()
    
    # Setup environment
    setup_virtual_environment()
    install_dependencies()
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print("\nAvailable commands:")
    print("1. Run agent: python setup.py run")
    print("2. Run tests: python setup.py test")
    print("3. Manual run: source venv/bin/activate && python spotify_agent.py")
    
    # Check command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        if command == "run":
            run_agent()
        elif command == "test":
            run_tests()
        else:
            print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()