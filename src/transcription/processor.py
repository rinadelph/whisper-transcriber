"""
Transcription processor for handling Whisper API interactions and response processing.
"""

import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Generator, Callable
import logging
from datetime import datetime

from openai import OpenAI
from openai.types.audio import Transcription

logger = logging.getLogger(__name__)

class TranscriptionProcessor:
    """Handles the transcription process and API interactions."""

    def __init__(self, client: OpenAI) -> None:
        """
        Initialize the processor.
        
        Args:
            client: OpenAI client instance
        """
        self.client = client
        self.retry_delays = [1, 2, 4, 8, 16]  # Exponential backoff
        logger.info("TranscriptionProcessor initialized")

    def _transcribe_chunk(
        self,
        chunk_path: Path,
        prompt: Optional[str] = None,
        language: Optional[str] = None,
        response_format: str = "text",
        timestamp_granularities: Optional[List[str]] = None
    ) -> Transcription:
        """
        Transcribe a single audio chunk with retries.
        
        Args:
            chunk_path: Path to the audio chunk
            prompt: Optional prompt for better accuracy
            language: Optional language code
            response_format: Format of the response
            timestamp_granularities: Timestamp granularity options
            
        Returns:
            Transcription response from the API
        """
        for attempt, delay in enumerate(self.retry_delays, 1):
            try:
                with open(chunk_path, "rb") as audio_file:
                    response = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        prompt=prompt,
                        language=language,
                        response_format=response_format,
                        timestamp_granularities=timestamp_granularities
                    )
                    logger.info(f"Successfully transcribed chunk: {chunk_path}")
                    return response
                    
            except Exception as e:
                if attempt == len(self.retry_delays):
                    logger.error(f"Failed to transcribe chunk after {attempt} attempts: {e}")
                    raise
                
                logger.warning(f"Attempt {attempt} failed, retrying in {delay}s: {e}")
                time.sleep(delay)

    def process_chunks(
        self,
        chunk_paths: List[Path],
        output_path: Path,
        language: Optional[str] = None,
        response_format: str = "text",
        timestamp_granularities: Optional[List[str]] = None,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> str:
        """
        Process a list of audio chunks and combine their transcriptions.
        
        Args:
            chunk_paths: List of paths to audio chunks
            output_path: Path to save the final transcription
            language: Optional language code
            response_format: Format of the response
            timestamp_granularities: Optional list of timestamp granularities
            progress_callback: Optional callback for progress updates
            
        Returns:
            The complete transcription text
        """
        transcriptions = []
        total_chunks = len(chunk_paths)
        current_chunk_path = None
        
        try:
            for i, chunk_path in enumerate(chunk_paths, 1):
                current_chunk_path = chunk_path
                try:
                    # Ensure chunk exists
                    if not chunk_path.exists():
                        raise FileNotFoundError(f"Chunk file not found: {chunk_path}")
                        
                    # Process chunk with retries
                    for attempt in range(5):
                        try:
                            with open(chunk_path, "rb") as audio_file:
                                response = self.client.audio.transcriptions.create(
                                    model="whisper-1",
                                    file=audio_file,
                                    language=language,
                                    response_format=response_format,
                                    timestamp_granularities=timestamp_granularities
                                )
                                
                                # Extract text from response
                                if response_format == "verbose_json":
                                    text = response.text
                                else:
                                    text = response
                                    
                                transcriptions.append(text)
                                logger.info(f"Successfully transcribed chunk: {chunk_path}")
                                
                                if progress_callback:
                                    progress_callback(i, total_chunks, text)
                                    
                                break  # Success, exit retry loop
                                
                        except Exception as e:
                            if attempt < 4:  # Don't log on last attempt
                                logger.warning(f"Attempt {attempt + 1} failed, retrying in {2 ** attempt}s: {e}")
                                time.sleep(2 ** attempt)
                            else:
                                raise  # Re-raise on last attempt
                                
                except Exception as e:
                    logger.error(f"Failed to transcribe chunk after 5 attempts: {e}")
                    raise
                    
                logger.info(f"Processed chunk {i} of {total_chunks}")
                
            # Combine all transcriptions
            final_text = "\n\n".join(t.strip() for t in transcriptions if t.strip())
            
            # Write the final text to the output file
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(final_text)
            except Exception as e:
                logger.error(f"Failed to write output file: {e}")
                raise
            
            return final_text
            
        except Exception as e:
            logger.error(f"Error during transcription processing: {e}")
            raise
            
        finally:
            # Clean up current chunk if it exists
            if current_chunk_path and current_chunk_path.exists():
                try:
                    current_chunk_path.unlink()
                except Exception as e:
                    logger.warning(f"Failed to clean up chunk {current_chunk_path}: {e}")