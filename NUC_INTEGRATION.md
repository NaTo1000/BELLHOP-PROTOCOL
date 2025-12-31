# NUC Integration and Data Aggregation

## Overview
The NUC (Next Unit of Computing) serves as the central command and control node for the BELLHOP mesh network. It aggregates data from all mesh nodes, performs security analysis, and provides monitoring and management capabilities.

## Architecture

### System Components
```
┌─────────────────────────────────────────────────────────────┐
│                        NUC System                            │
├─────────────────┬──────────────────┬────────────────────────┤
│  Data Ingestion │   Processing     │   Storage & Output     │
│                 │                  │                        │
│  • Mesh Gateway │   • Analysis     │   • Database          │
│  • API Server   │   • ML Engine    │   • Web Dashboard     │
│  • Log Receiver │   • Correlator   │   • Alert System      │
└─────────────────┴──────────────────┴────────────────────────┘
```

### Network Topology
```
Mesh Nodes (Field)          Gateway Node           NUC (Central)
┌──────────┐               ┌──────────┐          ┌──────────────┐
│  Node 1  │──────┐        │          │          │              │
└──────────┘      │        │          │          │   Database   │
                  ├────────│ Gateway  │──────────│   Analytics  │
┌──────────┐      │        │  Radio   │   WiFi/  │   Dashboard  │
│  Node 2  │──────┤        │   +      │   Eth    │   Alerts     │
└──────────┘      │        │   USB    │          │              │
                  │        │          │          │              │
┌──────────┐      │        │          │          └──────────────┘
│  Node N  │──────┘        └──────────┘
└──────────┘
```

## Data Flow

### 6000-Package Initialization Stream

During the initialization phase, the NUC receives and monitors all 6000 packages:

```python
class InitializationMonitor:
    def __init__(self):
        self.phases = {
            'discovery': {'range': (1, 1000), 'received': []},
            'key_exchange': {'range': (1001, 2000), 'received': []},
            'channel_setup': {'range': (2001, 3000), 'received': []},
            'security_testing': {'range': (3001, 4000), 'received': []},
            'geofence_setup': {'range': (4001, 5000), 'received': []},
            'finalization': {'range': (5001, 6000), 'received': []}
        }
    
    def process_init_packet(self, packet_num, data):
        """
        Process and log initialization packets
        """
        # Determine phase
        phase = self.get_phase_for_packet(packet_num)
        
        # Store packet data
        self.phases[phase]['received'].append({
            'packet_num': packet_num,
            'timestamp': time.time(),
            'data': data,
            'node_id': data.get('node_id'),
            'status': 'success'
        })
        
        # Log to database
        self.log_init_packet(packet_num, phase, data)
        
        # Check phase completion
        if self.is_phase_complete(phase):
            self.trigger_phase_completion(phase)
    
    def get_phase_status(self):
        """
        Return completion status of all phases
        """
        status = {}
        for phase, info in self.phases.items():
            start, end = info['range']
            expected = end - start + 1
            received = len(info['received'])
            status[phase] = {
                'expected': expected,
                'received': received,
                'complete': received >= expected,
                'percentage': (received / expected) * 100
            }
        return status
```

### Continuous Data Stream

After initialization, continuous streaming of operational data:

```python
class DataStreamHandler:
    def __init__(self, database):
        self.db = database
        self.stream_buffer = []
        self.batch_size = 100
    
    def ingest_packet(self, packet):
        """
        Ingest packet from mesh network
        """
        # Parse packet
        parsed = self.parse_packet(packet)
        
        # Add metadata
        parsed['ingestion_time'] = time.time()
        parsed['nuc_id'] = get_nuc_id()
        
        # Buffer for batch processing
        self.stream_buffer.append(parsed)
        
        # Process if buffer full
        if len(self.stream_buffer) >= self.batch_size:
            self.flush_buffer()
    
    def flush_buffer(self):
        """
        Process buffered packets
        """
        if not self.stream_buffer:
            return
        
        # Batch insert to database
        self.db.insert_many(self.stream_buffer)
        
        # Process each packet
        for packet in self.stream_buffer:
            self.analyze_packet(packet)
            self.check_alerts(packet)
            self.update_metrics(packet)
        
        # Clear buffer
        self.stream_buffer = []
```

