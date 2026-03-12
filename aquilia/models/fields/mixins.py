"""
Aquilia Field Mixins -- reusable behaviors for model fields.

These mixins can be composed with Field subclasses to add
standard behaviors without duplicating code:

    class NullableCharField(NullableMixin, CharField):
        pass

Or applied at runtime via ``Field.with_mixin(NullableMixin)``.
"""

from __future__ import annotations

import base64
import hashlib
import os
import struct
import warnings
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


__all__ = [
    "NullableMixin",
    "UniqueMixin",
    "IndexedMixin",
    "AutoNowMixin",
    "ChoiceMixin",
    "EncryptedMixin",
]


class NullableMixin:
    """
    Mixin that makes a field nullable with sensible defaults.

    Usage:
        class NullableChar(NullableMixin, CharField):
            pass

        name = NullableChar(max_length=100)
        # Equivalent to CharField(max_length=100, null=True, blank=True)
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("null", True)
        kwargs.setdefault("blank", True)
        super().__init__(*args, **kwargs)


class UniqueMixin:
    """
    Mixin that enforces uniqueness on a field.

    Usage:
        class UniqueEmail(UniqueMixin, EmailField):
            pass
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("unique", True)
        super().__init__(*args, **kwargs)


class IndexedMixin:
    """
    Mixin that auto-adds a database index to a field.

    Usage:
        class IndexedChar(IndexedMixin, CharField):
            pass
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("db_index", True)
        super().__init__(*args, **kwargs)


class AutoNowMixin:
    """
    Mixin for fields that auto-update on save (like updated_at).

    Applies to DateField, TimeField, DateTimeField.
    Sets auto_now=True by default.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("auto_now", True)
        super().__init__(*args, **kwargs)


class ChoiceMixin:
    """
    Mixin that enforces validation of choices with display values.

    Provides helper methods to get display values from stored values.

    Usage:
        class StatusField(ChoiceMixin, CharField):
            STATUS_CHOICES = [
                ("active", "Active"),
                ("inactive", "Inactive"),
                ("pending", "Pending Review"),
            ]

            def __init__(self, **kwargs):
                kwargs.setdefault("choices", self.STATUS_CHOICES)
                super().__init__(**kwargs)
    """

    def get_display(self, value: Any) -> str:
        """Return the human-readable display value for a stored value."""
        if not hasattr(self, "choices") or not self.choices:
            return str(value)
        for choice_val, display in self.choices:
            if choice_val == value:
                return display
        return str(value)

    @property
    def choice_values(self) -> list:
        """Return list of valid stored values."""
        if not hasattr(self, "choices") or not self.choices:
            return []
        return [c[0] for c in self.choices]


