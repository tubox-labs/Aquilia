"""
Security -- artifact signing, verification, and encryption at rest.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("aquilia.mlops.security")


class ArtifactSigner:
    """
    Signs and verifies modelpack artifacts.

    Wraps the pack signer module with registry-level key management.
    """

    def __init__(
        self,
        private_key_path: str | None = None,
        public_key_path: str | None = None,
        hmac_secret: str | None = None,
    ):
        self._private_key = private_key_path
        self._public_key = public_key_path
        self._hmac_secret = hmac_secret

    async def sign(self, archive_path: str) -> str:
        """Sign an archive and return signature path."""
        from ..pack.signer import HMACSigner, RSASigner, sign_archive

        if self._hmac_secret:
            signer = HMACSigner(self._hmac_secret)
        elif self._private_key:
            signer = RSASigner(self._private_key, self._public_key)
        else:
            from aquilia.faults.domains import ConfigMissingFault

            raise ConfigMissingFault(key="mlops.signing.key")

        return await sign_archive(archive_path, signer)

    async def verify(self, archive_path: str, sig_path: str) -> bool:
        """Verify an archive signature."""
        from ..pack.signer import HMACSigner, RSASigner, verify_archive

        if self._hmac_secret:
            signer = HMACSigner(self._hmac_secret)
        elif self._public_key:
            signer = RSASigner(public_key_path=self._public_key)
        else:
            from aquilia.faults.domains import ConfigMissingFault

            raise ConfigMissingFault(key="mlops.signing.verification_key")

        return await verify_archive(archive_path, sig_path, signer)


class EncryptionManager:
    """
    Encryption at rest for registry blob storage.

    Uses Fernet (AES-128-CBC) from ``cryptography`` (already an Aquilia dep).
    """

    def __init__(self, key: bytes | None = None):
        if key:
            self._key = key
        else:
            from cryptography.fernet import Fernet

            self._key = Fernet.generate_key()

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        from cryptography.fernet import Fernet

        f = Fernet(self._key)
        return f.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        """Decrypt data."""
        from cryptography.fernet import Fernet

        f = Fernet(self._key)
        return f.decrypt(token)

    @property
    def key(self) -> bytes:
        return self._key