## Data Storage

### Database Schema

#### Nodes Table
```sql
CREATE TABLE nodes (
    node_id INTEGER PRIMARY KEY,
    mac_address TEXT UNIQUE,
    first_seen TIMESTAMP,
    last_seen TIMESTAMP,
    status TEXT,  -- active, inactive, suspicious, blocked
    location_lat REAL,
    location_lon REAL,
    firmware_version TEXT,
    hardware_type TEXT,
    public_key TEXT
);
```

#### Packets Table
```sql
CREATE TABLE packets (
    packet_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    source_node INTEGER,
    dest_node INTEGER,
    packet_type TEXT,
    sequence_number INTEGER,
    rssi INTEGER,
    snr REAL,
    frequency REAL,
    encrypted BOOLEAN,
    payload_size INTEGER,
    FOREIGN KEY (source_node) REFERENCES nodes(node_id)
);
```

#### Security Events Table
```sql
CREATE TABLE security_events (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    event_type TEXT,  -- geofence_breach, replay_detected, etc.
    severity TEXT,    -- low, medium, high, critical
    node_id INTEGER,
    details JSON,
    resolved BOOLEAN,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);
```

#### Geofence Data Table
```sql
CREATE TABLE geofence_validations (
    validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    node_id INTEGER,
    gps_lat REAL,
    gps_lon REAL,
    signal_estimated_lat REAL,
    signal_estimated_lon REAL,
    inside_fence BOOLEAN,
    confidence REAL,
    validation_methods JSON,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);
```

#### Network Metrics Table
```sql
CREATE TABLE network_metrics (
    metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    total_nodes INTEGER,
    active_nodes INTEGER,
    packets_per_second REAL,
    average_rssi REAL,
    average_latency REAL,
    packet_loss_rate REAL,
    channel_usage JSON
);
```

## Analysis Engine

### Real-Time Analytics

```python
class AnalyticsEngine:
    def __init__(self, database):
        self.db = database
        self.anomaly_detector = AnomalyDetector()
        self.threat_correlator = ThreatCorrelator()
    
    def analyze_network_health(self):
        """
        Analyze overall network health
        """
        metrics = {
            'total_nodes': self.db.count_active_nodes(),
            'packet_rate': self.db.get_packet_rate(window=60),
            'average_rssi': self.db.get_average_rssi(window=300),
            'packet_loss': self.db.get_packet_loss_rate(window=300),
            'security_events': self.db.count_security_events(window=3600)
        }
        
        # Compute health score (0-100)
        health_score = self.compute_health_score(metrics)
        
        return {
            'metrics': metrics,
            'health_score': health_score,
            'status': self.get_health_status(health_score)
        }
    
    def detect_anomalies(self, node_id):
        """
        Detect anomalous behavior for a node
        """
        # Get historical data
        history = self.db.get_node_history(node_id, days=7)
        
        # Check various metrics
        anomalies = []
        
        # Unusual packet rate
        if self.anomaly_detector.is_rate_anomalous(history):
            anomalies.append('unusual_packet_rate')
        
        # Unusual location
        if self.anomaly_detector.is_location_anomalous(history):
            anomalies.append('unusual_location')
        
        # Unusual time of activity
        if self.anomaly_detector.is_timing_anomalous(history):
            anomalies.append('unusual_activity_time')
        
        # Unusual destinations
        if self.anomaly_detector.is_destinations_anomalous(history):
            anomalies.append('unusual_destinations')
        
        return anomalies
```

### Machine Learning

