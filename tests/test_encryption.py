"""
Unit tests for encryption module.
"""

import pytest
import os
from bellhop.encryption import (
    AESGCMCipher, ChaCha20Cipher, PacketEncryptor,
    KeyDerivation, EncryptionError
)


class TestAESGCMCipher:
    """Tests for AES-256-GCM cipher."""
    
    def test_initialization(self):
        """Test cipher initialization."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        assert cipher is not None
    
    def test_invalid_key_length(self):
        """Test that invalid key length raises error."""
        with pytest.raises(ValueError):
            AESGCMCipher(b"short_key")
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        plaintext = b"Hello, BELLHOP!"
        associated_data = b"header_data"
        
        ciphertext, nonce = cipher.encrypt(plaintext, associated_data)
        assert len(nonce) == 12
        assert ciphertext != plaintext
        
        decrypted = cipher.decrypt(ciphertext, nonce, associated_data)
        assert decrypted == plaintext
    
    def test_tampered_ciphertext(self):
        """Test that tampered ciphertext fails authentication."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        plaintext = b"Hello, BELLHOP!"
        associated_data = b"header_data"
        
        ciphertext, nonce = cipher.encrypt(plaintext, associated_data)
        
        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0xFF
        
        with pytest.raises(EncryptionError):
            cipher.decrypt(bytes(tampered), nonce, associated_data)
    
    def test_wrong_associated_data(self):
        """Test that wrong associated data fails authentication."""
        key = os.urandom(32)
        cipher = AESGCMCipher(key)
        
        plaintext = b"Hello, BELLHOP!"
        associated_data = b"header_data"
        
        ciphertext, nonce = cipher.encrypt(plaintext, associated_data)
        
        with pytest.raises(EncryptionError):
            cipher.decrypt(ciphertext, nonce, b"wrong_header")


class TestChaCha20Cipher:
    """Tests for ChaCha20-Poly1305 cipher."""
    
    def test_initialization(self):
        """Test cipher initialization."""
        key = os.urandom(32)
        cipher = ChaCha20Cipher(key)
        assert cipher is not None
    
    def test_encrypt_decrypt(self):
        """Test encryption and decryption."""
        key = os.urandom(32)
        cipher = ChaCha20Cipher(key)
        
        plaintext = b"Hello, ChaCha20!"
        associated_data = b"header_data"
        
        ciphertext, nonce = cipher.encrypt(plaintext, associated_data)
        assert len(nonce) == 12
        assert ciphertext != plaintext
        
        decrypted = cipher.decrypt(ciphertext, nonce, associated_data)
        assert decrypted == plaintext


class TestKeyDerivation:
    """Tests for key derivation functions."""
    
    def test_derive_key(self):
        """Test PBKDF2 key derivation."""
        password = b"password123"
        salt = b"salt123"
        
        key1 = KeyDerivation.derive_key(password, salt)
        assert len(key1) == 32
        
        # Same inputs should produce same key
        key2 = KeyDerivation.derive_key(password, salt)
        assert key1 == key2
        
        # Different inputs should produce different keys
        key3 = KeyDerivation.derive_key(password, b"different_salt")
        assert key1 != key3
    
    def test_hkdf_expand(self):
        """Test HKDF expansion."""
        master_key = os.urandom(32)
        info = b"context_info"
        
        derived = KeyDerivation.hkdf_expand(master_key, info, length=32)
        assert len(derived) == 32
        
        # Different info should produce different keys
        derived2 = KeyDerivation.hkdf_expand(master_key, b"different_info", length=32)
        assert derived != derived2


class TestPacketEncryptor:
    """Tests for high-level packet encryptor."""
    
    def test_encrypt_decrypt_packet(self):
        """Test packet encryption and decryption."""
        key = os.urandom(32)
        encryptor = PacketEncryptor(key)
        
        payload = b"Test packet payload"
        header = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        
        ciphertext, nonce, algo = encryptor.encrypt_packet(payload, header)
        assert algo == PacketEncryptor.ALGORITHM_AES_GCM
        
        decrypted = encryptor.decrypt_packet(ciphertext, nonce, header)
        assert decrypted == payload
    
    def test_chacha20_algorithm(self):
        """Test ChaCha20 algorithm selection."""
        key = os.urandom(32)
        encryptor = PacketEncryptor(key, PacketEncryptor.ALGORITHM_CHACHA20)
        
        payload = b"Test packet payload"
        header = b"\x01\x02\x03\x04\x05\x06\x07\x08"
        
        ciphertext, nonce, algo = encryptor.encrypt_packet(payload, header)
        assert algo == PacketEncryptor.ALGORITHM_CHACHA20
        
        decrypted = encryptor.decrypt_packet(ciphertext, nonce, header)
        assert decrypted == payload
    
    def test_key_version(self):
        """Test key version management."""
        key = os.urandom(32)
        encryptor = PacketEncryptor(key)
        
        assert encryptor.get_key_version() == 0x01
        
        encryptor.set_key_version(0x42)
        assert encryptor.get_key_version() == 0x42


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
