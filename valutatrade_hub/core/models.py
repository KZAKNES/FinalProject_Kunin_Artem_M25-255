import datetime
import hashlib
from typing import Optional


class User:
    def __init__(self, user_id: int, username: str, password: str,
                 registration_date: Optional[datetime.datetime] = None):
        self._user_id = user_id
        self._username = username
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(password, self._salt)
        self._registration_date = registration_date or datetime.datetime.now()

    def _generate_salt(self) -> str:
        """Соль для пароля"""
        import secrets
        return secrets.token_hex(16)

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def get_user_info(self) -> dict:
        """Возвращает данные пользователя без пароля"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat()
        }

    def change_password(self, new_password: str) -> None:
        """Изменяет пароль пользователя."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        self._salt = self._generate_salt()
        self._hashed_password = self._hash_password(new_password, self._salt)

    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль"""
        return self._hashed_password == self._hash_password(password, self._salt)

    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str) -> None:
        if not value:
            raise ValueError("Имя не может быть пустым.")
        self._username = value

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime.datetime:
        return self._registration_date
