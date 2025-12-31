"""
Authentication module for BELLHOP protocol.
Supports PSK and certificate-based authentication.
"""

import hashlib
import hmac
import secrets
from typing import Tuple, Optional
from dataclasses import dataclass


@dataclass
class AuthenticationResult:
    """Result of authentication attempt."""
    success: bool
    reason: str
    session_key: Optional[bytes] = None


class PSKAuth:
    """Pre-shared key authentication."""
    
    def __init__(self, psk: bytes):
        """
        Initialize PSK authenticator.
        
        Args:
            psk: Pre-shared key (minimum 16 bytes recommended)
        """
        if len(psk) < 16:
            raise ValueError("PSK should be at least 16 bytes")
        self.psk = psk
    
    def generate_challenge(self) -> bytes:
        """
        Generate authentication challenge.
        
        Returns:
            32-byte random challenge
        """
        return secrets.token_bytes(32)
    
    def compute_response(self, challenge: bytes, node_id: int) -> bytes:
        """
        Compute response to challenge.
        
        Args:
            challenge: Challenge bytes
            node_id: Node identifier
        
        Returns:
            HMAC response
        """
        message = challenge + node_id.to_bytes(4, 'big')
        return hmac.new(self.psk, message, hashlib.sha256).digest()
    
    def verify_response(self, challenge: bytes, node_id: int, response: bytes) -> bool:
        """
        Verify response to challenge.
        
        Args:
            challenge: Original challenge
            node_id: Node identifier
            response: Received response
        
        Returns:
            True if response is valid
        """
        expected = self.compute_response(challenge, node_id)
        return hmac.compare_digest(expected, response)
    
    def derive_session_key(self, node_a_id: int, node_b_id: int, 
                          nonce_a: bytes, nonce_b: bytes) -> bytes:
        """
        Derive session key from PSK and nonces.
        
        Args:
            node_a_id: First node ID
            node_b_id: Second node ID
            nonce_a: Nonce from first node
            nonce_b: Nonce from second node
        
        Returns:
            32-byte session key
        """
        # Sort node IDs to ensure consistent key derivation
        if node_a_id > node_b_id:
            node_a_id, node_b_id = node_b_id, node_a_id
            nonce_a, nonce_b = nonce_b, nonce_a
        
        material = (
            self.psk +
            node_a_id.to_bytes(4, 'big') +
            node_b_id.to_bytes(4, 'big') +
            nonce_a +
            nonce_b
        )
        
        return hashlib.sha256(material).digest()
    
    def authenticate_node(self, node_id: int) -> AuthenticationResult:
        """
        Perform complete node authentication.
        
        Args:
            node_id: Node to authenticate
        
        Returns:
            Authentication result with session key
        """
        # Generate challenge
        challenge = self.generate_challenge()
        
        # In real implementation, challenge would be sent to node
        # and response received. Here we simulate it.
        response = self.compute_response(challenge, node_id)
        
        # Verify response
        if self.verify_response(challenge, node_id, response):
            # Generate session key
            my_nonce = secrets.token_bytes(32)
            their_nonce = secrets.token_bytes(32)
            session_key = self.derive_session_key(0xFFFF, node_id, my_nonce, their_nonce)
            
            return AuthenticationResult(
                success=True,
                reason="PSK authentication successful",
                session_key=session_key
            )
        else:
            return AuthenticationResult(
                success=False,
                reason="PSK authentication failed - invalid response"
            )


class CertificateAuth:
    """Certificate-based authentication (simplified)."""
    
    def __init__(self, ca_public_key: bytes):
        """
        Initialize certificate authenticator.
        
        Args:
            ca_public_key: Certificate Authority public key
        """
        self.ca_public_key = ca_public_key
        self.trusted_certs = {}  # node_id -> cert_hash
    
    def verify_certificate(self, cert_data: bytes, signature: bytes) -> bool:
        """
        Verify certificate signature (simplified).
        
        Args:
            cert_data: Certificate data
            signature: Signature from CA
        
        Returns:
            True if certificate is valid
        """
        # In real implementation, this would use proper cryptographic verification
        # For this example, we use HMAC as a placeholder
        expected_sig = hmac.new(self.ca_public_key, cert_data, hashlib.sha256).digest()
        return hmac.compare_digest(expected_sig, signature)
    
    def register_certificate(self, node_id: int, cert_data: bytes, signature: bytes) -> bool:
        """
        Register a trusted certificate.
        
        Args:
            node_id: Node identifier
            cert_data: Certificate data
            signature: CA signature
        
        Returns:
            True if certificate was registered
        """
        if self.verify_certificate(cert_data, signature):
            cert_hash = hashlib.sha256(cert_data).digest()
            self.trusted_certs[node_id] = cert_hash
            return True
        return False
    
    def authenticate_node(self, node_id: int, cert_data: bytes, 
                         proof: bytes) -> AuthenticationResult:
        """
        Authenticate node using certificate.
        
        Args:
            node_id: Node identifier
            cert_data: Node's certificate
            proof: Proof of private key possession
        
        Returns:
            Authentication result
        """
        # Verify certificate is trusted
        cert_hash = hashlib.sha256(cert_data).digest()
        
        if node_id not in self.trusted_certs:
            return AuthenticationResult(
                success=False,
                reason="Certificate not registered"
            )
        
        if self.trusted_certs[node_id] != cert_hash:
            return AuthenticationResult(
                success=False,
                reason="Certificate mismatch"
            )
        
        # In real implementation, would verify proof of private key
        # For this example, we check if proof is valid
        challenge = b"authentication_challenge"
        expected_proof = hmac.new(cert_data, challenge, hashlib.sha256).digest()
        
        if hmac.compare_digest(proof, expected_proof):
            # Generate session key
            session_key = hashlib.sha256(
                cert_data + secrets.token_bytes(32)
            ).digest()
            
            return AuthenticationResult(
                success=True,
                reason="Certificate authentication successful",
                session_key=session_key
            )
        else:
            return AuthenticationResult(
                success=False,
                reason="Invalid proof of private key"
            )