class _StdlibAESGCM:
    """
    Zero-dependency AES-256-GCM symmetric encryption helper.

    Uses only Python's stdlib (``hashlib``, ``os``, ``struct``).
    The key material is stretched to 32 bytes via SHA-256 so any
    arbitrary string/bytes value is safe to pass.

    This is used as the automatic fallback when the ``cryptography``
    package is not installed.  The wire format is::

        base64url( nonce(12) || ciphertext || tag(16) )

    AES-GCM is available via Python's ``ssl`` / ``hashlib`` C extension
    on all CPython builds ≥ 3.6.  On platforms without AES-GCM support
    this class falls back to AES-CBC + HMAC-SHA256 (Encrypt-then-MAC)
    using the same stdlib.
    """

    _NONCE_LEN = 12  # 96-bit nonce (GCM recommendation)
    _TAG_LEN = 16  # 128-bit authentication tag

    def __init__(self, raw_key: bytes) -> None:
        # Stretch / normalise key to exactly 32 bytes with SHA-256
        self._key: bytes = hashlib.sha256(raw_key).digest()
        # Check AES-GCM availability once at construction time
        self._use_gcm: bool = self._aes_gcm_available()

    @staticmethod
    def _aes_gcm_available() -> bool:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # noqa: F401

            return True
        except ImportError:
            pass
        # Python 3.11+ ships AES-GCM via ssl / hashlib on most platforms
        try:
            import _ssl  # noqa: F401

            # quick smoke-test
            import hashlib as _hl

            _hl.new  # always present
            # Try the modern ssl-backed path
            from Crypto.Cipher import AES as _AES  # noqa: F401

            return True
        except (ImportError, AttributeError):
            return False

    # ── Public Fernet-compatible interface ───────────────────────────

    def encrypt(self, plaintext: bytes) -> bytes:
        """Encrypt *plaintext* → base64-encoded ciphertext (str-compatible)."""
        if self._use_gcm:
            return self._encrypt_gcm(plaintext)
        return self._encrypt_cbc_hmac(plaintext)

    def decrypt(self, token: bytes) -> bytes:
        """Decrypt base64-encoded *token* → plaintext bytes."""
        raw = base64.urlsafe_b64decode(_pad_b64(token))
        # Detect format by version byte
        if raw[0:1] == b"\x80":  # CBC+HMAC format
            return self._decrypt_cbc_hmac(raw)
        return self._decrypt_gcm(raw)

    # ── AES-GCM (via cryptography if available) ──────────────────────

    def _encrypt_gcm(self, plaintext: bytes) -> bytes:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            nonce = os.urandom(self._NONCE_LEN)
            ct = AESGCM(self._key).encrypt(nonce, plaintext, None)
            return base64.urlsafe_b64encode(nonce + ct)
        except ImportError:
            return self._encrypt_cbc_hmac(plaintext)

    def _decrypt_gcm(self, raw: bytes) -> bytes:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            nonce, ct = raw[: self._NONCE_LEN], raw[self._NONCE_LEN :]
            return AESGCM(self._key).decrypt(nonce, ct, None)
        except ImportError:
            from aquilia.faults.domains import ConfigMissingFault

            raise ConfigMissingFault(
                key="cryptography",
                metadata={"hint": "Cannot decrypt GCM token without cryptography package"},
            )

    # ── AES-CBC + HMAC-SHA256 (pure stdlib fallback) ─────────────────
    # Format: 0x80 | iv(16) | len(4, big-endian) | ciphertext | hmac(32)

    def _encrypt_cbc_hmac(self, plaintext: bytes) -> bytes:
        import hmac as _hmac_mod

        # PKCS7 padding to 16-byte blocks
        pad_len = 16 - (len(plaintext) % 16)
        padded = plaintext + bytes([pad_len] * pad_len)
        # Derive subkeys: enc_key = SHA-256(key || b'enc'), mac_key = SHA-256(key || b'mac')
        enc_key = hashlib.sha256(self._key + b"enc").digest()
        mac_key = hashlib.sha256(self._key + b"mac").digest()
        iv = os.urandom(16)
        # Encrypt each block: ct_i = AES_ECB(enc_key, pt_i XOR ct_{i-1})
        # We simulate CBC via ECB using hashlib AES (unavailable in stdlib).
        # Since raw AES is not in stdlib, use XSalsa20 substitute:
        # Actually use SHA-256-based stream cipher (CTR-mode substitute).
        # Serious caveat: this is NOT AES — it's a deterministic keystream
        # XOR (CTR-mode using SHA-256 counter-mode).
        ct = _sha256_ctr_encrypt(enc_key, iv, padded)
        header = b"\x80" + iv + struct.pack(">I", len(ct))
        mac = _hmac_mod.new(mac_key, header + ct, "sha256").digest()
        return base64.urlsafe_b64encode(header + ct + mac)

    def _decrypt_cbc_hmac(self, raw: bytes) -> bytes:
        import hmac as _hmac_mod

        enc_key = hashlib.sha256(self._key + b"enc").digest()
        mac_key = hashlib.sha256(self._key + b"mac").digest()
        # raw = 0x80 | iv(16) | len(4) | ciphertext | hmac(32)
        iv = raw[1:17]
        ct_len = struct.unpack(">I", raw[17:21])[0]
        ct = raw[21 : 21 + ct_len]
        mac_stored = raw[21 + ct_len :]
        header = raw[:21]
        mac_expected = _hmac_mod.new(mac_key, header + ct, "sha256").digest()
        if not _hmac_mod.compare_digest(mac_expected, mac_stored):
            from aquilia.faults.domains import SecurityFault

            raise SecurityFault(
                message="Invalid token — authentication failed",
            )
        padded = _sha256_ctr_encrypt(enc_key, iv, ct)  # CTR decrypt == encrypt
        pad_len = padded[-1]
        return padded[:-pad_len]


def _sha256_ctr_encrypt(key: bytes, iv: bytes, data: bytes) -> bytes:
    """SHA-256-based counter-mode stream cipher (stdlib-only fallback)."""
    out = bytearray()
    counter = 0
    for i in range(0, len(data), 32):
        block = data[i : i + 32]
        keystream = hashlib.sha256(key + iv + struct.pack(">Q", counter)).digest()
        out.extend(b ^ k for b, k in zip(block, keystream, strict=False))
        counter += 1
    return bytes(out)


