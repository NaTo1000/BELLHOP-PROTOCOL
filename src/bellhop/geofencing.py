"""
Geofencing module for BELLHOP protocol.
Implements location-based access control (invisible fence).
"""

import math
from typing import List, Dict, Tuple, Optional


class GPSPosition:
    """Represents a GPS position."""
    
    def __init__(self, lat: float, lon: float, altitude: Optional[float] = None):
        """
        Initialize GPS position.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            altitude: Altitude in meters (optional)
        """
        self.lat = lat
        self.lon = lon
        self.altitude = altitude
    
    def __repr__(self):
        alt_str = f", alt={self.altitude:.1f}m" if self.altitude is not None else ""
        return f"GPSPosition({self.lat:.6f}, {self.lon:.6f}{alt_str})"


class GeofenceBoundary:
    """Represents a geofence boundary."""
    
    def __init__(self, coordinates: List[GPSPosition], 
                 altitude_min: float = 0.0, altitude_max: float = 500.0,
                 buffer_zone: float = 50.0):
        """
        Initialize geofence boundary.
        
        Args:
            coordinates: List of GPS positions defining polygon vertices
            altitude_min: Minimum altitude in meters
            altitude_max: Maximum altitude in meters
            buffer_zone: Buffer zone in meters for warnings
        """
        if len(coordinates) < 3:
            raise ValueError("Boundary must have at least 3 vertices")
        
        self.coordinates = coordinates
        self.altitude_min = altitude_min
        self.altitude_max = altitude_max
        self.buffer_zone = buffer_zone


class GPSValidator:
    """Validates GPS positions against geofence boundaries."""
    
    @staticmethod
    def point_in_polygon(point: GPSPosition, polygon: List[GPSPosition]) -> bool:
        """
        Check if point is inside polygon using ray casting algorithm.
        
        Args:
            point: GPS position to test
            polygon: List of GPS positions defining polygon
        
        Returns:
            True if point is inside polygon
        """
        x, y = point.lon, point.lat
        n = len(polygon)
        inside = False
        
        p1x, p1y = polygon[0].lon, polygon[0].lat
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n].lon, polygon[i % n].lat
            
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            
            p1x, p1y = p2x, p2y
        
        return inside
    
    @staticmethod
    def calculate_distance(pos1: GPSPosition, pos2: GPSPosition) -> float:
        """
        Calculate distance between two GPS positions using Haversine formula.
        
        Args:
            pos1: First position
            pos2: Second position
        
        Returns:
            Distance in meters
        """
        R = 6371000  # Earth radius in meters
        
        lat1 = math.radians(pos1.lat)
        lat2 = math.radians(pos2.lat)
        dlat = math.radians(pos2.lat - pos1.lat)
        dlon = math.radians(pos2.lon - pos1.lon)
        
        a = math.sin(dlat/2)**2 + \
            math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    @staticmethod
    def distance_to_boundary(point: GPSPosition, boundary: List[GPSPosition]) -> float:
        """
        Calculate minimum distance from point to boundary.
        
        Args:
            point: GPS position
            boundary: List of GPS positions defining boundary
        
        Returns:
            Minimum distance to boundary in meters
        """
        min_distance = float('inf')
        
        for i in range(len(boundary)):
            vertex = boundary[i]
            distance = GPSValidator.calculate_distance(point, vertex)
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def validate(self, position: GPSPosition, boundary: GeofenceBoundary) -> Tuple[bool, str, float]:
        """
        Validate GPS position against boundary.
        
        Args:
            position: GPS position to validate
            boundary: Geofence boundary
        
        Returns:
            Tuple of (is_valid, reason, confidence)
        """
        # Check 2D position
        inside = self.point_in_polygon(position, boundary.coordinates)
        
        if not inside:
            distance = self.distance_to_boundary(position, boundary.coordinates)
            return False, f"Outside fence by {distance:.1f}m", 0.95
        
        # Check altitude if available
        if position.altitude is not None:
            if position.altitude < boundary.altitude_min:
                return False, f"Below minimum altitude ({position.altitude:.1f}m < {boundary.altitude_min:.1f}m)", 0.90
            if position.altitude > boundary.altitude_max:
                return False, f"Above maximum altitude ({position.altitude:.1f}m > {boundary.altitude_max:.1f}m)", 0.90
        
        # Check if in buffer zone (warning)
        distance = self.distance_to_boundary(position, boundary.coordinates)
        if distance < boundary.buffer_zone:
            return True, f"In buffer zone ({distance:.1f}m from edge)", 0.70
        
        return True, "Position valid", 0.95


