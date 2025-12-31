# BELLHOP Implementation Guide

## Overview
This guide provides step-by-step instructions for implementing the BELLHOP security protocol on Meshtastic-compatible hardware.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Hardware Setup](#hardware-setup)
3. [Software Installation](#software-installation)
4. [Configuration](#configuration)
5. [Initialization](#initialization)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### Hardware Requirements
- **Mesh Nodes**: 
  - Meshtastic-compatible device (e.g., T-Beam, RAK4631)
  - ESP32 or nRF52840 microcontroller
  - LoRa radio module (SX1276, SX1262)
  - GPS module (NEO-6M or better)
  - Cryptographic co-processor (ATECC608A recommended)
  
- **NUC (Central Node)**:
  - Intel NUC or equivalent
  - 4+ CPU cores
  - 16GB RAM minimum
  - 256GB SSD
  - USB 3.0 port
  - Network connectivity

### Software Requirements
- **Mesh Nodes**:
  - PlatformIO or Arduino IDE
  - ESP32/nRF52 toolchain
  - Meshtastic firmware base
  
- **NUC**:
  - Linux (Ubuntu 22.04 LTS recommended)
  - Python 3.9+
  - PostgreSQL 14+
  - Git

## Hardware Setup

### Step 1: Assemble Mesh Node

```
1. Connect LoRa module to microcontroller
   - SPI interface (MISO, MOSI, SCK, CS)
   - DIO0 (interrupt)
   - RESET pin

2. Connect GPS module
   - UART interface (TX, RX)
   - PPS (pulse-per-second) for time sync

3. Connect secure element (ATECC608A)
   - I2C interface (SDA, SCL)
   - Address: 0x60

4. Connect power supply
   - 3.3V regulated
   - Battery + solar panel (optional)

5. Connect antenna
   - Impedance matched (50Ω)
   - Appropriate frequency (433/868/915 MHz)
```

### Step 2: Setup NUC

```bash
# Connect gateway node to NUC via USB
# Identify serial port
ls -l /dev/ttyUSB*

# Should show something like /dev/ttyUSB0
```

### Step 3: Network Configuration

```
Connect NUC to network:
1. Ethernet (preferred) or WiFi
2. Static IP recommended for dashboard access
3. Configure firewall rules for dashboard port (8080)
```

## Software Installation

### Mesh Node Firmware

#### Step 1: Clone Repository
```bash
git clone https://github.com/NaTo1000/BELLHOP-PROTOCOL.git
cd BELLHOP-PROTOCOL/firmware
```

#### Step 2: Install PlatformIO
```bash
pip install platformio
```

#### Step 3: Configure Hardware
Edit `platformio.ini`:
```ini
[env:tbeam]
platform = espressif32
board = t-beam
framework = arduino

; Build flags
build_flags = 
    -DBELLHOP_PROTOCOL=1
    -DFREQUENCY_BAND=915
    -DSECURE_ELEMENT=ATECC608A

; Libraries
lib_deps = 
    meshtastic/RadioLib
    adafruit/Adafruit ATECCX08A
    bblanchon/ArduinoJson
```

#### Step 4: Build and Flash
```bash
# Build firmware
pio run -e tbeam

# Flash to device
pio run -e tbeam -t upload

# Monitor serial output
pio device monitor -b 115200
```

### NUC Software

#### Step 1: System Update
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

#### Step 2: Install Dependencies
```bash
# Python and development tools
sudo apt-get install -y python3 python3-pip python3-venv git

# Database
sudo apt-get install -y postgresql postgresql-contrib

# System libraries
sudo apt-get install -y libpq-dev build-essential
```

#### Step 3: Clone and Setup
```bash
# Clone repository
git clone https://github.com/NaTo1000/BELLHOP-PROTOCOL.git
cd BELLHOP-PROTOCOL/nuc-software

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

#### Step 4: Database Setup
```bash
# Create database user
sudo -u postgres createuser bellhop

# Create database
sudo -u postgres createdb bellhop

# Set password
sudo -u postgres psql -c "ALTER USER bellhop WITH PASSWORD 'your_password';"

# Initialize schema
python3 setup_database.py
```

## Configuration

### Step 1: Generate Encryption Keys
```bash
# Generate network master key
python3 tools/keygen.py --output /etc/bellhop/master.key

# Generate node keys
python3 tools/keygen.py --node-id 1 --output /etc/bellhop/nodes/node1.key

# Store keys securely
chmod 600 /etc/bellhop/*.key
```

### Step 2: Configure Network
Edit `config.yaml`:
```yaml
network:
  network_id: "YOUR_UNIQUE_NETWORK_ID"
  network_name: "Your Network Name"

security:
  authentication:
    mode: "PSK"
    psk: "your_secure_password_at_least_32_chars"

geofencing:
  enabled: true
  boundary:
    coordinates:
      - lat: YOUR_LAT_1
        lon: YOUR_LON_1
      - lat: YOUR_LAT_2
        lon: YOUR_LON_2
      # Add more vertices for your boundary
```

### Step 3: Configure Each Node
```bash
# Flash configuration to node
python3 tools/config_node.py \
  --serial-port /dev/ttyUSB0 \
  --node-id 1 \
  --config config.yaml
```

## Initialization

### Step 1: Start Gateway
```bash
# On NUC, start gateway service
sudo systemctl start bellhop-gateway

# Check status
sudo systemctl status bellhop-gateway
```

### Step 2: Initialize First Node
```bash
# Power on first node
# It will automatically start initialization sequence

# Monitor on NUC
tail -f /var/log/bellhop/gateway.log

# You should see:
# [INFO] Node 0x0001 starting initialization
# [INFO] Phase 1: Discovery (0/1000 packets)
# ...
```

### Step 3: Monitor 6000-Package Sequence
```bash
# Use monitoring script
python3 tools/monitor_init.py

# Expected output:
# ========================================
# BELLHOP Initialization Monitor
# ========================================
# Phase 1 - Discovery:        100% (1000/1000)
# Phase 2 - Key Exchange:     100% (1000/1000)
# Phase 3 - Channel Setup:    100% (1000/1000)
# Phase 4 - Security Testing: 100% (1000/1000)
# Phase 5 - Geofence Setup:   100% (1000/1000)
# Phase 6 - Finalization:     100% (1000/1000)
# 
# Initialization complete!
# Node 0x0001 is now operational.
```

### Step 4: Add More Nodes
```bash
# Power on additional nodes one at a time
# Each will go through initialization sequence
# Wait for completion before adding next node
```

## Testing

### Test 1: Basic Connectivity
```bash
# Send test packet from node to NUC
python3 tools/send_test_packet.py --node-id 1

# Verify reception on NUC
# Check dashboard or logs
```

### Test 2: Encryption
```bash
# Verify encryption is working
python3 tools/test_encryption.py

# Expected output:
# [PASS] Encryption algorithm: AES-256-GCM
# [PASS] Key size: 256 bits
# [PASS] IV uniqueness verified
# [PASS] Authentication tag valid
```

### Test 3: Frequency Hopping
```bash
# Monitor frequency hopping
python3 tools/monitor_hopping.py --duration 60

# Should show hopping across all 50 channels
# Verify timing accuracy
```

### Test 4: Geofencing
```bash
# Test geofence validation
python3 tools/test_geofence.py

# Try with node inside fence
# Expected: PASS

# Simulate node outside fence (change GPS coords)
# Expected: REJECT + Alert
```

### Test 5: Anti-Jamming
```bash
# Simulate jamming on specific channels
python3 tools/simulate_jamming.py --channels 10,11,12

# Network should:
# 1. Detect jammed channels
# 2. Blacklist them
# 3. Continue operating on remaining channels
```

### Test 6: NUC Integration
```bash
# Verify data streaming to NUC
python3 tools/verify_nuc_stream.py

# Check:
# - Packets received in database
# - Dashboard updates
# - Analytics working
# - Alerts triggering
```

## Deployment

### Step 1: Install Systemd Services
```bash
# Copy service files
sudo cp systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable bellhop-gateway
sudo systemctl enable bellhop-analytics
sudo systemctl enable bellhop-dashboard

# Start services
sudo systemctl start bellhop-gateway
sudo systemctl start bellhop-analytics
sudo systemctl start bellhop-dashboard
```

### Step 2: Configure Startup
```bash
# Ensure services start on boot
sudo systemctl enable postgresql
sudo systemctl enable bellhop-gateway
sudo systemctl enable bellhop-analytics
sudo systemctl enable bellhop-dashboard
```

### Step 3: Setup Monitoring
```bash
# Install monitoring tools
pip install prometheus-client

# Start metrics exporter
python3 tools/metrics_exporter.py &

# Configure alerts
cp alerts/alert_rules.yaml /etc/bellhop/
```

### Step 4: Access Dashboard
```
Open browser to: http://NUC_IP:8080

Default credentials (CHANGE THESE):
Username: admin
Password: bellhop123

You should see:
- Network map with all nodes
- Real-time metrics
- Security events
- Geofence status
```

## Troubleshooting

### Issue: Node Won't Initialize
**Symptoms**: Stuck in initialization, not progressing through phases

**Solutions**:
```bash
# Check GPS signal
# GPS must have fix for time synchronization
python3 tools/check_gps.py --serial-port /dev/ttyUSB0

# Check encryption keys
# Verify keys are properly provisioned
python3 tools/verify_keys.py --node-id 1

# Check radio configuration
# Ensure frequency band matches region
python3 tools/check_radio.py --node-id 1

# Reset and retry
python3 tools/reset_node.py --node-id 1
```

### Issue: Geofence False Positives
**Symptoms**: Valid nodes rejected, located inside fence

**Solutions**:
```bash
# Check GPS accuracy
# Poor GPS signal can cause position errors
# Solution: Wait for better GPS fix (more satellites)

# Adjust validation threshold
# Edit config.yaml:
geofencing:
  validation_threshold: 0.5  # Lower from 0.6

# Increase buffer zone
geofencing:
  boundary:
    buffer_zone: 100  # Increase from 50 meters

# Verify reference node positions
# Ensure reference nodes are correctly positioned
python3 tools/verify_reference_nodes.py
```

### Issue: High Packet Loss
**Symptoms**: Many packets not reaching destination

**Solutions**:
```bash
# Check RSSI levels
python3 tools/check_signal.py

# If RSSI < -110 dBm:
# - Move nodes closer
# - Increase TX power
# - Use better antenna
# - Check for obstacles

# Check for interference
python3 tools/spectrum_scan.py

# If interference detected:
# - Enable adaptive channel selection
# - Blacklist affected channels
# - Switch frequency band if available
```

### Issue: NUC Not Receiving Data
**Symptoms**: Dashboard shows no data, nodes appear offline

**Solutions**:
```bash
# Check gateway connection
lsusb  # Should show gateway device
ls -l /dev/ttyUSB*  # Should show serial port

# Check gateway service
sudo systemctl status bellhop-gateway

# Check logs
tail -f /var/log/bellhop/gateway.log

# Test serial communication
python3 tools/test_serial.py --port /dev/ttyUSB0

# Verify database connection
python3 tools/test_db.py

# Check firewall
sudo ufw status
# Ensure port 8080 is open for dashboard
```

### Issue: Dashboard Not Loading
**Symptoms**: Cannot access web interface

**Solutions**:
```bash
# Check dashboard service
sudo systemctl status bellhop-dashboard

# Check logs
tail -f /var/log/bellhop/dashboard.log

# Verify port binding
netstat -tlnp | grep 8080

# Test locally
curl http://localhost:8080

# Check firewall
sudo ufw allow 8080/tcp
```

## Performance Tuning

### Optimize for Range
```yaml
# config.yaml
radio:
  spreading_factor: 12  # Increase from 7
  coding_rate: "4/8"    # Increase from 4/5
  bandwidth: 125        # Keep at 125 kHz

frequency_hopping:
  hop_duration: 50      # Slow down to 20 hops/sec
```

### Optimize for Throughput
```yaml
# config.yaml
radio:
  spreading_factor: 7   # Decrease to 7
  coding_rate: "4/5"    # Keep at 4/5
  bandwidth: 250        # Increase to 250 kHz

frequency_hopping:
  hop_duration: 5       # Speed up to 200 hops/sec
```

### Optimize for Battery Life
```yaml
# config.yaml
radio:
  tx_power: 10          # Reduce from 20 dBm
  adaptive_power: true  # Enable power adaptation

frequency_hopping:
  hop_duration: 50      # Slow down to save power
```

## Maintenance

### Regular Tasks

**Daily**:
- Check dashboard for alerts
- Verify all nodes online
- Review security events

**Weekly**:
- Database vacuum
- Log rotation
- Backup configuration

**Monthly**:
- Update firmware if available
- Review and update geofence boundaries
- Test disaster recovery procedures
- Rotate encryption keys

### Backup Procedures
```bash
# Backup database
pg_dump bellhop > backup_$(date +%Y%m%d).sql

# Backup configuration
tar -czf config_backup_$(date +%Y%m%d).tar.gz /etc/bellhop/

# Backup logs
tar -czf logs_backup_$(date +%Y%m%d).tar.gz /var/log/bellhop/
```

### Update Firmware
```bash
# Backup current firmware
cp .pio/build/tbeam/firmware.bin firmware_backup.bin

# Pull latest changes
git pull origin main

# Build new firmware
pio run -e tbeam

# Flash to nodes (one at a time)
pio run -e tbeam -t upload --upload-port /dev/ttyUSB0
```

## Support

For additional help:
- Documentation: https://github.com/NaTo1000/BELLHOP-PROTOCOL
- Issues: https://github.com/NaTo1000/BELLHOP-PROTOCOL/issues
- Discussions: https://github.com/NaTo1000/BELLHOP-PROTOCOL/discussions

## Conclusion

You now have a fully functional BELLHOP secure mesh network! The system provides:
- ✓ End-to-end encryption
- ✓ Anti-jamming through frequency hopping
- ✓ Geofencing for location-based access control
- ✓ Central monitoring via NUC
- ✓ Real-time security alerts
- ✓ Comprehensive network analytics

Enjoy your secure mesh network!
