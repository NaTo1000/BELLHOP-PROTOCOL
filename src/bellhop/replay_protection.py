"""
Replay protection module for BELLHOP protocol.
Implements sliding window replay detection.
"""

import time
from typing import Tuple, Optional


class ReplayProtector:
    """Implements replay protection using sliding window and timestamps."""
    
    def __init__(self, window_size: int = 64, max_time_diff: float = 30.0):
        """
        Initialize replay protector.
        
        Args:
            window_size: Size of replay detection window
            max_time_diff: Maximum allowed time difference in seconds
        """
        self.window_size = window_size
        self.max_time_diff = max_time_diff
        self.highest_seq = 0
        self.received_bitmap = 0
        self.last_timestamp = time.time()
    
    def check_replay(self, seq_num: int, timestamp: Optional[float] = None) -> Tuple[bool, bool, str]:
        """
        Check if sequence number is a replay.
        
        Args:
            seq_num: Sequence number from packet
            timestamp: Optional packet timestamp for time-based validation
        
        Returns:
            Tuple of (is_valid, should_accept, reason)
        """
        # Time-based validation if timestamp provided
        if timestamp is not None:
            current_time = time.time()
            time_diff = abs(current_time - timestamp)
            
            if time_diff > self.max_time_diff:
                return False, False, f"Timestamp outside window ({time_diff:.1f}s > {self.max_time_diff}s)"
        
        # Sequence number validation
        
        # Packet too old (beyond window)
        if seq_num + self.window_size < self.highest_seq:
            return False, False, f"Sequence number too old ({seq_num} vs {self.highest_seq})"
        
        # New highest sequence number
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
            
            if timestamp is not None:
                self.last_timestamp = timestamp
            
            return True, True, "New sequence number accepted"
        
        # Within window - check if already received
        bit_pos = self.highest_seq - seq_num
        
        if bit_pos >= self.window_size:
            return False, False, "Sequence number outside window"
        
        if self.received_bitmap & (1 << bit_pos):
            return False, False, f"Replay detected - sequence {seq_num} already received"
        
        # Within window and not received yet
        self.received_bitmap |= (1 << bit_pos)
        
        if timestamp is not None:
            self.last_timestamp = timestamp
        
        return True, True, "Sequence number accepted (within window)"
    
    def reset(self):
        """Reset replay protector state."""
        self.highest_seq = 0
        self.received_bitmap = 0
        self.last_timestamp = time.time()
    
    def get_state(self) -> dict:
        """
        Get current state of replay protector.
        
        Returns:
            Dictionary with current state
        """
        # Count received packets in window
        received_count = bin(self.received_bitmap).count('1')
        
        return {
            'highest_seq': self.highest_seq,
            'window_size': self.window_size,
            'packets_in_window': received_count,
            'last_timestamp': self.last_timestamp,
            'max_time_diff': self.max_time_diff
        }


class NodeReplayProtector:
    """Manages replay protection for multiple nodes."""
    
    def __init__(self, window_size: int = 64, max_time_diff: float = 30.0):
        """
        Initialize node replay protector.
        
        Args:
            window_size: Size of replay detection window per node
            max_time_diff: Maximum allowed time difference in seconds
        """
        self.window_size = window_size
        self.max_time_diff = max_time_diff
        self.protectors = {}  # node_id -> ReplayProtector
    
    def check_replay(self, node_id: int, seq_num: int, 
                    timestamp: Optional[float] = None) -> Tuple[bool, bool, str]:
        """
        Check if packet from a node is a replay.
        
        Args:
            node_id: Source node ID
            seq_num: Sequence number from packet
            timestamp: Optional packet timestamp
        
        Returns:
            Tuple of (is_valid, should_accept, reason)
        """
        # Create protector for node if doesn't exist
        if node_id not in self.protectors:
            self.protectors[node_id] = ReplayProtector(
                window_size=self.window_size,
                max_time_diff=self.max_time_diff
            )
        
        return self.protectors[node_id].check_replay(seq_num, timestamp)
    
    def reset_node(self, node_id: int):
        """Reset replay protection for a specific node."""
        if node_id in self.protectors:
            self.protectors[node_id].reset()
    
    def remove_node(self, node_id: int):
        """Remove replay protection for a node."""
        if node_id in self.protectors:
            del self.protectors[node_id]
    
    def get_node_state(self, node_id: int) -> Optional[dict]:
        """
        Get replay protection state for a node.
        
        Args:
            node_id: Node ID
        
        Returns:
            State dictionary or None if node not found
        """
        if node_id in self.protectors:
            return self.protectors[node_id].get_state()
        return None
    
    def get_all_states(self) -> dict:
        """
        Get replay protection state for all nodes.
        
        Returns:
            Dictionary mapping node_id to state
        """
        return {
            node_id: protector.get_state()
            for node_id, protector in self.protectors.items()
        }


# Example usage
if __name__ == "__main__":
    print("Testing ReplayProtector...")
    print("="*50)
    
    # Create single-node protector
    protector = ReplayProtector(window_size=64, max_time_diff=30.0)
    
    # Test sequence
    test_sequences = [1, 2, 3, 5, 4, 3, 6, 100, 99, 98, 1, 101]
    
    print("\nSequence Number Tests:")
    print("-"*50)
    for seq in test_sequences:
        valid, accept, reason = protector.check_replay(seq)
        status = "✓ ACCEPT" if accept else "✗ REJECT"
        print(f"Seq {seq:3d}: {status:10s} - {reason}")
    
    # Test with timestamps
    print("\nTimestamp Tests:")
    print("-"*50)
    
    protector.reset()
    current_time = time.time()
    
    # Valid timestamp
    valid, accept, reason = protector.check_replay(1, current_time)
    print(f"Current time: {accept} - {reason}")
    
    # Old timestamp (should fail)
    old_time = current_time - 60  # 60 seconds ago
    valid, accept, reason = protector.check_replay(2, old_time)
    print(f"Old time (-60s): {accept} - {reason}")
    
    # Future timestamp (should fail)
    future_time = current_time + 60  # 60 seconds in future
    valid, accept, reason = protector.check_replay(3, future_time)
    print(f"Future time (+60s): {accept} - {reason}")
    
    # Valid timestamp within window
    valid_time = current_time - 15  # 15 seconds ago (within 30s window)
    valid, accept, reason = protector.check_replay(4, valid_time)
    print(f"Valid time (-15s): {accept} - {reason}")
    
    # Test multi-node protector
    print("\n" + "="*50)
    print("Testing NodeReplayProtector...")
    print("="*50)
    
    node_protector = NodeReplayProtector()
    
    # Test multiple nodes
    print("\nMulti-Node Tests:")
    print("-"*50)
    
    test_data = [
        (0x0001, 1),
        (0x0001, 2),
        (0x0002, 1),  # Different node, same seq is OK
        (0x0001, 2),  # Same node, replay
        (0x0002, 2),
        (0x0001, 3),
    ]
    
    for node_id, seq in test_data:
        valid, accept, reason = node_protector.check_replay(node_id, seq)
        status = "✓ ACCEPT" if accept else "✗ REJECT"
        print(f"Node 0x{node_id:04x}, Seq {seq}: {status:10s} - {reason}")
    
    # Show state
    print("\nNode States:")
    print("-"*50)
    for node_id, state in node_protector.get_all_states().items():
        print(f"Node 0x{node_id:04x}:")
        print(f"  Highest seq: {state['highest_seq']}")
        print(f"  Packets in window: {state['packets_in_window']}")
    
    print("\n✓ Replay protection operational!")
