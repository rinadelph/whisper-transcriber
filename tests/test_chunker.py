"""
Tests for audio chunking functionality.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import os
from unittest.mock import Mock, patch

from pydub import AudioSegment
from src.transcription.chunker import AudioChunker

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def sample_audio(temp_dir):
    """Create a sample audio file for testing."""
    # Create a 1-second silent audio segment
    audio = AudioSegment.silent(duration=1000)
    file_path = temp_dir / "test.mp3"
    audio.export(str(file_path), format="mp3")
    return file_path

@pytest.fixture
def large_audio(temp_dir):
    """Create a large audio file that exceeds chunk size."""
    # Create a 30-second audio with alternating sound and silence
    segments = []
    for _ in range(30):
        segments.append(AudioSegment.silent(duration=500))
        segments.append(AudioSegment.sine(440, duration=500))  # 440Hz tone
    
    audio = sum(segments)
    file_path = temp_dir / "large_test.mp3"
    audio.export(str(file_path), format="mp3")
    return file_path

class TestAudioChunker:
    """Tests for AudioChunker class."""

    def test_init_creates_temp_dir(self, temp_dir):
        """Test that initializing creates the temp directory."""
        chunk_dir = temp_dir / "chunks"
        chunker = AudioChunker(chunk_dir)
        assert chunk_dir.exists()
        assert chunk_dir.is_dir()

    def test_cleanup_removes_temp_files(self, temp_dir):
        """Test cleanup of temporary files."""
        chunk_dir = temp_dir / "chunks"
        chunker = AudioChunker(chunk_dir)
        
        # Create some temp files
        (chunk_dir / "test1.temp.mp3").write_bytes(b"test1")
        (chunk_dir / "test2.temp.mp3").write_bytes(b"test2")
        
        chunker.cleanup()
        assert not list(chunk_dir.glob("*.temp.*"))

    def test_small_file_no_chunking(self, temp_dir, sample_audio):
        """Test that small files aren't chunked."""
        chunker = AudioChunker(temp_dir)
        chunks = list(chunker.chunk_audio(sample_audio))
        
        assert len(chunks) == 1
        assert chunks[0].suffix == sample_audio.suffix

    @patch('os.path.getsize')
    def test_large_file_chunking(self, mock_getsize, temp_dir, large_audio):
        """Test chunking of large files."""
        # Mock file size to force chunking
        mock_getsize.return_value = AudioChunker.MAX_CHUNK_SIZE + 1024
        
        chunker = AudioChunker(temp_dir)
        chunks = list(chunker.chunk_audio(large_audio))
        
        assert len(chunks) > 1
        for chunk in chunks:
            assert os.path.getsize(chunk) <= AudioChunker.MAX_CHUNK_SIZE

    def test_find_split_points(self, temp_dir, large_audio):
        """Test finding split points in audio."""
        chunker = AudioChunker(temp_dir)
        audio = AudioSegment.from_file(str(large_audio))
        
        split_points = chunker._find_split_points(audio)
        
        assert isinstance(split_points, list)
        assert all(isinstance(point, int) for point in split_points)
        assert all(0 <= point <= len(audio) for point in split_points)

    def test_error_handling(self, temp_dir):
        """Test error handling for invalid files."""
        chunker = AudioChunker(temp_dir)
        invalid_file = temp_dir / "invalid.mp3"
        invalid_file.write_bytes(b"not an audio file")
        
        with pytest.raises(Exception):
            list(chunker.chunk_audio(invalid_file))

    def test_temp_file_naming(self, temp_dir):
        """Test temporary file naming convention."""
        chunker = AudioChunker(temp_dir)
        test_path = Path("test.mp3")
        temp_path = chunker._get_temp_path(test_path, 0)
        
        assert temp_path.parent == temp_dir
        assert "test_chunk_0_" in temp_path.stem
        assert temp_path.suffix == ".temp.mp3" 