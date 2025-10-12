# Text-to-Speech (TTS) Integration with ElevenLabs

This document describes the ElevenLabs text-to-speech integration implemented in the Iris frontend.

## Features

- **Synchronized Response**: Text and audio appear together for seamless experience
- **Pre-loaded Audio**: TTS audio is prepared before text is shown
- **Multiple Voice Options**: Support for different ElevenLabs voices
- **Background Processing**: TTS generation happens without blocking the UI

## Setup

### 1. Environment Variables

Add your ElevenLabs API key to your `.env` file:

```bash
ELEVENLABS_API_KEY=your_api_key_here
```

### 2. Dependencies

The required dependency is already included in `requirements.txt`:

```
elevenlabs>=0.2.24
```

Install with:
```bash
pip install elevenlabs
```

## API Endpoint

### POST `/api/text-to-speech`

Converts text to speech using ElevenLabs API.

**Request Body:**
```json
{
  "text": "Text to convert to speech",
  "voice_id": "JBFqnCBsd6RMkjVDRZzb",  // Optional, defaults to default voice
  "model_id": "eleven_multilingual_v2", // Optional, defaults to multilingual model
  "output_format": "mp3_44100_128"      // Optional, defaults to MP3 44.1kHz 128kbps
}
```

**Response:**
```json
{
  "success": true,
  "audio_data": "base64_encoded_audio_data",
  "format": "mp3_44100_128",
  "voice_id": "JBFqnCBsd6RMkjVDRZzb",
  "model_id": "eleven_multilingual_v2"
}
```

## Frontend Integration

### UI Components

- **Synchronized Display**: Text remains hidden until audio is ready, then both appear together
- **Background Processing**: No UI elements needed - audio generation happens seamlessly
- **Audio Management**: Automatic cleanup of audio resources

### JavaScript Functions

- `prepareTTSAudio()`: Converts text to speech and prepares audio for playback
- `playPreparedAudio()`: Plays the pre-loaded audio
- `playTTS()`: Legacy function that combines preparation and playback
- `stopTTS()`: Stops currently playing audio and cleans up resources
- **Synchronized Flow**: Audio preparation → Text typing + Audio playback simultaneously

## Usage

1. **Get AI Response**: Use voice input to get a response from Iris
2. **Synchronized Experience**: Text and audio appear together once audio is ready
3. **Seamless Playback**: No user interaction needed - everything happens automatically
4. **Auto-cleanup**: Audio automatically stops when clearing or starting new requests

## Testing

Run the test script to verify TTS functionality:

```bash
cd frontend
python test_tts.py
```

This will test:
- ElevenLabs API connection
- Direct TTS conversion
- Flask endpoint functionality
- Audio file generation

## Voice Options

### Default Voice
- **ID**: `JBFqnCBsd6RMkjVDRZzb`
- **Type**: Natural, conversational voice
- **Language**: Multilingual support

### Available Models
- `eleven_multilingual_v2`: Best quality, supports multiple languages
- `eleven_monolingual_v1`: English only, faster processing

### Output Formats
- `mp3_44100_128`: High quality MP3 (default)
- `mp3_44100_64`: Standard quality MP3
- `mp3_22050_32`: Lower quality, smaller file size
- `pcm_44100`: Uncompressed audio (requires Pro tier)

## Error Handling

The implementation includes comprehensive error handling:

- **API Key Missing**: Clear error message if ElevenLabs API key not configured
- **Network Issues**: Graceful handling of connection problems
- **Audio Playback**: Error handling for browser audio issues
- **Invalid Text**: Validation for empty or invalid text input
- **Generator Responses**: Automatic handling of ElevenLabs API generator objects

## Browser Compatibility

- **Audio Support**: Works in all modern browsers with audio support
- **Base64 Decoding**: Uses standard Web APIs for audio data handling
- **Blob URLs**: Automatic cleanup of temporary audio URLs

## Performance Considerations

- **Audio Caching**: Audio data is generated on-demand
- **Memory Management**: Automatic cleanup of audio objects and URLs
- **Network Optimization**: Efficient base64 encoding for API responses
- **User Experience**: Non-blocking audio generation with visual feedback

## Troubleshooting

### Common Issues

1. **"ElevenLabs API not configured"**
   - Check that `ELEVENLABS_API_KEY` is set in your `.env` file
   - Restart the Flask server after adding the API key

2. **"TTS conversion failed"**
   - Verify your ElevenLabs API key is valid
   - Check your internet connection
   - Ensure you have sufficient ElevenLabs credits

3. **"Generator response error"**
   - This has been fixed in the current implementation
   - The API now automatically handles ElevenLabs generator responses
   - If you see this error, update to the latest version

4. **Audio not playing**
   - Check browser audio permissions
   - Try refreshing the page
   - Check browser console for JavaScript errors

5. **Text not appearing or audio not synchronized**
   - Check browser audio permissions
   - Ensure response text is available
   - Check browser console for TTS preparation errors
   - Try clearing and getting a new response

### Debug Mode

Enable debug logging by checking the browser console for detailed TTS operation logs.

## Future Enhancements

Potential improvements for the TTS integration:

- **Voice Selection**: UI for choosing different voices
- **Speed Control**: Adjustable playback speed
- **Volume Control**: Audio volume adjustment
- **Auto-play**: Option to automatically play responses
- **Voice Cloning**: Support for custom voice models
- **Streaming**: Real-time audio streaming for long responses
