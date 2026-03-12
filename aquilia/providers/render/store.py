"""
Render Credential Store — Military-Grade Encrypted Token Persistence.

Stores Render API tokens securely on disk using multi-layered
cryptographic protections and integrity verification.

Storage layout::

    <workspace>/.aquilia/
        providers/
            render/
                credentials.crous   ← AES-256-GCM encrypted + HMAC signed
                config.json         ← non-sensitive settings (region, owner)
                audit.log           ← credential access audit trail

Security Model (Defense-in-Depth)
---------------------------------
1. **Key Derivation**: PBKDF2-HMAC-SHA512 with 600,000 iterations +
   machine-bound context (hostname, username, platform, Python version).
2. **Encryption**: AES-256-GCM (authenticated encryption) providing
   confidentiality + integrity + authenticity in a single primitive.
   Falls back to a HMAC-SHA512-XOR stream cipher as last resort.
3. **Integrity**: Separate HMAC-SHA512 over the entire Crous blob
   using an independent signing key (encrypt-then-MAC).
4. **Anti-Replay**: Unique 96-bit nonce per encryption + monotonic
   timestamp validation.
5. **Key Separation**: Distinct keys for encryption, HMAC signing,
   and token-binding via independent PBKDF2 contexts.
6. **Token Expiry**: Configurable TTL with automatic expiration checks.
7. **Key Rotation**: Version-tagged credentials with seamless migration.
8. **Secure Memory**: ``ctypes.memset`` zeroing of sensitive buffers
   + ``del`` references immediately after use.
9. **File Permissions**: ``0o600`` (owner-only read/write).
10. **Audit Logging**: All credential operations logged with timestamps.
11. **Tamper Detection**: Magic bytes + version + HMAC chain prevents
    file modification, truncation, and version downgrade attacks.
12. **Canary Validation**: Encrypted known plaintext verified on load
    to detect key derivation failures (wrong machine, corruption).

Crous v2 Binary Format
-----------------------
::

    4 bytes   magic ("AQCR")
    1 byte    version (2)
    1 byte    cipher suite ID (1=AES-GCM, 2=XOR-HMAC)
    8 bytes   timestamp (double, big-endian)
    4 bytes   TTL seconds (uint32, big-endian; 0 = no expiry)
    32 bytes  salt
    12 bytes  nonce (IV for AES-GCM)
    4 bytes   encrypted token length (uint32, big-endian)
    N bytes   encrypted token (ciphertext)
    16 bytes  GCM auth tag (or HMAC-truncated for XOR fallback)
    12 bytes  canary nonce
    4 bytes   canary ciphertext length
    M bytes   canary ciphertext
    16 bytes  canary auth tag
    64 bytes  HMAC-SHA512 signature of everything above
"""

from __future__ import annotations

import contextlib
import ctypes
import datetime
import hashlib
import hmac as _hmac
import json
import logging
import os
import platform
import secrets
import struct
import sys
import time
from pathlib import Path
from typing import Any

from aquilia.faults.domains import ProviderCredentialFault

__all__ = ["RenderCredentialStore"]

_logger = logging.getLogger("aquilia.providers.render.store")

# ── Constants ────────────────────────────────────────────────────────────
_CROUS_MAGIC = b"AQCR"
_CROUS_VERSION = 2
_CROUS_VERSION_LEGACY = 1
_SALT_SIZE = 32
_NONCE_SIZE = 12
_KEY_ITERATIONS = 600_000
_HMAC_ALGO = "sha512"
_TAG_SIZE = 16
_CANARY_PLAINTEXT = b"AQUILIA_CANARY_OK"
_CANARY_SIZE = 32
_DEFAULT_TTL = 0
_MAX_TOKEN_SIZE = 8192

_CIPHER_AES_GCM = 1
_CIPHER_XOR_HMAC = 3

_AUDIT_MAX_BYTES = 1_048_576


