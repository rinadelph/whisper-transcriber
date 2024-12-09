"""
Performance tests for the Whisper Transcriber application.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import time
import psutil
import os
from unittest.mock import Mock, patch
import threading
import queue

from pydub import AudioSegment
from openai.types.audio import Transcription

from src.transcription import WhisperTranscriber
from src.utils import FileHandler

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client with configurable delay."""
    mock_client = Mock()
    
    def delayed_response(*args, **kwargs):
        time.sleep(0.1)  # Simulate API latency
        return Transcription(text="Test transcription")
    
    mock_client.audio.transcriptions.create.side_effect = delayed_response
    return mock_client

class TestPerformance:
    """Performance tests for transcription system."""

    def test_memory_usage(self, temp_dir, mock_openai_client):
        """Test memory usage during large file processing."""
        # Create a large audio file (1 minute)
        audio = AudioSegment.silent(duration=60000)
        large_file = temp_dir / "large.mp3"
        audio.export(str(large_file), format="mp3")
        
        # Monitor memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss
        
        # Process file
        transcriber = WhisperTranscriber("test_api_key", temp_dir)
        output_path = temp_dir / "large_transcription.txt"
        
        with patch('os.path.getsize', return_value=30*1024*1024):  # 30MB
            transcriber.transcribe_file(large_file, output_path)
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        assert memory_increase < 100 * 1024 * 1024

    def test_processing_time(self, temp_dir, mock_openai_client):
        """Test processing time for different file sizes."""
        file_sizes = [1000, 5000, 10000]  # milliseconds
        processing_times = []
        
        for duration in file_sizes:
            # Create audio file
            audio = AudioSegment.silent(duration=duration)
            file_path = temp_dir / f"test_{duration}ms.mp3"
            audio.export(str(file_path), format="mp3")
            
            # Measure processing time
            start_time = time.time()
            
            transcriber = WhisperTranscriber("test_api_key", temp_dir)
            output_path = temp_dir / f"transcription_{duration}ms.txt"
            transcriber.transcribe_file(file_path, output_path)
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Processing time should scale roughly linearly
            if len(processing_times) > 1:
                ratio = processing_time / processing_times[0]
                expected_ratio = duration / file_sizes[0]
                assert 0.5 <= ratio / expected_ratio <= 2.0

    def test_concurrent_load(self, temp_dir, mock_openai_client):
        """Test system behavior under concurrent load."""
        num_concurrent = 5
        results = queue.Queue()
        
        def process_file(file_path):
            try:
                start_time = time.time()
                transcriber = WhisperTranscriber("test_api_key", temp_dir)
                output_path = temp_dir / f"{file_path.stem}_output.txt"
                transcriber.transcribe_file(file_path, output_path)
                processing_time = time.time() - start_time
                results.put(("success", processing_time))
            except Exception as e:
                results.put(("error", str(e)))
        
        # Create test files
        audio_files = []
        for i in range(num_concurrent):
            audio = AudioSegment.silent(duration=2000)
            file_path = temp_dir / f"concurrent_{i}.mp3"
            audio.export(str(file_path), format="mp3")
            audio_files.append(file_path)
        
        # Process files concurrently
        threads = []
        start_time = time.time()
        
        for file_path in audio_files:
            thread = threading.Thread(target=process_file, args=(file_path,))
            thread.start()
            threads.append(thread)
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Collect results
        processing_times = []
        while not results.empty():
            result = results.get()
            assert result[0] == "success"
            processing_times.append(result[1])
        
        # Verify performance characteristics
        assert len(processing_times) == num_concurrent
        avg_time = sum(processing_times) / len(processing_times)
        # Verify reasonable processing time (adjust based on your requirements)
        assert avg_time < 5.0

    def test_resource_limits(self, temp_dir, mock_openai_client):
        """Test behavior when approaching resource limits."""
        # Monitor system resources
        process = psutil.Process()
        
        def monitor_resources():
            while True:
                cpu_percent = process.cpu_percent()
                memory_percent = process.memory_percent()
                if cpu_percent > 90 or memory_percent > 90:
                    return False
                time.sleep(0.1)
        
        # Start resource monitoring in a separate thread
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # Create and process multiple large files
        for i in range(3):
            audio = AudioSegment.silent(duration=20000)
            file_path = temp_dir / f"large_{i}.mp3"
            audio.export(str(file_path), format="mp3")
            
            transcriber = WhisperTranscriber("test_api_key", temp_dir)
            output_path = temp_dir / f"large_{i}_output.txt"
            
            with patch('os.path.getsize', return_value=28*1024*1024):
                transcriber.transcribe_file(file_path, output_path)
        
        # Verify resource monitoring thread is still running
        assert monitor_thread.is_alive() 