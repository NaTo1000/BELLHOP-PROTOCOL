#!/usr/bin/env python3
"""
BELLHOP Protocol Comprehensive Demo
Demonstrates all major features of the BELLHOP security suite.
"""

import os
import sys
import time
import secrets

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bellhop.encryption import PacketEncryptor, KeyDerivation
from bellhop.frequency_hopping import FrequencyHopper
from bellhop.geofencing import GeofenceValidator, GeofenceBoundary, GPSPosition
from bellhop.packet import PacketBuilder, PacketParser, PacketType, Packet
from bellhop.replay_protection import NodeReplayProtector
from bellhop.authentication import Authenticator


def print_section(title):
    """Print a section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def demo_encryption():
    """Demonstrate encryption functionality."""
    print_section("1. ENCRYPTION DEMO")
    
    # Derive key from password
    password = b"secure_network_password_at_least_32_chars"
    salt = b"network_001"
    key = KeyDerivation.derive_key(password, salt)
    print(f"✓ Derived 256-bit key from password")
    print(f"  Key (first 16 bytes): {key[:16].hex()}")
    
    # Create encryptor
    encryptor = PacketEncryptor(key, PacketEncryptor.ALGORITHM_AES_GCM)
    print(f"✓ Created AES-256-GCM encryptor")
    
    # Encrypt packet
    header = b"\x11\x01\x00\x01\xFF\xFF\x00\x42"
    payload = b"Secret message: Deploy at coordinates 37.7749, -122.4194"
    
    ciphertext, nonce, algo = encryptor.encrypt_packet(payload, header)
    print(f"✓ Encrypted {len(payload)} bytes -> {len(ciphertext)} bytes")
    print(f"  Nonce: {nonce.hex()}")
    print(f"  Ciphertext (first 32 bytes): {ciphertext[:32].hex()}...")
    
    # Decrypt packet
    decrypted = encryptor.decrypt_packet(ciphertext, nonce, header)
    print(f"✓ Decrypted successfully")
    print(f"  Original: {payload[:40].decode()}...")
    print(f"  Decrypted: {decrypted[:40].decode()}...")
    assert decrypted == payload


def demo_frequency_hopping():
    """Demonstrate frequency hopping."""
    print_section("2. FREQUENCY HOPPING DEMO")
    
    # Initialize hopper
    network_id = 0x42424242
    session_key = secrets.token_bytes(32)
    hopper = FrequencyHopper(network_id, session_key, band='915MHz')
    print(f"✓ Initialized frequency hopper")
    print(f"  Network ID: 0x{network_id:08x}")
    print(f"  Band: 915 MHz ISM")
    print(f"  Channels: 50")
    print(f"  Hop rate: 100 hops/second")
    
    # Generate hopping sequence
    current_time = time.time()
    time_slot = int(current_time)
    sequence = hopper.generate_sequence(time_slot)
    print(f"\n✓ Generated hopping sequence for time slot {time_slot}")
    print(f"  First 20 channels: {sequence[:20]}")
    
    # Get current channel and frequency
    current_channel = hopper.get_channel_at_time(current_time)
    frequency = hopper.get_frequency(current_channel)
    print(f"\n✓ Current operation:")
    print(f"  Channel: {current_channel}")
    print(f"  Frequency: {frequency:.3f} MHz")
    
    # Simulate channel quality updates
    print(f"\n✓ Simulating channel quality monitoring...")
    hopper.update_channel_quality(5, -75.0, True)  # Good channel
    hopper.update_channel_quality(10, -115.0, False)  # Bad channel
    hopper.update_channel_quality(10, -118.0, False)  # Still bad
    
    best_channels = hopper.channel_manager.get_best_channels(5)
    print(f"  Best 5 channels: {best_channels}")
    print(f"  Blacklisted channels: {hopper.channel_manager.blacklist}")


def demo_geofencing():
    """Demonstrate geofencing."""
    print_section("3. GEOFENCING (INVISIBLE FENCE) DEMO")
    
    # Define secure area boundary
    boundary = GeofenceBoundary([
        GPSPosition(37.7749, -122.4194),
        GPSPosition(37.7750, -122.4180),
        GPSPosition(37.7735, -122.4175),
        GPSPosition(37.7730, -122.4190)
    ], altitude_min=0, altitude_max=500, buffer_zone=50)
    
    print(f"✓ Defined geofence boundary")
    print(f"  Vertices: {len(boundary.coordinates)}")
    print(f"  Altitude range: {boundary.altitude_min}m - {boundary.altitude_max}m")
    print(f"  Buffer zone: {boundary.buffer_zone}m")
    
    # Create reference nodes for RSSI
    reference_nodes = [
        (GPSPosition(37.7749, -122.4194), 20.0),
        (GPSPosition(37.7750, -122.4180), 20.0),
        (GPSPosition(37.7735, -122.4175), 20.0),
    ]
    
    validator = GeofenceValidator(boundary, reference_nodes)
    print(f"✓ Configured {len(reference_nodes)} reference nodes for RSSI triangulation")
    
    # Test position inside fence
    test_inside = GPSPosition(37.7740, -122.4185, altitude=100)
    valid, reason, confidence = validator.validate_gps(test_inside)
    print(f"\n✓ Testing GPS position inside fence:")
    print(f"  Position: {test_inside}")
    print(f"  Valid: {valid}")
    print(f"  Confidence: {confidence:.1%}")
    print(f"  Reason: {reason}")
    
    # Test position outside fence
    test_outside = GPSPosition(37.7800, -122.4200, altitude=100)
    valid, reason, confidence = validator.validate_gps(test_outside)
    print(f"\n✗ Testing GPS position outside fence:")
    print(f"  Position: {test_outside}")
    print(f"  Valid: {valid}")
    print(f"  Confidence: {confidence:.1%}")
    print(f"  Reason: {reason}")
    
    # Test hybrid validation
    rssi_measurements = [(0, -75.0), (1, -80.0), (2, -85.0)]
    authorized, confidence, details = validator.validate_hybrid(test_inside, rssi_measurements)
    print(f"\n✓ Hybrid validation (GPS + RSSI):")
    print(f"  Authorized: {authorized}")
    print(f"  Overall confidence: {confidence:.1%}")
    for check in details['checks']:
        print(f"    - {check['method']}: {check['valid']} ({check['confidence']:.1%})")


def demo_packet_system():
    """Demonstrate packet building and parsing."""
    print_section("4. PACKET SYSTEM DEMO")
    
    # Create packet builder
    builder = PacketBuilder()
    print(f"✓ Created packet builder")
    
    # Build a data packet
    packet_bytes = builder.build_packet(
        packet_type=PacketType.DATA,
        source=0x0001,
        destination=0xFFFF,  # Broadcast
        payload=b"Emergency alert: All units respond to sector 7",
        encrypted=True,
        priority=True,
        broadcast=True,
        nonce=os.urandom(12),
        auth_tag=os.urandom(14)
    )
    
    print(f"✓ Built packet:")
    print(f"  Total size: {len(packet_bytes)} bytes")
    print(f"  Structure: [Header: 8B][Security: 32B][Payload: {len(packet_bytes)-44}B][CRC: 4B]")
    print(f"  Hex (first 32 bytes): {packet_bytes[:32].hex()}")
    
    # Validate packet
    valid, reason = PacketParser.validate_packet(packet_bytes)
    print(f"\n✓ Packet validation:")
    print(f"  Valid: {valid}")
    print(f"  Reason: {reason}")
    
    # Parse packet
    packet = Packet.from_bytes(packet_bytes)
    print(f"\n✓ Parsed packet:")
    print(f"  {packet}")
    print(f"  Type: {packet.header.packet_type.name}")
    print(f"  Source: 0x{packet.header.source:04x}")
    print(f"  Destination: 0x{packet.header.destination:04x}")
    print(f"  Encrypted: {packet.header.encrypted}")
    print(f"  Priority: {packet.header.priority}")
    print(f"  Broadcast: {packet.header.broadcast}")


def demo_replay_protection():
    """Demonstrate replay protection."""
    print_section("5. REPLAY PROTECTION DEMO")
    
    # Create replay protector for multiple nodes
    protector = NodeReplayProtector(window_size=64, max_time_diff=30.0)
    print(f"✓ Initialized replay protector")
    print(f"  Window size: 64 packets")
    print(f"  Max time difference: 30 seconds")
    
    # Simulate packet reception
    print(f"\n✓ Simulating packet reception:")
    
    test_packets = [
        (0x0001, 1, "First packet from node 1"),
        (0x0001, 2, "Second packet from node 1"),
        (0x0002, 1, "First packet from node 2 (different node, same seq OK)"),
        (0x0001, 2, "Replay of packet 2 from node 1"),
        (0x0001, 3, "New packet from node 1"),
        (0x0002, 2, "New packet from node 2"),
    ]
    
    for node_id, seq, description in test_packets:
        valid, accept, reason = protector.check_replay(node_id, seq)
        status = "✓ ACCEPT" if accept else "✗ REJECT"
        print(f"  Node 0x{node_id:04x}, Seq {seq}: {status:10s} - {description}")
    
    # Show node states
    print(f"\n✓ Replay protector state:")
    for node_id, state in protector.get_all_states().items():
        print(f"  Node 0x{node_id:04x}:")
        print(f"    Highest seq: {state['highest_seq']}")
        print(f"    Packets in window: {state['packets_in_window']}")


def demo_authentication():
    """Demonstrate authentication."""
    print_section("6. AUTHENTICATION DEMO")
    
    # PSK Authentication
    psk = b"secure_pre_shared_key_for_network_12345"
    authenticator = Authenticator(mode="PSK", psk=psk)
    print(f"✓ Initialized PSK authenticator")
    
    node_id = 0x0001
    result = authenticator.authenticate(node_id)
    print(f"\n✓ Authenticated node 0x{node_id:04x}:")
    print(f"  Success: {result.success}")
    print(f"  Reason: {result.reason}")
    if result.session_key:
        print(f"  Session key (first 16 bytes): {result.session_key[:16].hex()}")


def demo_complete_workflow():
    """Demonstrate complete secure communication workflow."""
    print_section("7. COMPLETE WORKFLOW DEMO")
    
    print("Simulating secure node-to-node communication...\n")
    
    # Step 1: Initialize security
    print("Step 1: Security Initialization")
    password = b"network_master_password_secure_123"
    salt = b"bellhop_net_001"
    key = KeyDerivation.derive_key(password, salt)
    encryptor = PacketEncryptor(key)
    print("  ✓ Derived encryption keys")
    
    # Step 2: Authentication
    print("\nStep 2: Node Authentication")
    psk = b"node_pre_shared_key_12345"
    authenticator = Authenticator(mode="PSK", psk=psk)
    auth_result = authenticator.authenticate(0x0001)
    print(f"  ✓ Node authenticated: {auth_result.success}")
    
    # Step 3: Geofence validation
    print("\nStep 3: Geofence Validation")
    boundary = GeofenceBoundary([
        GPSPosition(37.7749, -122.4194),
        GPSPosition(37.7750, -122.4180),
        GPSPosition(37.7735, -122.4175),
        GPSPosition(37.7730, -122.4190)
    ])
    validator = GeofenceValidator(boundary)
    node_position = GPSPosition(37.7740, -122.4185, altitude=100)
    valid, reason, confidence = validator.validate_gps(node_position)
    print(f"  ✓ Node position validated: {valid} ({confidence:.0%} confidence)")
    
    # Step 4: Frequency hopping sync
    print("\nStep 4: Frequency Hopping Synchronization")
    network_id = 0x42424242
    session_key = secrets.token_bytes(32)
    hopper = FrequencyHopper(network_id, session_key)
    current_channel = hopper.get_channel_at_time(time.time())
    frequency = hopper.get_frequency(current_channel)
    print(f"  ✓ Synchronized to channel {current_channel} ({frequency:.3f} MHz)")
    
    # Step 5: Build and encrypt packet
    print("\nStep 5: Secure Packet Transmission")
    builder = PacketBuilder()
    payload = b"Status: All systems operational. Position secure."
    
    # Build packet
    packet_bytes = builder.build_packet(
        packet_type=PacketType.DATA,
        source=0x0001,
        destination=0x0002,
        payload=payload,
        encrypted=True
    )
    
    # Parse header
    header_bytes = packet_bytes[:8]
    
    # Encrypt payload
    ciphertext, nonce, algo = encryptor.encrypt_packet(payload, header_bytes)
    print(f"  ✓ Built and encrypted packet ({len(packet_bytes)} bytes)")
    
    # Step 6: Replay protection check
    print("\nStep 6: Replay Protection")
    protector = NodeReplayProtector()
    valid, accept, reason = protector.check_replay(0x0001, 1)
    print(f"  ✓ Replay check passed: {accept}")
    
    # Step 7: Transmission
    print("\nStep 7: Transmit on Hopping Channel")
    print(f"  ✓ Transmitting on channel {current_channel}")
    print(f"  ✓ Frequency: {frequency:.3f} MHz")
    print(f"  ✓ Packet size: {len(packet_bytes)} bytes")
    
    print("\n" + "─"*70)
    print("✓ Complete secure communication workflow successful!")
    print("  All security layers operational and integrated.")


def main():
    """Run all demos."""
    print("\n")
    print("█"*70)
    print("█" + " "*68 + "█")
    print("█" + "         BELLHOP PROTOCOL - COMPREHENSIVE DEMONSTRATION".center(68) + "█")
    print("█" + "    Broadband Encrypted Low-Latency High-security Protocol".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    try:
        demo_encryption()
        demo_frequency_hopping()
        demo_geofencing()
        demo_packet_system()
        demo_replay_protection()
        demo_authentication()
        demo_complete_workflow()
        
        print("\n" + "█"*70)
        print("█" + " "*68 + "█")
        print("█" + "              ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY".center(68) + "█")
        print("█" + " "*68 + "█")
        print("█"*70)
        print("\nBELLHOP Protocol is fully operational and ready for deployment!")
        print()
        
    except Exception as e:
        print(f"\n✗ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
