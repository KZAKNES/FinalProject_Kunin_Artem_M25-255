import sys

from valutatrade_hub.cli.interface import main as cli_main
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.scheduler import Scheduler
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


def run_scheduler():
    print("Запуск планировщика обновления курсов")
    print("Нажмите Ctrl+C для остановки")

    try:
        config = ParserConfig()
        coingecko_client = CoinGeckoClient(config)
        exchangerate_client = ExchangeRateApiClient(config)
        storage = RatesStorage(config)
        clients = {
            'CoinGecko': coingecko_client,
            'ExchangeRate-API': exchangerate_client
        }
        updater = RatesUpdater(config, clients, storage)
        scheduler = Scheduler(config)
        scheduler.schedule_updates(updater.run_update, interval_minutes=60)
        scheduler.run_scheduler()

    except KeyboardInterrupt:
        print("\nПланировщик остановлен пользователем")
    except Exception as e:
        print(f"Ошибка в планировщике: {e}")
        sys.exit(1)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'scheduler':
        run_scheduler()
    else:
        cli_main()


if __name__ == "__main__":
    main()
