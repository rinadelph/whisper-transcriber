"""
Settings management for the Whisper Transcriber application.
Handles persistent storage and retrieval of user preferences.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Settings:
    """Manages application settings and user preferences."""
    
    DEFAULT_SETTINGS = {
        "language": "auto",
        "enable_timestamps": False,
        "last_output_dir": None,
        "window_size": {
            "width": 600,
            "height": 400
        },
        "api_settings": {
            "response_format": "text",
            "temperature": 0,
            "max_retries": 3
        },
        "performance": {
            "chunk_size_mb": 25,
            "min_silence_len": 500,
            "silence_thresh": -40
        }
    }
    
    def __init__(self, config_dir: Path) -> None:
        """
        Initialize settings manager.
        
        Args:
            config_dir: Directory for storing configuration files
        """
        self.config_dir = config_dir
        self.config_file = config_dir / "settings.json"
        self.settings: Dict[str, Any] = {}
        self._load_settings()
        logger.info("Settings manager initialized")
    
    def _load_settings(self) -> None:
        """Load settings from file or create with defaults."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    stored_settings = json.load(f)
                # Merge with defaults to handle new settings
                self.settings = {**self.DEFAULT_SETTINGS, **stored_settings}
                logger.info("Settings loaded from file")
            else:
                self.settings = self.DEFAULT_SETTINGS.copy()
                self._save_settings()
                logger.info("Default settings created")
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.settings = self.DEFAULT_SETTINGS.copy()
    
    def _save_settings(self) -> None:
        """Save current settings to file."""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            logger.info("Settings saved to file")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key to retrieve
            default: Default value if key doesn't exist
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key to set
            value: Value to store
        """
        self.settings[key] = value
        self._save_settings()
        logger.debug(f"Setting updated: {key}={value}")
    
    def update(self, settings: Dict[str, Any]) -> None:
        """
        Update multiple settings at once.
        
        Args:
            settings: Dictionary of settings to update
        """
        self.settings.update(settings)
        self._save_settings()
        logger.debug(f"Settings updated: {settings}")
    
    def reset(self, key: Optional[str] = None) -> None:
        """
        Reset settings to default.
        
        Args:
            key: Optional specific setting to reset
        """
        if key:
            if key in self.DEFAULT_SETTINGS:
                self.settings[key] = self.DEFAULT_SETTINGS[key]
                logger.info(f"Reset setting: {key}")
            else:
                logger.warning(f"Unknown setting: {key}")
        else:
            self.settings = self.DEFAULT_SETTINGS.copy()
            logger.info("All settings reset to default")
        self._save_settings()
    
    def get_recent_directories(self) -> list:
        """Get list of recently used directories."""
        return self.settings.get("recent_directories", [])
    
    def add_recent_directory(self, directory: str) -> None:
        """
        Add directory to recent list.
        
        Args:
            directory: Directory path to add
        """
        recent = self.get_recent_directories()
        if directory in recent:
            recent.remove(directory)
        recent.insert(0, directory)
        # Keep only last 5 directories
        recent = recent[:5]
        self.settings["recent_directories"] = recent
        self._save_settings()
    
    def export_settings(self, export_path: Path) -> None:
        """
        Export settings to file.
        
        Args:
            export_path: Path to export settings to
        """
        try:
            settings_with_meta = {
                "metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "version": "1.0"
                },
                "settings": self.settings
            }
            with open(export_path, 'w') as f:
                json.dump(settings_with_meta, f, indent=4)
            logger.info(f"Settings exported to: {export_path}")
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            raise
    
    def import_settings(self, import_path: Path) -> None:
        """
        Import settings from file.
        
        Args:
            import_path: Path to import settings from
        """
        try:
            with open(import_path, 'r') as f:
                imported = json.load(f)
            
            if "settings" in imported:
                # Merge with defaults to ensure all required settings exist
                self.settings = {**self.DEFAULT_SETTINGS, **imported["settings"]}
                self._save_settings()
                logger.info(f"Settings imported from: {import_path}")
            else:
                raise ValueError("Invalid settings file format")
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            raise
``` 