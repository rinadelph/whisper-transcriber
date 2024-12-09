"""
GUI Module for Whisper Transcriber
Handles all graphical interface components and user interactions.
"""

from pathlib import Path
from typing import Optional, Callable, Any
import logging

from .window import MainWindow

logger = logging.getLogger(__name__)

__all__ = ['MainWindow']