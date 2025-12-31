"""
Packet structure module for BELLHOP protocol.
Handles packet building, parsing, and validation.
"""

import struct
import zlib
from enum import IntEnum
from typing import Optional, Tuple
from dataclasses import dataclass


class PacketType(IntEnum):
    """Packet type identifiers."""
    DATA = 0x01
    CONTROL = 0x02
    KEY_EXCHANGE = 0x03
    HEARTBEAT = 0x04
    GEOFENCE_UPDATE = 0x05
    SECURITY_ALERT = 0x06
    TIME_SYNC = 0x07


@dataclass
class PacketHeader:
    """Packet header structure."""
    version: int  # 4 bits
    encrypted: bool
    priority: bool
    broadcast: bool
    requires_ack: bool
    packet_type: PacketType
    source: int  # 16 bits
    destination: int  # 16 bits
    sequence: int  # 16 bits
    
    def to_bytes(self) -> bytes:
        """Convert header to bytes."""
        # Byte 0: Version and flags
        version_flags = (self.version & 0x0F) << 4
        if self.encrypted:
            version_flags |= 0x01
        if self.priority:
            version_flags |= 0x02
        if self.broadcast:
            version_flags |= 0x04
        if self.requires_ack:
            version_flags |= 0x08
        
        # Pack header (8 bytes)
        return struct.pack(">BBHHH",
            version_flags,
            self.packet_type,
            self.source,
            self.destination,
            self.sequence
        )
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'PacketHeader':
        """Parse header from bytes."""
        if len(data) < 8:
            raise ValueError("Header must be at least 8 bytes")
        
        version_flags, pkt_type, source, dest, seq = struct.unpack(">BBHHH", data[:8])
        
        return cls(
            version=(version_flags >> 4) & 0x0F,
            encrypted=(version_flags & 0x01) != 0,
            priority=(version_flags & 0x02) != 0,
            broadcast=(version_flags & 0x04) != 0,
            requires_ack=(version_flags & 0x08) != 0,
            packet_type=PacketType(pkt_type),
            source=source,
            destination=dest,
            sequence=seq
        )


@dataclass
class SecuritySection:
    """Security section structure."""
    algorithm: int  # 1 byte
    key_version: int  # 1 byte
    nonce: bytes  # 16 bytes (12 used for GCM, padded)
    auth_tag: bytes  # 14 bytes (extracted from ciphertext)
    
    def to_bytes(self) -> bytes:
        """Convert security section to bytes."""
        # Ensure nonce is 16 bytes (pad if needed)
        nonce = self.nonce[:16].ljust(16, b'\x00')
        
        # Ensure auth_tag is 14 bytes
        auth_tag = self.auth_tag[:14].ljust(14, b'\x00')
        
        return struct.pack(">BB", self.algorithm, self.key_version) + nonce + auth_tag
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'SecuritySection':
        """Parse security section from bytes."""
        if len(data) < 32:
            raise ValueError("Security section must be 32 bytes")
        
        algorithm, key_version = struct.unpack(">BB", data[:2])
        nonce = data[2:18]
        auth_tag = data[18:32]
        
        return cls(
            algorithm=algorithm,
            key_version=key_version,
            nonce=nonce,
            auth_tag=auth_tag
        )


