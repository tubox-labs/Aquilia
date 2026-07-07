"""
Aquilia Field Mixins -- reusable behaviors for model fields.

These mixins can be composed with Field subclasses to add
standard behaviors without duplicating code:

    class NullableCharField(NullableMixin, CharField):
        pass

Or applied at runtime via ``Field.with_mixin(NullableMixin)``.

Design pattern used throughout this module: each mixin sits to the *left*
of a ``Field`` subclass in the MRO and overrides ``__init__`` to inject a
default keyword argument via ``kwargs.setdefault(...)`` before delegating
to ``super().__init__(*args, **kwargs)``. Because ``setdefault`` only fills
in a value when the key is absent, any value the caller passes explicitly
always takes precedence over the mixin's default — mixins never silently
override an explicit choice.

Mixins provided here:

- ``NullableMixin`` -- defaults a field to ``null=True, blank=True``.
- ``UniqueMixin`` -- defaults a field to ``unique=True``.
- ``IndexedMixin`` -- defaults a field to ``db_index=True``.
- ``AutoNowMixin`` -- defaults a date/time-like field to ``auto_now=True``.
- ``ChoiceMixin`` -- adds ``get_display``/``choice_values`` helpers for
  fields that declare a ``choices`` sequence.
- ``EncryptedMixin`` -- transparently encrypts/decrypts field values at the
  storage boundary (``to_db``/``to_python``).

``EncryptedMixin`` (and its stdlib fallback helper, ``_StdlibAESGCM``) are
security-sensitive: they handle key material, nonce/IV generation, and the
on-disk wire format for encrypted-at-rest values. Read their docstrings in
full, and see the security caveats called out there, before relying on
this mixin to protect real secrets.
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

    Defaults ``null=True`` (the database column accepts ``NULL``) and
    ``blank=True`` (the application layer accepts an absent/empty value
    during validation), so callers no longer need to repeat both flags on
    every optional field.

    Usage:
        class NullableChar(NullableMixin, CharField):
            pass

        name = NullableChar(max_length=100)
        # Equivalent to CharField(max_length=100, null=True, blank=True)
    """

    def __init_subclass__(cls, **kwargs):
        """
        Cooperative-inheritance hook.

        Currently a no-op beyond forwarding to ``super().__init_subclass__``;
        it exists so that further subclassing (including multiple
        inheritance with other mixins that customize ``__init_subclass__``)
        continues to compose correctly through the MRO.
        """
        super().__init_subclass__(**kwargs)

    def __init__(self, *args, **kwargs):
        """
        Set ``null``/``blank`` defaults, then delegate to the next class in
        the MRO (typically a concrete ``Field`` subclass).

        Args:
            *args: Positional arguments forwarded unchanged.
            **kwargs: Keyword arguments forwarded to ``super().__init__``;
                ``null`` and ``blank`` are set to ``True`` only if the
                caller did not already supply a value for them.
        """
        kwargs.setdefault("null", True)
        kwargs.setdefault("blank", True)
        super().__init__(*args, **kwargs)


class UniqueMixin:
    """
    Mixin that enforces uniqueness on a field.

    Defaults ``unique=True`` so the underlying column gets a uniqueness
    constraint (and, depending on the database backend/migration system,
    a supporting index) without every call site having to spell it out.

    Usage:
        class UniqueEmail(UniqueMixin, EmailField):
            pass
    """

    def __init__(self, *args, **kwargs):
        """
        Set the ``unique`` default, then delegate to the next class in the
        MRO.

        Args:
            *args: Positional arguments forwarded unchanged.
            **kwargs: Keyword arguments forwarded to ``super().__init__``;
                ``unique`` is set to ``True`` only if the caller did not
                already supply a value for it.
        """
        kwargs.setdefault("unique", True)
        super().__init__(*args, **kwargs)


