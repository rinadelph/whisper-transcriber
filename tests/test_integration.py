"""
Integration tests for the Whisper Transcriber application.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import os
from unittest.mock import Mock, patch
import threading
import queue
from datetime import datetime

from pydub import AudioSegment
from openai.types.audio import Transcription

from src.gui import MainWindow
from src.transcription import WhisperTranscriber
from src.utils import FileHandler, AudioValidator

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
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock_client = Mock()
    mock_client.audio.transcriptions.create.return_value = Transcription(text="Test transcription")
    return mock_client

class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    def test_complete_transcription_workflow(self, temp_dir, sample_audio, mock_openai_client):
        """Test complete transcription workflow from file selection to output."""
        # Set up test environment
        api_key = "test_api_key"
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        # Initialize transcriber with mock client
        with patch('openai.OpenAI', return_value=mock_openai_client):
            transcriber = WhisperTranscriber(api_key, temp_dir)
            
            # Process file
            output_path = output_dir / "transcription.txt"
            transcriber.transcribe_file(
                sample_audio,
                output_path,
                language="en",
                enable_timestamps=True
            )
            
            # Verify output
            assert output_path.exists()
            content = output_path.read_text()
            assert "Test transcription" in content

    def test_gui_integration(self, temp_dir, sample_audio, mock_openai_client):
        """Test GUI integration with transcription process."""
        api_key = "test_api_key"
        
        # Initialize GUI with mock client
        with patch('openai.OpenAI', return_value=mock_openai_client):
            window = MainWindow(api_key, temp_dir)
            
            # Simulate file selection
            window.current_file = sample_audio
            window.output_dir = temp_dir
            window.file_path_var.set(str(sample_audio))
            window.output_path_var.set(str(temp_dir))
            
            # Start transcription
            window._start_transcription()
            
            # Wait for processing to complete
            while window.is_processing:
                window.root.update()
            
            # Verify output file was created
            output_files = list(temp_dir.glob("*transcription*.txt"))
            assert len(output_files) == 1
            assert "Test transcription" in output_files[0].read_text()

    def test_large_file_handling(self, temp_dir, mock_openai_client):
        """Test handling of large audio files that require chunking."""
        # Create a large audio file
        audio = AudioSegment.silent(duration=30000)  # 30 seconds
        large_file = temp_dir / "large.mp3"
        audio.export(str(large_file), format="mp3")
        
        # Mock file size to force chunking
        with patch('os.path.getsize', return_value=26*1024*1024):  # 26MB
            transcriber = WhisperTranscriber("test_api_key", temp_dir)
            output_path = temp_dir / "large_transcription.txt"
            
            # Process file
            transcriber.transcribe_file(large_file, output_path)
            
            # Verify chunking occurred
            assert mock_openai_client.audio.transcriptions.create.call_count > 1

    def test_error_recovery(self, temp_dir, sample_audio, mock_openai_client):
        """Test error recovery during transcription process."""
        # Configure mock to fail on first attempt
        mock_openai_client.audio.transcriptions.create.side_effect = [
            Exception("API Error"),
            Transcription(text="Successful retry")
        ]
        
        transcriber = WhisperTranscriber("test_api_key", temp_dir)
        output_path = temp_dir / "error_test.txt"
        
        # Process file
        transcriber.transcribe_file(sample_audio, output_path)
        
        # Verify retry succeeded
        assert output_path.exists()
        assert "Successful retry" in output_path.read_text()

    def test_resource_cleanup(self, temp_dir, sample_audio, mock_openai_client):
        """Test proper cleanup of temporary resources."""
        transcriber = WhisperTranscriber("test_api_key", temp_dir)
        output_path = temp_dir / "cleanup_test.txt"
        
        # Process file
        transcriber.transcribe_file(sample_audio, output_path)
        
        # Verify temp files are cleaned up
        temp_files = list(temp_dir.glob("*.temp.*"))
        assert len(temp_files) == 0

    def test_concurrent_processing(self, temp_dir, mock_openai_client):
        """Test handling of concurrent transcription requests."""
        # Create multiple audio files
        audio_files = []
        for i in range(3):
            audio = AudioSegment.silent(duration=1000)
            file_path = temp_dir / f"test_{i}.mp3"
            audio.export(str(file_path), format="mp3")
            audio_files.append(file_path)
        
        # Process files concurrently
        threads = []
        results = queue.Queue()
        
        def process_file(file_path):
            try:
                transcriber = WhisperTranscriber("test_api_key", temp_dir)
                output_path = temp_dir / f"{file_path.stem}_output.txt"
                transcriber.transcribe_file(file_path, output_path)
                results.put(("success", file_path))
            except Exception as e:
                results.put(("error", file_path, str(e)))
        
        # Start processing threads
        for file_path in audio_files:
            thread = threading.Thread(target=process_file, args=(file_path,))
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify results
        while not results.empty():
            result = results.get()
            assert result[0] == "success" 