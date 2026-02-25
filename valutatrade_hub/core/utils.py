import json
import os
from typing import Any, Dict, List


def load_data(file_path: str) -> List[Dict[str, Any]]:
    """Загружает данные из JSON файла."""
    if not os.path.exists(file_path):
        return []
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_data(data: List[Dict[str, Any]], file_path: str) -> None:
    """Сохраняет данные в JSON файл."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
