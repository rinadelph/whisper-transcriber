"""
Audio chunking system for handling large audio files.
Implements intelligent splitting and chunk management.
"""

import os
from pathlib import Path
from typing import List, Generator, Optional, Callable
import logging
from datetime import datetime, timedelta
import shutil

from pydub import AudioSegment
from pydub.silence import detect_nonsilent

logger = logging.getLogger(__name__)

class AudioChunker:
    """Handles the chunking of large audio files."""

    MAX_CHUNK_SIZE = 24 * 1024 * 1024  # 24MB in bytes (leaving 1MB buffer)
    MIN_SILENCE_LEN = 700  # minimum silence length in ms
    SILENCE_THRESH = -35  # silence threshold in dB
    MAX_CHUNK_DURATION = 15 * 60 * 1000  # 15 minutes in milliseconds
    
    def __init__(self, temp_dir: Path) -> None:
        """
        Initialize the audio chunker.
        
        Args:
            temp_dir: Directory for temporary chunk storage
        """
        self.temp_dir = temp_dir
        self.temp_dir.mkdir(exist_ok=True)
        self._cleanup_old_temp_files()
        logger.info(f"AudioChunker initialized with temp dir: {temp_dir}")

    def _cleanup_old_temp_files(self) -> None:
        """Clean up old temporary files and ensure temp directory is empty."""
        if self.temp_dir.exists():
            # Remove entire temp directory and recreate it
            shutil.rmtree(self.temp_dir)
            self.temp_dir.mkdir(exist_ok=True)
            logger.info("Cleaned up temp directory")

    def _get_temp_path(self, original_path: Path, chunk_num: int) -> Path:
        """Generate temporary file path for a chunk."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.temp_dir / f"{original_path.stem}_chunk_{chunk_num}_{timestamp}.temp.mp3"

    def _find_split_points(self, audio: AudioSegment) -> List[int]:
        """
        Find optimal split points at silence periods.
        
        Args:
            audio: Audio segment to analyze
            
        Returns:
            List of millisecond positions for splits
        """
        # Calculate target chunk duration based on typical MP3 bitrate
        # Assuming ~192kbps MP3, 24MB = ~17 minutes
        target_duration = min(
            self.MAX_CHUNK_DURATION,  # Cap at 15 minutes
            (self.MAX_CHUNK_SIZE * 8) // (192 * 1024) * 1000  # Convert bytes to duration
        )
        
        split_points = []
        current_pos = 0
        
        while current_pos < len(audio):
            # Find the next chunk boundary
            end_pos = min(current_pos + target_duration, len(audio))
            
            if end_pos >= len(audio):
                break
                
            # Look for silence around the target point
            search_start = max(0, end_pos - 5000)  # Look 5 seconds before
            search_end = min(len(audio), end_pos + 5000)  # Look 5 seconds after
            search_segment = audio[search_start:search_end]
            
            # Find silent points
            silent_ranges = detect_nonsilent(
                search_segment,
                min_silence_len=self.MIN_SILENCE_LEN,
                silence_thresh=self.SILENCE_THRESH,
                seek_step=100
            )
            
            if silent_ranges:
                # Find the silence closest to our target point
                target_relative = end_pos - search_start
                closest_point = None
                min_distance = float('inf')
                
                for start, end in silent_ranges:
                    mid_point = (start + end) // 2
                    distance = abs(mid_point - target_relative)
                    if distance < min_distance:
                        min_distance = distance
                        closest_point = mid_point + search_start
                
                if closest_point is not None:
                    split_points.append(closest_point)
                    current_pos = closest_point
                else:
                    # If no silence found, split at target point
                    split_points.append(end_pos)
                    current_pos = end_pos
            else:
                # If no silence found, split at target point
                split_points.append(end_pos)
                current_pos = end_pos
        
        return split_points

    def chunk_audio(
        self,
        file_path: Path,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Generator[Path, None, None]:
        """
        Split audio file into chunks of appropriate size.
        
        Args:
            file_path: Path to the audio file
            progress_callback: Optional callback for progress updates (current_chunk, total_chunks)
            
        Yields:
            Paths to the temporary chunk files
        """
        try:
            # Clean up any leftover temp files before starting
            self._cleanup_old_temp_files()
            
            audio = AudioSegment.from_file(str(file_path))
            logger.info(f"Loaded audio file: {file_path} ({len(audio)}ms)")
            
            # If file is small enough, return as is
            file_size = os.path.getsize(file_path)
            if file_size <= self.MAX_CHUNK_SIZE and len(audio) <= self.MAX_CHUNK_DURATION:
                temp_path = self._get_temp_path(file_path, 0)
                audio.export(
                    temp_path,
                    format='mp3',
                    parameters=["-ac", "1", "-q:a", "0"]  # High quality mono MP3
                )
                if progress_callback:
                    progress_callback(1, 1)
                logger.info(f"File small enough to process as single chunk: {temp_path}")
                yield temp_path
                return
            
            # Find split points
            split_points = self._find_split_points(audio)
            
            # Add start and end points
            split_points = [0] + split_points + [len(audio)]
            total_chunks = len(split_points) - 1
            
            logger.info(f"Splitting audio into {total_chunks} chunks")
            
            # Create chunks
            for i in range(total_chunks):
                start = split_points[i]
                end = split_points[i + 1]
                
                chunk = audio[start:end]
                temp_path = self._get_temp_path(file_path, i)
                
                # Export as high quality mono MP3
                chunk.export(
                    temp_path,
                    format='mp3',
                    parameters=[
                        "-ac", "1",  # Mono
                        "-q:a", "0"  # Highest quality
                    ]
                )
                
                chunk_size = os.path.getsize(temp_path)
                logger.info(
                    f"Created chunk {i+1} of {total_chunks}: {temp_path} "
                    f"(Duration: {(end-start)/1000:.2f}s, Size: {chunk_size/1024/1024:.2f}MB)"
                )
                
                if progress_callback:
                    progress_callback(i + 1, total_chunks)
                yield temp_path
                
        except Exception as e:
            logger.error(f"Error chunking audio file: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up all temporary files."""
        self._cleanup_old_temp_files() 