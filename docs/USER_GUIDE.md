# Whisper Transcriber - User Guide

## Table of Contents
1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Basic Usage](#basic-usage)
4. [Advanced Features](#advanced-features)
5. [Troubleshooting](#troubleshooting)
6. [FAQ](#faq)

## Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key
- Sufficient disk space for audio processing

### Step-by-Step Installation
1. Clone the repository or download the latest release:
   ```bash
   git clone <repository-url>
   cd whisper-transcriber
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows:
   .\venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up your API key:
   - Copy `.env.example` to `.env`
   - Add your OpenAI API key to the `.env` file:
     ```
     OPENAI_API_KEY=your_api_key_here
     ```

## Getting Started

### First Run
1. Activate your virtual environment (if not already activated)
2. Run the application:
   ```bash
   python main.py
   ```
3. The application window will appear, ready for use

### Interface Overview
- **File Selection**: Choose your audio file using the "Browse" button
- **Output Directory**: Select where to save the transcription
- **Options Panel**: Configure transcription settings
- **Progress Bar**: Shows transcription progress
- **Status Display**: Provides current operation status

## Basic Usage

### Transcribing an Audio File
1. Click "Browse" to select your audio file
2. Choose an output directory
3. Click "Transcribe" to start the process
4. Monitor progress in the status bar
5. Find your transcription in the output directory

### Supported File Formats
- MP3 (.mp3)
- MP4 (.mp4)
- WAV (.wav)
- M4A (.m4a)
- WEBM (.webm)
- MPGA (.mpga)
- MPEG (.mpeg)

### Output Format
- Default: Plain text (.txt)
- Filename format: `original_name_transcription_YYYYMMDD_HHMMSS.txt`
- Optional: Timestamps can be enabled in settings

## Advanced Features

### Language Selection
- Auto-detection (default)
- Manual language selection for better accuracy
- Supports 50+ languages

### Timestamp Options
- Enable word-level timestamps
- Useful for precise audio-text alignment
- Format: `[HH:MM:SS.mmm] word`

### Large File Handling
- Automatic chunking for files > 25MB
- Intelligent splitting at silence points
- Progress tracking per chunk
- Automatic reassembly

### Error Recovery
- Automatic retry on API failures
- Session recovery after crashes
- Temporary file cleanup
- Progress preservation

## Troubleshooting

### Common Issues

#### Application Won't Start
1. Verify Python version: `python --version`
2. Check virtual environment activation
3. Verify all dependencies are installed
4. Check for error messages in the console

#### API Key Issues
1. Verify `.env` file exists
2. Check API key format
3. Ensure no extra spaces or quotes
4. Verify API key validity

#### File Processing Errors
1. Check file format compatibility
2. Verify file isn't corrupted
3. Ensure sufficient disk space
4. Check file permissions

#### Performance Issues
1. Close unnecessary applications
2. Check available disk space
3. Monitor system resources
4. Consider processing in smaller chunks

### Error Messages
- "API Key not found": Check `.env` file
- "Unsupported format": Verify file type
- "File too large": Enable chunking
- "Permission denied": Check file/folder permissions

## FAQ

### General Questions

**Q: How long does transcription take?**  
A: Processing time depends on file size, typically 1-2x the audio duration.

**Q: What's the maximum file size?**  
A: No strict limit, but files >25MB are automatically chunked.

**Q: Which languages are supported?**  
A: 50+ languages with >50% accuracy. See supported languages list.

### Technical Questions

**Q: Can I process multiple files?**  
A: Yes, but one at a time through the GUI.

**Q: Where are temporary files stored?**  
A: In the `temp` directory, automatically cleaned up.

**Q: How accurate is the transcription?**  
A: Depends on audio quality and language, typically 80-95% accurate.

### Best Practices

1. **Audio Quality**
   - Use clear recordings
   - Minimize background noise
   - Maintain consistent volume

2. **File Preparation**
   - Convert to supported formats
   - Split very long recordings
   - Remove unnecessary sections

3. **Resource Management**
   - Monitor disk space
   - Close unnecessary applications
   - Regular system maintenance

4. **Error Prevention**
   - Keep API key secure
   - Regular backups
   - Monitor system resources
``` 