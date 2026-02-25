from abc import ABC, abstractmethod
from typing import Dict

import requests

from valutatrade_hub.parser_service.config import ParserConfig


class ApiRequestError(Exception):
    """Ошибка запроса к API"""
    pass


class BaseApiClient(ABC):
    """Базовый класс для API клиентов"""

    def __init__(self, config: ParserConfig):
        self.config = config

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы валют от API"""
        pass


class CoinGeckoClient(BaseApiClient):

    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы криптовалют от CoinGecko"""
        crypto_ids = [self.config.CRYPTO_ID_MAP[code]
                     for code in self.config.CRYPTO_CURRENCIES
                     if code in self.config.CRYPTO_ID_MAP]

        params = {
            "ids": ",".join(crypto_ids),
            "vs_currencies": self.config.BASE_CURRENCY.lower()
        }

        try:
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()
            rates = {}

            for code, gecko_id in self.config.CRYPTO_ID_MAP.items():
                if gecko_id in data:
                    rate = data[gecko_id].get(self.config.BASE_CURRENCY.lower())
                    if rate is not None:
                        pair = f"{code}_{self.config.BASE_CURRENCY}"
                        rates[pair] = float(rate)

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса к CoinGecko: {str(e)}") from e
        except (ValueError, KeyError) as e:
            raise ApiRequestError(
                f"Ошибка обработки данных от CoinGecko: {str(e)}"
            ) from e


class ExchangeRateApiClient(BaseApiClient):
    """Клиент ExchangeRate-API"""

    def fetch_rates(self) -> Dict[str, float]:
        """Получить курсы фиатных валют от ExchangeRate-API"""
        if not self.config.EXCHANGERATE_API_KEY:
            raise ApiRequestError("Не задан API ключ для ExchangeRate-API")

        url = (f"{self.config.EXCHANGERATE_API_URL}/"
               f"{self.config.EXCHANGERATE_API_KEY}/"
               f"latest/{self.config.BASE_CURRENCY}")

        try:
            response = requests.get(
                url,
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()

            data = response.json()

            if data.get("result") != "success":
                raise ApiRequestError(
                    f"Ошибка API: {data.get('error-type', 'Неизвестная ошибка')}"
                )

            rates = {}
            for code in self.config.FIAT_CURRENCIES:
                if code in data.get("rates", {}):
                    rate = data["rates"][code]
                    pair = f"{code}_{self.config.BASE_CURRENCY}"
                    rates[pair] = float(rate)

            return rates

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса к ExchangeRate-API: {str(e)}") from e
        except (ValueError, KeyError) as e:
            raise ApiRequestError(
                f"Ошибка обработки данных от ExchangeRate-API: {str(e)}"
            ) from e
