import json
import os
from datetime import datetime
from typing import Any, Dict, List

from valutatrade_hub.parser_service.config import ParserConfig


class StorageError(Exception):
    """Исключение ошибок"""
    pass


class RatesStorage:
    """Класс хранения курсов валют"""

    def __init__(self, config: ParserConfig):
        self.config = config

    def save_rates(self, rates: Dict[str, Dict[str, Any]]) -> None:
        try:
            data = {
                "pairs": rates,
                "last_refresh": datetime.utcnow().isoformat() + "Z"
            }

            os.makedirs(os.path.dirname(self.config.RATES_FILE_PATH), exist_ok=True)

            temp_path = self.config.RATES_FILE_PATH + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            os.replace(temp_path, self.config.RATES_FILE_PATH)

        except Exception as e:
            raise StorageError(f"Ошибка сохранения курсов: {str(e)}") from e

    def load_rates(self) -> Dict[str, Dict[str, Any]]:
        """Загрузить актуальные курсы из кэша"""
        try:
            if not os.path.exists(self.config.RATES_FILE_PATH):
                return {}

            with open(self.config.RATES_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("pairs", {})

        except Exception as e:
            raise StorageError(f"Ошибка загрузки курсов: {str(e)}") from e

    def save_history_record(self, record: Dict[str, Any]) -> None:
        """Сохранить запись в историю"""
        try:
            os.makedirs(os.path.dirname(self.config.HISTORY_FILE_PATH), exist_ok=True)

            records = []
            if os.path.exists(self.config.HISTORY_FILE_PATH):
                with open(self.config.HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                    records = json.load(f)

            records.append(record)

            temp_path = self.config.HISTORY_FILE_PATH + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)

            os.replace(temp_path, self.config.HISTORY_FILE_PATH)

        except Exception as e:
            raise StorageError(f"Ошибка сохранения истории: {str(e)}") from e

    def get_history(self) -> List[Dict[str, Any]]:
        """Получить историю"""
        try:
            if not os.path.exists(self.config.HISTORY_FILE_PATH):
                return []

            with open(self.config.HISTORY_FILE_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            raise StorageError(f"Ошибка загрузки истории: {str(e)}") from e
