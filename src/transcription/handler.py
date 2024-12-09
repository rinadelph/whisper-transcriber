"""
Handles the transcription process for audio files.
"""

import logging
from pathlib import Path
from typing import Optional, Callable
import time
from openai import OpenAI
import backoff  # For exponential backoff

from .chunker import AudioChunker

logger = logging.getLogger(__name__)

class TranscriptionHandler:
    """Handles the transcription of audio files using OpenAI's Whisper API."""
    
    def __init__(self, api_key: str, temp_dir: Path):
        """
        Initialize the transcription handler.
        
        Args:
            api_key: OpenAI API key
            temp_dir: Directory for temporary file storage
        """
        self.client = OpenAI(api_key=api_key)
        self.temp_dir = temp_dir
        self.chunker = AudioChunker(temp_dir / "chunks")
        
    @backoff.on_exception(
        backoff.expo,
        (Exception),
        max_tries=3,
        max_time=300
    )
    def _transcribe_chunk(self, chunk_path: Path, previous_text: str = "") -> str:
        """
        Transcribe a single chunk with retries and proper prompting.
        
        Args:
            chunk_path: Path to the audio chunk
            previous_text: Text from previous chunk for context
            
        Returns:
            Transcribed text from the chunk
        """
        # Use the last ~200 tokens of previous text as context
        prompt = previous_text.split()[-200:] if previous_text else []
        prompt = " ".join(prompt)
        
        with open(chunk_path, "rb") as audio_file:
            try:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",  # Get detailed output
                    prompt=prompt,  # Use previous text as context
                    temperature=0.3  # Lower temperature for more consistent output
                )
                # Extract the full text from the response
                return response.text
            except Exception as e:
                logger.error(f"Error transcribing chunk {chunk_path}: {e}")
                raise
        
    def transcribe_file(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> str:
        """
        Transcribe an audio file.
        
        Args:
            file_path: Path to the audio file
            progress_callback: Optional callback for progress updates
            
        Returns:
            The complete transcription text
        """
        try:
            # Clean up any previous temp files
            self.chunker.cleanup()
            
            # Process chunks
            transcription_parts = []
            chunk_paths = list(self.chunker.chunk_audio(file_path, progress_callback))
            total_chunks = len(chunk_paths)
            
            logger.info(f"Starting transcription of {total_chunks} chunks")
            
            # Keep track of previous text for context
            previous_text = ""
            
            for i, chunk_path in enumerate(chunk_paths, 1):
                try:
                    # Add small delay between API calls to avoid rate limits
                    if i > 1:
                        time.sleep(1)
                    
                    logger.info(f"Transcribing chunk {i}/{total_chunks}")
                    
                    # Transcribe with context from previous chunk
                    chunk_text = self._transcribe_chunk(chunk_path, previous_text)
                    transcription_parts.append(chunk_text)
                    previous_text = chunk_text  # Update context for next chunk
                    
                    if progress_callback:
                        progress_callback(i, total_chunks)
                    
                except Exception as e:
                    logger.error(f"Error transcribing chunk {i}: {e}")
                    raise
                finally:
                    # Clean up chunk immediately after use
                    try:
                        chunk_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to clean up chunk {chunk_path}: {e}")
            
            # Join all parts with double newline for paragraph separation
            # and clean up any artifacts from the chunking process
            full_text = "\n\n".join(part.strip() for part in transcription_parts if part.strip())
            
            # Post-process to remove any obvious artifacts from chunking
            full_text = full_text.replace("...", ".")  # Remove multiple periods
            full_text = "\n".join(line.strip() for line in full_text.splitlines() if line.strip())
            
            return full_text
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
        finally:
            # Ensure all temporary files are cleaned up
            self.chunker.cleanup() 