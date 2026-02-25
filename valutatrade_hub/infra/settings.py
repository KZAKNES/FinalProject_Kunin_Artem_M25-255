import json
import os
from typing import Any, Dict, Optional


class SettingsLoader:
#Реализация через __new__ из-за простоты и читабельности
    _instance: Optional['SettingsLoader'] = None
    _initialized: bool = False

    def __new__(cls) -> 'SettingsLoader':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._config: Dict[str, Any] = {}
            self._load_config()
            self.__class__._initialized = True

    def _load_config(self) -> None:
        """Подгружает конфигурацию из файла"""
        if os.path.exists('pyproject.toml'):
            try:
                import toml
                with open('pyproject.toml', 'r', encoding='utf-8') as f:
                    data = toml.load(f)
                self._config = data.get('tool', {}).get('valutatrade', {})
            except ImportError:
                pass
            except Exception:
                pass

        if not self._config and os.path.exists('config.json'):
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception:
                pass

        if not self._config:
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Возвращает конфигурацию"""
        return {
            "data_path": "data",
            "rates_ttl_seconds": 3600,  
            "default_base_currency": "USD",
            "log_path": "logs",
            "log_format": "json",
            "log_level": "INFO",
            "log_rotation": {
                "max_bytes": 10485760,  
                "backup_count": 5
            }
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Получает значение конфигурации по ключу"""
        return self._config.get(key, default)

    def reload(self) -> None:
        """Перезагружает конфигурацию из файла"""
        self._load_config()

    @property
    def data_path(self) -> str:
        """Путь к дданным"""
        return self.get('data_path', 'data')

    @property
    def rates_ttl_seconds(self) -> int:
        return self.get('rates_ttl_seconds', 3600)

    @property
    def default_base_currency(self) -> str:
        return self.get('default_base_currency', 'USD')

    @property
    def log_path(self) -> str:
        """Путь к логам"""
        return self.get('log_path', 'logs')

    @property
    def log_format(self) -> str:
        """Формат логов (string или json)."""
        return self.get('log_format', 'json')

    @property
    def log_level(self) -> str:
        """Уровень логирования (INFO, DEBUG и т.д.)."""
        return self.get('log_level', 'INFO')

    @property
    def log_rotation(self) -> Dict[str, Any]:
        return self.get('log_rotation', {
            "max_bytes": 10485760,  
            "backup_count": 5
        })
