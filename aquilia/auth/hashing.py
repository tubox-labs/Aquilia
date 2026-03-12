"""
AquilAuth - Password Hashing

Production-grade, multi-algorithm password hashing engine.

Supported algorithms (ordered by recommendation):
  1. **argon2id** — Memory-hard, GPU-resistant, PHC winner.
     Requires: ``pip install argon2-cffi``
  2. **scrypt** — Memory-hard KDF, built into Python ``hashlib`` (3.6+). No extra deps.
  3. **bcrypt** — Time-tested Blowfish-based KDF. Requires: ``pip install bcrypt``
  4. **pbkdf2_sha512** — PBKDF2-HMAC-SHA-512, built-in ``hashlib``. NIST SP 800-132.
  5. **pbkdf2_sha256** — PBKDF2-HMAC-SHA-256, built-in ``hashlib``. Legacy fallback.

All outputs are self-describing PHC-format strings so ``verify()``
always picks the correct back-end.

OWASP 2024 recommended minimums are used as defaults.
"""

from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from typing import Any

from aquilia.faults.domains import ConfigInvalidFault

# ── Optional C-accelerated backends ────────────────────────────────────────

try:
    from argon2 import PasswordHasher as Argon2PasswordHasher
    from argon2.exceptions import InvalidHashError as InvalidHash
    from argon2.exceptions import VerifyMismatchError

    HAS_ARGON2 = True
except ImportError:
    HAS_ARGON2 = False

try:
    import bcrypt as _bcrypt_mod

    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False


# ============================================================================
# HasherConfig — algorithm parameters in a portable data object
# ============================================================================

SUPPORTED_ALGORITHMS = (
    "argon2id",
    "scrypt",
    "bcrypt",
    "pbkdf2_sha512",
    "pbkdf2_sha256",
)


@dataclass
class HasherConfig:
    """
    Algorithm-agnostic configuration for :class:`PasswordHasher`.

    Instantiate directly, or use :meth:`from_dict` / the
    ``AquilaConfig.PasswordHasher`` builder from ``aquilia.pyconfig``.

    Example::

        cfg = HasherConfig(algorithm="argon2id", time_cost=3, memory_cost=131072)
        hasher = PasswordHasher.from_config(cfg)
    """

    algorithm: str = "argon2id"

    # Argon2
    time_cost: int = 2
    memory_cost: int = 65536  # 64 MiB (KiB units)
    parallelism: int = 4
    hash_len: int = 32
    salt_len: int = 16

    # scrypt
    scrypt_n: int = 32768
    scrypt_r: int = 8
    scrypt_p: int = 1
    scrypt_dklen: int = 32

    # bcrypt
    bcrypt_rounds: int = 12

    # PBKDF2
    pbkdf2_iterations: int = 600_000
    pbkdf2_sha512_iterations: int = 210_000
    pbkdf2_dklen: int = 32

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HasherConfig:
        """Build from a plain dict (e.g. serialised from ``pyconfig``)."""
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return asdict(self)


# ============================================================================
# PasswordHasher — multi-algorithm password hashing engine
# ============================================================================


