from __future__ import annotations

import base64
import hashlib
import hmac
import os
from functools import lru_cache

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM  # type: ignore[attr-defined]
except ImportError:  # pragma: no cover - optional dependency fallback
    class AESGCM:  # type: ignore[override]
        """Lightweight XOR+HMAC wrapper used when cryptography is unavailable."""

        _TAG_LENGTH = 32

        def __init__(self, key: bytes) -> None:
            if not isinstance(key, (bytes, bytearray)):
                raise TypeError("key must be bytes")
            self._key = bytes(key)

        def _expand(self, nonce: bytes, length: int) -> bytes:
            counter = 0
            output = bytearray()
            while len(output) < length:
                counter_bytes = counter.to_bytes(4, "big")
                digest = hashlib.sha256(nonce + counter_bytes + self._key).digest()
                output.extend(digest)
                counter += 1
            return bytes(output[:length])

        def encrypt(self, nonce: bytes, data: bytes, associated_data: bytes | None) -> bytes:
            stream = self._expand(nonce, len(data))
            ciphertext = bytes(a ^ b for a, b in zip(data, stream))
            mac = hmac.new(self._key, nonce + ciphertext + (associated_data or b""), hashlib.sha256).digest()
            return ciphertext + mac

        def decrypt(self, nonce: bytes, data: bytes, associated_data: bytes | None) -> bytes:
            if len(data) < self._TAG_LENGTH:
                raise ValueError("ciphertext too short")
            ciphertext, tag = data[:-self._TAG_LENGTH], data[-self._TAG_LENGTH:]
            expected = hmac.new(self._key, nonce + ciphertext + (associated_data or b""), hashlib.sha256).digest()
            if not hmac.compare_digest(tag, expected):
                raise ValueError("authentication failed")
            stream = self._expand(nonce, len(ciphertext))
            return bytes(a ^ b for a, b in zip(ciphertext, stream))

from app.settings import get_settings


class EncryptionError(Exception):
    """Raised when encryption key configuration is invalid."""


@lru_cache(maxsize=1)
def _load_key() -> bytes:
    settings = get_settings()
    raw = settings.encryption_key.strip()
    if not raw:
        raise EncryptionError("ENCRYPTION_KEY is required")

    candidates: list[bytes] = []
    try:
        candidates.append(base64.urlsafe_b64decode(raw))
    except Exception:
        pass
    try:
        candidates.append(bytes.fromhex(raw))
    except ValueError:
        pass
    candidates.append(raw.encode("utf-8"))

    for key in candidates:
        if len(key) in {16, 24, 32}:
            return key
    raise EncryptionError("ENCRYPTION_KEY must decode to 16, 24, or 32 bytes")


def encrypt_secret(plaintext: str) -> str:
    key = _load_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_secret(ciphertext_b64: str) -> str:
    key = _load_key()
    data = base64.urlsafe_b64decode(ciphertext_b64.encode("utf-8"))
    nonce, ciphertext = data[:12], data[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def mask_token(token: str) -> str:
    if len(token) <= 4:
        return token
    return f"{token[:4]}" + "•" * (len(token) - 4)


def compute_worker_signature(secret: str, payload: bytes, timestamp: str) -> str:
    message = payload + timestamp.encode("utf-8")
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return digest


def verify_worker_signature(secret: str, payload: bytes, timestamp: str, signature: str) -> bool:
    expected = compute_worker_signature(secret, payload, timestamp)
    return hmac.compare_digest(expected, signature)
