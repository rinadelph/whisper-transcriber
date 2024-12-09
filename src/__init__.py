"""
Whisper Transcriber
A GUI application for transcribing audio files using OpenAI's Whisper API.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__license__ = "MIT"

import logging
import os
from pathlib import Path

# Setup base paths
ROOT_DIR = Path(__file__).parent.parent
TEMP_DIR = ROOT_DIR / "temp"
OUTPUT_DIR = ROOT_DIR / "output"

# Create necessary directories
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(ROOT_DIR / "whisper_transcriber.log")
    ]
)

logger = logging.getLogger(__name__) 