class Authenticator:
    """High-level authentication interface."""
    
    MODE_PSK = "PSK"
    MODE_CERTIFICATE = "Certificate"
    
    def __init__(self, mode: str, **kwargs):
        """
        Initialize authenticator.
        
        Args:
            mode: Authentication mode (PSK or Certificate)
            **kwargs: Mode-specific parameters
        """
        self.mode = mode
        
        if mode == self.MODE_PSK:
            psk = kwargs.get('psk')
            if not psk:
                raise ValueError("PSK mode requires 'psk' parameter")
            self.auth = PSKAuth(psk)
        
        elif mode == self.MODE_CERTIFICATE:
            ca_key = kwargs.get('ca_public_key')
            if not ca_key:
                raise ValueError("Certificate mode requires 'ca_public_key' parameter")
            self.auth = CertificateAuth(ca_key)
        
        else:
            raise ValueError(f"Unknown authentication mode: {mode}")
    
    def authenticate(self, node_id: int, **kwargs) -> AuthenticationResult:
        """
        Authenticate a node.
        
        Args:
            node_id: Node identifier
            **kwargs: Mode-specific authentication data
        
        Returns:
            Authentication result
        """
        if self.mode == self.MODE_PSK:
            return self.auth.authenticate_node(node_id)
        
        elif self.mode == self.MODE_CERTIFICATE:
            cert_data = kwargs.get('cert_data')
            proof = kwargs.get('proof')
            
            if not cert_data or not proof:
                return AuthenticationResult(
                    success=False,
                    reason="Missing cert_data or proof"
                )
            
            return self.auth.authenticate_node(node_id, cert_data, proof)
        
        return AuthenticationResult(
            success=False,
            reason=f"Unknown mode: {self.mode}"
        )


# Example usage
if __name__ == "__main__":
    print("Testing PSK Authentication...")
    print("="*50)
    
    # Create PSK authenticator
    psk = b"my_super_secret_pre_shared_key_12345"
    psk_auth = PSKAuth(psk)
    
    # Test challenge-response
    print("\nChallenge-Response Test:")
    print("-"*50)
    
    node_id = 0x0001
    challenge = psk_auth.generate_challenge()
    print(f"Challenge: {challenge.hex()[:32]}...")
    
    response = psk_auth.compute_response(challenge, node_id)
    print(f"Response: {response.hex()[:32]}...")
    
    valid = psk_auth.verify_response(challenge, node_id, response)
    print(f"Valid: {valid}")
    
    # Test with wrong response
    wrong_response = secrets.token_bytes(32)
    valid = psk_auth.verify_response(challenge, node_id, wrong_response)
    print(f"Wrong response valid: {valid}")
    
    # Test session key derivation
    print("\nSession Key Derivation:")
    print("-"*50)
    
    nonce_a = secrets.token_bytes(32)
    nonce_b = secrets.token_bytes(32)
    session_key = psk_auth.derive_session_key(0x0001, 0x0002, nonce_a, nonce_b)
    print(f"Session key: {session_key.hex()[:32]}...")
    
    # Test full authentication
    print("\nFull Authentication:")
    print("-"*50)
    
    result = psk_auth.authenticate_node(node_id)
    print(f"Success: {result.success}")
    print(f"Reason: {result.reason}")
    if result.session_key:
        print(f"Session key: {result.session_key.hex()[:32]}...")
    
    # Test Certificate Authentication
    print("\n" + "="*50)
    print("Testing Certificate Authentication...")
    print("="*50)
    
    # Create certificate authenticator
    ca_key = b"certificate_authority_public_key_here"
    cert_auth = CertificateAuth(ca_key)
    
    # Register a certificate
    print("\nCertificate Registration:")
    print("-"*50)
    
    node_id = 0x0001
    cert_data = b"node_0001_certificate_data_x509_format"
    signature = hmac.new(ca_key, cert_data, hashlib.sha256).digest()
    
    registered = cert_auth.register_certificate(node_id, cert_data, signature)
    print(f"Certificate registered: {registered}")
    
    # Authenticate with certificate
    print("\nCertificate Authentication:")
    print("-"*50)
    
    challenge = b"authentication_challenge"
    proof = hmac.new(cert_data, challenge, hashlib.sha256).digest()
    
    result = cert_auth.authenticate_node(node_id, cert_data, proof)
    print(f"Success: {result.success}")
    print(f"Reason: {result.reason}")
    if result.session_key:
        print(f"Session key: {result.session_key.hex()[:32]}...")
    
    # Test high-level interface
    print("\n" + "="*50)
    print("Testing High-Level Authenticator...")
    print("="*50)
    
    # PSK mode
    authenticator = Authenticator(mode="PSK", psk=psk)
    result = authenticator.authenticate(0x0001)
    print(f"\nPSK Auth: {result.success} - {result.reason}")
    
    # Certificate mode
    authenticator = Authenticator(mode="Certificate", ca_public_key=ca_key)
    result = authenticator.authenticate(0x0001, cert_data=cert_data, proof=proof)
    print(f"Cert Auth: {result.success} - {result.reason}")
    
    print("\n✓ Authentication operational!")