class PasswordHasher:
    """
    Multi-algorithm password hasher with automatic algorithm detection.

    Supports argon2id, scrypt, bcrypt, PBKDF2-SHA-256, and PBKDF2-SHA-512.
    Hash strings are self-describing (PHC format) so ``verify()`` always
    picks the correct back-end regardless of what ``algorithm`` was
    configured at construction time.

    Usage::

        hasher = PasswordHasher()                       # argon2id (default)
        hasher = PasswordHasher(algorithm="scrypt")     # scrypt (zero-dep)
        hasher = PasswordHasher.from_config(cfg)        # from HasherConfig

        hashed = hasher.hash("s3cret")
        assert hasher.verify(hashed, "s3cret")
    """

    def __init__(
        self,
        algorithm: str | None = None,
        # Argon2
        time_cost: int = 2,
        memory_cost: int = 65536,
        parallelism: int = 4,
        hash_len: int = 32,
        salt_len: int = 16,
        # scrypt
        scrypt_n: int = 32768,
        scrypt_r: int = 8,
        scrypt_p: int = 1,
        scrypt_dklen: int = 32,
        # bcrypt
        bcrypt_rounds: int = 12,
        # PBKDF2
        pbkdf2_iterations: int = 600_000,
        pbkdf2_sha512_iterations: int = 210_000,
        pbkdf2_dklen: int = 32,
        # Legacy compat
        iterations: int | None = None,
    ):
        # Auto-detect best available algorithm
        if algorithm is None:
            algorithm = "argon2id" if HAS_ARGON2 else "pbkdf2_sha256"

        if algorithm not in SUPPORTED_ALGORITHMS:
            raise ConfigInvalidFault(
                key="auth.hashing.algorithm",
                reason=f"Unsupported algorithm {algorithm!r}. Choose from: {', '.join(SUPPORTED_ALGORITHMS)}",
            )

        self.algorithm = algorithm

        # ── Argon2 ──────────────────────────────────────────────────
        self.time_cost = time_cost
        self.memory_cost = memory_cost
        self.parallelism = parallelism
        self.hash_len = hash_len
        self.salt_len = salt_len

        if algorithm == "argon2id":
            if not HAS_ARGON2:
                raise ImportError("argon2-cffi not installed. Install with: pip install argon2-cffi")
            self._argon2 = Argon2PasswordHasher(
                time_cost=time_cost,
                memory_cost=memory_cost,
                parallelism=parallelism,
                hash_len=hash_len,
                salt_len=salt_len,
            )

        # ── scrypt ──────────────────────────────────────────────────
        self.scrypt_n = scrypt_n
        self.scrypt_r = scrypt_r
        self.scrypt_p = scrypt_p
        self.scrypt_dklen = scrypt_dklen

        # ── bcrypt ──────────────────────────────────────────────────
        self.bcrypt_rounds = bcrypt_rounds
        if algorithm == "bcrypt" and not HAS_BCRYPT:
            raise ImportError("bcrypt not installed. Install with: pip install bcrypt")

        # ── PBKDF2 ─────────────────────────────────────────────────
        self.pbkdf2_iterations = iterations or pbkdf2_iterations
        self.pbkdf2_sha512_iterations = pbkdf2_sha512_iterations
        self.pbkdf2_dklen = pbkdf2_dklen

    @classmethod
    def from_config(cls, config: HasherConfig) -> PasswordHasher:
        """Build a PasswordHasher from a :class:`HasherConfig`."""
        return cls(
            algorithm=config.algorithm,
            time_cost=config.time_cost,
            memory_cost=config.memory_cost,
            parallelism=config.parallelism,
            hash_len=config.hash_len,
            salt_len=config.salt_len,
            scrypt_n=config.scrypt_n,
            scrypt_r=config.scrypt_r,
            scrypt_p=config.scrypt_p,
            scrypt_dklen=config.scrypt_dklen,
            bcrypt_rounds=config.bcrypt_rounds,
            pbkdf2_iterations=config.pbkdf2_iterations,
            pbkdf2_sha512_iterations=config.pbkdf2_sha512_iterations,
            pbkdf2_dklen=config.pbkdf2_dklen,
        )

    # ════════════════════════════════════════════════════════════════
    #  hash()
    # ════════════════════════════════════════════════════════════════

    def hash(self, password: str) -> str:
        """Hash *password* with the configured algorithm (PHC format output)."""
        algo = self.algorithm
        if algo == "argon2id":
            return self._hash_argon2(password)
        elif algo == "scrypt":
            return self._hash_scrypt(password)
        elif algo == "bcrypt":
            return self._hash_bcrypt(password)
        elif algo == "pbkdf2_sha512":
            return self._hash_pbkdf2(password, "sha512", self.pbkdf2_sha512_iterations)
        else:
            return self._hash_pbkdf2(password, "sha256", self.pbkdf2_iterations)

    # ════════════════════════════════════════════════════════════════
    #  verify()
    # ════════════════════════════════════════════════════════════════

    def verify(self, password_hash: str, password: str) -> bool:
        """Verify *password* against *password_hash* (auto-detects algorithm)."""
        try:
            if password_hash.startswith("$argon2"):
                return self._verify_argon2(password_hash, password)
            elif password_hash.startswith("$scrypt$"):
                return self._verify_scrypt(password_hash, password)
            elif password_hash.startswith(("$2b$", "$2a$", "$2y$")):
                return self._verify_bcrypt(password_hash, password)
            elif password_hash.startswith("$pbkdf2_sha512$"):
                return self._verify_pbkdf2(password_hash, password, "sha512")
            elif password_hash.startswith("$pbkdf2_sha256$"):
                return self._verify_pbkdf2(password_hash, password, "sha256")
            else:
                return False
        except Exception:
            return False

    async def hash_async(self, password: str) -> str:
        """Hash password without blocking the event loop."""
        import asyncio

        return await asyncio.to_thread(self.hash, password)

    async def verify_async(self, password_hash: str, password: str) -> bool:
        """Verify password without blocking the event loop."""
        import asyncio

        return await asyncio.to_thread(self.verify, password_hash, password)

    # ════════════════════════════════════════════════════════════════
    #  Rehash detection
    # ════════════════════════════════════════════════════════════════

    def check_needs_rehash(self, password_hash: str) -> bool:
        """Check if *password_hash* should be regenerated with current params."""
        if self.algorithm == "argon2id" and HAS_ARGON2:
            if password_hash.startswith("$argon2"):
                try:
                    return self._argon2.check_needs_rehash(password_hash)
                except (InvalidHash, AttributeError):
                    return True
            return True

        if self.algorithm == "scrypt":
            if not password_hash.startswith("$scrypt$"):
                return True
            try:
                parts = password_hash.split("$")
                param_dict = dict(p.split("=") for p in parts[2].split(","))
                return (
                    int(param_dict.get("n", 0)) != self.scrypt_n
                    or int(param_dict.get("r", 0)) != self.scrypt_r
                    or int(param_dict.get("p", 0)) != self.scrypt_p
                )
            except (IndexError, ValueError):
                return True

        if self.algorithm == "bcrypt":
            if not password_hash.startswith(("$2b$", "$2a$", "$2y$")):
                return True
            try:
                rounds = int(password_hash.split("$")[2])
                return rounds != self.bcrypt_rounds
            except (IndexError, ValueError):
                return True

        if self.algorithm == "pbkdf2_sha512":
            if not password_hash.startswith("$pbkdf2_sha512$"):
                return True
            try:
                iterations = int(password_hash.split("$")[2])
                return iterations != self.pbkdf2_sha512_iterations
            except (IndexError, ValueError):
                return True

        if self.algorithm == "pbkdf2_sha256":
            if not password_hash.startswith("$pbkdf2_sha256$"):
                return True
            try:
                iterations = int(password_hash.split("$")[2])
                return iterations != self.pbkdf2_iterations
            except (IndexError, ValueError):
                return True

        return True

    # ── Argon2id ───────────────────────────────────────────────────

    def _hash_argon2(self, password: str) -> str:
        return self._argon2.hash(password)

    def _verify_argon2(self, password_hash: str, password: str) -> bool:
        if not HAS_ARGON2:
            return False
        try:
            hasher = getattr(self, "_argon2", None)
            if hasher is None:
                hasher = Argon2PasswordHasher()
            hasher.verify(password_hash, password)
            return True
        except VerifyMismatchError:
            return False

    # ── scrypt (stdlib — zero deps) ────────────────────────────────

    def _hash_scrypt(self, password: str) -> str:
        salt = secrets.token_bytes(self.salt_len)
        dk = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=self.scrypt_n,
            r=self.scrypt_r,
            p=self.scrypt_p,
            dklen=self.scrypt_dklen,
        )
        salt_b64 = base64.b64encode(salt).decode()
        dk_b64 = base64.b64encode(dk).decode()
        params = f"n={self.scrypt_n},r={self.scrypt_r},p={self.scrypt_p}"
        return f"$scrypt${params}${salt_b64}${dk_b64}"

    def _verify_scrypt(self, password_hash: str, password: str) -> bool:
        try:
            parts = password_hash.split("$")
            if len(parts) != 5 or parts[1] != "scrypt":
                return False
            param_dict = dict(p.split("=") for p in parts[2].split(","))
            n, r, p = int(param_dict["n"]), int(param_dict["r"]), int(param_dict["p"])
            salt = base64.b64decode(parts[3])
            stored = base64.b64decode(parts[4])
            computed = hashlib.scrypt(
                password.encode(),
                salt=salt,
                n=n,
                r=r,
                p=p,
                dklen=len(stored),
            )
            return secrets.compare_digest(computed, stored)
        except (IndexError, ValueError, KeyError):
            return False

    # ── bcrypt ─────────────────────────────────────────────────────

    def _hash_bcrypt(self, password: str) -> str:
        salt = _bcrypt_mod.gensalt(rounds=self.bcrypt_rounds)
        return _bcrypt_mod.hashpw(password.encode(), salt).decode()

    def _verify_bcrypt(self, password_hash: str, password: str) -> bool:
        if not HAS_BCRYPT:
            return False
        try:
            return _bcrypt_mod.checkpw(password.encode(), password_hash.encode())
        except (ValueError, TypeError):
            return False

    # ── PBKDF2 (SHA-256 / SHA-512) ────────────────────────────────

    def _hash_pbkdf2(self, password: str, digest: str, iterations: int) -> str:
        salt = secrets.token_bytes(self.salt_len)
        dk = hashlib.pbkdf2_hmac(
            digest,
            password.encode(),
            salt,
            iterations,
            dklen=self.pbkdf2_dklen,
        )
        salt_b64 = base64.b64encode(salt).decode()
        dk_b64 = base64.b64encode(dk).decode()
        tag = f"pbkdf2_{digest}"
        return f"${tag}${iterations}${salt_b64}${dk_b64}"

    def _verify_pbkdf2(self, password_hash: str, password: str, digest: str) -> bool:
        try:
            tag = f"pbkdf2_{digest}"
            parts = password_hash.split("$")
            if len(parts) != 5 or parts[1] != tag:
                return False
            iterations = int(parts[2])
            salt = base64.b64decode(parts[3])
            stored = base64.b64decode(parts[4])
            computed = hashlib.pbkdf2_hmac(
                digest,
                password.encode(),
                salt,
                iterations,
                dklen=len(stored),
            )
            return secrets.compare_digest(computed, stored)
        except (IndexError, ValueError):
            return False


