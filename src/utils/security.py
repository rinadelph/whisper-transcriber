"""Security module for handling sensitive data and operations."""

import os
import re
import hashlib
import secrets
import logging
import platform
from pathlib import Path
from typing import Optional, Dict, Any
from base64 import b64encode, b64decode
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manages security operations and sensitive data handling."""
    
    def __init__(self, config_dir: Path) -> None:
        """Initialize security manager.
        
        Args:
            config_dir: Directory for storing security-related files
        """
        self.config_dir = config_dir
        self.key_file = config_dir / ".key"
        self._initialize_security()
        logger.info("Security manager initialized")
    
    def _initialize_security(self) -> None:
        """Initialize security components and key storage."""
        try:
            if not self.key_file.exists():
                key = Fernet.generate_key()
                self.config_dir.mkdir(parents=True, exist_ok=True)
                self.key_file.write_bytes(key)
                self._set_secure_permissions(self.key_file)
            
            self.cipher_suite = Fernet(self.key_file.read_bytes())
            logger.info("Security components initialized")
        except Exception as e:
            logger.error(f"Error initializing security: {e}")
            raise
    
    def _set_secure_permissions(self, file_path: Path) -> None:
        """Set secure file permissions based on the operating system.
        
        Args:
            file_path: Path to secure
        """
        if platform.system() == "Windows":
            import win32security
            import win32con
            import win32api
            
            # Get current user's SID
            user_sid = win32security.GetTokenInformation(
                win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY),
                win32security.TokenUser
            )[0]
            
            # Create DACL with full control for current user only
            dacl = win32security.ACL()
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                win32con.GENERIC_ALL,
                user_sid
            )
            
            # Set security descriptor
            security_desc = win32security.SECURITY_DESCRIPTOR()
            security_desc.SetSecurityDescriptorDacl(1, dacl, 0)
            win32security.SetFileSecurity(
                str(file_path),
                win32security.DACL_SECURITY_INFORMATION,
                security_desc
            )
        else:
            file_path.chmod(0o600)
    
    def encrypt_api_key(self, api_key: str) -> bytes:
        """Encrypt API key for storage.
        
        Args:
            api_key: API key to encrypt
            
        Returns:
            Encrypted API key
        """
        try:
            return self.cipher_suite.encrypt(api_key.encode())
        except Exception as e:
            logger.error(f"Error encrypting API key: {e}")
            raise
    
    def decrypt_api_key(self, encrypted_key: bytes) -> str:
        """Decrypt stored API key.
        
        Args:
            encrypted_key: Encrypted API key
            
        Returns:
            Decrypted API key
        """
        try:
            return self.cipher_suite.decrypt(encrypted_key).decode()
        except Exception as e:
            logger.error(f"Error decrypting API key: {e}")
            raise
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate OpenAI API key format.
        
        Args:
            api_key: API key to validate
            
        Returns:
            True if valid, False otherwise
        """
        pattern = r'^sk-[A-Za-z0-9]{48}$'
        return bool(re.match(pattern, api_key))
    
    @staticmethod
    def sanitize_path(path: str) -> str:
        """Sanitize file path to prevent path traversal.
        
        Args:
            path: Path to sanitize
            
        Returns:
            Sanitized path
        """
        # Normalize path separators to forward slashes
        path = path.replace("\\", "/")
        # Remove any leading slashes or parent directory references
        path = os.path.normpath(path).lstrip(os.sep).lstrip(".")
        # Convert back to forward slashes
        return path.replace("\\", "/")
    
    @staticmethod
    def validate_file_access(file_path: Path) -> bool:
        """Validate file access permissions.
        
        Args:
            file_path: Path to validate
            
        Returns:
            True if access is allowed, False otherwise
        """
        try:
            # Check if path exists and is a file
            if not file_path.is_file():
                return False
            
            # Check if path is absolute
            if not file_path.is_absolute():
                return False
            
            # Check file permissions
            return os.access(file_path, os.R_OK)
        except Exception:
            return False
    
    def secure_temp_file(self, file_path: Path) -> None:
        """Secure temporary file permissions.
        
        Args:
            file_path: Path to secure
        """
        try:
            self._set_secure_permissions(file_path)
            logger.debug(f"Secured temporary file: {file_path}")
        except Exception as e:
            logger.error(f"Error securing temporary file: {e}")
            raise
    
    def secure_cleanup(self, file_path: Path) -> None:
        """Securely delete sensitive file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if file_path.exists():
                # Overwrite with random data before deletion
                size = file_path.stat().st_size
                with open(file_path, 'wb') as f:
                    f.write(secrets.token_bytes(size))
                file_path.unlink()
                logger.debug(f"Securely deleted file: {file_path}")
        except Exception as e:
            logger.error(f"Error during secure cleanup: {e}")
            raise
    
    @staticmethod
    def hash_content(content: bytes) -> str:
        """Generate secure hash of content.
        
        Args:
            content: Content to hash
            
        Returns:
            Content hash
        """
        return hashlib.sha256(content).hexdigest()
    
    def validate_settings_integrity(self, settings: Dict[str, Any], signature: str) -> bool:
        """Validate settings file integrity.
        
        Args:
            settings: Settings dictionary
            signature: Settings signature
            
        Returns:
            True if valid, False otherwise
        """
        try:
            content = str(sorted(settings.items())).encode()
            return self.hash_content(content) == signature
        except Exception as e:
            logger.error(f"Error validating settings integrity: {e}")
            return False
    
    def generate_settings_signature(self, settings: Dict[str, Any]) -> str:
        """Generate signature for settings.
        
        Args:
            settings: Settings dictionary
            
        Returns:
            Settings signature
        """
        try:
            content = str(sorted(settings.items())).encode()
            return self.hash_content(content)
        except Exception as e:
            logger.error(f"Error generating settings signature: {e}")
            raise 