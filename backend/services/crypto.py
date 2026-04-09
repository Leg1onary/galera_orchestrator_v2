from __future__ import annotations

import base64
import logging
import sys

from cryptography.fernet import Fernet, InvalidToken

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fernet instance — initialised once at module import time.
# If FERNET_SECRET_KEY is invalid, the application fails fast on startup.
# ---------------------------------------------------------------------------
def _init_fernet() -> Fernet:
    key = settings.FERNET_SECRET_KEY.encode()

    # Fernet requires a URL-safe base64-encoded 32-byte key.
    # Validate format eagerly so misconfiguration is caught at startup.
    try:
        decoded = base64.urlsafe_b64decode(key + b"==")  # padding-tolerant
        if len(decoded) != 32:
            raise ValueError(
                f"FERNET_SECRET_KEY must decode to exactly 32 bytes, "
                f"got {len(decoded)} bytes."
            )
    except Exception as exc:
        print(
            f"FATAL: Invalid FERNET_SECRET_KEY — {exc}. "
            "Generate with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"",
            file=sys.stderr,
        )
        # We intentionally do NOT sys.exit() here so that tests can patch
        # the key before import. In production the first encrypt/decrypt
        # call will fail with a clear error.
        raise

    return Fernet(key)


try:
    _fernet = _init_fernet()
    _fernet_available = True
except Exception:
    _fernet = None  # type: ignore[assignment]
    _fernet_available = False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def encrypt_password(plain: str) -> str:
    """
    Encrypt a plaintext database password using Fernet symmetric encryption.

    Returns the ciphertext as a UTF-8 string suitable for storage in SQLite.
    The result is deterministically decryptable with decrypt_password().

    Raises RuntimeError if Fernet is not properly initialised.
    """
    if not _fernet_available:
        raise RuntimeError(
            "Fernet encryption is not available. "
            "Check FERNET_SECRET_KEY configuration."
        )
    ciphertext: bytes = _fernet.encrypt(plain.encode("utf-8"))
    return ciphertext.decode("utf-8")


def decrypt_password(cipher: str) -> str:
    """
    Decrypt a Fernet-encrypted database password ciphertext.

    Returns the original plaintext password.

    Raises:
        RuntimeError: if Fernet is not properly initialised.
        ValueError: if the ciphertext is invalid or was encrypted with
                    a different key (e.g. after key rotation).
    """
    if not _fernet_available:
        raise RuntimeError(
            "Fernet decryption is not available. "
            "Check FERNET_SECRET_KEY configuration."
        )
    try:
        plaintext: bytes = _fernet.decrypt(cipher.encode("utf-8"))
        return plaintext.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError(
            "Failed to decrypt password — token is invalid or key has changed. "
            "If FERNET_SECRET_KEY was rotated, existing passwords cannot be recovered."
        ) from exc


def is_encrypted(value: str) -> bool:
    """
    Heuristic check: Fernet tokens start with 'gAAAAA'.
    Useful to avoid double-encrypting already-encrypted values.
    """
    return value.startswith("gAAAAA")