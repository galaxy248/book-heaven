import json
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import load_pem_private_key
import base64
from pathlib import Path


class TokenGenerator():
    def __init__(self) -> None:
        self.path = Path(__file__).parent
        try:
            self._private_key = self.load_private_key()
        except Exception as e:
            self._private_key = self.generate_private_key(save=True)
        
        self._public_key = self._private_key.public_key()

    def generate_private_key(self, save: bool):
        key_size = 2048

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size,
        )

        if save:
            self.save_private_key(private_key)

        return private_key


    def load_private_key(self):
        with open(self.path / 'private_key.pem', 'rb') as f:
            pem = f.read()
        
        return load_pem_private_key(pem, None)


    def save_private_key(self, key):
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open(self.path / 'private_key.pem', 'wb') as f:
            f.write(pem)

    def encrypt(self, message: dict):
        if not isinstance(message, dict):
            raise ValueError
        
        return base64.b64encode(
            self._public_key.encrypt(
                base64.b64encode(json.dumps(message).encode('ascii')),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
        )

    def decrypt(self, encrypted_message):
        return json.loads(
            base64.b64decode(
                self._private_key.decrypt(
                    base64.b64decode(encrypted_message),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            )
        )
