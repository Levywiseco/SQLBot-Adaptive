import base64
import hashlib

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from common.core.config import settings

TRANSPORT_PREFIX = 'adaptive:rsa-oaep:v1:'
ENCRYPTED_PREFIX = 'adaptive:encrypted:v1:'

_transport_private_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)


def get_transport_public_key() -> str:
    return _transport_private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode('ascii')


def _fernet() -> Fernet:
    digest = hashlib.sha256(settings.SECRET_KEY.encode('utf-8')).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _decrypt_transport(text: str) -> str:
    payload = base64.b64decode(text.removeprefix(TRANSPORT_PREFIX), validate=True)
    plaintext = _transport_private_key.decrypt(
        payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    return plaintext.decode('utf-8')

async def sqlbot_decrypt(text: str) -> str:
    if text.startswith(TRANSPORT_PREFIX):
        return _decrypt_transport(text)
    if text.startswith(ENCRYPTED_PREFIX):
        token = text.removeprefix(ENCRYPTED_PREFIX).encode('ascii')
        return _fernet().decrypt(token).decode('utf-8')

    # Transitional read compatibility for secrets written before the migration.
    from sqlbot_xpack.core import sqlbot_decrypt as xpack_sqlbot_decrypt
    return await xpack_sqlbot_decrypt(text)

async def sqlbot_encrypt(text: str) -> str:
    if text.startswith(ENCRYPTED_PREFIX):
        return text
    if text.startswith(TRANSPORT_PREFIX):
        text = _decrypt_transport(text)
    token = _fernet().encrypt(text.encode('utf-8')).decode('ascii')
    return f'{ENCRYPTED_PREFIX}{token}'
