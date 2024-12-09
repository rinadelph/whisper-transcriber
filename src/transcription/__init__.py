"""
Transcription Module for Whisper Transcriber
Handles audio file processing and interaction with OpenAI's Whisper API.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List, Generator, Callable
import logging

from openai import OpenAI
from pydub import AudioSegment

from .chunker import AudioChunker
from .processor import TranscriptionProcessor

logger = logging.getLogger(__name__)

__all__ = ['WhisperTranscriber', 'AudioChunker']

class WhisperTranscriber:
    """Handles audio transcription using OpenAI's Whisper API."""
    
    def __init__(self, api_key: str, temp_dir: Path) -> None:
        """
        Initialize the transcriber with OpenAI API key.
        
        Args:
            api_key: OpenAI API key for authentication
            temp_dir: Directory for temporary file storage
        """
        self.client = OpenAI(api_key=api_key)
        self.supported_formats = {'mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm'}
        self.chunker = AudioChunker(temp_dir)
        self.processor = TranscriptionProcessor(self.client)
        logger.info("WhisperTranscriber initialized")
    
    def transcribe_file(
        self,
        file_path: Path,
        output_path: Path,
        language: Optional[str] = None,
        response_format: str = "text",
        enable_timestamps: bool = False,
        chunk_callback: Optional[Callable[[int, int], None]] = None,
        transcription_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> None:
        """
        Transcribe an audio file, handling chunking if necessary.
        
        Args:
            file_path: Path to the audio file
            output_path: Path where to save the transcription
            language: Optional language code
            response_format: Format of the response (text or json)
            enable_timestamps: Whether to include timestamps
            chunk_callback: Callback for chunk processing progress (current, total)
            transcription_callback: Callback for transcription progress (current, total, text)
        """
        try:
            # Validate file format
            if not file_path.suffix.lstrip('.').lower() in self.supported_formats:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
            
            # Set up timestamp options
            timestamp_granularities = ["word"] if enable_timestamps else None
            
            # Process chunks
            chunk_paths = list(self.chunker.chunk_audio(file_path, chunk_callback))
            total_chunks = len(chunk_paths)
            
            self.processor.process_chunks(
                chunk_paths,
                output_path,
                language=language,
                response_format=response_format,
                timestamp_granularities=timestamp_granularities,
                progress_callback=transcription_callback
            )
            
            # Cleanup temporary files
            self.chunker.cleanup()
            
            logger.info(f"Successfully transcribed {file_path} to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to transcribe {file_path}: {e}")
            self.chunker.cleanup()  # Ensure cleanup even on failure
            raise
        
    def cleanup(self):
        """Clean up any temporary resources."""
        try:
            self.chunker.cleanup()
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
            
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()