# BELLHOP Protocol - Example Code

This directory contains example implementations and pseudocode for the BELLHOP security protocol.

## Contents

### Core Functions

#### 1. Packet Encryption/Decryption
```python
# Example: encrypt_packet.py

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os

def encrypt_packet(plaintext, key, associated_data):
    """
    Encrypt packet using AES-256-GCM
    
    Args:
        plaintext: bytes - Data to encrypt
        key: bytes - 32-byte encryption key
        associated_data: bytes - Header data for authentication
    
    Returns:
        tuple: (ciphertext, nonce)
    """
    # Generate random nonce (96 bits for GCM)
    nonce = os.urandom(12)
    
    # Create cipher instance
    cipher = AESGCM(key)
    
    # Encrypt and authenticate
    ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
    
    return ciphertext, nonce

def decrypt_packet(ciphertext, key, nonce, associated_data):
    """
    Decrypt and verify packet
    
    Args:
        ciphertext: bytes - Encrypted data
        key: bytes - 32-byte decryption key
        nonce: bytes - 12-byte nonce used for encryption
        associated_data: bytes - Header data for authentication
    
    Returns:
        bytes: Decrypted plaintext or None if verification fails
    """
    cipher = AESGCM(key)
    
    try:
        plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
        return plaintext
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # Generate key (in practice, derive from master key)
    key = AESGCM.generate_key(bit_length=256)
    
    # Create test packet
    payload = b"Hello, BELLHOP!"
    header = b"\x01\x01\x00\x01\x00\xFF\x00\x01"  # Example header
    
    # Encrypt
    ciphertext, nonce = encrypt_packet(payload, key, header)
    print(f"Encrypted: {ciphertext.hex()}")
    print(f"Nonce: {nonce.hex()}")
    
    # Decrypt
    plaintext = decrypt_packet(ciphertext, key, nonce, header)
    print(f"Decrypted: {plaintext}")
```

#### 2. Frequency Hopping Sequence Generator
```python
# Example: frequency_hopping.py

import hashlib
import struct

class FrequencyHopper:
    def __init__(self, network_id, session_key, num_channels=50):
        """
        Initialize frequency hopper
        
        Args:
            network_id: int - Network identifier
            session_key: bytes - 32-byte session key
            num_channels: int - Number of available channels
        """
        self.network_id = network_id
        self.session_key = session_key
        self.num_channels = num_channels
    
    def generate_sequence(self, time_slot):
        """
        Generate hopping sequence for a time slot
        
        Args:
            time_slot: int - Current time slot (e.g., GPS second)
        
        Returns:
            list: Sequence of channel numbers
        """
        # Create seed from network ID, time slot, and session key
        seed_data = struct.pack(">I", self.network_id) + \
                    struct.pack(">Q", time_slot) + \
                    self.session_key
        
        # Use HMAC-SHA256 as PRNG seed
        seed = hashlib.sha256(seed_data).digest()
        
        # Generate sequence using Linear Congruential Generator
        # (In production, use ChaCha20 or similar CSPRNG)
        sequence = []
        current = int.from_bytes(seed[:8], 'big')
        
        # LCG parameters (example - use better values in production)
        a = 1664525
        c = 1013904223
        m = 2**32
        
        while len(sequence) < self.num_channels:
            current = (a * current + c) % m
            channel = current % self.num_channels
            
            # Ensure no duplicates
            if channel not in sequence:
                sequence.append(channel)
        
        return sequence
    
    def get_channel_at_time(self, time_slot, offset_ms=0):
        """
        Get the channel to use at a specific time
        
        Args:
            time_slot: int - Current time slot
            offset_ms: int - Millisecond offset within time slot
        
        Returns:
            int: Channel number to use
        """
        sequence = self.generate_sequence(time_slot)
        
        # Calculate position in sequence based on millisecond offset
        # Assuming 10ms per hop (100 hops/second)
        hop_duration_ms = 10
        hop_index = (offset_ms // hop_duration_ms) % len(sequence)
        
        return sequence[hop_index]

# Example usage
if __name__ == "__main__":
    import time
    
    # Initialize hopper
    network_id = 0x12345678
    session_key = b"a" * 32  # In practice, use real key
    hopper = FrequencyHopper(network_id, session_key)
    
    # Get current time slot (GPS second)
    time_slot = int(time.time())
    
    # Generate sequence
    sequence = hopper.generate_sequence(time_slot)
    print(f"Hopping sequence for time slot {time_slot}:")
    print(sequence)
    
    # Get channel at specific time
    channel = hopper.get_channel_at_time(time_slot, offset_ms=50)
    print(f"\nChannel at 50ms offset: {channel}")
```

