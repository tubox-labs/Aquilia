"""
Render Credential Store — Crous-Encrypted Token Persistence.

Stores Render API tokens securely on disk using the Crous binary
serialization format and HMAC-SHA256 signing, ensuring tokens are
never stored in plain text.

Storage layout::

    ~/.aquilia/
        providers/
            render/
                credentials.crous   ← signed + encrypted token blob
                config.json         ← non-sensitive settings (region, owner)

Security Model
--------------
1. The API token is encrypted with a machine-derived key:
   ``HMAC-SHA256(hostname + username + "aquilia.render", salt)``
2. The encrypted blob is serialised using Crous binary format.
3. An HMAC signature covers the entire blob; tampering is detected.
4. File permissions are set to ``0o600`` (owner-only read/write).
5. Tokens in memory are cleared after use when possible.
"""

from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import logging
import os
import platform
import secrets
import struct
import time
from pathlib import Path
from typing import Any, Dict, Optional

from aquilia.faults.domains import ProviderCredentialFault

__all__ = ["RenderCredentialStore"]

_logger = logging.getLogger("aquilia.providers.render.store")

# ── Constants ────────────────────────────────────────────────────────────
_CROUS_MAGIC = b"AQCR"   # Crous binary magic bytes
_CROUS_VERSION = 1
_SALT_SIZE = 32           # bytes
_KEY_ITERATIONS = 200_000 # PBKDF2 iterations
_HMAC_ALGO = "sha256"

# Default store location
_DEFAULT_STORE_DIR = Path.home() / ".aquilia" / "providers" / "render"


def _derive_key(salt: bytes, context: str = "") -> bytes:
    """Derive an encryption key from machine identity + salt.

    Uses PBKDF2-HMAC-SHA256 with machine-specific context to produce
    a 32-byte key.  This ensures credentials are bound to the machine
    they were created on.
    """
    hostname = platform.node()
    username = os.environ.get("USER", os.environ.get("USERNAME", "aquilia"))
    identity = f"{hostname}:{username}:aquilia.render:{context}"

    return hashlib.pbkdf2_hmac(
        "sha256",
        identity.encode("utf-8"),
        salt,
        _KEY_ITERATIONS,
        dklen=32,
    )


def _xor_encrypt(data: bytes, key: bytes) -> bytes:
    """XOR-based stream cipher (repeating key).

    This is NOT a production-grade cipher; it's sufficient for
    local credential storage where the threat model is casual
    file browsing (not targeted attacks).  For higher security,
    use ``cryptography.fernet`` if available.
    """
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def _compute_hmac(key: bytes, data: bytes) -> bytes:
    """Compute HMAC-SHA256."""
    return _hmac.new(key, data, hashlib.sha256).digest()


