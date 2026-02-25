import logging
from datetime import datetime
from typing import Any, Dict

from valutatrade_hub.parser_service.api_clients import ApiRequestError, BaseApiClient
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage


class RatesUpdater:
    """Класс для обновления курсов"""

    def __init__(
        self,
        config: ParserConfig,
        clients: Dict[str, BaseApiClient],
        storage: RatesStorage
    ):
        self.config = config
        self.clients = clients
        self.storage = storage
        self.logger = logging.getLogger(__name__)

    def run_update(self) -> Dict[str, Any]:
        """Выполнить обновление курсов"""
        self.logger.info("Начало обновления курсов")

        all_rates = {}
        update_results = {}

        for source_name, client in self.clients.items():
            try:
                self.logger.info(f"Получение курсов от {source_name}")
                rates = client.fetch_rates()
                all_rates.update(rates)
                update_results[source_name] = {
                    "success": True,
                    "count": len(rates),
                    "rates": rates
                }
                self.logger.info(
                    f"Успешно получено {len(rates)} курсов от {source_name}"
                )

            except ApiRequestError as e:
                self.logger.error(
                    f"Ошибка при получении курсов от {source_name}: {str(e)}"
                )
                update_results[source_name] = {
                    "success": False,
                    "error": str(e)
                }
                continue
            except Exception as e:
                error_msg = (
                    f"Неожиданная ошибка при получении курсов от {source_name}: "
                    f"{str(e)}"
                )
                self.logger.error(error_msg)
                update_results[source_name] = {
                    "success": False,
                    "error": str(e)
                }
                continue

        if all_rates:
            try:
                cache_data = {}
                timestamp = datetime.utcnow().isoformat() + "Z"

                for pair, rate in all_rates.items():
                    source = (
                        "CoinGecko" if any(
                            crypto in pair for crypto in self.config.CRYPTO_CURRENCIES
                        )
                        else "ExchangeRate-API"
                    )

                    cache_data[pair] = {
                        "rate": rate,
                        "updated_at": timestamp,
                        "source": source
                    }

                self.storage.save_rates(cache_data)
                self.logger.info(
                    f"Успешно сохранено {len(cache_data)} курсов в кэш"
                )

            except Exception as e:
                self.logger.error(f"Ошибка при сохранении курсов в кэш: {str(e)}")
                raise

        try:
            timestamp = datetime.utcnow().isoformat() + "Z"
            for pair, rate in all_rates.items():
                source = (
                    "CoinGecko" if any(
                        crypto in pair for crypto in self.config.CRYPTO_CURRENCIES
                    )
                    else "ExchangeRate-API"
                )

                record_id = f"{pair}_{timestamp.replace(':', '-')}"

                record = {
                    "id": record_id,
                    "from_currency": pair.split("_")[0],
                    "to_currency": pair.split("_")[1],
                    "rate": rate,
                    "timestamp": timestamp,
                    "source": source
                }

                self.storage.save_history_record(record)

        except Exception as e:
            self.logger.error(f"Ошибка при сохранении истории курсов: {str(e)}")

        self.logger.info("Обновление курсов завершено")

        return {
            "success": len(all_rates) > 0,
            "rates_count": len(all_rates),
            "sources": update_results,
            "timestamp": (
                timestamp if 'timestamp' in locals()
                else datetime.utcnow().isoformat() + "Z"
            )
        }
