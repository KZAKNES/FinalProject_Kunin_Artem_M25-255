import datetime
import time
from typing import Any, Dict

from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.core.exceptions import (
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import User
from valutatrade_hub.decorators import log_action
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader


class UserUseCase:
    @staticmethod
    @log_action("REGISTER")
    def register_user(username: str, password: str) -> User:
        """Регистрация нового пользователя"""
        db = DatabaseManager()
        users = db.load_data('users.json')

        if any(user['username'] == username for user in users):
            raise ValueError(f"Имя пользователя '{username}' уже занято")

        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")

        user_id = max([user['user_id'] for user in users], default=0) + 1

        user = User(user_id, username, password)

        user_data = user.get_user_info()
        user_data['hashed_password'] = user.hashed_password
        user_data['salt'] = user.salt

        users.append(user_data)
        db.save_data(users, 'users.json')

        portfolios = db.load_data('portfolios.json')
        portfolios.append({
            'user_id': user_id,
            'wallets': {}
        })
        db.save_data(portfolios, 'portfolios.json')

        return user

    @staticmethod
    @log_action("LOGIN")
    def login_user(username: str, password: str) -> User:
        """Вход пользователя в систему"""
        db = DatabaseManager()
        users = db.load_data('users.json')

        user_data = next((user for user in users if user['username'] == username), None)
        if not user_data:
            raise ValueError(f"Пользователь '{username}' не найден")

        user = User(
            user_data['user_id'],
            user_data['username'],
            '', 
            user_data['registration_date']
        )
        user._salt = user_data['salt']
        user._hashed_password = user_data['hashed_password']

        if not user.verify_password(password):
            raise ValueError("Неверный пароль")

        return user


class PortfolioUseCase:
    @staticmethod
    def get_portfolio(user_id: int) -> Dict[str, Any]:
        """Портфель пользователя"""
        db = DatabaseManager()
        portfolios = db.load_data('portfolios.json')
        return next((p for p in portfolios if p['user_id'] == user_id), None)

    @staticmethod
    def update_portfolio(user_id: int, wallets: Dict[str, float]) -> None:
        """Обновить портфель пользователя"""
        db = DatabaseManager()
        portfolios = db.load_data('portfolios.json')

        portfolio = next((p for p in portfolios if p['user_id'] == user_id), None)
        if not portfolio:
            portfolio = {
                'user_id': user_id,
                'wallets': {}
            }
            portfolios.append(portfolio)

        portfolio['wallets'] = wallets

        db.save_data(portfolios, 'portfolios.json')

    @staticmethod
    @log_action("BUY")
    def buy_currency(user_id: int, currency_code: str, amount: float) -> None:
        """Купить валюту"""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        try:
            _ = get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise CurrencyNotFoundError(currency_code) from e

        portfolio = PortfolioUseCase.get_portfolio(user_id)
        if not portfolio:
            PortfolioUseCase.update_portfolio(user_id, {})
            portfolio = PortfolioUseCase.get_portfolio(user_id)

        wallets = portfolio['wallets']
        wallets[currency_code] = wallets.get(currency_code, 0) + amount

        PortfolioUseCase.update_portfolio(user_id, wallets)

    @staticmethod
    @log_action("SELL")
    def sell_currency(user_id: int, currency_code: str, amount: float) -> None:
        """Продать валюту"""
        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        try:
            _ = get_currency(currency_code)
        except CurrencyNotFoundError as e:
            raise CurrencyNotFoundError(currency_code) from e

        portfolio = PortfolioUseCase.get_portfolio(user_id)
        if not portfolio:
            raise InsufficientFundsError(0, amount, currency_code)

        wallets = portfolio['wallets']
        available = wallets.get(currency_code, 0)
        if available < amount:
            raise InsufficientFundsError(available, amount, currency_code)

        wallets[currency_code] -= amount
        if wallets[currency_code] <= 0:
            del wallets[currency_code]

        PortfolioUseCase.update_portfolio(user_id, wallets)


class RateUseCase:
    @staticmethod
    def get_rate(from_code: str, to_code: str) -> Dict[str, Any]:
        """Получить курс валюты"""
        try:
            _ = get_currency(from_code)
            _ = get_currency(to_code)
        except CurrencyNotFoundError as e:
            raise CurrencyNotFoundError(e.code) from e

        db = DatabaseManager()
        settings = SettingsLoader()

        rates_timestamp = db.get_rates_timestamp()
        current_time = time.time()

        if rates_timestamp is None or (
            current_time - rates_timestamp
        ) > settings.rates_ttl_seconds:

            pass

        rates = db.load_data('rates.json')
        
        if not rates:
            return {
                'rate': 1.0,
                'updated_at': datetime.datetime.now().isoformat()
            }
        
        pairs = (rates[0].get("pairs", {}) if isinstance(rates, list) and len(rates) > 0
                 else rates.get("pairs", {}))

        rate_key = f"{from_code}_{to_code}"

        if rate_key in pairs:
            return {
                'rate': pairs[rate_key]["rate"],
                'updated_at': pairs[rate_key]["updated_at"]
            }

        return {
            'rate': 1.0,
            'updated_at': datetime.datetime.now().isoformat()
        }

    @staticmethod
    def update_rates(rates: Dict[str, Dict[str, Any]]) -> None:
        """Обновить курс валюты"""
        db = DatabaseManager()

        db.save_data([rates], 'rates.json')
