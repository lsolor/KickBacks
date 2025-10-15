from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass


API_KEY_BYTES = 32
API_KEY_SALT_BYTES = 16


def _sha256(value: str) -> str:
    digest = hashlib.sha256()
    digest.update(value.encode("utf-8"))
    return digest.hexdigest()


def hash_api_key(raw_key: str, salt: str) -> str:
    return _sha256(f"{salt}:{raw_key}")


def verify_api_key(raw_key: str, salt: str, expected_hash: str) -> bool:
    candidate = hash_api_key(raw_key, salt)
    return secrets.compare_digest(candidate, expected_hash)


@dataclass(frozen=True)
class GeneratedApiKey:
    raw_key: str
    salt: str
    key_hash: str


def generate_api_key() -> GeneratedApiKey:
    salt = secrets.token_hex(API_KEY_SALT_BYTES)
    raw_key = secrets.token_urlsafe(API_KEY_BYTES)
    key_hash = hash_api_key(raw_key=raw_key, salt=salt)
    return GeneratedApiKey(raw_key=raw_key, salt=salt, key_hash=key_hash)
