"""加密凭据存储 — 用 Fernet 对称加密"""

import json
from pathlib import Path

from cryptography.fernet import Fernet


def generate_key(key_file: Path):
    key = Fernet.generate_key()
    key_file.write_bytes(key)
    key_file.chmod(0o600)


def encrypt_credentials(key_file: Path, cred_file: Path, creds: dict):
    key = key_file.read_bytes()
    f = Fernet(key)
    data = json.dumps(creds, ensure_ascii=False).encode("utf-8")
    encrypted = f.encrypt(data)
    cred_file.write_bytes(encrypted)
    cred_file.chmod(0o600)


def decrypt_credentials(key_file: Path, cred_file: Path) -> dict:
    key = key_file.read_bytes()
    f = Fernet(key)
    encrypted = cred_file.read_bytes()
    data = f.decrypt(encrypted)
    return json.loads(data.decode("utf-8"))
