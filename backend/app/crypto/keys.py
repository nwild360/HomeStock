"""
Hybrid Cryptographic Key Management for JWT Signing

Generates both classical (RSA-2048) and post-quantum (Dilithium3) key pairs
on application startup for hybrid JWT signing.

All keys are ephemeral (in-memory only) and regenerate on container restart,
which invalidates all existing tokens. This is acceptable for security.

Architecture:
- RS256 (RSA-2048): For backward compatibility and current security
- Dilithium3 (FIPS 204): For post-quantum resistance
"""

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import oqs
import logging
import hashlib

logger = logging.getLogger(__name__)


class HybridKeyPair:
    """
    Singleton class to hold hybrid cryptographic keys for JWT signing.

    Generates and manages:
    - RSA-2048 key pair (for RS256 signing)
    - Dilithium3 key pair (for post-quantum signing)
    """

    _instance = None

    # RSA keys (classical)
    _rsa_private_key_pem: str = None
    _rsa_public_key_pem: str = None

    # Dilithium keys (post-quantum)
    _dilithium_private_key: bytes = None
    _dilithium_public_key: bytes = None
    _dilithium_signer: oqs.Signature = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HybridKeyPair, cls).__new__(cls)
            cls._instance._generate_keys()
        return cls._instance

    def _generate_keys(self):
        """Generate both RSA and Dilithium key pairs on first instantiation."""
        logger.info("=" * 60)
        logger.info("Generating hybrid cryptographic keys for JWT signing")
        logger.info("=" * 60)

        # Generate RSA keys
        self._generate_rsa_keys()

        # Generate Dilithium keys
        self._generate_dilithium_keys()

        logger.info("=" * 60)
        logger.info("Hybrid key generation complete")
        logger.info("=" * 60)

    def _generate_rsa_keys(self):
        """Generate RSA-2048 key pair for classical RS256 signing."""
        logger.info("Generating RSA-2048 key pair (RS256)...")

        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )

        # Serialize private key to PEM format
        self._rsa_private_key_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        # Extract public key and serialize to PEM format
        public_key = private_key.public_key()
        self._rsa_public_key_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        fingerprint = self._get_fingerprint(self._rsa_public_key_pem)
        logger.info(f"✓ RSA-2048 generated | Fingerprint: {fingerprint}")

    def _generate_dilithium_keys(self):
        """Generate Dilithium3 key pair for post-quantum signing."""
        logger.info("Generating Dilithium3 key pair (PQC FIPS 204)...")

        # Initialize Dilithium3 signer
        self._dilithium_signer = oqs.Signature("Dilithium3")

        # Generate keypair (returns public key, stores private key internally)
        self._dilithium_public_key = self._dilithium_signer.generate_keypair()

        # Export private key for storage
        self._dilithium_private_key = self._dilithium_signer.export_secret_key()

        fingerprint = self._get_fingerprint(self._dilithium_public_key)
        logger.info(f"✓ Dilithium3 generated | Fingerprint: {fingerprint}")
        logger.info(f"  Public key size: {len(self._dilithium_public_key)} bytes")
        logger.info(f"  Private key size: {len(self._dilithium_private_key)} bytes")

    def _get_fingerprint(self, key_data: bytes | str) -> str:
        """Get a short fingerprint of a key for logging."""
        if isinstance(key_data, str):
            key_data = key_data.encode()
        digest = hashlib.sha256(key_data).hexdigest()
        return digest[:16]  # First 16 chars

    # RSA Key Properties
    @property
    def rsa_private_key(self) -> str:
        """Get the RSA private key in PEM format (for RS256 signing)."""
        return self._rsa_private_key_pem

    @property
    def rsa_public_key(self) -> str:
        """Get the RSA public key in PEM format (for RS256 verification)."""
        return self._rsa_public_key_pem

    # Dilithium Key Properties
    @property
    def dilithium_public_key(self) -> bytes:
        """Get the Dilithium3 public key (for verification)."""
        return self._dilithium_public_key

    @property
    def dilithium_private_key(self) -> bytes:
        """Get the Dilithium3 private key (for signing)."""
        return self._dilithium_private_key

    def dilithium_sign(self, message: bytes) -> bytes:
        """
        Sign a message with Dilithium3.

        Args:
            message: The message to sign

        Returns:
            The Dilithium3 signature (approx 3,293 bytes)
        """
        return self._dilithium_signer.sign(message)

    def dilithium_verify(self, message: bytes, signature: bytes) -> bool:
        """
        Verify a Dilithium3 signature.

        Args:
            message: The original message
            signature: The signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            return self._dilithium_signer.verify(message, signature, self._dilithium_public_key)
        except Exception as e:
            logger.warning(f"Dilithium verification failed: {e}")
            return False


# Singleton instance - instantiated once on import
_key_pair = HybridKeyPair()


# Public API functions
def get_rsa_private_key() -> str:
    """Get the RSA private key for RS256 JWT signing."""
    return _key_pair.rsa_private_key


def get_rsa_public_key() -> str:
    """Get the RSA public key for RS256 JWT verification."""
    return _key_pair.rsa_public_key


def get_dilithium_public_key() -> bytes:
    """Get the Dilithium3 public key for PQC verification."""
    return _key_pair.dilithium_public_key


def dilithium_sign(message: bytes) -> bytes:
    """Sign a message with Dilithium3 (post-quantum)."""
    return _key_pair.dilithium_sign(message)


def dilithium_verify(message: bytes, signature: bytes) -> bool:
    """Verify a Dilithium3 signature."""
    return _key_pair.dilithium_verify(message, signature)
