"""
Encryption module for BELLHOP protocol.
Provides AES-256-GCM and ChaCha20-Poly1305 encryption.
"""

import os
from typing import Tuple, Optional
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import hashlib


class EncryptionError(Exception):
    """Base exception for encryption errors."""
    pass


class AESGCMCipher:
    """AES-256-GCM cipher implementation."""
    
    def __init__(self, key: bytes):
        """
        Initialize AES-256-GCM cipher.
        
        Args:
            key: 32-byte encryption key
        
        Raises:
            ValueError: If key is not 32 bytes
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for AES-256")
        self.cipher = AESGCM(key)
    
    def encrypt(self, plaintext: bytes, associated_data: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt data using AES-256-GCM.
        
        Args:
            plaintext: Data to encrypt
            associated_data: Additional authenticated data (not encrypted)
        
        Returns:
            Tuple of (ciphertext, nonce)
        """
        nonce = os.urandom(12)  # 96 bits for GCM
        ciphertext = self.cipher.encrypt(nonce, plaintext, associated_data)
        return ciphertext, nonce
    
    def decrypt(self, ciphertext: bytes, nonce: bytes, associated_data: bytes) -> bytes:
        """
        Decrypt data using AES-256-GCM.
        
        Args:
            ciphertext: Data to decrypt (includes auth tag)
            nonce: 12-byte nonce used for encryption
            associated_data: Additional authenticated data
        
        Returns:
            Decrypted plaintext
        
        Raises:
            EncryptionError: If decryption or authentication fails
        """
        try:
            plaintext = self.cipher.decrypt(nonce, ciphertext, associated_data)
            return plaintext
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")


class ChaCha20Cipher:
    """ChaCha20-Poly1305 cipher implementation."""
    
    def __init__(self, key: bytes):
        """
        Initialize ChaCha20-Poly1305 cipher.
        
        Args:
            key: 32-byte encryption key
        
        Raises:
            ValueError: If key is not 32 bytes
        """
        if len(key) != 32:
            raise ValueError("Key must be 32 bytes for ChaCha20")
        self.cipher = ChaCha20Poly1305(key)
    
    def encrypt(self, plaintext: bytes, associated_data: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt data using ChaCha20-Poly1305.
        
        Args:
            plaintext: Data to encrypt
            associated_data: Additional authenticated data (not encrypted)
        
        Returns:
            Tuple of (ciphertext, nonce)
        """
        nonce = os.urandom(12)  # 96 bits
        ciphertext = self.cipher.encrypt(nonce, plaintext, associated_data)
        return ciphertext, nonce
    
    def decrypt(self, ciphertext: bytes, nonce: bytes, associated_data: bytes) -> bytes:
        """
        Decrypt data using ChaCha20-Poly1305.
        
        Args:
            ciphertext: Data to decrypt (includes auth tag)
            nonce: 12-byte nonce used for encryption
            associated_data: Additional authenticated data
        
        Returns:
            Decrypted plaintext
        
        Raises:
            EncryptionError: If decryption or authentication fails
        """
        try:
            plaintext = self.cipher.decrypt(nonce, ciphertext, associated_data)
            return plaintext
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {e}")


class KeyDerivation:
    """Key derivation functions."""
    
    @staticmethod
    def derive_key(password: bytes, salt: bytes, iterations: int = 100000) -> bytes:
        """
        Derive a 32-byte key from password using PBKDF2.
        
        Args:
            password: Password or pre-shared key
            salt: Salt value (should be unique per network/node)
            iterations: Number of PBKDF2 iterations
        
        Returns:
            32-byte derived key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
            backend=default_backend()
        )
        return kdf.derive(password)
    
    @staticmethod
    def hkdf_expand(master_key: bytes, info: bytes, length: int = 32) -> bytes:
        """
        Expand master key using HKDF-Expand (simplified).
        
        Args:
            master_key: Master key material
            info: Context-specific information
            length: Output key length in bytes
        
        Returns:
            Derived key of specified length
        """
        # Simplified HKDF-Expand using HMAC-SHA256
        output = b''
        counter = 1
        while len(output) < length:
            h = hashlib.sha256()
            h.update(output[-32:] if output else b'')
            h.update(info)
            h.update(bytes([counter]))
            h.update(master_key)
            output += h.digest()
            counter += 1
        return output[:length]


class PacketEncryptor:
    """High-level packet encryption interface."""
    
    ALGORITHM_AES_GCM = 0x01
    ALGORITHM_CHACHA20 = 0x02
    
    def __init__(self, key: bytes, algorithm: int = ALGORITHM_AES_GCM):
        """
        Initialize packet encryptor.
        
        Args:
            key: 32-byte encryption key
            algorithm: Encryption algorithm (ALGORITHM_AES_GCM or ALGORITHM_CHACHA20)
        """
        if algorithm == self.ALGORITHM_AES_GCM:
            self.cipher = AESGCMCipher(key)
        elif algorithm == self.ALGORITHM_CHACHA20:
            self.cipher = ChaCha20Cipher(key)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")
        
        self.algorithm = algorithm
        self.key_version = 0x01
    
    def encrypt_packet(self, payload: bytes, header: bytes) -> Tuple[bytes, bytes, int]:
        """
        Encrypt a packet payload.
        
        Args:
            payload: Packet payload to encrypt
            header: Packet header (used as additional authenticated data)
        
        Returns:
            Tuple of (ciphertext, nonce, algorithm_id)
        """
        ciphertext, nonce = self.cipher.encrypt(payload, header)
        return ciphertext, nonce, self.algorithm
    
    def decrypt_packet(self, ciphertext: bytes, nonce: bytes, header: bytes) -> bytes:
        """
        Decrypt a packet payload.
        
        Args:
            ciphertext: Encrypted payload
            nonce: Nonce used for encryption
            header: Packet header (used as additional authenticated data)
        
        Returns:
            Decrypted payload
        
        Raises:
            EncryptionError: If decryption fails
        """
        return self.cipher.decrypt(ciphertext, nonce, header)
    
    def get_key_version(self) -> int:
        """Get current key version."""
        return self.key_version
    
    def set_key_version(self, version: int):
        """Set key version."""
        self.key_version = version & 0xFF


# Example usage
if __name__ == "__main__":
    # Generate a key from password
    password = b"my_secure_password_at_least_32_characters_long"
    salt = b"network_id_12345"
    key = KeyDerivation.derive_key(password, salt)
    
    # Create encryptor
    encryptor = PacketEncryptor(key, PacketEncryptor.ALGORITHM_AES_GCM)
    
    # Encrypt a packet
    header = b"\x11\x01\x00\x01\x00\xFF\x00\x42"  # Example header
    payload = b"Hello, BELLHOP! This is a secure message."
    
    ciphertext, nonce, algo = encryptor.encrypt_packet(payload, header)
    print(f"Encrypted {len(payload)} bytes -> {len(ciphertext)} bytes")
    print(f"Nonce: {nonce.hex()}")
    print(f"Algorithm: 0x{algo:02x}")
    
    # Decrypt the packet
    decrypted = encryptor.decrypt_packet(ciphertext, nonce, header)
    print(f"Decrypted: {decrypted.decode()}")
    
    # Verify
    assert decrypted == payload, "Decryption failed!"
    print("✓ Encryption/decryption successful!")
