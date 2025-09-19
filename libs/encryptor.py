from cryptography.fernet import Fernet

class Encryptor:
    @staticmethod
    def generate_key() -> str:
        """
        Generate a new encryption key (base64 string).
        Safe to store in a database or environment variable.
        """
        return Fernet.generate_key().decode()

    def __init__(self, key: str):
        """
        Initialize with a base64-encoded key string.
        """
        self.key = key.encode()
        self.cipher = Fernet(self.key)

    def encrypt(self, data: str) -> str:
        """
        Encrypt a string and return base64-encoded ciphertext.
        """
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        """
        Decrypt a base64-encoded ciphertext back to plain string.
        """
        return self.cipher.decrypt(token.encode()).decode()
