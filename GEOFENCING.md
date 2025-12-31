# Geofencing Protocol (Invisible Fence)

## Overview
The BELLHOP Geofencing Protocol, also known as the "Invisible Fence," prevents unauthorized access to the mesh network from nodes located outside defined geographical boundaries. This creates a security perimeter that is transparent to authorized users but impenetrable to outsiders.

## Core Concepts

### Virtual Security Perimeter
The geofence creates a virtual boundary that:
- Restricts network access by location
- Protects against remote attacks
- Ensures physical proximity of nodes
- Prevents signal hijacking from distance

### Multi-Layer Validation
1. **GPS-based verification**
2. **Signal strength validation**
3. **Time-of-flight measurement**
4. **Multi-node triangulation**

## GPS-Based Geofencing

### Boundary Definition
```
# Define fence as polygon vertices
fence = {
    "name": "secure_area_1",
    "type": "polygon",
    "coordinates": [
        {"lat": 37.7749, "lon": -122.4194},
        {"lat": 37.7750, "lon": -122.4180},
        {"lat": 37.7735, "lon": -122.4175},
        {"lat": 37.7730, "lon": -122.4190}
    ],
    "altitude_min": 0,      # meters
    "altitude_max": 500,    # meters
    "buffer_zone": 50       # meters (warning zone)
}
```

### Point-in-Polygon Algorithm
```python
def point_in_polygon(point, polygon):
    """
    Ray casting algorithm for point-in-polygon test
    """
    x, y = point
    n = len(polygon)
    inside = False
    
    p1x, p1y = polygon[0]
    for i in range(1, n + 1):
        p2x, p2y = polygon[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    
    return inside

def validate_gps_position(node_position, fence):
    """
    Validate if node is within geofence
    """
    # Check 2D position
    in_fence = point_in_polygon(
        (node_position['lat'], node_position['lon']),
        [(c['lat'], c['lon']) for c in fence['coordinates']]
    )
    
    # Check altitude if available
    if 'altitude' in node_position:
        alt = node_position['altitude']
        if alt < fence['altitude_min'] or alt > fence['altitude_max']:
            in_fence = False
    
    return in_fence
```

### GPS Anti-Spoofing
To prevent fake GPS coordinates:

1. **Multi-Constellation Validation**
   - Use GPS + GLONASS + Galileo
   - Compare positions from different systems
   - Reject if discrepancy > 20 meters

2. **Signal Strength Check**
   - Verify GPS satellite signal strength
   - Detect impossible signal levels
   - Monitor signal-to-noise ratio

3. **Time Consistency**
   - Validate GPS time vs network time
   - Check for time jumps
   - Ensure smooth position transitions

4. **Movement Pattern Analysis**
   - Track position history
   - Detect impossible velocity
   - Validate acceleration limits

## Signal-Based Geofencing

### RSSI Triangulation
Use signal strength from multiple reference nodes to estimate position:

```python
def rssi_to_distance(rssi, tx_power=-20, path_loss_exponent=2.5):
    """
    Convert RSSI to distance estimate
    rssi: received signal strength (dBm)
    tx_power: transmit power (dBm)
    path_loss_exponent: environment-dependent (2-4)
    """
    if rssi == 0:
        return -1.0
    
    ratio = (tx_power - rssi) / (10 * path_loss_exponent)
    distance = pow(10, ratio)
    return distance

def trilaterate(reference_nodes, distances):
    """
    Estimate position using trilateration
    reference_nodes: list of (x, y) coordinates
    distances: list of distances to each reference node
    """
    # Requires at least 3 reference nodes
    if len(reference_nodes) < 3:
        return None
    
    # Solve using least squares optimization
    # (Simplified - real implementation would use proper solver)
    # Returns estimated (x, y) position
    pass
```

### Reference Node Placement
- Minimum 3 reference nodes per fence
- Positioned at fence boundary
- Known fixed locations
- High-power transmission
- Continuous beacon broadcast

### Signal Fingerprinting
Create signal strength map of authorized area:

```python
signal_map = {
    "area_id": "secure_zone_1",
    "grid_size": 10,  # meters
    "fingerprints": {
        "cell_0_0": {
            "ref_node_1": -65,  # dBm
            "ref_node_2": -72,
            "ref_node_3": -68
        },
        "cell_0_1": {
            "ref_node_1": -68,
            "ref_node_2": -70,
            "ref_node_3": -65
        },
        # ... more cells
    }
}

def match_fingerprint(observed_rssi, signal_map):
    """
    Match observed signal strengths to known locations
    Returns best matching location and confidence
    """
    best_match = None
    best_score = float('inf')
    
    for cell_id, fingerprint in signal_map['fingerprints'].items():
        score = 0
        for node, expected_rssi in fingerprint.items():
            if node in observed_rssi:
                score += abs(observed_rssi[node] - expected_rssi)
        
        if score < best_score:
            best_score = score
            best_match = cell_id
    
    confidence = 1.0 / (1.0 + best_score)
    return best_match, confidence
```

## Time-of-Flight Validation

### Round-Trip Time Measurement
```python
def measure_distance_by_time(rtt_nanoseconds):
    """
    Calculate distance from round-trip time
    Speed of light: ~3×10^8 m/s
    """
    SPEED_OF_LIGHT = 299792458  # m/s
    distance = (rtt_nanoseconds * 1e-9 * SPEED_OF_LIGHT) / 2
    return distance

def validate_proximity(node_id, max_distance_meters):
    """
    Verify node is within expected range using ToF
    """
    # Send timestamped challenge
    challenge_sent_time = get_precise_timestamp()
    send_challenge(node_id, challenge_sent_time)
    
    # Wait for timestamped response
    response = wait_for_response(node_id, timeout=1.0)
    response_recv_time = get_precise_timestamp()
    
    # Calculate round-trip time
    rtt = response_recv_time - challenge_sent_time
    
    # Subtract processing delay
    processing_delay = response.processing_time
    propagation_time = rtt - processing_delay
    
    # Calculate distance
    distance = measure_distance_by_time(propagation_time)
    
    return distance <= max_distance_meters
```

## Hybrid Geofencing

### Multi-Method Validation
Combine all methods for maximum security:

```python
def validate_node_location(node):
    """
    Comprehensive location validation
    Returns: (authorized, confidence, reasons)
    """
    checks = []
    
    # GPS validation
    if node.has_gps():
        gps_valid = validate_gps_position(node.gps_position, fence)
        gps_spoofing_detected = check_gps_spoofing(node)
        checks.append({
            'method': 'GPS',
            'valid': gps_valid and not gps_spoofing_detected,
            'confidence': 0.9 if not gps_spoofing_detected else 0.1
        })
    
    # Signal strength validation
    rssi_data = get_rssi_from_reference_nodes(node)
    if len(rssi_data) >= 3:
        estimated_position = trilaterate(reference_nodes, rssi_data)
        signal_valid = point_in_polygon(estimated_position, fence)
        checks.append({
            'method': 'RSSI',
            'valid': signal_valid,
            'confidence': 0.7
        })
    
    # Time-of-flight validation
    tof_valid = all([
        validate_proximity(node, ref_node.max_distance)
        for ref_node in reference_nodes
    ])
    checks.append({
        'method': 'ToF',
        'valid': tof_valid,
        'confidence': 0.8
    })
    
    # Signal fingerprint matching
    fingerprint_match, fp_confidence = match_fingerprint(rssi_data, signal_map)
    checks.append({
        'method': 'Fingerprint',
        'valid': fingerprint_match is not None,
        'confidence': fp_confidence
    })
    
    # Compute weighted decision
    total_confidence = sum(c['confidence'] for c in checks)
    valid_confidence = sum(c['confidence'] for c in checks if c['valid'])
    
    authorized = (valid_confidence / total_confidence) > 0.6
    confidence = valid_confidence / total_confidence
    
    return authorized, confidence, checks
```

## Dynamic Geofencing

### Adaptive Boundaries
The fence can adapt to environmental conditions:

```python
class AdaptiveGeofence:
    def __init__(self, base_fence):
        self.base_fence = base_fence
        self.current_fence = base_fence
        self.history = []
    
    def adapt_to_conditions(self, conditions):
        """
        Adjust fence based on:
        - Weather (GPS accuracy degradation)
        - Interference (signal-based methods)
        - Threat level (tighten or relax)
        - Time of day
        """
        if conditions['gps_accuracy'] < 5:  # meters
            # GPS reliable, use strict boundaries
            self.current_fence = self.base_fence
        elif conditions['interference_level'] < 0.3:
            # Signal-based methods reliable
            self.use_signal_based_fence()
        else:
            # Fall back to conservative fence
            self.use_conservative_fence()
    
    def use_signal_based_fence(self):
        # Expand fence slightly to account for GPS uncertainty
        self.current_fence = expand_polygon(
            self.base_fence, 
            buffer=20  # meters
        )
    
    def use_conservative_fence(self):
        # Shrink fence for higher security
        self.current_fence = shrink_polygon(
            self.base_fence,
            buffer=-10  # meters
        )
```

## Fence Breach Response

### Immediate Actions
When a fence breach is detected:

1. **Alert Generation**
   ```python
   def handle_fence_breach(node, location):
       alert = {
           'timestamp': get_timestamp(),
           'node_id': node.id,
           'location': location,
           'severity': 'HIGH',
           'type': 'GEOFENCE_BREACH'
       }
       
       # Send to NUC for analysis
       send_to_nuc(alert)
       
       # Notify network administrators
       notify_admins(alert)
       
       # Log the event
       log_security_event(alert)
   ```

2. **Node Quarantine**
   - Immediately block network access
   - Revoke encryption keys
   - Mark node as suspicious
   - Require re-authentication

3. **Network Protection**
   - Alert other nodes
   - Strengthen authentication
   - Increase monitoring
   - Activate backup channels

### Investigation
- Review node history
- Analyze movement patterns
- Check for GPS spoofing
- Correlate with other events
- Determine if legitimate (GPS error) or attack

## Integration with Initialization Sequence

### Phase 5: Geofence Establishment (Packages 4001-5000)

```python
def geofence_initialization():
    """
    Establish geofencing during initialization
    """
    # Packages 4001-4100: Boundary definition
    broadcast_fence_coordinates()
    
    # Packages 4101-4300: Reference node discovery
    discover_reference_nodes()
    calibrate_signal_strengths()
    
    # Packages 4301-4500: GPS validation setup
    sync_gps_constellations()
    establish_baseline_accuracy()
    
    # Packages 4501-4700: Signal fingerprinting
    build_signal_strength_map()
    validate_fingerprint_accuracy()
    
    # Packages 4701-4900: Time-of-flight calibration
    measure_propagation_delays()
    calibrate_reference_distances()
    
    # Packages 4901-5000: Final validation
    test_geofence_detection()
    confirm_all_nodes_valid()
    activate_geofence()
```

## NUC Integration

### Data Streaming to Central Node
```python
def stream_geofence_data_to_nuc():
    """
    Continuously send geofence data to NUC for monitoring
    """
    data_packet = {
        'timestamp': get_timestamp(),
        'active_nodes': [
            {
                'node_id': node.id,
                'gps_position': node.gps,
                'estimated_position': node.triangulated_pos,
                'fence_status': 'inside',
                'confidence': 0.95
            }
            for node in get_active_nodes()
        ],
        'fence_breaches': get_recent_breaches(),
        'reference_nodes': get_reference_node_status(),
        'fence_health': assess_fence_health()
    }
    
    send_encrypted_to_nuc(data_packet)
```

## Performance Metrics

### Target Performance
- **Position Accuracy**: ±10 meters (GPS), ±20 meters (signal-based)
- **Validation Time**: <1 second per node
- **False Positive Rate**: <1% (legitimate nodes rejected)
- **False Negative Rate**: <0.1% (attackers accepted)
- **Update Frequency**: Every 30 seconds per node
- **Power Consumption**: <50mA additional draw

## Security Considerations

### Attack Vectors
1. **GPS Spoofing**: Mitigated by multi-constellation + signal validation
2. **Signal Replay**: Mitigated by time-of-flight + nonce
3. **Reference Node Compromise**: Mitigated by redundancy + anomaly detection
4. **Fence Boundary Probing**: Mitigated by buffer zones + logging

### Privacy Considerations
- Location data encrypted in transit
- Only relative positions shared
- Absolute coordinates limited to authorized nodes
- Regular key rotation
- Data retention limits

## Conclusion
The BELLHOP Geofencing Protocol provides robust location-based access control, creating an "invisible fence" that protects the mesh network from unauthorized remote access while maintaining usability for legitimate users.