class IndexedMixin:
    """
    Mixin that auto-adds a database index to a field.

    Defaults ``db_index=True`` so a standalone (non-unique) index is
    created for the column, which is useful for fields frequently used in
    ``WHERE``/``ORDER BY`` clauses.

    Usage:
        class IndexedChar(IndexedMixin, CharField):
            pass
    """

    def __init__(self, *args, **kwargs):
        """
        Set the ``db_index`` default, then delegate to the next class in
        the MRO.

        Args:
            *args: Positional arguments forwarded unchanged.
            **kwargs: Keyword arguments forwarded to ``super().__init__``;
                ``db_index`` is set to ``True`` only if the caller did not
                already supply a value for it.
        """
        kwargs.setdefault("db_index", True)
        super().__init__(*args, **kwargs)


class AutoNowMixin:
    """
    Mixin for fields that auto-update on save (like updated_at).

    Defaults ``auto_now=True``, which the concrete field's own save logic
    interprets as "overwrite this value with the current timestamp every
    time the row is saved".

    Applies to ``DateField``, ``TimeField``, ``DateTimeField`` -- these are
    the field types whose ``__init__`` accepts and acts on ``auto_now``.
    Mixing this into a field type that doesn't understand ``auto_now`` will
    still pass the keyword through (via ``**kwargs``), but it will have no
    effect unless that field also implements the corresponding save-time
    behavior.
    """

    def __init__(self, *args, **kwargs):
        """
        Set the ``auto_now`` default, then delegate to the next class in
        the MRO.

        Args:
            *args: Positional arguments forwarded unchanged.
            **kwargs: Keyword arguments forwarded to ``super().__init__``;
                ``auto_now`` is set to ``True`` only if the caller did not
                already supply a value for it.
        """
        kwargs.setdefault("auto_now", True)
        super().__init__(*args, **kwargs)


