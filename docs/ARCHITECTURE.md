# Application Architecture

## Directory Structure
```
whisper-transcriber/
├── docs/
│   └── README.md
├── src/
│   ├── __init__.py
│   ├── gui/
│   │   ├── __init__.py
│   │   └── window.py
│   ├── transcription/
│   │   ├── __init__.py
│   │   ├── chunker.py
│   │   └── processor.py
│   └── utils/
│       ├── __init__.py
│       └── file_handler.py
├── tests/
│   └── __init__.py
├── output/
├── requirements.txt
├── .env.example
└── main.py
```

## Component Overview

### 1. GUI Module (`src/gui/`)
- `window.py`: Main application window implementation
  - File selection dialog
  - Progress display
  - Status updates
  - Configuration options

### 2. Transcription Module (`src/transcription/`)
- `chunker.py`: Handles audio file splitting
  - File size validation
  - Intelligent chunk splitting
  - Temporary file management
- `processor.py`: Manages API interaction
  - OpenAI API integration
  - Rate limiting
  - Error handling
  - Response processing

### 3. Utils Module (`src/utils/`)
- `file_handler.py`: File operations
  - Input validation
  - Output file management
  - Temporary file cleanup
  - Format conversion

## Data Flow
1. User Input → GUI
2. GUI → File Handler
3. File Handler → Chunker
4. Chunker → Processor
5. Processor → OpenAI API
6. Processor → File Handler
7. File Handler → Output Files

## Key Components

### Audio Processing
- Format validation
- Chunk size calculation
- Silence detection for splitting
- Memory-efficient processing

### API Integration
- Authentication management
- Request rate limiting
- Error recovery
- Response validation

### File Management
- Input validation
- Output organization
- Temporary file handling
- Cleanup procedures

## Error Handling Strategy
1. Input Validation
   - File format checking
   - Size verification
   - Permission validation

2. Processing Errors
   - Chunk processing failures
   - Memory management
   - Recovery procedures

3. API Errors
   - Connection issues
   - Rate limiting
   - Authentication problems

4. Output Errors
   - Disk space
   - Write permissions
   - File conflicts

## Performance Considerations
- Multithreaded processing
- Memory management
- Disk I/O optimization
- API rate limiting
``` 