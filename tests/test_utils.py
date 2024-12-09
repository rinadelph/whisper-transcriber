"""
Tests for utility functions and classes.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

from src.utils import FileHandler, AudioValidator

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_audio_file(temp_dir):
    """Create a sample audio file for testing."""
    audio_file = temp_dir / "test.mp3"
    audio_file.write_bytes(b"dummy audio content")
    return audio_file

class TestFileHandler:
    """Tests for FileHandler class."""

    def test_generate_output_filename(self, temp_dir):
        """Test output filename generation."""
        input_path = temp_dir / "test.mp3"
        result = FileHandler.generate_output_filename(input_path)
        
        assert result.parent == input_path.parent
        assert result.suffix == ".txt"
        assert "test_transcription_" in result.stem
        assert datetime.now().strftime("%Y%m%d") in result.stem

    def test_generate_output_filename_custom_suffix(self, temp_dir):
        """Test output filename generation with custom suffix."""
        input_path = temp_dir / "test.mp3"
        result = FileHandler.generate_output_filename(input_path, suffix="_custom")
        
        assert "_custom_" in result.stem

class TestAudioValidator:
    """Tests for AudioValidator class."""

    def test_is_valid_format_supported(self, sample_audio_file):
        """Test validation of supported audio formats."""
        supported_formats = {"mp3", "wav", "m4a"}
        assert AudioValidator.is_valid_format(sample_audio_file, supported_formats)

    def test_is_valid_format_unsupported(self, temp_dir):
        """Test validation of unsupported audio formats."""
        unsupported_file = temp_dir / "test.xyz"
        unsupported_file.write_bytes(b"dummy content")
        supported_formats = {"mp3", "wav", "m4a"}
        
        assert not AudioValidator.is_valid_format(unsupported_file, supported_formats)

    def test_is_valid_format_case_insensitive(self, temp_dir):
        """Test case-insensitive format validation."""
        upper_case_file = temp_dir / "test.MP3"
        upper_case_file.write_bytes(b"dummy content")
        supported_formats = {"mp3", "wav", "m4a"}
        
        assert AudioValidator.is_valid_format(upper_case_file, supported_formats)

    def test_is_valid_format_empty_formats(self, sample_audio_file):
        """Test validation with empty supported formats."""
        assert not AudioValidator.is_valid_format(sample_audio_file, set())

    def test_is_valid_format_nonexistent_file(self):
        """Test validation of nonexistent file."""
        nonexistent_file = Path("nonexistent.mp3")
        supported_formats = {"mp3", "wav", "m4a"}
        
        assert AudioValidator.is_valid_format(nonexistent_file, supported_formats) 