class RSSITriangulator:
    """Estimates position using RSSI trilateration."""
    
    def __init__(self, reference_nodes: List[Tuple[GPSPosition, float]]):
        """
        Initialize RSSI triangulator.
        
        Args:
            reference_nodes: List of (position, tx_power) tuples for reference nodes
        """
        if len(reference_nodes) < 3:
            raise ValueError("Need at least 3 reference nodes for trilateration")
        
        self.reference_nodes = reference_nodes
    
    @staticmethod
    def rssi_to_distance(rssi: float, tx_power: float = 20.0, 
                        path_loss_exponent: float = 2.5) -> float:
        """
        Convert RSSI to distance estimate.
        
        Args:
            rssi: Received signal strength in dBm
            tx_power: Transmit power in dBm
            path_loss_exponent: Environment-dependent (2-4, typical 2.5)
        
        Returns:
            Estimated distance in meters
        """
        if rssi == 0 or rssi > tx_power:
            return -1.0
        
        ratio = (tx_power - rssi) / (10 * path_loss_exponent)
        distance = math.pow(10, ratio)
        return distance
    
    def estimate_position(self, rssi_measurements: List[Tuple[int, float]]) -> Optional[GPSPosition]:
        """
        Estimate position using RSSI trilateration.
        
        Args:
            rssi_measurements: List of (node_index, rssi) tuples
        
        Returns:
            Estimated GPS position or None if insufficient data
        """
        if len(rssi_measurements) < 3:
            return None
        
        # Convert RSSI to distances
        distances = []
        positions = []
        
        for node_idx, rssi in rssi_measurements[:3]:  # Use first 3 nodes
            if node_idx >= len(self.reference_nodes):
                continue
            
            ref_pos, tx_power = self.reference_nodes[node_idx]
            distance = self.rssi_to_distance(rssi, tx_power)
            
            if distance > 0:
                distances.append(distance)
                positions.append(ref_pos)
        
        if len(distances) < 3:
            return None
        
        # Simplified trilateration (centroid weighted by inverse distance)
        total_weight = sum(1.0 / d for d in distances)
        
        est_lat = sum(pos.lat / dist for pos, dist in zip(positions, distances)) / total_weight
        est_lon = sum(pos.lon / dist for pos, dist in zip(positions, distances)) / total_weight
        
        return GPSPosition(est_lat, est_lon)


