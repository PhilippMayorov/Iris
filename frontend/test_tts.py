#!/usr/bin/env python3
"""
Test script for ElevenLabs Text-to-Speech functionality
"""

import os
import sys
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_elevenlabs_connection():
    """Test ElevenLabs API connection and TTS functionality"""
    try:
        from elevenlabs import ElevenLabs
        
        api_key = os.getenv('ELEVENLABS_API_KEY')
        if not api_key:
            print("❌ ELEVENLABS_API_KEY not found in environment variables")
            return False
        
        print("✅ ElevenLabs API key found")
        
        # Initialize client
        client = ElevenLabs(api_key=api_key)
        print("✅ ElevenLabs client initialized")
        
        # Test TTS conversion
        test_text = "Hello! This is a test of the ElevenLabs text-to-speech functionality."
        voice_id = "JBFqnCBsd6RMkjVDRZzb"  # Default voice
        model_id = "eleven_multilingual_v2"
        output_format = "mp3_44100_128"
        
        print(f"🎤 Converting text to speech: '{test_text}'")
        print(f"🔊 Using voice: {voice_id}")
        print(f"🤖 Using model: {model_id}")
        print(f"📁 Output format: {output_format}")
        
        # Make the TTS request
        response = client.text_to_speech.convert(
            voice_id=voice_id,
            output_format=output_format,
            text=test_text,
            model_id=model_id
        )
        
        # Handle generator response from ElevenLabs API
        if hasattr(response, '__iter__') and not isinstance(response, (bytes, str)):
            # Convert generator to bytes
            audio_bytes = b''.join(response)
            print("✅ TTS conversion successful! (Generator response handled)")
        else:
            # Direct bytes response
            audio_bytes = response
            print("✅ TTS conversion successful! (Direct bytes response)")
        
        print(f"📊 Audio data size: {len(audio_bytes)} bytes")
        
        # Save audio file for testing
        output_file = "test_tts_output.mp3"
        with open(output_file, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"💾 Audio saved to: {output_file}")
        
        # Test base64 encoding (as used in the API)
        audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
        print(f"📝 Base64 encoded size: {len(audio_b64)} characters")
        
        return True
        
    except ImportError:
        print("❌ ElevenLabs library not installed. Please install with: pip install elevenlabs")
        return False
    except Exception as e:
        print(f"❌ ElevenLabs test failed: {str(e)}")
        return False

def test_flask_endpoint():
    """Test the Flask TTS endpoint"""
    try:
        import requests
        
        # Test data
        test_data = {
            "text": "Hello from the Flask TTS endpoint!",
            "voice_id": "JBFqnCBsd6RMkjVDRZzb",
            "model_id": "eleven_multilingual_v2",
            "output_format": "mp3_44100_128"
        }
        
        print("🌐 Testing Flask TTS endpoint...")
        print(f"📤 Sending request to: http://127.0.0.1:5001/api/text-to-speech")
        print(f"📝 Test text: '{test_data['text']}'")
        
        # Make request to Flask endpoint
        response = requests.post(
            "http://127.0.0.1:5001/api/text-to-speech",
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Flask TTS endpoint working!")
                print(f"📊 Response contains audio data: {len(data.get('audio_data', ''))} characters")
                return True
            else:
                print(f"❌ Flask endpoint returned error: {data.get('error')}")
                return False
        else:
            print(f"❌ Flask endpoint returned status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to Flask server. Make sure the frontend is running on http://127.0.0.1:5001")
        return False
    except Exception as e:
        print(f"❌ Flask endpoint test failed: {str(e)}")
        return False

def main():
    """Run all TTS tests"""
    print("🧪 Testing ElevenLabs Text-to-Speech Integration")
    print("=" * 50)
    
    # Test 1: Direct ElevenLabs API
    print("\n1️⃣ Testing direct ElevenLabs API connection...")
    elevenlabs_ok = test_elevenlabs_connection()
    
    # Test 2: Flask endpoint (only if server is running)
    print("\n2️⃣ Testing Flask TTS endpoint...")
    flask_ok = test_flask_endpoint()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   ElevenLabs API: {'✅ PASS' if elevenlabs_ok else '❌ FAIL'}")
    print(f"   Flask Endpoint: {'✅ PASS' if flask_ok else '❌ FAIL'}")
    
    if elevenlabs_ok and flask_ok:
        print("\n🎉 All tests passed! TTS functionality is working correctly.")
        return 0
    elif elevenlabs_ok:
        print("\n⚠️  ElevenLabs API works, but Flask endpoint failed. Check if the frontend server is running.")
        return 1
    else:
        print("\n❌ ElevenLabs API test failed. Check your API key and internet connection.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
