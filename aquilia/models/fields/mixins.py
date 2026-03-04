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
import datetime
import hashlib
import warnings
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ..fields_module import Field


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


class EncryptedMixin:
    """
    Placeholder mixin for encrypted field storage.

    When a concrete encryption backend is configured, this mixin
    encrypts values before writing to the database and decrypts
    on read. Without a backend, it stores values as base64-encoded
    strings and emits a deprecation warning.

    By default, uses ``cryptography.fernet.Fernet`` symmetric encryption
    when a key is provided via ``configure_encryption_key()``. Falls back
    to base64 encoding (NOT secure) with a loud warning if neither a
    Fernet key nor custom backends are configured.

    Usage:
        class SecureTextField(EncryptedMixin, TextField):
            pass

        # Option 1: Provide a Fernet key (recommended)
        EncryptedMixin.configure_encryption_key(os.environ["ENCRYPTION_KEY"])

        # Option 2: Provide custom encrypt/decrypt callables
        EncryptedMixin.configure_encryption(encrypt_fn, decrypt_fn)

        secret = SecureTextField()
    """

    _encryption_backend: Optional[Callable] = None
    _decryption_backend: Optional[Callable] = None
    _fernet_instance: Optional[Any] = None  # cryptography.fernet.Fernet

    @classmethod
    def configure_encryption_key(cls, key: Union[str, bytes]) -> None:
        """
        Configure symmetric Fernet encryption using a key.

        The key must be a URL-safe base64-encoded 32-byte key.
        Generate one with ``cryptography.fernet.Fernet.generate_key()``.

        Args:
            key: Fernet-compatible encryption key (str or bytes).
        """
        try:
            from cryptography.fernet import Fernet
        except ImportError:
            raise ImportError(
                "The 'cryptography' package is required for Fernet encryption. "
                "Install it with: pip install cryptography"
            )
        if isinstance(key, str):
            key = key.encode("utf-8")
        cls._fernet_instance = Fernet(key)
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
        backend = type(self).__dict__.get('_encryption_backend') or type(self)._encryption_backend
        if backend:
            return backend(str_value)
        if self._fernet_instance is not None:
            return self._fernet_instance.encrypt(
                str_value.encode("utf-8")
            ).decode("ascii")
        # Fallback: base64 (NOT secure -- placeholder only)
        warnings.warn(
            "EncryptedMixin is using base64 encoding (NOT encryption). "
            "Call EncryptedMixin.configure_encryption_key(key) with a Fernet "
            "key, or configure_encryption(encrypt_fn, decrypt_fn) for a custom backend.",
            UserWarning,
            stacklevel=2,
        )
        return base64.b64encode(str_value.encode("utf-8")).decode("ascii")

    def to_python(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, str):
            decrypt = type(self).__dict__.get('_decryption_backend') or type(self)._decryption_backend
            if decrypt:
                return decrypt(value)
            if self._fernet_instance is not None:
                try:
                    return self._fernet_instance.decrypt(
                        value.encode("ascii")
                    ).decode("utf-8")
                except Exception:
                    # Value may not have been encrypted (e.g. legacy data)
                    return value
            # Fallback: base64 decode
            try:
                return base64.b64decode(value.encode("ascii")).decode("utf-8")
            except Exception:
                return value
        return value
