"""
Setup script for Gmail Agent

This script helps set up the necessary Google Cloud credentials and authentication
for the Gmail Agent to work properly.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_gcloud_installed():
    """Check if gcloud CLI is installed"""
    try:
        result = subprocess.run(['gcloud', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Google Cloud CLI is installed")
            print(f"Version: {result.stdout.strip()}")
            return True
        else:
            print("❌ Google Cloud CLI is not installed")
            return False
    except FileNotFoundError:
        print("❌ Google Cloud CLI is not installed")
        return False


def check_authentication():
    """Check if user is authenticated with gcloud"""
    try:
        result = subprocess.run(['gcloud', 'auth', 'list'], capture_output=True, text=True)
        if result.returncode == 0 and "ACTIVE" in result.stdout:
            print("✅ User is authenticated with gcloud")
            return True
        else:
            print("❌ User is not authenticated with gcloud")
            return False
    except Exception as e:
        print(f"❌ Error checking authentication: {e}")
        return False


def setup_application_default_credentials():
    """Set up application default credentials"""
    try:
        print("Setting up application default credentials...")
        result = subprocess.run([
            'gcloud', 'auth', 'application-default', 'login'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Application default credentials set up successfully")
            return True
        else:
            print(f"❌ Failed to set up credentials: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error setting up credentials: {e}")
        return False


def check_gmail_api():
    """Check if Gmail API is enabled"""
    try:
        result = subprocess.run([
            'gcloud', 'services', 'list', '--enabled', '--filter=name:gmail.googleapis.com'
        ], capture_output=True, text=True)
        
        if result.returncode == 0 and "gmail.googleapis.com" in result.stdout:
            print("✅ Gmail API is enabled")
            return True
        else:
            print("❌ Gmail API is not enabled")
            return False
    except Exception as e:
        print(f"❌ Error checking Gmail API: {e}")
        return False


def enable_gmail_api():
    """Enable Gmail API"""
    try:
        print("Enabling Gmail API...")
        result = subprocess.run([
            'gcloud', 'services', 'enable', 'gmail.googleapis.com'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Gmail API enabled successfully")
            return True
        else:
            print(f"❌ Failed to enable Gmail API: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error enabling Gmail API: {e}")
        return False


def main():
    """Main setup function"""
    print("Gmail Agent Setup")
    print("================")
    print()
    
    # Check gcloud installation
    if not check_gcloud_installed():
        print("\nPlease install Google Cloud CLI:")
        print("https://cloud.google.com/sdk/docs/install")
        return False
    
    print()
    
    # Check authentication
    if not check_authentication():
        print("\nPlease authenticate with gcloud:")
        print("gcloud auth login")
        return False
    
    print()
    
    # Check Gmail API
    if not check_gmail_api():
        if not enable_gmail_api():
            print("\nPlease enable Gmail API manually:")
            print("gcloud services enable gmail.googleapis.com")
            return False
    
    print()
    
    # Set up application default credentials
    if not setup_application_default_credentials():
        print("\nPlease set up application default credentials manually:")
        print("gcloud auth application-default login")
        return False
    
    print()
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the Gmail agent: python gmail_agent.py")
    print("3. Test with client: python test_gmail_client.py")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
