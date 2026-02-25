import logging
import time
from typing import Callable

import schedule

from valutatrade_hub.parser_service.config import ParserConfig


class Scheduler:
    """Периодического обновление курсов"""

    def __init__(self, config: ParserConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.jobs = []

    def schedule_updates(
        self,
        update_function: Callable,
        interval_minutes: int = 60
    ) -> None:
        job = schedule.every(interval_minutes).minutes.do(update_function)
        self.jobs.append(job)

        self.logger.info(
            f"Запланировано обновление курсов каждые {interval_minutes} минут"
        )

    def schedule_daily_updates(
        self,
        update_function: Callable,
        time_str: str = "00:00"
    ) -> None:
        job = schedule.every().day.at(time_str).do(update_function)
        self.jobs.append(job)

        self.logger.info(
            f"Запланировано ежедневное обновление курсов в {time_str}"
        )

    def run_scheduler(self) -> None:
        self.logger.info("Планировщик запущен")

        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Планировщик остановлен пользователем")
        except Exception as e:
            self.logger.error(f"Ошибка в планировщике: {str(e)}")
            raise

    def cancel_all_jobs(self) -> None:
        """Отмена задач"""
        for job in self.jobs:
            schedule.cancel_job(job)
        self.jobs.clear()

        self.logger.info("Все запланированные задачи отменены")
