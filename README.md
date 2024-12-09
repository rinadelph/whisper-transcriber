# Whisper Transcriber

A robust GUI application for transcribing audio files using OpenAI's Whisper API. This application handles large audio files by intelligently chunking them and maintaining context between chunks for accurate transcription.

## Features

- 🎯 GUI interface for easy file selection and progress tracking
- 📦 Smart chunking of large audio files (optimized 25MB chunks)
- 🔄 Context preservation between chunks for better accuracy
- 🛡️ Robust error handling and retry mechanism
- 🧹 Automatic temp file cleanup
- 📝 Support for multiple audio formats (mp3, mp4, mpeg, mpga, m4a, wav, webm)

## Requirements

- Python 3.8+
- FFmpeg (for audio processing)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whisper-transcriber.git
cd whisper-transcriber
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
   - Windows: `winget install FFmpeg` or via [Chocolatey](https://chocolatey.org/): `choco install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

4. Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_api_key_here
```

## Usage

1. Run the application:
```bash
python src/main.py
```

2. Use the GUI to:
   - Select an audio file
   - Choose output location
   - Start transcription
   - Monitor progress

## How it Works

1. **File Processing:**
   - Audio files are split into optimal chunks (up to 24MB)
   - Chunks are created at natural break points (silence)
   - Each chunk maintains context from previous chunks

2. **Transcription:**
   - Uses OpenAI's Whisper API
   - Implements exponential backoff for reliability
   - Maintains context between chunks for accuracy

3. **Output:**
   - Generates clean, formatted transcription
   - Removes chunking artifacts
   - Preserves proper formatting and punctuation

## Development

The project structure:
```
whisper-transcriber/
├── src/
│   ├── gui/
│   │   └── window.py
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   ├── handler.py
│   │   └── processor.py
│   └── main.py
├── temp/
├── .env
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI's Whisper API
- PyDub for audio processing
- FFmpeg for media handling 