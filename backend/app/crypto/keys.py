"""
Ed25519 Key Management for JWT Signing

Generates Ed25519 key pair on application startup for JWT signing.

All keys are ephemeral (in-memory only) and regenerate on container restart,
which invalidates all existing tokens. This is acceptable for security.

Ed25519 Benefits:
- Tiny signatures (64 bytes) - fits easily in cookies
- Fast signing and verification
- Modern, secure elliptic curve cryptography
"""

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
import logging
import hashlib

logger = logging.getLogger(__name__)


class Ed25519KeyPair:
    """
    Singleton class to hold Ed25519 keys for JWT signing.
    """

    _instance = None
    _private_key: ed25519.Ed25519PrivateKey = None
    _public_key: ed25519.Ed25519PublicKey = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Ed25519KeyPair, cls).__new__(cls)
            cls._instance._generate_keys()
        return cls._instance

    def _generate_keys(self):
        """Generate Ed25519 key pair on first instantiation."""
        logger.info("=" * 60)
        logger.info("Generating Ed25519 key pair for JWT signing")
        logger.info("=" * 60)

        # Generate Ed25519 private key
        self._private_key = ed25519.Ed25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

        # Get public key bytes for fingerprint logging
        public_key_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        fingerprint = self._get_fingerprint(public_key_bytes)
        logger.info(f"✓ Ed25519 generated | Fingerprint: {fingerprint}")
        logger.info(f"  Public key size: {len(public_key_bytes)} bytes (32 bytes)")
        logger.info(f"  Signature size: 64 bytes")
        logger.info("=" * 60)

    def _get_fingerprint(self, key_data: bytes) -> str:
        """Get a short fingerprint of a key for logging."""
        digest = hashlib.sha256(key_data).hexdigest()
        return digest[:16]  # First 16 chars

    @property
    def private_key(self) -> ed25519.Ed25519PrivateKey:
        """Get the Ed25519 private key object (for PyJWT signing)."""
        return self._private_key

    @property
    def public_key(self) -> ed25519.Ed25519PublicKey:
        """Get the Ed25519 public key object (for PyJWT verification)."""
        return self._public_key


# Singleton instance - instantiated once on import
_key_pair = Ed25519KeyPair()


# Public API functions
def get_ed25519_private_key() -> ed25519.Ed25519PrivateKey:
    """Get the Ed25519 private key object for JWT signing."""
    return _key_pair.private_key


def get_ed25519_public_key() -> ed25519.Ed25519PublicKey:
    """Get the Ed25519 public key object for JWT verification."""
    return _key_pair.public_key
