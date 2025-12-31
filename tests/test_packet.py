"""
Unit tests for packet module.
"""

import pytest
import os
from bellhop.packet import (
    PacketBuilder, PacketParser, PacketHeader, SecuritySection,
    PacketType, Packet
)


class TestPacketHeader:
    """Tests for packet header."""
    
    def test_to_bytes(self):
        """Test header serialization."""
        header = PacketHeader(
            version=1,
            encrypted=True,
            priority=False,
            broadcast=True,
            requires_ack=False,
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            sequence=42
        )
        
        header_bytes = header.to_bytes()
        assert len(header_bytes) == 8
    
    def test_from_bytes(self):
        """Test header deserialization."""
        header = PacketHeader(
            version=1,
            encrypted=True,
            priority=True,
            broadcast=False,
            requires_ack=True,
            packet_type=PacketType.HEARTBEAT,
            source=0x0001,
            destination=0x0002,
            sequence=100
        )
        
        header_bytes = header.to_bytes()
        parsed = PacketHeader.from_bytes(header_bytes)
        
        assert parsed.version == header.version
        assert parsed.encrypted == header.encrypted
        assert parsed.priority == header.priority
        assert parsed.broadcast == header.broadcast
        assert parsed.requires_ack == header.requires_ack
        assert parsed.packet_type == header.packet_type
        assert parsed.source == header.source
        assert parsed.destination == header.destination
        assert parsed.sequence == header.sequence


class TestSecuritySection:
    """Tests for security section."""
    
    def test_to_bytes(self):
        """Test security section serialization."""
        security = SecuritySection(
            algorithm=0x01,
            key_version=0x02,
            nonce=os.urandom(12),
            auth_tag=os.urandom(14)
        )
        
        security_bytes = security.to_bytes()
        assert len(security_bytes) == 32
    
    def test_from_bytes(self):
        """Test security section deserialization."""
        nonce = os.urandom(12)
        auth_tag = os.urandom(14)
        
        security = SecuritySection(
            algorithm=0x01,
            key_version=0x02,
            nonce=nonce,
            auth_tag=auth_tag
        )
        
        security_bytes = security.to_bytes()
        parsed = SecuritySection.from_bytes(security_bytes)
        
        assert parsed.algorithm == security.algorithm
        assert parsed.key_version == security.key_version
        assert parsed.nonce[:12] == nonce
        assert parsed.auth_tag[:14] == auth_tag


class TestPacketBuilder:
    """Tests for packet builder."""
    
    def test_build_packet(self):
        """Test packet building."""
        builder = PacketBuilder()
        
        packet = builder.build_packet(
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            payload=b"Hello, World!",
            encrypted=True,
            nonce=os.urandom(12),
            auth_tag=os.urandom(14)
        )
        
        # Minimum size: header(8) + security(32) + payload(13) + crc(4) = 57
        assert len(packet) >= 57
    
    def test_sequence_counter(self):
        """Test sequence counter increments."""
        builder = PacketBuilder()
        
        assert builder.get_next_sequence() == 0
        
        builder.build_packet(
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            payload=b"test"
        )
        
        assert builder.get_next_sequence() == 1


class TestPacketParser:
    """Tests for packet parser."""
    
    def test_parse_packet(self):
        """Test packet parsing."""
        builder = PacketBuilder()
        
        payload = b"Test payload"
        packet = builder.build_packet(
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            payload=payload,
            encrypted=True
        )
        
        header, security, parsed_payload, crc_valid = PacketParser.parse_packet(packet)
        
        assert header.packet_type == PacketType.DATA
        assert header.source == 0x0001
        assert header.destination == 0xFFFF
        assert parsed_payload == payload
        assert crc_valid is True
    
    def test_invalid_crc(self):
        """Test CRC validation."""
        builder = PacketBuilder()
        
        packet = builder.build_packet(
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            payload=b"test"
        )
        
        # Corrupt CRC
        corrupted = bytearray(packet)
        corrupted[-1] ^= 0xFF
        
        header, security, payload, crc_valid = PacketParser.parse_packet(bytes(corrupted))
        assert crc_valid is False
    
    def test_validate_packet(self):
        """Test packet validation."""
        builder = PacketBuilder()
        
        packet = builder.build_packet(
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            payload=b"test"
        )
        
        valid, reason = PacketParser.validate_packet(packet)
        assert valid is True
        assert "valid" in reason.lower()
    
    def test_too_small_packet(self):
        """Test handling of too-small packets."""
        with pytest.raises(ValueError):
            PacketParser.parse_packet(b"tiny")


class TestPacket:
    """Tests for high-level Packet class."""
    
    def test_from_bytes(self):
        """Test creating packet from bytes."""
        builder = PacketBuilder()
        
        packet_bytes = builder.build_packet(
            packet_type=PacketType.HEARTBEAT,
            source=0x0001,
            destination=0x0002,
            payload=b"heartbeat"
        )
        
        packet = Packet.from_bytes(packet_bytes)
        
        assert packet.header.packet_type == PacketType.HEARTBEAT
        assert packet.header.source == 0x0001
        assert packet.payload == b"heartbeat"
        assert packet.crc_valid is True
    
    def test_to_bytes(self):
        """Test converting packet to bytes."""
        builder = PacketBuilder()
        
        original_bytes = builder.build_packet(
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            payload=b"test"
        )
        
        packet = Packet.from_bytes(original_bytes)
        rebuilt_bytes = packet.to_bytes()
        
        # Should be able to parse rebuilt packet
        valid, reason = PacketParser.validate_packet(rebuilt_bytes)
        assert valid is True
    
    def test_repr(self):
        """Test packet string representation."""
        builder = PacketBuilder()
        
        packet_bytes = builder.build_packet(
            packet_type=PacketType.DATA,
            source=0x0001,
            destination=0xFFFF,
            payload=b"test"
        )
        
        packet = Packet.from_bytes(packet_bytes)
        repr_str = repr(packet)
        
        assert "Packet" in repr_str
        assert "DATA" in repr_str
        assert "0x0001" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
