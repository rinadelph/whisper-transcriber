"""
Tests for settings management functionality.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import json
from datetime import datetime

from src.utils.settings import Settings

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)

@pytest.fixture
def settings(temp_dir):
    """Create a Settings instance for testing."""
    return Settings(temp_dir)

class TestSettings:
    """Tests for Settings class."""

    def test_default_settings_creation(self, settings, temp_dir):
        """Test creation of default settings file."""
        config_file = temp_dir / "settings.json"
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            stored_settings = json.load(f)
        
        assert stored_settings == Settings.DEFAULT_SETTINGS

    def test_get_setting(self, settings):
        """Test retrieving settings."""
        assert settings.get("language") == "auto"
        assert settings.get("nonexistent", "default") == "default"

    def test_set_setting(self, settings):
        """Test setting individual settings."""
        settings.set("language", "en")
        assert settings.get("language") == "en"
        
        # Verify persistence
        settings_reloaded = Settings(settings.config_dir)
        assert settings_reloaded.get("language") == "en"

    def test_update_multiple_settings(self, settings):
        """Test updating multiple settings at once."""
        new_settings = {
            "language": "fr",
            "enable_timestamps": True
        }
        settings.update(new_settings)
        
        assert settings.get("language") == "fr"
        assert settings.get("enable_timestamps") is True

    def test_reset_specific_setting(self, settings):
        """Test resetting specific setting to default."""
        settings.set("language", "es")
        settings.reset("language")
        
        assert settings.get("language") == Settings.DEFAULT_SETTINGS["language"]

    def test_reset_all_settings(self, settings):
        """Test resetting all settings to default."""
        settings.set("language", "de")
        settings.set("enable_timestamps", True)
        settings.reset()
        
        assert settings.settings == Settings.DEFAULT_SETTINGS

    def test_recent_directories(self, settings):
        """Test managing recent directories."""
        dirs = ["/path/1", "/path/2", "/path/3"]
        
        for dir_path in dirs:
            settings.add_recent_directory(dir_path)
        
        recent = settings.get_recent_directories()
        assert len(recent) == 3
        assert recent[0] == dirs[-1]  # Most recent first

    def test_recent_directories_limit(self, settings):
        """Test recent directories list size limit."""
        dirs = [f"/path/{i}" for i in range(10)]
        
        for dir_path in dirs:
            settings.add_recent_directory(dir_path)
        
        recent = settings.get_recent_directories()
        assert len(recent) == 5  # Maximum 5 entries
        assert recent[0] == dirs[-1]  # Most recent first

    def test_export_settings(self, settings, temp_dir):
        """Test exporting settings to file."""
        export_path = temp_dir / "exported_settings.json"
        settings.set("language", "it")
        settings.export_settings(export_path)
        
        with open(export_path, 'r') as f:
            exported = json.load(f)
        
        assert "metadata" in exported
        assert "version" in exported["metadata"]
        assert exported["settings"]["language"] == "it"

    def test_import_settings(self, settings, temp_dir):
        """Test importing settings from file."""
        import_data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0"
            },
            "settings": {
                "language": "ja",
                "enable_timestamps": True
            }
        }
        
        import_path = temp_dir / "import_settings.json"
        with open(import_path, 'w') as f:
            json.dump(import_data, f)
        
        settings.import_settings(import_path)
        assert settings.get("language") == "ja"
        assert settings.get("enable_timestamps") is True

    def test_import_invalid_settings(self, settings, temp_dir):
        """Test importing invalid settings file."""
        invalid_data = {"invalid": "format"}
        import_path = temp_dir / "invalid_settings.json"
        
        with open(import_path, 'w') as f:
            json.dump(invalid_data, f)
        
        with pytest.raises(ValueError):
            settings.import_settings(import_path)

    def test_settings_persistence(self, temp_dir):
        """Test settings persistence across instances."""
        settings1 = Settings(temp_dir)
        settings1.set("language", "ru")
        
        settings2 = Settings(temp_dir)
        assert settings2.get("language") == "ru"

    def test_invalid_config_file(self, temp_dir):
        """Test handling of corrupted config file."""
        config_file = temp_dir / "settings.json"
        config_file.write_text("invalid json")
        
        settings = Settings(temp_dir)
        assert settings.settings == Settings.DEFAULT_SETTINGS
``` 