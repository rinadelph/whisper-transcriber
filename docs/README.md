# Whisper Audio Transcription Application

## Overview
This application provides a user-friendly interface for transcribing audio files using OpenAI's Whisper API. It allows users to select audio files through a graphical interface, automatically handles file chunking for large files, and saves transcriptions to text files.

## Features
- GUI-based file selection
- Support for multiple audio formats (mp3, mp4, mpeg, mpga, m4a, wav, webm)
- Automatic file chunking for files larger than 25MB
- Real-time progress tracking
- Error handling and recovery
- Organized output file management
- Detailed logging system

## Requirements
- Python 3.8 or higher
- OpenAI API key
- Internet connection
- Sufficient disk space for temporary files

## Installation
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your OpenAI API key

## Usage
1. Run the application:
   ```bash
   python main.py
   ```
2. Use the file picker to select your audio file
3. Choose output directory (optional)
4. Click "Transcribe" to begin processing
5. Monitor progress in the application window
6. Find your transcription in the output directory

## Supported File Formats
- MP3 (.mp3)
- MP4 (.mp4)
- MPEG (.mpeg)
- MPGA (.mpga)
- M4A (.m4a)
- WAV (.wav)
- WebM (.webm)

## Output Format
- Default: Plain text (.txt)
- Filename format: `{original_filename}_transcription_{timestamp}.txt`
- Optional formats available: JSON, SRT

## Error Handling
- Automatic retry for failed API calls
- Invalid file format detection
- Network error recovery
- Disk space monitoring

## Contributing
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License
MIT License - See LICENSE file for details 