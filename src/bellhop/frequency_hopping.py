"""
Frequency hopping module for BELLHOP protocol.
Implements cryptographic frequency hopping spread spectrum (FHSS).
"""

import hashlib
import struct
import time
from typing import List, Tuple, Optional


class ChannelManager:
    """Manages channel quality and blacklisting."""
    
    def __init__(self, num_channels: int = 50):
        """
        Initialize channel manager.
        
        Args:
            num_channels: Total number of available channels
        """
        self.num_channels = num_channels
        self.channel_quality = {i: 1.0 for i in range(num_channels)}
        self.blacklist = set()
        self.rssi_history = {i: [] for i in range(num_channels)}
        self.per_history = {i: [] for i in range(num_channels)}  # Packet Error Rate
    
    def update_channel_quality(self, channel: int, rssi: float, success: bool):
        """
        Update channel quality metrics.
        
        Args:
            channel: Channel number
            rssi: Received signal strength indicator (dBm)
            success: Whether packet was successfully received
        """
        if channel not in range(self.num_channels):
            return
        
        # Track RSSI
        self.rssi_history[channel].append(rssi)
        if len(self.rssi_history[channel]) > 100:
            self.rssi_history[channel] = self.rssi_history[channel][-100:]
        
        # Track packet error rate
        self.per_history[channel].append(0 if success else 1)
        if len(self.per_history[channel]) > 100:
            self.per_history[channel] = self.per_history[channel][-100:]
        
        # Calculate quality score (0.0 to 1.0)
        avg_rssi = sum(self.rssi_history[channel]) / len(self.rssi_history[channel])
        per = sum(self.per_history[channel]) / len(self.per_history[channel])
        
        # Normalize RSSI (-120 to -40 dBm range)
        rssi_score = max(0.0, min(1.0, (avg_rssi + 120) / 80))
        success_score = 1.0 - per
        
        self.channel_quality[channel] = (rssi_score * 0.4 + success_score * 0.6)
    
    def blacklist_channel(self, channel: int):
        """Add channel to blacklist."""
        if channel in range(self.num_channels):
            self.blacklist.add(channel)
    
    def whitelist_channel(self, channel: int):
        """Remove channel from blacklist."""
        self.blacklist.discard(channel)
    
    def get_available_channels(self) -> List[int]:
        """Get list of non-blacklisted channels."""
        return [ch for ch in range(self.num_channels) if ch not in self.blacklist]
    
    def get_best_channels(self, count: int = 10) -> List[int]:
        """
        Get the best quality channels.
        
        Args:
            count: Number of channels to return
        
        Returns:
            List of channel numbers sorted by quality
        """
        available = self.get_available_channels()
        sorted_channels = sorted(
            available,
            key=lambda ch: self.channel_quality[ch],
            reverse=True
        )
        return sorted_channels[:count]