```python
class AnomalyDetector:
    def __init__(self):
        self.models = {
            'packet_rate': IsolationForest(),
            'location': DBSCAN(),
            'behavior': OneClassSVM()
        }
        self.trained = False
    
    def train(self, historical_data):
        """
        Train ML models on historical data
        """
        # Extract features
        features = self.extract_features(historical_data)
        
        # Train each model
        for model_name, model in self.models.items():
            model_features = features[model_name]
            model.fit(model_features)
        
        self.trained = True
    
    def predict(self, node_data):
        """
        Predict if node behavior is anomalous
        """
        if not self.trained:
            return False, 0.0
        
        features = self.extract_features([node_data])
        anomaly_scores = []
        
        for model_name, model in self.models.items():
            score = model.predict(features[model_name])
            anomaly_scores.append(score)
        
        # Aggregate scores
        is_anomalous = sum(anomaly_scores) / len(anomaly_scores) > 0.5
        confidence = abs(sum(anomaly_scores) / len(anomaly_scores))
        
        return is_anomalous, confidence
```

## Monitoring Dashboard

### Web Interface

```python
from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    """
    Main dashboard view
    """
    return render_template('dashboard.html')

@app.route('/api/network/status')
def network_status():
    """
    Get current network status
    """
    analytics = AnalyticsEngine(database)
    status = analytics.analyze_network_health()
    return jsonify(status)

@app.route('/api/nodes/active')
def active_nodes():
    """
    Get list of active nodes
    """
    nodes = database.get_active_nodes()
    return jsonify([{
        'id': n.node_id,
        'location': {'lat': n.lat, 'lon': n.lon},
        'status': n.status,
        'last_seen': n.last_seen
    } for n in nodes])

@app.route('/api/security/events')
def security_events():
    """
    Get recent security events
    """
    events = database.get_security_events(limit=100)
    return jsonify([{
        'timestamp': e.timestamp,
        'type': e.event_type,
        'severity': e.severity,
        'node_id': e.node_id,
        'details': e.details
    } for e in events])

@app.route('/api/geofence/status')
def geofence_status():
    """
    Get geofence status
    """
    status = database.get_geofence_status()
    return jsonify({
        'boundary': status.coordinates,
        'nodes_inside': status.nodes_inside,
        'nodes_outside': status.nodes_outside,
        'recent_breaches': status.recent_breaches
    })
```

### Dashboard Features

1. **Real-Time Map**
   - Display all nodes on map
   - Show geofence boundary
   - Color-code by status
   - Update every 5 seconds

2. **Network Metrics**
   - Packet rate graph
   - Node count over time
   - Signal strength heatmap
   - Channel utilization

3. **Security Monitoring**
   - Recent security events
   - Threat level indicator
   - Anomaly alerts
   - Geofence breaches

4. **Node Management**
   - List all nodes
   - Individual node details
   - Block/unblock nodes
   - View node history

## Alert System

### Alert Rules

```python
class AlertManager:
    def __init__(self):
        self.rules = [
            {
                'name': 'geofence_breach',
                'condition': lambda e: e['type'] == 'geofence_breach',
                'severity': 'high',
                'action': self.alert_geofence_breach
            },
            {
                'name': 'replay_attack',
                'condition': lambda e: e['type'] == 'replay_detected',
                'severity': 'critical',
                'action': self.alert_replay_attack
            },
            {
                'name': 'node_offline',
                'condition': lambda e: e['type'] == 'node_timeout',
                'severity': 'medium',
                'action': self.alert_node_offline
            }
        ]
    
    def process_event(self, event):
        """
        Check event against alert rules
        """
        for rule in self.rules:
            if rule['condition'](event):
                self.trigger_alert(rule, event)
    
    def trigger_alert(self, rule, event):
        """
        Trigger alert through multiple channels
        """
        alert = {
            'timestamp': time.time(),
            'rule': rule['name'],
            'severity': rule['severity'],
            'event': event
        }
        
        # Log to database
        self.log_alert(alert)
        
        # Send notifications
        self.send_email_alert(alert)
        self.send_sms_alert(alert)
        self.update_dashboard(alert)
        
        # Execute rule action
        rule['action'](event)
```

