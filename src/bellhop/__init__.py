"""
BELLHOP Protocol - Broadband Encrypted Low-Latency High-security Overlay Protocol
A comprehensive security suite for Meshtastic mesh networks.
"""

__version__ = "1.0.0"
__author__ = "BELLHOP Protocol Contributors"

from .encryption import PacketEncryptor, AESGCMCipher, ChaCha20Cipher
from .frequency_hopping import FrequencyHopper, ChannelManager
from .geofencing import GeofenceValidator, GPSValidator, RSSITriangulator
from .packet import PacketBuilder, PacketParser, PacketType
from .replay_protection import ReplayProtector
from .authentication import Authenticator, PSKAuth, CertificateAuth

__all__ = [
    'PacketEncryptor',
    'AESGCMCipher',
    'ChaCha20Cipher',
    'FrequencyHopper',
    'ChannelManager',
    'GeofenceValidator',
    'GPSValidator',
    'RSSITriangulator',
    'PacketBuilder',
    'PacketParser',
    'PacketType',
    'ReplayProtector',
    'Authenticator',
    'PSKAuth',
    'CertificateAuth',
]
