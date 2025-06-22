from argon2 import PasswordHasher


class PasswordManager:
    def __init__(self):
        self._ph = PasswordHasher()

    def hash_password(self, password: str) -> str:
        return self._ph.hash(password)

    def verify_password(self, hashed_password: str, password: str) -> bool:
        return self._ph.verify(hashed_password, password)
