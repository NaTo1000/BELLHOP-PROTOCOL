# BELLHOP Protocol - Python Implementation

Full working implementation of the BELLHOP security protocol suite in Python.

## Directory Structure

```
src/bellhop/          - Core protocol implementation
├── __init__.py       - Package initialization
├── encryption.py     - AES-256-GCM and ChaCha20-Poly1305 encryption
├── frequency_hopping.py - Frequency hopping spread spectrum
├── geofencing.py     - GPS-based geofencing and RSSI triangulation
├── packet.py         - Packet building, parsing, and validation
├── replay_protection.py - Sliding window replay detection
└── authentication.py - PSK and certificate-based authentication

tests/                - Unit tests
├── test_encryption.py
└── test_packet.py

tools/                - Utility scripts (to be added)
```

## Installation

### Requirements
- Python 3.8 or higher
- cryptography library

### Install from source

```bash
# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .

# Or install in development mode with tests
pip install -e ".[dev]"
```

## Quick Start

### Run the Demo

```bash
python3 demo.py
```

This comprehensive demo showcases all protocol features:
1. Encryption/Decryption (AES-256-GCM)
2. Frequency Hopping (50 channels @ 100 hops/sec)
3. Geofencing (GPS + RSSI validation)
4. Packet System (building, parsing, validation)
5. Replay Protection (sliding window)
6. Authentication (PSK-based)
7. Complete Workflow (end-to-end secure communication)

### Basic Usage

#### Encryption

```python
from bellhop.encryption import PacketEncryptor, KeyDerivation

# Derive key from password
key = KeyDerivation.derive_key(b"password", b"salt")

# Create encryptor
encryptor = PacketEncryptor(key)

# Encrypt packet
header = b"\x11\x01\x00\x01\xFF\xFF\x00\x42"
payload = b"Secret message"
ciphertext, nonce, algo = encryptor.encrypt_packet(payload, header)

# Decrypt packet
decrypted = encryptor.decrypt_packet(ciphertext, nonce, header)
```

#### Frequency Hopping

```python
from bellhop.frequency_hopping import FrequencyHopper
import secrets
import time

# Initialize hopper
network_id = 0x12345678
session_key = secrets.token_bytes(32)
hopper = FrequencyHopper(network_id, session_key, band='915MHz')

# Get current channel
current_time = time.time()
channel = hopper.get_channel_at_time(current_time)
frequency = hopper.get_frequency(channel)

# Generate hopping sequence
time_slot = int(current_time)
sequence = hopper.generate_sequence(time_slot)
```

#### Geofencing

```python
from bellhop.geofencing import GeofenceValidator, GeofenceBoundary, GPSPosition

# Define boundary
boundary = GeofenceBoundary([
    GPSPosition(37.7749, -122.4194),
    GPSPosition(37.7750, -122.4180),
    GPSPosition(37.7735, -122.4175),
    GPSPosition(37.7730, -122.4190)
])

# Create validator
validator = GeofenceValidator(boundary)

# Validate position
position = GPSPosition(37.7740, -122.4185, altitude=100)
valid, reason, confidence = validator.validate_gps(position)
```

#### Packet System

```python
from bellhop.packet import PacketBuilder, PacketParser, PacketType
import os

# Build packet
builder = PacketBuilder()
packet = builder.build_packet(
    packet_type=PacketType.DATA,
    source=0x0001,
    destination=0xFFFF,
    payload=b"Hello, BELLHOP!",
    encrypted=True,
    nonce=os.urandom(12),
    auth_tag=os.urandom(14)
)

# Validate packet
valid, reason = PacketParser.validate_packet(packet)

# Parse packet
header, security, payload, crc_valid = PacketParser.parse_packet(packet)
```

#### Replay Protection

```python
from bellhop.replay_protection import NodeReplayProtector

# Create protector
protector = NodeReplayProtector(window_size=64, max_time_diff=30.0)

# Check for replay
node_id = 0x0001
seq_num = 42
valid, accept, reason = protector.check_replay(node_id, seq_num)
```

#### Authentication

```python
from bellhop.authentication import Authenticator

# PSK authentication
psk = b"my_secure_pre_shared_key"
authenticator = Authenticator(mode="PSK", psk=psk)

# Authenticate node
result = authenticator.authenticate(0x0001)
if result.success:
    session_key = result.session_key
```

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=bellhop --cov-report=html
```

## Features

### ✅ Complete Implementation

- **Encryption**: Full AES-256-GCM and ChaCha20-Poly1305 support
- **Frequency Hopping**: Cryptographic sequence generation with channel quality management
- **Geofencing**: GPS validation, RSSI triangulation, hybrid validation
- **Packet System**: Complete packet building/parsing with CRC validation
- **Replay Protection**: Sliding window with timestamp validation per node
- **Authentication**: PSK and certificate-based authentication

### 🔒 Security Features

- 256-bit encryption keys
- Perfect forward secrecy support
- Hardware-independent (pure Python)
- Constant-time operations where applicable
- Secure random number generation

### 📊 Performance

- Fast encryption/decryption (<1ms per packet)
- Efficient frequency hopping (100+ hops/second capable)
- Low memory footprint
- Scalable to 256+ nodes

## Examples

See `demo.py` for a comprehensive demonstration of all features working together.

### Individual Module Examples

Each module includes runnable examples:

```bash
# Test encryption
python3 -m bellhop.encryption

# Test frequency hopping
python3 -m bellhop.frequency_hopping

# Test geofencing
python3 -m bellhop.geofencing

# Test packet system
python3 -m bellhop.packet

# Test replay protection
python3 -m bellhop.replay_protection

# Test authentication
python3 -m bellhop.authentication
```

## Architecture

The implementation follows a modular architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (Mesh Network Application, NUC Integration, Dashboard)     │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                  BELLHOP Protocol Layer                      │
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │ Encryption   │ │   Packet     │ │ Replay Prot  │       │
│  │  (AES-GCM)   │ │  System      │ │  (Window)    │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
│                                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │  Frequency   │ │  Geofencing  │ │     Auth     │       │
│  │   Hopping    │ │  (GPS/RSSI)  │ │  (PSK/Cert)  │       │
│  └──────────────┘ └──────────────┘ └──────────────┘       │
└──────────────────────────────────────────────────────────────┘
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - See LICENSE file for details

## Security Considerations

- This is a reference implementation for educational and testing purposes
- For production use, consider:
  - Hardware security modules (HSM) for key storage
  - Formal security audit
  - Platform-specific optimizations
  - Real-time system integration

## Support

- **Documentation**: See main repository docs
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**BELLHOP Protocol - Secure. Resilient. Operational.**