class FrequencyHopper:
    """Implements cryptographic frequency hopping."""
    
    # Frequency bands (in MHz)
    BAND_433 = {
        'name': '433MHz',
        'base_freq': 433.050,
        'channel_spacing': 0.125,
        'num_channels': 50
    }
    
    BAND_868 = {
        'name': '868MHz',
        'base_freq': 863.000,
        'channel_spacing': 0.140,
        'num_channels': 50
    }
    
    BAND_915 = {
        'name': '915MHz',
        'base_freq': 902.000,
        'channel_spacing': 0.520,
        'num_channels': 50
    }
    
    def __init__(self, network_id: int, session_key: bytes, 
                 band: str = '915MHz', hop_duration_ms: int = 10):
        """
        Initialize frequency hopper.
        
        Args:
            network_id: 32-bit network identifier
            session_key: 32-byte session key for sequence generation
            band: Frequency band ('433MHz', '868MHz', or '915MHz')
            hop_duration_ms: Duration per hop in milliseconds
        """
        if len(session_key) != 32:
            raise ValueError("Session key must be 32 bytes")
        
        self.network_id = network_id
        self.session_key = session_key
        self.hop_duration_ms = hop_duration_ms
        
        # Select band configuration
        if band == '433MHz':
            self.band = self.BAND_433
        elif band == '868MHz':
            self.band = self.BAND_868
        elif band == '915MHz':
            self.band = self.BAND_915
        else:
            raise ValueError(f"Unknown band: {band}")
        
        self.num_channels = self.band['num_channels']
        self.channel_manager = ChannelManager(self.num_channels)
    
    def generate_sequence(self, time_slot: int, blacklist: Optional[set] = None) -> List[int]:
        """
        Generate pseudo-random hopping sequence for a time slot.
        
        Args:
            time_slot: Time slot identifier (e.g., GPS second)
            blacklist: Optional set of channels to exclude
        
        Returns:
            List of channel numbers in hopping order
        """
        # Create seed from network ID, time slot, and session key
        seed_data = struct.pack(">I", self.network_id) + \
                    struct.pack(">Q", time_slot) + \
                    self.session_key
        
        # Generate seed using HMAC-SHA256
        seed_hash = hashlib.sha256(seed_data).digest()
        
        # Use seed to generate sequence
        sequence = []
        available_channels = set(range(self.num_channels))
        
        if blacklist:
            available_channels -= blacklist
        
        if not available_channels:
            # If all channels blacklisted, use all channels
            available_channels = set(range(self.num_channels))
        
        available = list(available_channels)
        seed_int = int.from_bytes(seed_hash, 'big')
        
        # Generate permutation using Fisher-Yates shuffle with PRNG
        for i in range(len(available)):
            # Use cryptographic hash for randomness
            h = hashlib.sha256(seed_hash + struct.pack(">I", i)).digest()
            rand_val = int.from_bytes(h[:4], 'big')
            j = i + (rand_val % (len(available) - i))
            available[i], available[j] = available[j], available[i]
        
        return available
    
    def get_channel_at_time(self, timestamp: float, offset_ms: int = 0) -> int:
        """
        Get the channel to use at a specific time.
        
        Args:
            timestamp: Unix timestamp (seconds)
            offset_ms: Millisecond offset within the second
        
        Returns:
            Channel number to use
        """
        # Calculate time slot (seconds)
        time_slot = int(timestamp)
        
        # Calculate position within time slot
        total_ms = int((timestamp - time_slot) * 1000) + offset_ms
        hop_index = total_ms // self.hop_duration_ms
        
        # Generate sequence for this time slot
        blacklist = self.channel_manager.blacklist
        sequence = self.generate_sequence(time_slot, blacklist)
        
        # Wrap around if needed
        channel_index = hop_index % len(sequence)
        
        return sequence[channel_index]
    
    def get_frequency(self, channel: int) -> float:
        """
        Get frequency in MHz for a channel number.
        
        Args:
            channel: Channel number (0 to num_channels-1)
        
        Returns:
            Frequency in MHz
        """
        if channel not in range(self.num_channels):
            raise ValueError(f"Invalid channel: {channel}")
        
        return self.band['base_freq'] + (channel * self.band['channel_spacing'])
    
    def synchronize(self, reference_time: float) -> Tuple[int, float]:
        """
        Synchronize hopper to reference time.
        
        Args:
            reference_time: Reference timestamp (e.g., from GPS)
        
        Returns:
            Tuple of (current_channel, time_until_next_hop_ms)
        """
        current_channel = self.get_channel_at_time(reference_time)
        
        # Calculate time until next hop
        time_slot = int(reference_time)
        ms_in_slot = (reference_time - time_slot) * 1000
        hops_elapsed = int(ms_in_slot / self.hop_duration_ms)
        time_until_next = self.hop_duration_ms - (ms_in_slot - hops_elapsed * self.hop_duration_ms)
        
        return current_channel, time_until_next
    
    def update_channel_quality(self, channel: int, rssi: float, success: bool):
        """
        Update quality metrics for a channel.
        
        Args:
            channel: Channel number
            rssi: Received signal strength (dBm)
            success: Whether transmission was successful
        """
        self.channel_manager.update_channel_quality(channel, rssi, success)
        
        # Auto-blacklist if quality too low
        if self.channel_manager.channel_quality[channel] < 0.2:
            self.channel_manager.blacklist_channel(channel)


# Example usage
if __name__ == "__main__":
    import secrets
    
    # Initialize hopper
    network_id = 0x12345678
    session_key = secrets.token_bytes(32)
    hopper = FrequencyHopper(network_id, session_key, band='915MHz')
    
    # Get current time
    current_time = time.time()
    
    # Generate hopping sequence for current second
    time_slot = int(current_time)
    sequence = hopper.generate_sequence(time_slot)
    print(f"Hopping sequence for time slot {time_slot}:")
    print(f"First 10 channels: {sequence[:10]}")
    print(f"Total channels in sequence: {len(sequence)}")
    
    # Get current channel
    current_channel = hopper.get_channel_at_time(current_time)
    frequency = hopper.get_frequency(current_channel)
    print(f"\nCurrent channel: {current_channel} ({frequency:.3f} MHz)")
    
    # Synchronize
    channel, time_until_next = hopper.synchronize(current_time)
    print(f"Synchronized to channel {channel}, next hop in {time_until_next:.1f} ms")
    
    # Simulate channel quality updates
    print("\nSimulating channel quality updates...")
    hopper.update_channel_quality(5, -85.0, True)
    hopper.update_channel_quality(5, -88.0, True)
    hopper.update_channel_quality(10, -110.0, False)
    hopper.update_channel_quality(10, -115.0, False)
    
    # Get best channels
    best_channels = hopper.channel_manager.get_best_channels(5)
    print(f"Best 5 channels: {best_channels}")
    
    # Show blacklisted channels
    print(f"Blacklisted channels: {hopper.channel_manager.blacklist}")
    
    print("\n✓ Frequency hopping operational!")
