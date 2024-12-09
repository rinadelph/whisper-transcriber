"""
Utilities Module for Whisper Transcriber
Provides helper functions for file operations, validation, and error handling.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

__all__ = ['FileHandler', 'AudioValidator']

class FileHandler:
    """Handles file operations and management."""
    
    @staticmethod
    def generate_output_filename(input_path: Path, suffix: str = "_transcription") -> Path:
        """
        Generate an output filename based on the input file.
        
        Args:
            input_path: Path to the input file
            suffix: Suffix to add to the filename
            
        Returns:
            Path object for the output file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return input_path.parent / f"{input_path.stem}{suffix}_{timestamp}.txt"

class AudioValidator:
    """Validates audio files and their properties."""
    
    @staticmethod
    def is_valid_format(file_path: Path, supported_formats: set) -> bool:
        """
        Check if the file format is supported.
        
        Args:
            file_path: Path to the audio file
            supported_formats: Set of supported file extensions
            
        Returns:
            bool indicating if the format is supported
        """
        return file_path.suffix.lower().lstrip('.') in supported_formats 