import json
import os
from typing import Any, Dict, List, Optional

from valutatrade_hub.core.exceptions import ApiRequestError
from valutatrade_hub.infra.settings import SettingsLoader


class DatabaseManager:
    """Синглтон для работы с JSON"""

    _instance: Optional['DatabaseManager'] = None
    _initialized: bool = False

    def __new__(cls) -> 'DatabaseManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Инициализация синглтона только при первом вызове"""
        if not self._initialized:
            self._settings = SettingsLoader()
            self.__class__._initialized = True

    def _get_file_path(self, filename: str) -> str:
        """Получает полный путь к файлу данных"""
        data_path = self._settings.data_path
        return os.path.join(data_path, filename)

    def load_data(self, filename: str) -> List[Dict[str, Any]]:
        file_path = self._get_file_path(filename)

        if not os.path.exists(file_path):
            return []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
                else:
                    return []
        except json.JSONDecodeError as e:
            raise ApiRequestError(f"Ошибка парсинга JSON файла {filename}: "
                f"{str(e)}") from e
        except Exception as e:
            raise ApiRequestError(f"Ошибка чтения файла {filename}: "
                f"{str(e)}") from e

    def save_data(self, data: List[Dict[str, Any]], filename: str) -> None:
        file_path = self._get_file_path(filename)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
        except Exception as e:
            raise ApiRequestError(f"Ошибка записи в файл {filename}: {str(e)}") from e

    def get_rates_timestamp(self, filename: str = 'rates.json') -> Optional[float]:
        file_path = self._get_file_path(filename)

        if not os.path.exists(file_path):
            return None

        try:
            return os.path.getmtime(file_path)
        except Exception:
            return None
