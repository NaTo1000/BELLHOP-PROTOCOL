# Frequency Hopping Protocol

## Overview
The BELLHOP Frequency Hopping Spread Spectrum (FHSS) protocol provides anti-jamming and security through rapid channel switching.

## Frequency Bands

### ISM Band (433/868/915 MHz)
Depending on region, the protocol uses license-free ISM bands:
- **433 MHz**: Europe, Asia (433.05-434.79 MHz)
- **868 MHz**: Europe (863-870 MHz)
- **915 MHz**: Americas, Australia (902-928 MHz)

### Channel Allocation
- **Total Channels**: 50 per band
- **Channel Spacing**: 125 kHz minimum
- **Guard Bands**: 25 kHz between channels

## Hopping Sequence

### Pseudo-Random Sequence Generation
The hopping sequence is generated using a cryptographically secure pseudo-random number generator (CSPRNG) seeded with:
- Network ID (32-bit)
- Time slot (32-bit)
- Session key (256-bit)

### Algorithm
```
function generate_hop_sequence(network_id, time_slot, session_key):
    seed = HMAC-SHA256(session_key, network_id || time_slot)
    prng = ChaCha20(seed)
    
    sequence = []
    for i in range(50):
        channel = prng.next() % 50
        while channel in sequence:  # Ensure no repeats in sequence
            channel = prng.next() % 50
        sequence.append(channel)
    
    return sequence
```

### Synchronization
**Method 1: GPS Time Sync**
- Use GPS seconds as master clock
- Time slot = GPS_seconds / hop_duration
- Sub-second precision via PPS signal
- Drift compensation: ±10ms

**Method 2: Network Master Sync**
- Designated master broadcasts time
- Nodes adjust local clocks
- Two-way time transfer protocol
- Periodic resync every 10 seconds

**Method 3: Hybrid Sync**
- GPS when available
- Master fallback when GPS lost
- Peer-to-peer sync for redundancy
- Consensus algorithm for accuracy

## Hop Timing

### Basic Timing
- **Hop Duration**: 10ms (100 hops/second)
- **Dwell Time**: 8ms (time on channel)
- **Transition Time**: 2ms (switching time)

### Adaptive Timing
The protocol can adjust timing based on:
- Channel quality
- Data rate requirements
- Interference levels
- Battery conservation

**Fast Mode**: 5ms hop (200 hops/second)
- High security, high power
- Combat active jamming
- Short-duration messages

**Normal Mode**: 10ms hop (100 hops/second)
- Balanced security/power
- Standard operations
- General communications

**Slow Mode**: 50ms hop (20 hops/second)
- Battery saving
- Static environment
- Long messages

## Channel Quality Assessment

### Metrics
1. **RSSI (Received Signal Strength Indicator)**
   - Measured per channel
   - Averaged over 100 packets
   - Threshold: -100 dBm minimum

2. **SNR (Signal-to-Noise Ratio)**
   - Calculated from RSSI and noise floor
   - Threshold: 10 dB minimum
   - Dynamic adjustment

3. **PER (Packet Error Rate)**
   - Track failed packets per channel
   - Threshold: 5% maximum
   - Trigger channel blacklist

4. **Interference Detection**
   - Spectrum scan during initialization
   - Continuous monitoring
   - Adaptive avoidance

### Channel Blacklisting
When a channel becomes unreliable:
1. Mark channel as suspect after 10% PER
2. Blacklist after sustained issues
3. Remove from hop sequence
4. Generate new sequence without bad channels
5. Synchronize blacklist across network
6. Periodic re-evaluation (every 5 minutes)

## Anti-Jamming Features

### Reactive Measures
1. **Interference Detection**
   - Monitor all channels periodically
   - Identify jammed frequencies
   - Blacklist affected channels
   - Notify network of threats

2. **Adaptive Hopping**
   - Skip compromised channels
   - Increase hop rate in jammed environment
   - Use wider frequency spread
   - Employ directional antennas if available

3. **Power Management**
   - Increase transmit power on poor channels
   - Decrease power on clear channels
   - Optimize for battery vs. reliability

### Proactive Measures
1. **Unpredictable Sequences**
   - Cryptographic sequence generation
   - Frequent sequence rotation
   - Per-session uniqueness
   - No pattern repetition

2. **Multiple Band Support**
   - Switch between 433/868/915 MHz
   - Cross-band redundancy
   - Automatic band selection
   - Fallback capabilities

3. **Spread Spectrum**
   - Wide frequency distribution
   - Difficult to jam all channels
   - Graceful degradation
   - Maintain partial connectivity

## Implementation Details

### Hardware Requirements
- Fast frequency synthesizer (<2ms lock time)
- Wideband antenna (>20% bandwidth)
- Accurate time source (GPS or TCXO)
- Sufficient processing power for crypto

### Radio Configuration
```
# Frequency bands (MHz)
BAND_433 = [433.05 + i*0.125 for i in range(50)]
BAND_868 = [863.0 + i*0.14 for i in range(50)]
BAND_915 = [902.0 + i*0.52 for i in range(50)]

# Modulation
MODULATION = "LoRa"
BANDWIDTH = 125  # kHz
SPREADING_FACTOR = 7  # Fast, short range
CODING_RATE = 4/5  # Error correction

# Power
TX_POWER = 20  # dBm (adjustable)
```

### Software State Machine
```
STATE_INIT -> Scan all channels, assess quality
STATE_SYNC -> Synchronize with network time
STATE_KEYGEN -> Generate hopping sequence
STATE_HOP -> Execute hop sequence
STATE_MONITOR -> Continuous quality check
STATE_ADAPT -> Adjust sequence if needed
```

## Security Considerations

### Sequence Prediction Resistance
- 256-bit key space: 2^256 possible sequences
- New sequence per session
- Key derived from master secret
- Perfect forward secrecy

### Time Synchronization Attacks
- Authenticated time messages
- Bounded clock adjustment (±1 second max)
- Multiple time sources for validation
- Anomaly detection for time jumps

### Channel Hopping Disclosure
- Never transmit sequence explicitly
- Only transmit encrypted time sync
- Derive sequence independently
- No correlation between packets and hops

## Performance Metrics

### Expected Performance
- **Hop Accuracy**: ±2ms synchronization
- **Channel Coverage**: All 50 channels used equally
- **Jamming Resistance**: 90% channels can be jammed, network survives
- **Power Consumption**: 200mA @ 3.3V during operation
- **Latency**: <50ms additional delay
- **Throughput**: Minimal impact (<5% reduction)

### Testing Requirements
1. Validate hop timing accuracy
2. Verify synchronization across nodes
3. Test jamming resistance
4. Measure power consumption
5. Assess channel quality algorithms
6. Validate security of sequence generation

## Integration with BELLHOP Protocol

The frequency hopping protocol integrates with the main BELLHOP security suite:
- Phase 3 of initialization (packages 2001-3000)
- Synchronized with packet encryption
- Coordinated with geofencing
- Feeds data to NUC for analysis

## Conclusion
The frequency hopping protocol provides robust anti-jamming capabilities and additional security through obscurity, making the BELLHOP system highly resilient to interference and attacks.
