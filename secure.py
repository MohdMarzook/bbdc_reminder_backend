import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet, InvalidToken

load_dotenv()

class Encryptor:
    def __init__(self, key: str):
        if not key:
            raise ValueError("ENCRYPTION_KEY not found in environment variables.")
        self._cipher_suite = Fernet(key)

    def encrypt(self, message: str):
        encoded_message = message.encode()
        encrypted_message = self._cipher_suite.encrypt(encoded_message)
        return encrypted_message.decode()

    def decrypt(self, token: str):
        try:            
            decrypted_message = self._cipher_suite.decrypt(token.encode())
            return decrypted_message.decode()
        except InvalidToken:
            print("Decryption failed: Invalid token!")
            return None

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
key = ENCRYPTION_KEY.encode()
encryptor = Encryptor(key)