class GeofenceValidator:
    """Main geofence validation engine."""
    
    def __init__(self, boundary: GeofenceBoundary,
                 reference_nodes: Optional[List[Tuple[GPSPosition, float]]] = None):
        """
        Initialize geofence validator.
        
        Args:
            boundary: Geofence boundary definition
            reference_nodes: Optional reference nodes for RSSI-based validation
        """
        self.boundary = boundary
        self.gps_validator = GPSValidator()
        
        if reference_nodes and len(reference_nodes) >= 3:
            self.rssi_triangulator = RSSITriangulator(reference_nodes)
        else:
            self.rssi_triangulator = None
    
    def validate_gps(self, position: GPSPosition) -> Tuple[bool, str, float]:
        """
        Validate using GPS position only.
        
        Args:
            position: GPS position to validate
        
        Returns:
            Tuple of (is_valid, reason, confidence)
        """
        return self.gps_validator.validate(position, self.boundary)
    
    def validate_rssi(self, rssi_measurements: List[Tuple[int, float]]) -> Tuple[bool, str, float]:
        """
        Validate using RSSI measurements only.
        
        Args:
            rssi_measurements: List of (node_index, rssi) tuples
        
        Returns:
            Tuple of (is_valid, reason, confidence)
        """
        if not self.rssi_triangulator:
            return False, "No reference nodes configured", 0.0
        
        estimated_pos = self.rssi_triangulator.estimate_position(rssi_measurements)
        
        if not estimated_pos:
            return False, "Insufficient RSSI data", 0.0
        
        inside = self.gps_validator.point_in_polygon(estimated_pos, self.boundary.coordinates)
        
        if inside:
            return True, f"RSSI-based position valid", 0.70
        else:
            return False, f"RSSI-based position outside fence", 0.70
    
    def validate_hybrid(self, gps_position: Optional[GPSPosition],
                       rssi_measurements: Optional[List[Tuple[int, float]]]) -> Tuple[bool, float, Dict]:
        """
        Validate using hybrid approach (GPS + RSSI).
        
        Args:
            gps_position: GPS position (optional)
            rssi_measurements: RSSI measurements (optional)
        
        Returns:
            Tuple of (is_authorized, confidence, details)
        """
        checks = []
        
        # GPS validation
        if gps_position:
            gps_valid, reason, confidence = self.validate_gps(gps_position)
            checks.append({
                'method': 'GPS',
                'valid': gps_valid,
                'confidence': confidence,
                'reason': reason
            })
        
        # RSSI validation
        if rssi_measurements and self.rssi_triangulator:
            rssi_valid, reason, confidence = self.validate_rssi(rssi_measurements)
            checks.append({
                'method': 'RSSI',
                'valid': rssi_valid,
                'confidence': confidence,
                'reason': reason
            })
        
        if not checks:
            return False, 0.0, {'error': 'No validation data provided'}
        
        # Compute weighted decision
        total_confidence = sum(c['confidence'] for c in checks)
        valid_confidence = sum(c['confidence'] for c in checks if c['valid'])
        
        if total_confidence == 0:
            overall_confidence = 0.0
            authorized = False
        else:
            overall_confidence = valid_confidence / total_confidence
            authorized = overall_confidence > 0.6  # 60% threshold
        
        return authorized, overall_confidence, {'checks': checks}


# Example usage
if __name__ == "__main__":
    # Define geofence boundary (square around San Francisco)
    boundary = GeofenceBoundary([
        GPSPosition(37.7749, -122.4194),
        GPSPosition(37.7750, -122.4180),
        GPSPosition(37.7735, -122.4175),
        GPSPosition(37.7730, -122.4190)
    ], altitude_min=0, altitude_max=500, buffer_zone=50)
    
    # Define reference nodes for RSSI
    reference_nodes = [
        (GPSPosition(37.7749, -122.4194), 20.0),  # Node 0
        (GPSPosition(37.7750, -122.4180), 20.0),  # Node 1
        (GPSPosition(37.7735, -122.4175), 20.0),  # Node 2
    ]
    
    # Create validator
    validator = GeofenceValidator(boundary, reference_nodes)
    
    # Test GPS validation
    print("GPS Validation Tests:")
    print("-" * 50)
    
    # Test point inside fence
    test_pos_inside = GPSPosition(37.7740, -122.4185, altitude=100)
    valid, reason, confidence = validator.validate_gps(test_pos_inside)
    print(f"Inside: {valid} - {reason} (confidence: {confidence:.2f})")
    
    # Test point outside fence
    test_pos_outside = GPSPosition(37.7800, -122.4200, altitude=100)
    valid, reason, confidence = validator.validate_gps(test_pos_outside)
    print(f"Outside: {valid} - {reason} (confidence: {confidence:.2f})")
    
    # Test RSSI validation
    print("\nRSSI Validation Tests:")
    print("-" * 50)
    
    rssi_measurements = [
        (0, -75.0),  # Strong signal from node 0
        (1, -80.0),  # Medium signal from node 1
        (2, -85.0),  # Weaker signal from node 2
    ]
    
    valid, reason, confidence = validator.validate_rssi(rssi_measurements)
    print(f"RSSI-based: {valid} - {reason} (confidence: {confidence:.2f})")
    
    # Test hybrid validation
    print("\nHybrid Validation Tests:")
    print("-" * 50)
    
    authorized, confidence, details = validator.validate_hybrid(
        test_pos_inside,
        rssi_measurements
    )
    
    print(f"Authorized: {authorized} (confidence: {confidence:.2f})")
    for check in details['checks']:
        print(f"  - {check['method']}: {check['valid']} ({check['confidence']:.2f}) - {check['reason']}")
    
    print("\n✓ Geofencing operational!")
