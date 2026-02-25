import json
import logging
import logging.handlers
import os

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> None:
    """Настройка логов"""
    settings = SettingsLoader()

    log_path = settings.log_path
    os.makedirs(log_path, exist_ok=True)

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logging.basicConfig(level=log_level)

    log_file = os.path.join(log_path, 'actions.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=settings.log_rotation['max_bytes'],
        backupCount=settings.log_rotation['backup_count'],
        encoding='utf-8'
    )

    if settings.log_format.lower() == 'json':
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s %(name)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )

    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


class JsonFormatter(logging.Formatter):
    """Форматирование логов в JSON"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': self.formatTime(record, '%Y-%m-%dT%H:%M:%S'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        if hasattr(record, 'action'):
            log_entry['action'] = record.action
        if hasattr(record, 'username'):
            log_entry['username'] = record.username
        if hasattr(record, 'currency_code'):
            log_entry['currency_code'] = record.currency_code
        if hasattr(record, 'amount'):
            log_entry['amount'] = record.amount
        if hasattr(record, 'rate'):
            log_entry['rate'] = record.rate
        if hasattr(record, 'base'):
            log_entry['base'] = record.base
        if hasattr(record, 'result'):
            log_entry['result'] = record.result
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        if hasattr(record, 'error_message'):
            log_entry['error_message'] = record.error_message

        return json.dumps(log_entry, ensure_ascii=False)