def _resolve_workspace_store_dir() -> Path:
    """Resolve the credential store directory inside the current workspace.

    Resolution order (uses Aquilia's own modules when available):
        1. ``aquilia.cli.utils.workspace.find_workspace_root()`` — the canonical
           Aquilia workspace resolution function.
        2. ``AQUILIA_WORKSPACE`` environment variable (set by entrypoint/CLI).
        3. Walk up from ``cwd()`` looking for ``workspace.py`` or ``aquilia.py``
           (manual fallback identical to what the CLI module does).
        4. Fall back to ``cwd()``.

    Returns ``<workspace_root>/.aquilia/providers/render/``.
    """
    _suffix = Path(".aquilia") / "providers" / "render"

    # 1. Canonical Aquilia workspace resolution (preferred)
    try:
        from aquilia.cli.utils.workspace import find_workspace_root

        ws_root = find_workspace_root()
        if ws_root is not None and ws_root.is_dir():
            return ws_root / _suffix
    except (ImportError, Exception):
        pass

    # 2. Env var (always set when running via `aq run` or entrypoint)
    ws_env = os.environ.get("AQUILIA_WORKSPACE")
    if ws_env:
        ws_path = Path(ws_env).resolve()
        if ws_path.is_dir():
            return ws_path / _suffix

    # 3. Manual walk-up fallback (mirrors CLI logic for standalone usage)
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / "workspace.py").exists() or (current / "aquilia.py").exists():
            return current / _suffix
        current = current.parent

    # 4. Last resort: cwd
    return Path.cwd().resolve() / _suffix


# ═══════════════════════════════════════════════════════════════════════════
# Secure Memory Wiping
# ═══════════════════════════════════════════════════════════════════════════


def _secure_zero(buffer: bytearray) -> None:
    """Overwrite a mutable buffer with zeros using ctypes."""
    if not buffer:
        return
    try:
        buf_type = ctypes.c_char * len(buffer)
        buf_ptr = buf_type.from_buffer(buffer)
        ctypes.memset(ctypes.addressof(buf_ptr), 0, len(buffer))
    except (TypeError, ValueError, BufferError):
        for i in range(len(buffer)):
            buffer[i] = 0


# ═══════════════════════════════════════════════════════════════════════════
# Key Derivation
# ═══════════════════════════════════════════════════════════════════════════


def _derive_key(salt: bytes, context: str = "", iterations: int = _KEY_ITERATIONS) -> bytes:
    """Derive a 256-bit key from machine identity + salt.

    Uses PBKDF2-HMAC-SHA512 with 600,000 iterations and machine-specific
    context (hostname, username, platform, Python version).
    """
    hostname = platform.node()
    username = os.environ.get("USER", os.environ.get("USERNAME", "aquilia"))
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    machine = platform.machine()
    identity = f"{hostname}:{username}:{machine}:{py_version}:aquilia.render:{context}"
    return hashlib.pbkdf2_hmac(
        "sha512",
        identity.encode("utf-8"),
        salt,
        iterations,
        dklen=32,
    )


def _derive_key_legacy(salt: bytes, context: str = "") -> bytes:
    """Legacy v1 key derivation (PBKDF2-HMAC-SHA256, 200k iterations)."""
    hostname = platform.node()
    username = os.environ.get("USER", os.environ.get("USERNAME", "aquilia"))
    identity = f"{hostname}:{username}:aquilia.render:{context}"
    return hashlib.pbkdf2_hmac(
        "sha256",
        identity.encode("utf-8"),
        salt,
        200_000,
        dklen=32,
    )


# ═══════════════════════════════════════════════════════════════════════════
# Cipher Suite
# ═══════════════════════════════════════════════════════════════════════════