# ============================================================================
# Password Validation
# ============================================================================


class PasswordPolicy:
    """
    Password policy validator.

    Enforces:
    - Minimum length
    - Character requirements (uppercase, lowercase, digit, special)
    - Breached password check (optional, requires external API)
    - Common password blacklist
    """

    def __init__(
        self,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digit: bool = True,
        require_special: bool = False,
        check_breached: bool = False,
    ):
        self.min_length = min_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digit = require_digit
        self.require_special = require_special
        self.check_breached = check_breached

        self.blacklist = {
            "password",
            "password123",
            "12345678",
            "qwerty",
            "abc123",
            "monkey",
            "1234567",
            "letmein",
            "trustno1",
            "dragon",
            "baseball",
            "iloveyou",
            "master",
            "sunshine",
            "ashley",
            "bailey",
            "passw0rd",
            "shadow",
            "123123",
            "654321",
        }

    def validate(self, password: str) -> tuple[bool, list[str]]:
        """Validate password against policy. Returns (is_valid, errors)."""
        errors = []

        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters")

        if self.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if self.require_lowercase and not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if self.require_digit and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        if self.require_special:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain at least one special character")

        if password.lower() in self.blacklist:
            errors.append("Password is too common")

        if self.check_breached and self._is_breached(password):
            errors.append("Password has been found in data breaches")

        return (len(errors) == 0, errors)

    def _is_breached(self, password: str) -> bool:
        """Check if password has been breached (Have I Been Pwned API, k-anonymity)."""
        import urllib.request

        sha1_hash = hashlib.sha1(password.encode()).hexdigest().upper()
        prefix = sha1_hash[:5]
        suffix = sha1_hash[5:]

        try:
            url = f"https://api.pwnedpasswords.com/range/{prefix}"
            response = urllib.request.urlopen(url, timeout=2)
            hashes = response.read().decode().splitlines()
            for line in hashes:
                hash_suffix, _count = line.split(":")
                if hash_suffix == suffix:
                    return True
            return False
        except Exception:
            return False

    async def _is_breached_async(self, password: str) -> bool:
        import asyncio

        return await asyncio.to_thread(self._is_breached, password)

    async def validate_async(self, password: str) -> tuple[bool, list[str]]:
        """Async password validation (non-blocking breach check)."""
        errors = []
        original_check_breached = self.check_breached
        self.check_breached = False
        try:
            _valid, sync_errors = self.validate(password)
        finally:
            self.check_breached = original_check_breached
        errors.extend(sync_errors)
        if original_check_breached and await self._is_breached_async(password):
            errors.append("Password has been found in data breaches")
        return (len(errors) == 0, errors)


# ============================================================================
# Convenience Functions
# ============================================================================

_default_hasher: PasswordHasher | None = None


def get_password_hasher() -> PasswordHasher:
    """Get default password hasher instance."""
    global _default_hasher
    if _default_hasher is None:
        _default_hasher = PasswordHasher()
    return _default_hasher


def hash_password(password: str) -> str:
    """Hash password with default hasher."""
    return get_password_hasher().hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    """Verify password with default hasher."""
    return get_password_hasher().verify(password_hash, password)


def validate_password(password: str, policy: PasswordPolicy | None = None) -> tuple[bool, list[str]]:
    """Validate password against policy."""
    if policy is None:
        policy = PasswordPolicy()
    return policy.validate(password)
