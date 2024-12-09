"""Tests for security functionality."""

import pytest
from pathlib import Path
import tempfile
import shutil
import os
import json
from base64 import b64encode

from src.utils.security import SecurityManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def security_manager(temp_dir):
    """Create a SecurityManager instance for testing."""
    return SecurityManager(temp_dir)


class TestSecurityManager:
    """Tests for SecurityManager class."""

    def test_initialization(self, security_manager, temp_dir):
        """Test security initialization."""
        key_file = temp_dir / ".key"
        assert key_file.exists()
        assert key_file.stat().st_mode & 0o777 == 0o600

    def test_api_key_encryption(self, security_manager):
        """Test API key encryption and decryption."""
        api_key = "sk-" + "a" * 48
        encrypted = security_manager.encrypt_api_key(api_key)
        decrypted = security_manager.decrypt_api_key(encrypted)
        
        assert isinstance(encrypted, bytes)
        assert decrypted == api_key

    def test_api_key_validation(self, security_manager):
        """Test API key format validation."""
        valid_key = "sk-" + "a" * 48
        invalid_keys = [
            "invalid-key",
            "sk-" + "a" * 47,  # Too short
            "sk-" + "a" * 49,  # Too long
            "sk-" + "!" * 48,  # Invalid characters
        ]
        
        assert security_manager.validate_api_key(valid_key)
        for key in invalid_keys:
            assert not security_manager.validate_api_key(key)

    def test_path_sanitization(self, security_manager, temp_dir):
        """Test path sanitization."""
        paths = {
            "../dangerous/path": "dangerous/path",
            "/absolute/path": "absolute/path",
            "normal/path": "normal/path",
            "path/../attempt": "path/attempt"
        }
        
        for input_path, expected in paths.items():
            assert security_manager.sanitize_path(input_path) == expected

    def test_file_access_validation(self, security_manager, temp_dir):
        """Test file access validation."""
        # Create test file
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Test valid file
        assert security_manager.validate_file_access(test_file.absolute())
        
        # Test non-existent file
        assert not security_manager.validate_file_access(temp_dir / "nonexistent.txt")
        
        # Test directory
        assert not security_manager.validate_file_access(temp_dir)
        
        # Test relative path
        assert not security_manager.validate_file_access(Path("relative/path.txt"))

    def test_secure_temp_file(self, security_manager, temp_dir):
        """Test temporary file security."""
        test_file = temp_dir / "secure.tmp"
        test_file.write_text("sensitive data")
        
        security_manager.secure_temp_file(test_file)
        assert test_file.stat().st_mode & 0o777 == 0o600

    def test_secure_cleanup(self, security_manager, temp_dir):
        """Test secure file deletion."""
        test_file = temp_dir / "sensitive.txt"
        test_file.write_text("sensitive data")
        
        security_manager.secure_cleanup(test_file)
        assert not test_file.exists()

    def test_content_hashing(self, security_manager):
        """Test content hashing."""
        content = b"test content"
        hash1 = security_manager.hash_content(content)
        hash2 = security_manager.hash_content(b"different content")
        
        assert isinstance(hash1, str)
        assert len(hash1) == 64  # SHA-256 hash length
        assert hash1 != hash2

    def test_settings_integrity(self, security_manager):
        """Test settings integrity validation."""
        settings = {
            "setting1": "value1",
            "setting2": 123
        }
        
        # Generate signature
        signature = security_manager.generate_settings_signature(settings)
        
        # Validate correct settings
        assert security_manager.validate_settings_integrity(settings, signature)
        
        # Validate modified settings
        modified_settings = settings.copy()
        modified_settings["setting1"] = "modified"
        assert not security_manager.validate_settings_integrity(modified_settings, signature)

    def test_error_handling(self, security_manager, temp_dir):
        """Test error handling in security operations."""
        # Test invalid key decryption
        with pytest.raises(Exception):
            security_manager.decrypt_api_key(b"invalid encrypted data")
        
        # Test invalid file operations
        non_existent = temp_dir / "nonexistent.txt"
        with pytest.raises(Exception):
            security_manager.secure_temp_file(non_existent)

    def test_key_file_permissions(self, temp_dir):
        """Test key file permission handling."""
        # Create security manager
        manager = SecurityManager(temp_dir)
        key_file = temp_dir / ".key"
        
        # Verify initial permissions
        assert key_file.exists()
        assert key_file.stat().st_mode & 0o777 == 0o600
        
        # Attempt to modify permissions
        key_file.chmod(0o644)
        
        # Create new manager instance
        new_manager = SecurityManager(temp_dir)
        
        # Verify permissions were restored
        assert key_file.stat().st_mode & 0o777 == 0o600
