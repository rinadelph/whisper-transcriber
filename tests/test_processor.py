"""
Tests for transcription processor functionality.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch
import json

from openai.types.audio import Transcription
from src.transcription.processor import TranscriptionProcessor

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock_client = Mock()
    mock_client.audio.transcriptions.create.return_value = Transcription(text="Test transcription")
    return mock_client

@pytest.fixture
def processor(mock_openai_client):
    """Create a TranscriptionProcessor instance with mock client."""
    return TranscriptionProcessor(mock_openai_client)

@pytest.fixture
def sample_chunks(temp_dir):
    """Create sample audio chunk files."""
    chunks = []
    for i in range(3):
        chunk_path = temp_dir / f"chunk_{i}.mp3"
        chunk_path.write_bytes(b"dummy audio content")
        chunks.append(chunk_path)
    return chunks

class TestTranscriptionProcessor:
    """Tests for TranscriptionProcessor class."""

    def test_transcribe_chunk_success(self, processor, temp_dir):
        """Test successful chunk transcription."""
        chunk_path = temp_dir / "test.mp3"
        chunk_path.write_bytes(b"test audio")
        
        result = processor._transcribe_chunk(chunk_path)
        assert isinstance(result, Transcription)
        assert result.text == "Test transcription"

    def test_transcribe_chunk_retries(self, mock_openai_client, temp_dir):
        """Test retry mechanism for failed transcription."""
        # Configure mock to fail twice then succeed
        mock_openai_client.audio.transcriptions.create.side_effect = [
            Exception("API Error"),
            Exception("API Error"),
            Transcription(text="Success after retries")
        ]
        
        processor = TranscriptionProcessor(mock_openai_client)
        chunk_path = temp_dir / "test.mp3"
        chunk_path.write_bytes(b"test audio")
        
        result = processor._transcribe_chunk(chunk_path)
        assert result.text == "Success after retries"
        assert mock_openai_client.audio.transcriptions.create.call_count == 3

    def test_transcribe_chunk_all_retries_fail(self, mock_openai_client, temp_dir):
        """Test handling of persistent failures."""
        # Configure mock to always fail
        mock_openai_client.audio.transcriptions.create.side_effect = Exception("API Error")
        
        processor = TranscriptionProcessor(mock_openai_client)
        chunk_path = temp_dir / "test.mp3"
        chunk_path.write_bytes(b"test audio")
        
        with pytest.raises(Exception):
            processor._transcribe_chunk(chunk_path)

    def test_process_chunks_success(self, processor, sample_chunks, temp_dir):
        """Test successful processing of multiple chunks."""
        output_path = temp_dir / "output.txt"
        
        def chunk_generator():
            for chunk in sample_chunks:
                yield chunk
        
        processor.process_chunks(chunk_generator(), output_path)
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Test transcription" in content

    def test_process_chunks_with_context(self, mock_openai_client, sample_chunks, temp_dir):
        """Test context preservation between chunks."""
        processor = TranscriptionProcessor(mock_openai_client)
        output_path = temp_dir / "output.txt"
        
        # Configure mock to return different responses
        responses = [
            Transcription(text="First chunk."),
            Transcription(text="Second chunk."),
            Transcription(text="Third chunk.")
        ]
        mock_openai_client.audio.transcriptions.create.side_effect = responses
        
        def chunk_generator():
            for chunk in sample_chunks:
                yield chunk
        
        processor.process_chunks(chunk_generator(), output_path)
        
        # Verify that each call included context from previous chunk
        calls = mock_openai_client.audio.transcriptions.create.call_args_list
        assert len(calls) == 3
        assert calls[1][1].get('prompt') is not None
        assert "First chunk" in calls[1][1].get('prompt', '')

    def test_process_chunks_with_timestamps(self, processor, sample_chunks, temp_dir):
        """Test processing with timestamp granularities."""
        output_path = temp_dir / "output.txt"
        
        def chunk_generator():
            for chunk in sample_chunks:
                yield chunk
        
        processor.process_chunks(
            chunk_generator(),
            output_path,
            timestamp_granularities=["word"]
        )
        
        # Verify timestamp parameter was passed
        calls = processor.client.audio.transcriptions.create.call_args_list
        assert all('timestamp_granularities' in call[1] for call in calls)

    def test_error_handling_during_processing(self, processor, sample_chunks, temp_dir):
        """Test error handling during chunk processing."""
        output_path = temp_dir / "output.txt"
        
        # Make one chunk invalid
        invalid_chunk = temp_dir / "invalid.mp3"
        invalid_chunk.write_bytes(b"invalid audio")
        
        def chunk_generator():
            yield invalid_chunk
            for chunk in sample_chunks:
                yield chunk
        
        with pytest.raises(Exception):
            processor.process_chunks(chunk_generator(), output_path) 