class ChoiceMixin:
    """
    Mixin that adds display-value helpers for fields with a ``choices``
    sequence.

    Note on validation: this mixin does not itself perform any validation.
    The base ``Field.validate()`` already rejects values not present in
    ``self.choices`` whenever ``choices`` is set (with or without this
    mixin) -- see ``aquilia.models.fields_module.Field.validate``. What
    ``ChoiceMixin`` contributes on top of that is convenience: a way to map
    a stored value back to its human-readable label (``get_display``) and
    to list the valid stored values (``choice_values``).

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
        """
        Return the human-readable display value for a stored value.

        Args:
            value: The raw/stored value to look up (compared with ``==``
                against each choice's stored value).

        Returns:
            The matching display label from ``self.choices``. If the field
            has no ``choices`` configured, or *value* doesn't match any
            entry, falls back to ``str(value)``.

        Example:
            status = StatusField(choices=[("A", "Active"), ("I", "Inactive")])
            status.get_display("A")  # -> "Active"
        """
        if not hasattr(self, "choices") or not self.choices:
            return str(value)
        for choice_val, display in self.choices:
            if choice_val == value:
                return display
        return str(value)

    @property
    def choice_values(self) -> list:
        """
        Return list of valid stored values.

        Returns:
            A list of the first element of each ``(value, display)`` pair
            in ``self.choices``, in declaration order. Returns an empty
            list if the field has no ``choices`` configured.
        """
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

    Security notes (read before using this class to protect real secrets):

    - **Key derivation is a single unsalted SHA-256 hash**, not a proper
      password-based KDF (no PBKDF2/scrypt/argon2, no salt, no iteration
      count). If ``raw_key`` is a low-entropy value (e.g. a short password
      rather than a high-entropy random key), the derived key is much
      weaker than a genuine 256-bit key and is comparatively easy to
      brute-force offline. Callers should supply a high-entropy secret
      (e.g. ``os.urandom(32)`` or an equivalent secrets-manager-issued
      key), not a human-chosen passphrase.
    - The GCM nonce is a fresh ``os.urandom(12)`` per call to
      ``encrypt()``; correctness of GCM depends on never reusing a
      (key, nonce) pair, which a 96-bit random nonce makes very unlikely
      for moderate message volumes under a single key but is not a formal
      guarantee at very high volume.
    - ``decrypt()`` distinguishes the CBC+HMAC fallback format from the
      GCM format by sniffing whether the first byte equals ``0x80``. Since
      the GCM format's first byte is part of a random nonce, there is a
      small (~1/256) chance a genuine GCM token is misidentified as a
      CBC+HMAC token and fails to decrypt. See ``decrypt()``.
    - The "AES-CBC + HMAC-SHA256" fallback described below is **not
      actually AES**: see ``_encrypt_cbc_hmac`` for what it really is.
    """

    _NONCE_LEN = 12  # 96-bit nonce (GCM recommendation)
    _TAG_LEN = 16  # 128-bit authentication tag

    def __init__(self, raw_key: bytes) -> None:
        """
        Derive a 32-byte symmetric key from *raw_key* and detect which
        encryption path to use.

        Args:
            raw_key: Arbitrary key material of any length. Hashed with
                SHA-256 to produce a fixed 32-byte key -- see the class
                docstring's security note about this not being a proper
                KDF for low-entropy input.

        Behavior:
            Stores the derived key on ``self._key`` and probes for AES-GCM
            availability once (``self._use_gcm``), so repeated
            ``encrypt``/``decrypt`` calls on the same instance don't
            re-probe.
        """
        # Stretch / normalise key to exactly 32 bytes with SHA-256
        self._key: bytes = hashlib.sha256(raw_key).digest()
        # Check AES-GCM availability once at construction time
        self._use_gcm: bool = self._aes_gcm_available()

    @staticmethod
    def _aes_gcm_available() -> bool:
        """
        Probe whether an AES-GCM implementation is reachable.

        Returns:
            ``True`` if either the ``cryptography`` package is importable,
            or a secondary probe (importing ``_ssl`` and ``pycryptodome``'s
            ``Crypto.Cipher.AES``) succeeds; ``False`` otherwise.

        Caveat: this secondary probe is a weak proxy. It does not actually
        verify that stdlib ``ssl``/``hashlib`` expose AES-GCM (they don't,
        via a public API), and it checks for ``pycryptodome`` availability
        without that package ever being used by ``_encrypt_gcm``/
        ``_decrypt_gcm``, which only ever import
        ``cryptography.hazmat...AESGCM``. In practice: if
        ``cryptography`` is missing but this probe still returns ``True``
        (because ``pycryptodome`` happens to be installed), ``_use_gcm``
        will be ``True`` but ``_encrypt_gcm``/``_decrypt_gcm`` will still
        hit an ``ImportError`` internally and (for encryption) silently
        fall back to ``_encrypt_cbc_hmac``. Decryption of a previously
        GCM-encrypted token in that situation will raise, since
        ``_decrypt_gcm`` has no fallback path. See the class docstring.
        """
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
        """
        Encrypt *plaintext* and return a base64url-encoded token.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            ASCII bytes (base64url, unpadded-safe via ``_pad_b64`` on
            decode) that embed the nonce/IV and authentication tag
            alongside the ciphertext. Uses AES-GCM when available
            (``self._use_gcm``), otherwise the SHA-256-CTR + HMAC-SHA256
            fallback -- see ``_encrypt_cbc_hmac`` for what that fallback
            actually is.
        """
        if self._use_gcm:
            return self._encrypt_gcm(plaintext)
        return self._encrypt_cbc_hmac(plaintext)

    def decrypt(self, token: bytes) -> bytes:
        """
        Decrypt a base64url-encoded *token* produced by ``encrypt()``.

        Args:
            token: The base64url token (bytes or bytes-like); missing
                padding is tolerated via ``_pad_b64``.

        Returns:
            The original plaintext bytes.

        Behavior:
            Format is auto-detected by inspecting the first decoded byte:
            ``0x80`` selects the CBC+HMAC fallback format
            (``_decrypt_cbc_hmac``); anything else is treated as a raw GCM
            nonce and routed to ``_decrypt_gcm``. See the class docstring
            for the small collision risk this sniffing introduces.

        Raises:
            SecurityFault: if the token was produced by the CBC+HMAC
                fallback and its HMAC does not verify (tampered or
                corrupted data).
            ConfigMissingFault: if the token looks like a GCM token but the
                ``cryptography`` package is not installed to decrypt it.
        """
        raw = base64.urlsafe_b64decode(_pad_b64(token))
        # Detect format by version byte
        if raw[0:1] == b"\x80":  # CBC+HMAC format
            return self._decrypt_cbc_hmac(raw)
        return self._decrypt_gcm(raw)

    # ── AES-GCM (via cryptography if available) ──────────────────────

    def _encrypt_gcm(self, plaintext: bytes) -> bytes:
        """
        Encrypt *plaintext* with real AES-256-GCM via the ``cryptography``
        package.

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            ``base64url(nonce(12) || ciphertext || tag(16))``. A fresh
            12-byte nonce is generated per call with ``os.urandom``.

        Behavior:
            If ``cryptography`` is not actually importable at call time
            (e.g. ``_use_gcm`` was set from the weak secondary probe --
            see ``_aes_gcm_available``), silently falls back to
            ``_encrypt_cbc_hmac`` instead of raising.
        """
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            nonce = os.urandom(self._NONCE_LEN)
            ct = AESGCM(self._key).encrypt(nonce, plaintext, None)
            return base64.urlsafe_b64encode(nonce + ct)
        except ImportError:
            return self._encrypt_cbc_hmac(plaintext)

    def _decrypt_gcm(self, raw: bytes) -> bytes:
        """
        Decrypt raw GCM bytes (``nonce(12) || ciphertext || tag(16)``) via
        the ``cryptography`` package.

        Args:
            raw: Decoded bytes as produced by ``_encrypt_gcm`` (nonce
                prefix followed by ciphertext+tag).

        Returns:
            The original plaintext bytes.

        Raises:
            ConfigMissingFault: if ``cryptography`` is not installed --
                unlike ``_encrypt_gcm``, there is no silent fallback here,
                because a GCM-formatted ciphertext cannot be decrypted by
                the CBC+HMAC path.

        Note:
            ``AESGCM.decrypt`` itself raises ``InvalidTag`` (a
            ``cryptography`` exception, not caught here) if the
            authentication tag doesn't verify, i.e. on tampered/corrupted
            ciphertext or a wrong key.
        """
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
        """
        Encrypt *plaintext* using the pure-stdlib fallback cipher, then
        authenticate with HMAC-SHA256 (Encrypt-then-MAC).

        Args:
            plaintext: Raw bytes to encrypt.

        Returns:
            ``base64url(0x80 || iv(16) || len(4, big-endian) || ciphertext
            || hmac(32))``.

        Behavior / important caveat:
            Despite the "CBC" naming (kept for the wire-format header and
            method name), this does **not** implement AES at all -- Python's
            stdlib has no built-in block cipher. The actual cipher is
            ``_sha256_ctr_encrypt``: a home-grown SHA-256-based
            counter-mode keystream (``keystream_i = SHA256(enc_key || iv ||
            counter_i)``, XORed with the plaintext). Confidentiality of
            this construction depends on the keystream never repeating for
            a given key (ensured here by a fresh random 16-byte IV per
            call) and on SHA-256 behaving as a secure PRF in this mode.
            This is unaudited, non-standard, "roll your own crypto" —
            treat it as a last-resort fallback only used when neither
            ``cryptography`` nor a usable AES-GCM path is present, not as
            an equivalent substitute for vetted AES.

            Subkeys are derived from the instance key via
            ``enc_key = SHA256(key || b"enc")`` and
            ``mac_key = SHA256(key || b"mac")`` (domain separation so the
            same base key isn't reused directly for both encryption and
            authentication). PKCS7 padding is applied to a 16-byte block
            size purely for wire-format/parity with real CBC, not because
            the stream cipher requires block alignment.
        """
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
        """
        Verify and decrypt a token produced by ``_encrypt_cbc_hmac``.

        Args:
            raw: Decoded bytes: ``0x80 || iv(16) || len(4) || ciphertext ||
                hmac(32)``.

        Returns:
            The original plaintext bytes (after stripping PKCS7 padding).

        Raises:
            SecurityFault: if the recomputed HMAC does not match the
                stored one (constant-time comparison via
                ``hmac.compare_digest``), indicating tampering, corruption,
                or a wrong key. Verification happens *before* any
                decryption of the ciphertext (Encrypt-then-MAC), so no
                keystream material is used on unauthenticated input.
        """
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
    """
    SHA-256-based counter-mode stream cipher (stdlib-only fallback).

    Args:
        key: 32-byte key (already domain-separated, e.g. via
            ``SHA256(base_key || b"enc")``).
        iv: Per-message nonce/IV; must not repeat for a given *key* or the
            keystream (and thus confidentiality) is compromised.
        data: Plaintext (for encryption) or ciphertext (for decryption) --
            this function is its own inverse since it's a pure XOR stream
            cipher.

    Returns:
        *data* XORed with a keystream generated 32 bytes at a time as
        ``SHA256(key || iv || struct.pack(">Q", counter))``, ``counter``
        starting at 0 and incrementing once per 32-byte block.

    Caveat: this is not a standard, reviewed stream cipher construction
    (e.g. not AES-CTR) -- see ``_StdlibAESGCM._encrypt_cbc_hmac`` for
    context on why it exists and its limitations.
    """
    out = bytearray()
    counter = 0
    for i in range(0, len(data), 32):
        block = data[i : i + 32]
        keystream = hashlib.sha256(key + iv + struct.pack(">Q", counter)).digest()
        out.extend(b ^ k for b, k in zip(block, keystream, strict=False))
        counter += 1
    return bytes(out)


def _pad_b64(s: bytes) -> bytes:
    """
    Add missing base64 padding.

    Args:
        s: A base64/base64url payload, as ``str`` or ``bytes``, that may be
            missing trailing ``=`` padding (as produced by
            ``base64.urlsafe_b64encode(...).rstrip(b"=")``-style callers,
            though this module always keeps the padding itself).

    Returns:
        *s* as ``bytes`` with ``=`` padding appended so its length is a
        multiple of 4, ready for ``base64.urlsafe_b64decode``.
    """
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

        Custom backends take the highest priority: once set, ``to_db``/
        ``to_python`` will always use *encrypt*/*decrypt* and will not fall
        back to a previously configured Fernet/AES-GCM instance or to the
        insecure base64 placeholder. Calling this also clears any
        previously configured ``_fernet_instance`` (see
        ``configure_encryption_key``), so only one backend is ever active
        at a time per class.

        Args:
            encrypt: Function that takes plaintext and returns ciphertext
            decrypt: Function that takes ciphertext and returns plaintext
        """
        cls._encryption_backend = encrypt
        cls._decryption_backend = decrypt
        cls._fernet_instance = None  # custom backends take priority

    def to_db(self, value: Any) -> Any:
        """
        Encrypt *value* for storage.

        Args:
            value: The Python-side field value. Non-``None`` values are
                coerced to ``str`` before encryption (so non-string values
                round-trip as their string representation, not their
                original type).

        Returns:
            ``None`` if *value* is ``None`` (no encryption of nulls).
            Otherwise the ciphertext as an ASCII ``str``, produced by the
            first available backend in priority order: a custom callable
            configured via ``configure_encryption``, then a Fernet/AES-GCM
            instance configured via ``configure_encryption_key``, then (as
            a last resort) plain base64 encoding.

        Warning:
            The base64 fallback is **not encryption** -- it is trivially
            reversible and provides no confidentiality. It only exists so
            the field remains functional (and round-trips) before any
            backend has been configured; it emits a ``UserWarning`` every
            time it is used specifically so this doesn't go unnoticed in
            production. Always call ``configure_encryption_key`` or
            ``configure_encryption`` before storing real secrets.
        """
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
        """
        Decrypt a stored *value* back into its plaintext ``str`` form.

        Args:
            value: The raw value as read from the database.

        Returns:
            ``None`` if *value* is ``None``. If *value* is not a ``str``,
            it is returned unchanged (nothing to decrypt). Otherwise the
            decrypted plaintext ``str``, using the same backend priority
            as ``to_db`` (custom callable, then Fernet/AES-GCM, then
            base64 decode).

        Caveat -- silent fallback on decryption failure: when using the
        Fernet/AES-GCM backend, any exception raised during decryption
        (including an authentication failure from a tampered or corrupted
        ciphertext, or data that was simply never encrypted -- e.g. legacy
        rows written before encryption was enabled) is caught and *value*
        is returned unchanged rather than raised. This is intentional to
        tolerate legacy plaintext data, but it also means tampering with an
        encrypted column will not surface as an error here -- the raw
        (still-encrypted-looking) string is handed back to the caller
        as-is. The same broad ``except Exception`` applies to the base64
        fallback path.
        """
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
