from abc import ABC, abstractmethod
from typing import Dict


class CurrencyNotFoundError(Exception):
    def __init__(self, code: str):
        self.code = code
        super().__init__(f"Неизвестная валюта '{code}'")


class Currency(ABC):
    """Базовый класс для всех типов валют"""

    def __init__(self, name: str, code: str):
        """Создаёт объект валюты с именем и кодом"""
        if not name:
            raise ValueError("Имя валюты не может быть пустым")
        if not code or not (2 <= len(code) <= 5) or ' ' in code:
            raise ValueError("Код валюты должен быть от 2 до 5 символов без пробелов")

        self.name = name
        self.code = code.upper()

    @abstractmethod
    def get_display_info(self) -> str:
        pass


class FiatCurrency(Currency):
    """Класс для фиатных валют"""

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"


class CryptoCurrency(Currency):
    """Класс для криптовалют"""

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap

    def get_display_info(self) -> str:
        if self.market_cap >= 1e9:
            mcap_str = f"{self.market_cap/1e9:.2f}e9"
        elif self.market_cap >= 1e6:
            mcap_str = f"{self.market_cap/1e6:.2f}e6"
        else:
            mcap_str = f"{self.market_cap:.2f}"

        return (f"[CRYPTO] {self.code} — {self.name} "
                f"(Algo: {self.algorithm}, MCAP: {mcap_str})")


CURRENCY_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),
    "JPY": FiatCurrency("Japanese Yen", "JPY", "Japan"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),

    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 2.34e11),
    "ADA": CryptoCurrency("Cardano", "ADA", "Ouroboros", 3.45e10),
    "DOT": CryptoCurrency("Polkadot", "DOT", "NPoS", 8.91e9),
    "SOL": CryptoCurrency("Solana", "SOL", "Proof of History", 4.56e10),
}


def get_currency(code: str) -> Currency:
    """Получить валюту по коду"""
    code = code.upper()
    if code in CURRENCY_REGISTRY:
        return CURRENCY_REGISTRY[code]
    raise CurrencyNotFoundError(code)