class PacketBuilder:
    """Builds BELLHOP protocol packets."""
    
    PROTOCOL_VERSION = 1
    
    def __init__(self):
        """Initialize packet builder."""
        self.sequence_counter = 0
    
    def build_packet(self, 
                    packet_type: PacketType,
                    source: int,
                    destination: int,
                    payload: bytes,
                    encrypted: bool = True,
                    priority: bool = False,
                    broadcast: bool = False,
                    requires_ack: bool = False,
                    algorithm: int = 0x01,
                    key_version: int = 0x01,
                    nonce: Optional[bytes] = None,
                    auth_tag: Optional[bytes] = None) -> bytes:
        """
        Build a complete BELLHOP packet.
        
        Args:
            packet_type: Type of packet
            source: Source node ID
            destination: Destination node ID
            payload: Packet payload (plaintext or ciphertext)
            encrypted: Whether packet is encrypted
            priority: Priority flag
            broadcast: Broadcast flag
            requires_ack: Requires acknowledgment flag
            algorithm: Encryption algorithm ID
            key_version: Key version
            nonce: Encryption nonce (16 bytes, will be padded/truncated)
            auth_tag: Authentication tag (14 bytes, will be padded/truncated)
        
        Returns:
            Complete packet as bytes
        """
        # Build header
        header = PacketHeader(
            version=self.PROTOCOL_VERSION,
            encrypted=encrypted,
            priority=priority,
            broadcast=broadcast,
            requires_ack=requires_ack,
            packet_type=packet_type,
            source=source,
            destination=destination,
            sequence=self.sequence_counter
        )
        
        self.sequence_counter = (self.sequence_counter + 1) & 0xFFFF
        
        header_bytes = header.to_bytes()
        
        # Build security section
        if nonce is None:
            nonce = b'\x00' * 16
        if auth_tag is None:
            auth_tag = b'\x00' * 14
        
        security = SecuritySection(
            algorithm=algorithm,
            key_version=key_version,
            nonce=nonce,
            auth_tag=auth_tag
        )
        
        security_bytes = security.to_bytes()
        
        # Combine header, security, and payload
        packet = header_bytes + security_bytes + payload
        
        # Calculate and append CRC32
        crc = zlib.crc32(packet) & 0xFFFFFFFF
        packet += struct.pack(">I", crc)
        
        return packet
    
    def get_next_sequence(self) -> int:
        """Get the next sequence number without incrementing."""
        return self.sequence_counter