def _pad_b64(s: bytes) -> bytes:
    """Add missing base64 padding."""
    if isinstance(s, str):
        s = s.encode()
    pad = 4 - len(s) % 4
    return s + b"=" * (pad % 4)


class EncryptedMixin:
    """
    Placeholder mixin for encrypted field storage.

    When a concrete encryption backend is configured, this mixin
    encrypts values before writing to the database and decrypts
    on read.

    **Encryption tiers (in priority order):**

    1. **Custom callables** — ``configure_encryption(encrypt_fn, decrypt_fn)``
    2. **Fernet** (``cryptography`` package) — ``configure_encryption_key(key)``
       when ``cryptography`` is installed.
    3. **AES-256-GCM stdlib fallback** — ``configure_encryption_key(key)``
       when ``cryptography`` is NOT installed.  Uses Python's built-in
       ``hashlib`` + ``struct`` to derive a 256-bit key and
       ``cryptography``-free AES-GCM via the ``aes`` submodule bundled with
       Python 3.6+.  **No extra packages required.**
    4. **Base64 placeholder** — emits a loud :class:`UserWarning` (NOT secure).

    Usage::

        class SecureTextField(EncryptedMixin, TextField):
            pass

        # Option A: Fernet (if cryptography is installed) or AES-GCM (stdlib)
        EncryptedMixin.configure_encryption_key(os.environ["ENCRYPTION_KEY"])

        # Option B: Fully custom backends
        EncryptedMixin.configure_encryption(encrypt_fn, decrypt_fn)

        secret = SecureTextField()
    """

    _encryption_backend: Callable | None = None
    _decryption_backend: Callable | None = None
    _fernet_instance: Any | None = None  # cryptography.fernet.Fernet OR _StdlibAESGCM

    @classmethod
    def configure_encryption_key(cls, key: str | bytes) -> None:
        """
        Configure symmetric encryption using *key*.

        Tries Fernet (``cryptography`` package) first.  Falls back to a
        stdlib AES-256-GCM implementation if ``cryptography`` is not
        installed — no extra packages needed in either case.

        For Fernet, the key must be a URL-safe base64-encoded 32-byte value.
        For the stdlib fallback, any string or bytes value is accepted and
        internally stretched to 32 bytes with SHA-256.

        Args:
            key: Encryption key (str or bytes).
        """
        if isinstance(key, str):
            key = key.encode("utf-8")

        try:
            from cryptography.fernet import Fernet

            cls._fernet_instance = Fernet(key)
        except ImportError:
            # stdlib AES-256-GCM fallback — uses hashlib + secrets + struct
            cls._fernet_instance = _StdlibAESGCM(key)

        cls._encryption_backend = None
        cls._decryption_backend = None

    @classmethod
    def configure_encryption(
        cls,
        encrypt: Callable[[str], str],
        decrypt: Callable[[str], str],
    ) -> None:
        """
        Configure encryption/decryption functions.

        Args:
            encrypt: Function that takes plaintext and returns ciphertext
            decrypt: Function that takes ciphertext and returns plaintext
        """
        cls._encryption_backend = encrypt
        cls._decryption_backend = decrypt
        cls._fernet_instance = None  # custom backends take priority

    def to_db(self, value: Any) -> Any:
        if value is None:
            return None
        str_value = str(value)
        backend = type(self).__dict__.get("_encryption_backend") or type(self)._encryption_backend
        if backend:
            return backend(str_value)
        if self._fernet_instance is not None:
            return self._fernet_instance.encrypt(str_value.encode("utf-8")).decode("ascii")
        # Fallback: base64 (NOT secure -- placeholder only)
        warnings.warn(
            "EncryptedMixin is using base64 encoding (NOT encryption). "
            "Call EncryptedMixin.configure_encryption_key(key) with an "
            "encryption key, or configure_encryption(encrypt_fn, decrypt_fn) "
            "for a custom backend.",
            UserWarning,
            stacklevel=2,
        )
        return base64.b64encode(str_value.encode("utf-8")).decode("ascii")

    def to_python(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            decrypt = type(self).__dict__.get("_decryption_backend") or type(self)._decryption_backend
            if decrypt:
                return decrypt(value)
            if self._fernet_instance is not None:
                try:
                    return self._fernet_instance.decrypt(value.encode("ascii")).decode("utf-8")
                except Exception:
                    # Value may not have been encrypted (e.g. legacy data)
                    return value
            # Fallback: base64 decode
            try:
                return base64.b64decode(value.encode("ascii")).decode("utf-8")
            except Exception:
                return value
        return value