#### 3. Geofence Validation
```python
# Example: geofence.py

import math

class GeofenceValidator:
    def __init__(self, boundary_coords):
        """
        Initialize geofence validator
        
        Args:
            boundary_coords: list of dict - Polygon vertices
                [{'lat': 37.7749, 'lon': -122.4194}, ...]
        """
        self.boundary = boundary_coords
    
    def point_in_polygon(self, point):
        """
        Check if point is inside polygon using ray casting algorithm
        
        Args:
            point: dict - {'lat': float, 'lon': float}
        
        Returns:
            bool: True if point is inside polygon
        """
        x, y = point['lon'], point['lat']
        n = len(self.boundary)
        inside = False
        
        p1x, p1y = self.boundary[0]['lon'], self.boundary[0]['lat']
        for i in range(1, n + 1):
            p2x, p2y = self.boundary[i % n]['lon'], self.boundary[i % n]['lat']
            
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            
            p1x, p1y = p2x, p2y
        
        return inside
    
    def validate_position(self, gps_position):
        """
        Validate if GPS position is within geofence
        
        Args:
            gps_position: dict - {'lat': float, 'lon': float, 'altitude': float}
        
        Returns:
            tuple: (is_valid, reason)
        """
        # Check 2D position
        inside = self.point_in_polygon(gps_position)
        
        if not inside:
            return False, "Position outside geofence boundary"
        
        return True, "Position valid"
    
    def calculate_distance(self, point1, point2):
        """
        Calculate distance between two GPS coordinates (Haversine formula)
        
        Args:
            point1, point2: dict - {'lat': float, 'lon': float}
        
        Returns:
            float: Distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        lat1 = math.radians(point1['lat'])
        lat2 = math.radians(point2['lat'])
        dlat = math.radians(point2['lat'] - point1['lat'])
        dlon = math.radians(point2['lon'] - point1['lon'])
        
        a = math.sin(dlat/2)**2 + \
            math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c

# Example usage
if __name__ == "__main__":
    # Define geofence boundary
    boundary = [
        {'lat': 37.7749, 'lon': -122.4194},
        {'lat': 37.7750, 'lon': -122.4180},
        {'lat': 37.7735, 'lon': -122.4175},
        {'lat': 37.7730, 'lon': -122.4190}
    ]
    
    validator = GeofenceValidator(boundary)
    
    # Test point inside fence
    test_point_inside = {'lat': 37.7740, 'lon': -122.4185}
    valid, reason = validator.validate_position(test_point_inside)
    print(f"Point inside: {valid} - {reason}")
    
    # Test point outside fence
    test_point_outside = {'lat': 37.7800, 'lon': -122.4200}
    valid, reason = validator.validate_position(test_point_outside)
    print(f"Point outside: {valid} - {reason}")
```

#### 4. Replay Protection
```python
# Example: replay_protection.py

class ReplayProtector:
    def __init__(self, window_size=64):
        """
        Initialize replay protector with sliding window
        
        Args:
            window_size: int - Size of replay window
        """
        self.window_size = window_size
        self.highest_seq = 0
        self.received_bitmap = 0
    
    def check_replay(self, seq_num):
        """
        Check if sequence number is a replay
        
        Args:
            seq_num: int - Sequence number from packet
        
        Returns:
            tuple: (is_valid, should_accept, reason)
        """
        # Packet too old
        if seq_num + self.window_size < self.highest_seq:
            return False, False, "Sequence number too old"
        
        # New highest sequence
        if seq_num > self.highest_seq:
            diff = seq_num - self.highest_seq
            
            # Shift window
            if diff < self.window_size:
                self.received_bitmap = self.received_bitmap << diff
            else:
                self.received_bitmap = 0
            
            # Mark as received
            self.received_bitmap |= 1
            self.highest_seq = seq_num
            
            return True, True, "New sequence number accepted"
        
        # Within window - check if already received
        bit_pos = self.highest_seq - seq_num
        
        if self.received_bitmap & (1 << bit_pos):
            return False, False, "Replay detected - already received"
        
        # Within window and not received yet
        self.received_bitmap |= (1 << bit_pos)
        return True, True, "Sequence number accepted"

# Example usage
if __name__ == "__main__":
    protector = ReplayProtector(window_size=64)
    
    # Test sequence
    test_sequences = [1, 2, 3, 5, 4, 3, 6, 100, 99, 1]
    
    print("Testing replay protection:")
    for seq in test_sequences:
        valid, accept, reason = protector.check_replay(seq)
        status = "✓ ACCEPT" if accept else "✗ REJECT"
        print(f"Seq {seq:3d}: {status} - {reason}")
```