class RenderCredentialStore:
    """Secure, file-based credential store for Render API tokens.

    Encrypts tokens at rest and validates integrity on read.

    Args:
        store_dir: Directory to store credential files.

    Example::

        store = RenderCredentialStore()
        store.save(token="rnd_xxxxxxxxxxxx")
        token = store.load()
        store.clear()
    """

    def __init__(self, store_dir: Optional[Path] = None):
        self._dir = store_dir or _DEFAULT_STORE_DIR
        self._creds_file = self._dir / "credentials.crous"
        self._config_file = self._dir / "config.json"

    @property
    def credentials_path(self) -> Path:
        """Path to the encrypted credentials file."""
        return self._creds_file

    @property
    def config_path(self) -> Path:
        """Path to the non-sensitive config file."""
        return self._config_file

    def is_configured(self) -> bool:
        """Return True if credentials are stored."""
        return self._creds_file.exists()

    # ─── Save ────────────────────────────────────────────────────────

    def save(
        self,
        token: str,
        *,
        owner_name: Optional[str] = None,
        default_region: str = "oregon",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Encrypt and store the API token.

        Args:
            token: Render API bearer token.
            owner_name: Workspace/owner name (non-sensitive, stored in config).
            default_region: Default deployment region.
            metadata: Additional non-sensitive metadata.
        """
        self._dir.mkdir(parents=True, exist_ok=True)

        # ── Encrypt token ────────────────────────────────────────────
        salt = secrets.token_bytes(_SALT_SIZE)
        key = _derive_key(salt, context="token-encryption")
        token_bytes = token.encode("utf-8")
        encrypted = _xor_encrypt(token_bytes, key)

        # ── Build Crous binary blob ──────────────────────────────────
        # Format:
        #   4 bytes  magic ("AQCR")
        #   1 byte   version
        #   8 bytes  timestamp (double, big-endian)
        #   32 bytes salt
        #   4 bytes  encrypted token length (uint32, big-endian)
        #   N bytes  encrypted token
        #   32 bytes HMAC-SHA256 of everything above
        timestamp = time.time()
        payload = bytearray()
        payload.extend(_CROUS_MAGIC)
        payload.append(_CROUS_VERSION)
        payload.extend(struct.pack(">d", timestamp))
        payload.extend(salt)
        payload.extend(struct.pack(">I", len(encrypted)))
        payload.extend(encrypted)

        # Sign the entire payload
        hmac_key = _derive_key(salt, context="hmac-signing")
        signature = _compute_hmac(hmac_key, bytes(payload))
        payload.extend(signature)

        # Write with restricted permissions
        self._creds_file.write_bytes(bytes(payload))
        try:
            os.chmod(self._creds_file, 0o600)
        except OSError:
            pass  # Windows may not support chmod

        # ── Store non-sensitive config ───────────────────────────────
        config: Dict[str, Any] = {
            "owner_name": owner_name,
            "default_region": default_region,
            "stored_at": timestamp,
        }
        if metadata:
            config["metadata"] = metadata

        self._config_file.write_text(
            json.dumps(config, indent=2), encoding="utf-8"
        )
        try:
            os.chmod(self._config_file, 0o600)
        except OSError:
            pass

        _logger.info("Render credentials stored at %s", self._creds_file)

    # ─── Load ────────────────────────────────────────────────────────

    def load(self) -> Optional[str]:
        """Load and decrypt the stored API token.

        Returns:
            The decrypted API token, or None if no credentials are stored.

        Raises:
            ProviderCredentialFault: If the credentials file is corrupted,
                tampered with, or cannot be read.
        """
        if not self._creds_file.exists():
            _logger.debug("No credentials file found at %s", self._creds_file)
            return None

        try:
            blob = self._creds_file.read_bytes()
        except (OSError, PermissionError) as e:
            raise ProviderCredentialFault(
                f"Cannot read credentials: {e}",
                path=str(self._creds_file),
            ) from e

        # ── Parse Crous binary blob ──────────────────────────────────
        # Minimum size: 4 + 1 + 8 + 32 + 4 + 0 + 32 = 81 bytes
        if len(blob) < 81:
            raise ProviderCredentialFault(
                "Credentials file is too small — possibly corrupted",
                path=str(self._creds_file),
            )

        # Validate magic
        if blob[:4] != _CROUS_MAGIC:
            raise ProviderCredentialFault(
                "Invalid credentials file (bad magic bytes)",
                path=str(self._creds_file),
            )

        version = blob[4]
        if version != _CROUS_VERSION:
            raise ProviderCredentialFault(
                f"Unsupported credentials version: {version}",
                path=str(self._creds_file),
            )

        # Parse fields
        offset = 5
        timestamp = struct.unpack_from(">d", blob, offset)[0]
        offset += 8

        salt = blob[offset:offset + _SALT_SIZE]
        offset += _SALT_SIZE

        token_len = struct.unpack_from(">I", blob, offset)[0]
        offset += 4

        if offset + token_len + 32 > len(blob):
            raise ProviderCredentialFault(
                "Credentials file truncated",
                path=str(self._creds_file),
            )

        encrypted = blob[offset:offset + token_len]
        offset += token_len

        stored_signature = blob[offset:offset + 32]
        payload_to_verify = blob[:offset]

        # ── Verify HMAC ──────────────────────────────────────────────
        hmac_key = _derive_key(salt, context="hmac-signing")
        expected_signature = _compute_hmac(hmac_key, payload_to_verify)

        if not _hmac.compare_digest(stored_signature, expected_signature):
            raise ProviderCredentialFault(
                "Credential integrity check failed — file may be tampered",
                path=str(self._creds_file),
            )

        # ── Decrypt ──────────────────────────────────────────────────
        key = _derive_key(salt, context="token-encryption")
        token_bytes = _xor_encrypt(encrypted, key)

        try:
            return token_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ProviderCredentialFault(
                "Decrypted token is not valid UTF-8",
                path=str(self._creds_file),
            )

    # ─── Config ──────────────────────────────────────────────────────

    def load_config(self) -> Dict[str, Any]:
        """Load non-sensitive provider configuration."""
        if not self._config_file.exists():
            return {}
        try:
            return json.loads(self._config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_default_region(self) -> str:
        """Get the default deployment region."""
        return self.load_config().get("default_region", "oregon")

    def get_owner_name(self) -> Optional[str]:
        """Get the stored workspace/owner name."""
        return self.load_config().get("owner_name")

    # ─── Clear ───────────────────────────────────────────────────────

    def clear(self) -> None:
        """Securely delete stored credentials.

        Overwrites the file with random bytes before deletion
        to prevent recovery from unencrypted swap/disk sectors.
        """
        if self._creds_file.exists():
            # Overwrite with random data
            try:
                size = self._creds_file.stat().st_size
                self._creds_file.write_bytes(secrets.token_bytes(size))
            except OSError:
                pass
            try:
                self._creds_file.unlink()
            except OSError as e:
                _logger.warning("Could not delete credentials: %s", e)

        if self._config_file.exists():
            try:
                self._config_file.unlink()
            except OSError:
                pass

        _logger.info("Render credentials cleared")

    # ─── Utility ─────────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """Return credential store status (for CLI display)."""
        config = self.load_config()
        return {
            "configured": self.is_configured(),
            "credentials_path": str(self._creds_file),
            "config_path": str(self._config_file),
            "owner_name": config.get("owner_name"),
            "default_region": config.get("default_region", "oregon"),
            "stored_at": config.get("stored_at"),
        }
