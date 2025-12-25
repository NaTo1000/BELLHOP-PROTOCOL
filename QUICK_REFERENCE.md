# BELLHOP Protocol - Quick Reference Card

## At a Glance

**BELLHOP** = **B**roadband **E**ncrypted **L**ow-**L**atency **H**igh-security **O**verlay **P**rotocol

A military-grade security suite for Meshtastic mesh networks.

## Core Components

### 1. Encryption
- **Algorithm**: AES-256-GCM (primary), ChaCha20-Poly1305 (fallback)
- **Key Size**: 256 bits
- **Rotation**: Every 24 hours or 1M packets
- **Authentication**: HMAC-SHA256

### 2. Frequency Hopping
- **Channels**: 50 per band
- **Hop Rate**: 100 hops/second (10ms per channel)
- **Bands**: 433 MHz / 868 MHz / 915 MHz (ISM)
- **Sync**: GPS time or network master

### 3. Geofencing
- **Methods**: GPS + RSSI triangulation + Time-of-Flight
- **Accuracy**: ±10m (GPS), ±20m (signal-based)
- **Validation**: <1 second per node
- **Anti-Spoofing**: Multi-constellation GPS verification

### 4. Initialization (6000 Packages)
1. **Discovery** (1-1000): Network topology
2. **Key Exchange** (1001-2000): Secure credentials
3. **Channel Setup** (2001-3000): Frequency sync
4. **Security Testing** (3001-4000): Validation
5. **Geofence Setup** (4001-5000): Boundaries
6. **Finalization** (5001-6000): Activation

### 5. NUC (Central Node)
- **Function**: Data aggregation and monitoring
- **Features**: ML analytics, web dashboard, alerts
- **Database**: PostgreSQL with full audit trail
- **Connection**: USB gateway or network

## Packet Format

```
[Header: 8B][Security: 32B][Payload: 0-256B][CRC: 4B]
```

**Total Overhead**: 44 bytes per packet

## Quick Commands

### Configuration
```bash
# Edit main config
nano config.yaml

# Generate keys
python3 tools/keygen.py --output /etc/bellhop/master.key

# Configure node
python3 tools/config_node.py --node-id 1 --config config.yaml
```

### Deployment
```bash
# Start NUC services
sudo systemctl start bellhop-gateway
sudo systemctl start bellhop-analytics
sudo systemctl start bellhop-dashboard

# Flash firmware
cd firmware && pio run -e tbeam -t upload

# Monitor initialization
python3 tools/monitor_init.py
```

### Testing
```bash
# Test encryption
python3 tools/test_encryption.py

# Test geofence
python3 tools/test_geofence.py

# Check network health
curl http://localhost:8080/api/network/status
```

### Troubleshooting
```bash
# Check GPS
python3 tools/check_gps.py --serial-port /dev/ttyUSB0

# Check signal strength
python3 tools/check_signal.py

# View logs
tail -f /var/log/bellhop/gateway.log

# Reset node
python3 tools/reset_node.py --node-id 1
```

## Key Parameters (config.yaml)

```yaml
# Network
network_id: "BELLHOP_NET_001"
max_nodes: 256

# Security
encryption_algorithm: "AES-256-GCM"
key_rotation_interval: 86400  # 24 hours
authentication_mode: "PSK"    # or Certificate

# Radio
frequency_band: "915MHz"      # or 433MHz, 868MHz
hop_duration: 10              # milliseconds
tx_power: 20                  # dBm

# Geofencing
geofence_enabled: true
validation_threshold: 0.6     # 60% confidence
position_accuracy: 20         # meters

# NUC
nuc_enabled: true
dashboard_port: 8080
alert_email: "admin@example.com"
```

## Performance Targets

| Metric | Target | Typical |
|--------|--------|---------|
| Latency | <100ms | 50-80ms |
| Packet Rate | 100/sec | 80-100/sec |
| Throughput | 25 KB/s | 20 KB/s |
| Range (LoS) | 2-10 km | 5-8 km |
| Battery Life | 24-48h | 30-36h |
| Hop Accuracy | ±2ms | ±1ms |

## Security Levels

### Critical (99.9%+ Protection)
- ✓ Eavesdropping
- ✓ Replay attacks
- ✓ Packet tampering

### High (95-99% Protection)
- ✓ GPS spoofing
- ✓ Node impersonation
- ✓ Geofence bypass

### Good (90%+ Protection)
- ✓ Jamming (if ≥5 channels clear)
- ✓ Man-in-the-middle

## Common Issues & Solutions

### Issue: Node won't initialize
**Solution**: Check GPS fix, verify keys, ensure correct frequency band

### Issue: Geofence false positives
**Solution**: Increase buffer zone, lower validation threshold, wait for better GPS

### Issue: High packet loss
**Solution**: Check RSSI (<-110 dBm too weak), move nodes closer, check for interference

### Issue: Dashboard not accessible
**Solution**: Check firewall (allow port 8080), verify service running, test locally

### Issue: Jamming detected
**Solution**: System auto-adapts, blacklists channels, continues on remaining frequencies

## Documentation Quick Links

| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Overview and quick start |
| [SECURITY_PROTOCOL.md](SECURITY_PROTOCOL.md) | Complete security spec |
| [FREQUENCY_HOPPING.md](FREQUENCY_HOPPING.md) | FHSS details |
| [GEOFENCING.md](GEOFENCING.md) | Invisible fence protocol |
| [PACKET_STRUCTURE.md](PACKET_STRUCTURE.md) | Packet format & auth |
| [NUC_INTEGRATION.md](NUC_INTEGRATION.md) | Central node setup |
| [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | Step-by-step guide |
| [EXAMPLES.md](EXAMPLES.md) | Code examples |
| [TECHNICAL_SUMMARY.md](TECHNICAL_SUMMARY.md) | Technical overview |
| [config.yaml](config.yaml) | Configuration reference |

## Hardware Checklist

### Mesh Node
- [ ] Meshtastic device (T-Beam, RAK4631, etc.)
- [ ] LoRa radio (SX1276/SX1262)
- [ ] GPS module with PPS
- [ ] ATECC608A secure element
- [ ] Antenna (50Ω, correct frequency)
- [ ] Power supply (3.3V, 200mA peak)

### NUC (Central)
- [ ] Intel NUC (i5+, 16GB RAM, 256GB SSD)
- [ ] Network connection (Ethernet preferred)
- [ ] USB port for gateway
- [ ] Linux OS (Ubuntu 22.04 LTS)

## Support

- **Issues**: https://github.com/NaTo1000/BELLHOP-PROTOCOL/issues
- **Discussions**: https://github.com/NaTo1000/BELLHOP-PROTOCOL/discussions
- **Documentation**: Repository docs/ folder

## License

MIT License - See LICENSE file

---

**For detailed information, consult the full documentation.**

**BELLHOP: Secure. Resilient. Connected.**