#### 5. Packet Builder
```python
# Example: packet_builder.py

import struct
import zlib

class PacketBuilder:
    PROTOCOL_VERSION = 1
    
    # Packet types
    TYPE_DATA = 0x01
    TYPE_CONTROL = 0x02
    TYPE_KEY_EXCHANGE = 0x03
    TYPE_HEARTBEAT = 0x04
    
    def build_header(self, packet_type, source, destination, sequence, encrypted=True):
        """
        Build 8-byte packet header
        
        Returns:
            bytes: Header bytes
        """
        # Byte 0: Version and flags
        version_flags = (self.PROTOCOL_VERSION << 4)
        if encrypted:
            version_flags |= 0x01
        
        return struct.pack(">BBHHH",
            version_flags,
            packet_type,
            source,
            destination,
            sequence
        )
    
    def build_security_section(self, algorithm, key_version, iv, tag):
        """
        Build 32-byte security section
        
        Returns:
            bytes: Security section bytes
        """
        return struct.pack(">BB", algorithm, key_version) + iv + tag
    
    def build_packet(self, packet_type, source, dest, seq, payload, key, nonce):
        """
        Build complete BELLHOP packet
        
        Returns:
            bytes: Complete packet ready for transmission
        """
        # Build header
        header = self.build_header(packet_type, source, dest, seq)
        
        # Encrypt payload (simplified - use real encryption)
        ciphertext = payload  # Would be encrypt_packet(payload, key, header)
        tag = b'\x00' * 14  # Would be actual authentication tag
        
        # Build security section
        security = self.build_security_section(0x01, 0x01, nonce, tag)
        
        # Combine
        packet = header + security + ciphertext
        
        # Add CRC
        crc = zlib.crc32(packet) & 0xFFFFFFFF
        packet += struct.pack(">I", crc)
        
        return packet
    
    def parse_packet(self, packet_bytes):
        """
        Parse BELLHOP packet
        
        Returns:
            dict: Parsed packet components
        """
        if len(packet_bytes) < 44:  # Minimum packet size
            return None
        
        # Parse header
        version_flags, pkt_type, source, dest, seq = struct.unpack(">BBHHH", packet_bytes[0:8])
        
        version = (version_flags >> 4) & 0x0F
        encrypted = (version_flags & 0x01) != 0
        
        # Parse security section
        algorithm, key_version = struct.unpack(">BB", packet_bytes[8:10])
        iv = packet_bytes[10:26]
        tag = packet_bytes[26:40]
        
        # Parse payload
        ciphertext = packet_bytes[40:-4]
        
        # Verify CRC
        crc_received = struct.unpack(">I", packet_bytes[-4:])[0]
        crc_calculated = zlib.crc32(packet_bytes[:-4]) & 0xFFFFFFFF
        
        return {
            'version': version,
            'encrypted': encrypted,
            'type': pkt_type,
            'source': source,
            'destination': dest,
            'sequence': seq,
            'algorithm': algorithm,
            'key_version': key_version,
            'iv': iv,
            'tag': tag,
            'ciphertext': ciphertext,
            'crc_valid': crc_received == crc_calculated
        }

# Example usage
if __name__ == "__main__":
    builder = PacketBuilder()
    
    # Build test packet
    packet = builder.build_packet(
        packet_type=PacketBuilder.TYPE_DATA,
        source=0x0001,
        dest=0xFFFF,
        seq=42,
        payload=b"Hello, BELLHOP!",
        key=b"a" * 32,
        nonce=b"b" * 16
    )
    
    print(f"Built packet: {len(packet)} bytes")
    print(f"Hex: {packet.hex()}")
    
    # Parse packet
    parsed = builder.parse_packet(packet)
    print(f"\nParsed packet:")
    for key, value in parsed.items():
        if isinstance(value, bytes):
            print(f"  {key}: {value.hex()}")
        else:
            print(f"  {key}: {value}")
```

## Running Examples

```bash
# Install dependencies
pip install cryptography

# Run individual examples
python3 encrypt_packet.py
python3 frequency_hopping.py
python3 geofence.py
python3 replay_protection.py
python3 packet_builder.py
```

## Integration

These examples demonstrate core BELLHOP protocol functions. For full implementation:

1. Integrate with Meshtastic firmware
2. Add hardware-specific code for radio, GPS, secure element
3. Implement complete key management
4. Add network layer functionality
5. Integrate with NUC data streaming

See [Implementation Guide](../IMPLEMENTATION_GUIDE.md) for details.