### Notification Channels

```python
def send_email_alert(alert):
    """
    Send email notification
    """
    import smtplib
    from email.mime.text import MIMEText
    
    msg = MIMEText(f"""
    BELLHOP Security Alert
    
    Time: {alert['timestamp']}
    Severity: {alert['severity']}
    Rule: {alert['rule']}
    
    Details:
    {json.dumps(alert['event'], indent=2)}
    """)
    
    msg['Subject'] = f"[{alert['severity'].upper()}] BELLHOP Alert"
    msg['From'] = 'bellhop@security.local'
    msg['To'] = 'admin@example.com'
    
    # Send via SMTP
    # (implementation details)

def send_sms_alert(alert):
    """
    Send SMS notification for critical alerts
    """
    if alert['severity'] == 'critical':
        message = f"BELLHOP CRITICAL: {alert['rule']} - Check dashboard"
        # Send via SMS gateway
        # (implementation details)
```

## Performance Optimization

### Data Pipeline

```python
class DataPipeline:
    def __init__(self):
        self.ingestion_queue = queue.Queue(maxsize=10000)
        self.processing_pool = ThreadPoolExecutor(max_workers=4)
        self.batch_size = 100
    
    def start(self):
        """
        Start pipeline workers
        """
        # Start ingestion worker
        threading.Thread(target=self.ingestion_worker).start()
        
        # Start processing workers
        for _ in range(4):
            threading.Thread(target=self.processing_worker).start()
    
    def ingestion_worker(self):
        """
        Receive packets from gateway
        """
        while True:
            packet = receive_from_gateway()
            self.ingestion_queue.put(packet)
    
    def processing_worker(self):
        """
        Process packets from queue
        """
        batch = []
        while True:
            try:
                packet = self.ingestion_queue.get(timeout=1)
                batch.append(packet)
                
                if len(batch) >= self.batch_size:
                    self.process_batch(batch)
                    batch = []
            except queue.Empty:
                if batch:
                    self.process_batch(batch)
                    batch = []
```

## Hardware Specifications

### Recommended NUC Configuration
- **CPU**: Intel Core i5 or better (4+ cores)
- **RAM**: 16GB minimum
- **Storage**: 256GB SSD minimum
- **Network**: Gigabit Ethernet
- **USB**: USB 3.0 for gateway connection
- **OS**: Linux (Ubuntu 22.04 LTS recommended)

### Gateway Hardware
- Meshtastic T-Beam or similar
- USB connection to NUC
- External antenna recommended
- GPS module for time sync

## Deployment

### Installation
```bash
# Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip postgresql

# Install Python packages
pip3 install flask sqlalchemy cryptography numpy scikit-learn

# Setup database
sudo -u postgres createdb bellhop
python3 setup_database.py

# Start services
systemctl start bellhop-gateway
systemctl start bellhop-analytics
systemctl start bellhop-dashboard
```

### Configuration
```yaml
# config.yaml
nuc:
  node_id: 0xFFFF
  network_id: "BELLHOP_NET_001"
  
gateway:
  serial_port: "/dev/ttyUSB0"
  baud_rate: 115200
  
database:
  host: "localhost"
  port: 5432
  name: "bellhop"
  user: "bellhop"
  
dashboard:
  host: "0.0.0.0"
  port: 8080
  
alerts:
  email:
    enabled: true
    smtp_server: "smtp.example.com"
    recipients: ["admin@example.com"]
  sms:
    enabled: false
```

## Conclusion
The NUC integration provides centralized monitoring, analysis, and management for the BELLHOP mesh network, enabling comprehensive security oversight and rapid response to threats.