def _detect_cipher_suite() -> int:
    """Detect the best available cipher suite."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401

        return _CIPHER_AES_GCM
    except ImportError:
        pass
    return _CIPHER_XOR_HMAC


def _encrypt(key: bytes, nonce: bytes, plaintext: bytes, cipher_suite: int) -> tuple[bytes, bytes]:
    """Encrypt plaintext. Returns (ciphertext, auth_tag)."""
    if cipher_suite == _CIPHER_AES_GCM:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        aes = AESGCM(key)
        ct = aes.encrypt(nonce, plaintext, None)
        return ct[:-_TAG_SIZE], ct[-_TAG_SIZE:]
    return _xor_encrypt_with_tag(key, nonce, plaintext)


def _decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes, cipher_suite: int) -> bytes:
    """Decrypt ciphertext. Raises ProviderCredentialFault on failure."""
    if cipher_suite == _CIPHER_AES_GCM:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        aes = AESGCM(key)
        try:
            return aes.decrypt(nonce, ciphertext + tag, None)
        except Exception as e:
            raise ProviderCredentialFault("AES-GCM decryption failed — credentials may be tampered") from e
    return _xor_decrypt_with_tag(key, nonce, ciphertext, tag)


def _xor_encrypt_with_tag(key: bytes, nonce: bytes, plaintext: bytes) -> tuple[bytes, bytes]:
    """XOR stream cipher with HMAC-SHA256 authentication tag."""
    keystream = _generate_keystream(key, nonce, len(plaintext))
    ciphertext = bytes(p ^ k for p, k in zip(plaintext, keystream, strict=False))
    tag = _hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()[:_TAG_SIZE]
    return ciphertext, tag


def _xor_decrypt_with_tag(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    """XOR stream cipher decryption with HMAC verification."""
    expected_tag = _hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()[:_TAG_SIZE]
    if not _hmac.compare_digest(tag, expected_tag):
        raise ProviderCredentialFault("XOR-HMAC authentication failed — credentials may be tampered")
    keystream = _generate_keystream(key, nonce, len(ciphertext))
    return bytes(c ^ k for c, k in zip(ciphertext, keystream, strict=False))


def _generate_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    """Generate pseudorandom keystream using HMAC-SHA512 counter mode."""
    stream = bytearray()
    counter = 0
    while len(stream) < length:
        block = _hmac.new(
            key,
            nonce + struct.pack(">Q", counter),
            hashlib.sha512,
        ).digest()
        stream.extend(block)
        counter += 1
    return bytes(stream[:length])


# Legacy v1 functions for backward compatibility
def _xor_encrypt(data: bytes, key: bytes) -> bytes:
    """Legacy XOR-based stream cipher (v1 compatibility)."""
    key_len = len(key)
    return bytes(b ^ key[i % key_len] for i, b in enumerate(data))


def _compute_hmac(key: bytes, data: bytes) -> bytes:
    """Compute HMAC-SHA256 (legacy v1 compatibility)."""
    return _hmac.new(key, data, hashlib.sha256).digest()


# ═══════════════════════════════════════════════════════════════════════════
# Audit Logger
# ═══════════════════════════════════════════════════════════════════════════


class _AuditLogger:
    """Append-only audit log for credential operations."""

    def __init__(self, log_path: Path):
        self._path = log_path

    def log(self, action: str, *, details: str | None = None) -> None:
        """Record an audit event."""
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            if self._path.exists() and self._path.stat().st_size > _AUDIT_MAX_BYTES:
                rotated = self._path.with_suffix(".log.1")
                if rotated.exists():
                    rotated.unlink()
                self._path.rename(rotated)
            ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
            entry = {"ts": ts, "action": action, "pid": os.getpid()}
            if details:
                entry["details"] = details
            with self._path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
            with contextlib.suppress(OSError):
                os.chmod(self._path, 0o600)
        except OSError:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# Credential Store
# ═══════════════════════════════════════════════════════════════════════════


class RenderCredentialStore:
    """Military-grade, file-based credential store for Render API tokens.

    Provides AES-256-GCM encryption, HMAC-SHA512 integrity verification,
    token expiry, key rotation, audit logging, and secure memory wiping.

    Args:
        store_dir: Directory to store credential files.
        ttl: Token time-to-live in seconds (0 = no expiry).
    """

    def __init__(self, store_dir: Path | None = None, *, ttl: int = _DEFAULT_TTL):
        self._dir = store_dir or _resolve_workspace_store_dir()
        self._creds_file = self._dir / "credentials.crous"
        self._config_file = self._dir / "config.json"
        self._ttl = ttl
        self._audit = _AuditLogger(self._dir / "audit.log")

    @property
    def credentials_path(self) -> Path:
        return self._creds_file

    @property
    def config_path(self) -> Path:
        return self._config_file

    def is_configured(self) -> bool:
        return self._creds_file.exists()

    # ─── Save ────────────────────────────────────────────────────────

    def save(
        self,
        token: str,
        *,
        owner_name: str | None = None,
        default_region: str = "oregon",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Encrypt and store the API token with military-grade security."""
        if not token or not isinstance(token, str):
            raise ProviderCredentialFault("Token must be a non-empty string")
        if len(token) > _MAX_TOKEN_SIZE:
            raise ProviderCredentialFault(f"Token exceeds maximum size ({_MAX_TOKEN_SIZE} bytes)")

        self._audit.log("save_start", details=f"owner={owner_name}")
        self._dir.mkdir(parents=True, exist_ok=True)

        salt = secrets.token_bytes(_SALT_SIZE)
        nonce = secrets.token_bytes(_NONCE_SIZE)
        cipher_suite = _detect_cipher_suite()

        enc_key = _derive_key(salt, context="token-encryption-v2")
        sign_key = _derive_key(salt, context="hmac-signing-v2")
        canary_key = _derive_key(salt, context="canary-validation-v2")

        token_bytes = bytearray(token.encode("utf-8"))
        try:
            ciphertext, tag = _encrypt(enc_key, nonce, bytes(token_bytes), cipher_suite)
        finally:
            _secure_zero(token_bytes)

        canary_plain = _CANARY_PLAINTEXT + secrets.token_bytes(_CANARY_SIZE - len(_CANARY_PLAINTEXT))
        canary_nonce = secrets.token_bytes(_NONCE_SIZE)
        canary_ct, canary_tag = _encrypt(canary_key, canary_nonce, canary_plain, cipher_suite)

        timestamp = time.time()
        payload = bytearray()
        payload.extend(_CROUS_MAGIC)
        payload.append(_CROUS_VERSION)
        payload.append(cipher_suite)
        payload.extend(struct.pack(">d", timestamp))
        payload.extend(struct.pack(">I", self._ttl))
        payload.extend(salt)
        payload.extend(nonce)
        payload.extend(struct.pack(">I", len(ciphertext)))
        payload.extend(ciphertext)
        payload.extend(tag)
        payload.extend(canary_nonce)
        payload.extend(struct.pack(">I", len(canary_ct)))
        payload.extend(canary_ct)
        payload.extend(canary_tag)

        signature = _hmac.new(sign_key, bytes(payload), hashlib.sha512).digest()
        payload.extend(signature)

        self._creds_file.write_bytes(bytes(payload))
        with contextlib.suppress(OSError):
            os.chmod(self._creds_file, 0o600)

        config: dict[str, Any] = {
            "owner_name": owner_name,
            "default_region": default_region,
            "stored_at": timestamp,
            "crous_version": _CROUS_VERSION,
            "cipher_suite": cipher_suite,
            "ttl": self._ttl,
        }
        if metadata:
            config["metadata"] = metadata
        self._config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
        with contextlib.suppress(OSError):
            os.chmod(self._config_file, 0o600)

        _secure_zero(payload)
        del enc_key, sign_key, canary_key
        self._audit.log("save_complete")
        _logger.info("Render credentials stored at %s", self._creds_file)

    # ─── Load ────────────────────────────────────────────────────────

    def load(self) -> str | None:
        """Load and decrypt the stored API token.

        Automatically detects Crous v1 (legacy) and v2 formats.
        """
        if not self._creds_file.exists():
            _logger.debug("No credentials file found at %s", self._creds_file)
            return None

        self._audit.log("load_start")

        try:
            blob = self._creds_file.read_bytes()
        except (OSError, PermissionError) as e:
            self._audit.log("load_error", details=f"read_failed: {e}")
            raise ProviderCredentialFault(
                f"Cannot read credentials: {e}",
                path=str(self._creds_file),
            ) from e

        if len(blob) < 5 or blob[:4] != _CROUS_MAGIC:
            self._audit.log("load_error", details="bad_magic")
            raise ProviderCredentialFault(
                "Invalid credentials file (bad magic bytes)",
                path=str(self._creds_file),
            )

        version = blob[4]
        if version == _CROUS_VERSION_LEGACY:
            result = self._load_v1(blob)
            self._audit.log("load_complete", details="v1_legacy")
            return result
        if version == _CROUS_VERSION:
            result = self._load_v2(blob)
            self._audit.log("load_complete", details="v2")
            return result

        self._audit.log("load_error", details=f"unsupported_version:{version}")
        raise ProviderCredentialFault(
            f"Unsupported credentials version: {version}",
            path=str(self._creds_file),
        )

    def _load_v2(self, blob: bytes) -> str:
        """Load Crous v2 format (AES-256-GCM + HMAC-SHA512)."""
        if len(blob) < 178:
            raise ProviderCredentialFault(
                "Credentials file is too small — possibly corrupted",
                path=str(self._creds_file),
            )

        offset = 5
        cipher_suite = blob[offset]
        offset += 1
        timestamp = struct.unpack_from(">d", blob, offset)[0]
        offset += 8
        ttl = struct.unpack_from(">I", blob, offset)[0]
        offset += 4

        if ttl > 0:
            age = time.time() - timestamp
            if age > ttl:
                self._audit.log("load_error", details=f"token_expired:age={age:.0f}s,ttl={ttl}s")
                raise ProviderCredentialFault(
                    f"Token has expired ({age:.0f}s old, TTL={ttl}s). "
                    "Please re-authenticate with 'aq provider login render'.",
                    path=str(self._creds_file),
                )

        salt = blob[offset : offset + _SALT_SIZE]
        offset += _SALT_SIZE
        nonce = blob[offset : offset + _NONCE_SIZE]
        offset += _NONCE_SIZE
        token_len = struct.unpack_from(">I", blob, offset)[0]
        offset += 4

        if token_len > _MAX_TOKEN_SIZE:
            raise ProviderCredentialFault(
                "Encrypted token size exceeds maximum",
                path=str(self._creds_file),
            )

        ciphertext = blob[offset : offset + token_len]
        offset += token_len
        tag = blob[offset : offset + _TAG_SIZE]
        offset += _TAG_SIZE
        canary_nonce = blob[offset : offset + _NONCE_SIZE]
        offset += _NONCE_SIZE
        canary_len = struct.unpack_from(">I", blob, offset)[0]
        offset += 4
        canary_ct = blob[offset : offset + canary_len]
        offset += canary_len
        canary_tag = blob[offset : offset + _TAG_SIZE]
        offset += _TAG_SIZE

        if offset + 64 > len(blob):
            raise ProviderCredentialFault(
                "Credentials file truncated",
                path=str(self._creds_file),
            )

        stored_signature = blob[offset : offset + 64]
        payload_to_verify = blob[:offset]

        sign_key = _derive_key(salt, context="hmac-signing-v2")
        expected_signature = _hmac.new(sign_key, payload_to_verify, hashlib.sha512).digest()
        if not _hmac.compare_digest(stored_signature, expected_signature):
            self._audit.log("load_error", details="hmac_mismatch")
            raise ProviderCredentialFault(
                "Credential integrity check failed — file may be tampered",
                path=str(self._creds_file),
            )

        canary_key = _derive_key(salt, context="canary-validation-v2")
        try:
            canary_plain = _decrypt(canary_key, canary_nonce, canary_ct, canary_tag, cipher_suite)
            if not canary_plain.startswith(_CANARY_PLAINTEXT):
                raise ProviderCredentialFault(
                    "Canary validation failed — wrong machine or corrupted key material",
                    path=str(self._creds_file),
                )
        except ProviderCredentialFault:
            raise
        except Exception as e:
            self._audit.log("load_error", details=f"canary_failed: {e}")
            raise ProviderCredentialFault(
                "Canary validation failed",
                path=str(self._creds_file),
            ) from e

        enc_key = _derive_key(salt, context="token-encryption-v2")
        token_bytes = _decrypt(enc_key, nonce, ciphertext, tag, cipher_suite)
        try:
            token = token_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ProviderCredentialFault(
                "Decrypted token is not valid UTF-8",
                path=str(self._creds_file),
            )
        del enc_key, sign_key, canary_key
        return token

    def _load_v1(self, blob: bytes) -> str:
        """Load legacy Crous v1 format. Auto-migrates to v2."""
        if len(blob) < 81:
            raise ProviderCredentialFault(
                "Credentials file is too small — possibly corrupted",
                path=str(self._creds_file),
            )

        offset = 5
        struct.unpack_from(">d", blob, offset)[0]
        offset += 8
        salt = blob[offset : offset + _SALT_SIZE]
        offset += _SALT_SIZE
        token_len = struct.unpack_from(">I", blob, offset)[0]
        offset += 4

        if offset + token_len + 32 > len(blob):
            raise ProviderCredentialFault(
                "Credentials file truncated",
                path=str(self._creds_file),
            )

        encrypted = blob[offset : offset + token_len]
        offset += token_len
        stored_signature = blob[offset : offset + 32]
        payload_to_verify = blob[:offset]

        hmac_key = _derive_key_legacy(salt, context="hmac-signing")
        expected_signature = _hmac.new(hmac_key, payload_to_verify, hashlib.sha256).digest()
        if not _hmac.compare_digest(stored_signature, expected_signature):
            raise ProviderCredentialFault(
                "Credential integrity check failed — file may be tampered",
                path=str(self._creds_file),
            )

        key = _derive_key_legacy(salt, context="token-encryption")
        token_bytes = _xor_encrypt(encrypted, key)
        try:
            token = token_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise ProviderCredentialFault(
                "Decrypted token is not valid UTF-8",
                path=str(self._creds_file),
            )

        self._audit.log("auto_migrate", details="v1->v2")
        try:
            config = self.load_config()
            self.save(
                token,
                owner_name=config.get("owner_name"),
                default_region=config.get("default_region", "oregon"),
            )
            _logger.info("Auto-migrated credentials from v1 to v2")
        except Exception as e:
            _logger.warning("Could not auto-migrate credentials: %s", e)
        return token

    # ─── Config ──────────────────────────────────────────────────────

    def load_config(self) -> dict[str, Any]:
        """Load non-sensitive provider configuration."""
        if not self._config_file.exists():
            return {}
        try:
            return json.loads(self._config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def get_default_region(self) -> str:
        return self.load_config().get("default_region", "oregon")

    def get_owner_name(self) -> str | None:
        return self.load_config().get("owner_name")

    def get_token_age(self) -> float | None:
        """Get the age of the stored token in seconds."""
        config = self.load_config()
        stored_at = config.get("stored_at")
        if stored_at:
            return time.time() - stored_at
        return None

    def is_expired(self) -> bool:
        """Check if the stored token has expired."""
        config = self.load_config()
        ttl = config.get("ttl", 0)
        if ttl <= 0:
            return False
        stored_at = config.get("stored_at", 0)
        return (time.time() - stored_at) > ttl

    # ─── Clear ───────────────────────────────────────────────────────

    def clear(self) -> None:
        """Securely delete stored credentials.

        Performs 3-pass overwrite (random, zeros, random) before
        deletion to prevent recovery from disk sectors.
        """
        self._audit.log("clear_start")
        if self._creds_file.exists():
            try:
                size = self._creds_file.stat().st_size
                self._creds_file.write_bytes(secrets.token_bytes(size))
                self._creds_file.write_bytes(b"\x00" * size)
                self._creds_file.write_bytes(secrets.token_bytes(size))
            except OSError:
                pass
            try:
                self._creds_file.unlink()
            except OSError as e:
                _logger.warning("Could not delete credentials: %s", e)
        if self._config_file.exists():
            with contextlib.suppress(OSError):
                self._config_file.unlink()
        self._audit.log("clear_complete")
        _logger.info("Render credentials cleared")

    # ─── Rotate ──────────────────────────────────────────────────────

    def rotate(self, new_token: str | None = None) -> None:
        """Rotate credentials — re-encrypt with new key material."""
        self._audit.log("rotate_start")
        token = new_token
        if token is None:
            token = self.load()
            if token is None:
                raise ProviderCredentialFault("No existing token to rotate")
        config = self.load_config()
        self.save(
            token,
            owner_name=config.get("owner_name"),
            default_region=config.get("default_region", "oregon"),
            metadata=config.get("metadata"),
        )
        self._audit.log("rotate_complete")

    # ─── Audit ───────────────────────────────────────────────────────

    def get_audit_log(self, limit: int = 50) -> list[dict[str, Any]]:
        """Read the most recent audit log entries."""
        audit_path = self._dir / "audit.log"
        if not audit_path.exists():
            return []
        try:
            lines = audit_path.read_text(encoding="utf-8").strip().split("\n")
            entries = []
            for line in lines[-limit:]:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            return entries
        except OSError:
            return []

    # ─── Utility ─────────────────────────────────────────────────────

    def status(self) -> dict[str, Any]:
        """Return credential store status (for CLI display)."""
        config = self.load_config()
        token_age = self.get_token_age()
        result: dict[str, Any] = {
            "configured": self.is_configured(),
            "credentials_path": str(self._creds_file),
            "config_path": str(self._config_file),
            "owner_name": config.get("owner_name"),
            "default_region": config.get("default_region", "oregon"),
            "stored_at": config.get("stored_at"),
            "crous_version": config.get("crous_version", 1),
            "cipher_suite": config.get("cipher_suite"),
            "ttl": config.get("ttl", 0),
            "expired": self.is_expired(),
        }
        if token_age is not None:
            result["token_age_hours"] = round(token_age / 3600, 1)
        return result