class PacketParser:
    """Parses BELLHOP protocol packets."""
    
    MIN_PACKET_SIZE = 44  # Header (8) + Security (32) + CRC (4)
    
    @staticmethod
    def parse_packet(packet: bytes) -> Tuple[PacketHeader, SecuritySection, bytes, bool]:
        """
        Parse a BELLHOP packet.
        
        Args:
            packet: Complete packet bytes
        
        Returns:
            Tuple of (header, security, payload, crc_valid)
        
        Raises:
            ValueError: If packet is malformed
        """
        if len(packet) < PacketParser.MIN_PACKET_SIZE:
            raise ValueError(f"Packet too small: {len(packet)} bytes (minimum {PacketParser.MIN_PACKET_SIZE})")
        
        # Parse header
        header = PacketHeader.from_bytes(packet[:8])
        
        # Parse security section
        security = SecuritySection.from_bytes(packet[8:40])
        
        # Extract payload
        payload = packet[40:-4]
        
        # Verify CRC
        crc_received = struct.unpack(">I", packet[-4:])[0]
        crc_calculated = zlib.crc32(packet[:-4]) & 0xFFFFFFFF
        crc_valid = (crc_received == crc_calculated)
        
        return header, security, payload, crc_valid
    
    @staticmethod
    def validate_packet(packet: bytes) -> Tuple[bool, str]:
        """
        Validate packet structure and CRC.
        
        Args:
            packet: Complete packet bytes
        
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            if len(packet) < PacketParser.MIN_PACKET_SIZE:
                return False, f"Packet too small ({len(packet)} bytes)"
            
            # Parse packet
            header, security, payload, crc_valid = PacketParser.parse_packet(packet)
            
            if not crc_valid:
                return False, "CRC check failed"
            
            if header.version != 1:
                return False, f"Unsupported protocol version: {header.version}"
            
            return True, "Packet valid"
        
        except Exception as e:
            return False, f"Parse error: {e}"


class Packet:
    """High-level packet interface."""
    
    def __init__(self, header: PacketHeader, security: SecuritySection, 
                 payload: bytes, crc_valid: bool = True):
        """
        Initialize packet.
        
        Args:
            header: Packet header
            security: Security section
            payload: Packet payload
            crc_valid: Whether CRC was valid
        """
        self.header = header
        self.security = security
        self.payload = payload
        self.crc_valid = crc_valid
    
    @classmethod
    def from_bytes(cls, packet_bytes: bytes) -> 'Packet':
        """
        Create packet from bytes.
        
        Args:
            packet_bytes: Complete packet as bytes
        
        Returns:
            Packet object
        """
        header, security, payload, crc_valid = PacketParser.parse_packet(packet_bytes)
        return cls(header, security, payload, crc_valid)
    
    def to_bytes(self) -> bytes:
        """
        Convert packet to bytes.
        
        Returns:
            Complete packet as bytes
        """
        builder = PacketBuilder()
        builder.sequence_counter = self.header.sequence
        
        return builder.build_packet(
            packet_type=self.header.packet_type,
            source=self.header.source,
            destination=self.header.destination,
            payload=self.payload,
            encrypted=self.header.encrypted,
            priority=self.header.priority,
            broadcast=self.header.broadcast,
            requires_ack=self.header.requires_ack,
            algorithm=self.security.algorithm,
            key_version=self.security.key_version,
            nonce=self.security.nonce,
            auth_tag=self.security.auth_tag
        )
    
    def __repr__(self):
        return (f"Packet(type={self.header.packet_type.name}, "
                f"src=0x{self.header.source:04x}, "
                f"dst=0x{self.header.destination:04x}, "
                f"seq={self.header.sequence}, "
                f"payload={len(self.payload)} bytes, "
                f"crc_valid={self.crc_valid})")


# Example usage
if __name__ == "__main__":
    import os
    
    # Create packet builder
    builder = PacketBuilder()
    
    # Build a data packet
    print("Building packet...")
    packet_bytes = builder.build_packet(
        packet_type=PacketType.DATA,
        source=0x0001,
        destination=0xFFFF,  # Broadcast
        payload=b"Hello, BELLHOP! This is a test message.",
        encrypted=True,
        priority=False,
        broadcast=True,
        requires_ack=False,
        algorithm=0x01,  # AES-256-GCM
        key_version=0x01,
        nonce=os.urandom(12),  # Will be padded to 16
        auth_tag=os.urandom(14)
    )
    
    print(f"Built packet: {len(packet_bytes)} bytes")
    print(f"Hex: {packet_bytes[:64].hex()}...")
    
    # Validate packet
    print("\nValidating packet...")
    valid, reason = PacketParser.validate_packet(packet_bytes)
    print(f"Valid: {valid} - {reason}")
    
    # Parse packet
    print("\nParsing packet...")
    header, security, payload, crc_valid = PacketParser.parse_packet(packet_bytes)
    
    print(f"Header:")
    print(f"  Version: {header.version}")
    print(f"  Type: {header.packet_type.name}")
    print(f"  Source: 0x{header.source:04x}")
    print(f"  Destination: 0x{header.destination:04x}")
    print(f"  Sequence: {header.sequence}")
    print(f"  Encrypted: {header.encrypted}")
    print(f"  Broadcast: {header.broadcast}")
    
    print(f"\nSecurity:")
    print(f"  Algorithm: 0x{security.algorithm:02x}")
    print(f"  Key Version: 0x{security.key_version:02x}")
    print(f"  Nonce: {security.nonce[:12].hex()}")
    
    print(f"\nPayload: {len(payload)} bytes")
    print(f"CRC Valid: {crc_valid}")
    
    # Test high-level interface
    print("\n" + "="*50)
    print("Testing high-level Packet class...")
    packet = Packet.from_bytes(packet_bytes)
    print(packet)
    
    # Round-trip test
    rebuilt = packet.to_bytes()
    assert rebuilt == packet_bytes, "Round-trip failed!"
    
    print("\n✓ Packet building and parsing operational!")
