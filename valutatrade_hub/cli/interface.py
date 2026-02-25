import argparse
from typing import Optional
import os
import json

from valutatrade_hub.core.exceptions import (
    ApiRequestError,
    CurrencyNotFoundError,
    InsufficientFundsError,
)
from valutatrade_hub.core.models import User
from valutatrade_hub.core.usecases import PortfolioUseCase, RateUseCase, UserUseCase
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.parser_service.api_clients import (
    ApiRequestError as ParserApiRequestError,
)
from valutatrade_hub.parser_service.api_clients import (
    CoinGeckoClient,
    ExchangeRateApiClient,
)
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.parser_service.storage import RatesStorage
from valutatrade_hub.parser_service.updater import RatesUpdater


class CLIInterface:
    def __init__(self):
        self.current_user: Optional[User] = None
        self.session_file = "data/session.json"
        self._load_session()
        self.parser = argparse.ArgumentParser(
            prog='ValutaTrade Hub',
            description=('Платформа для управления виртуальным '
                         'портфелем фиатных и криптовалют')
        )
        self.subparsers = self.parser.add_subparsers(
            dest='command',
            help='Доступные команды'
        )
        self._setup_commands()
    ''' Сессии я добавил для сохранения авторизации между запусками, 
        так как консольное приложение завершалось
        после каждой команды'''
    def _load_session(self):
        """Загружает текущую сессию из файла."""
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                user_id = data.get("user_id")

                if user_id:
                    db = DatabaseManager()
                    users = db.load_data("users.json")

                    user_data = next(
                        (u for u in users if u["user_id"] == user_id),
                        None
                    )

                    if user_data:
                        from valutatrade_hub.core.models import User

                        self.current_user = User(
                            user_data["user_id"],
                            user_data["username"],
                            "",
                            user_data["registration_date"]
                        )

                        self.current_user._salt = user_data["salt"]
                        self.current_user._hashed_password = user_data["hashed_password"]
            except Exception:
                pass
            
    def _save_session(self):
        """Сохраняет текущую сессию."""
        if not self.current_user:
            return

        try:
            os.makedirs("data", exist_ok=True)

            with open(self.session_file, "w", encoding="utf-8") as f:
                json.dump(
                    {"user_id": self.current_user.user_id},
                    f,
                    indent=2
                )

        except Exception:
            pass

    def _clear_session(self):
        """Удаляет файл сессии."""
        if os.path.exists(self.session_file):
            os.remove(self.session_file)

    def _setup_commands(self):
        register_parser = self.subparsers.add_parser('register',
            help='Зарегистрировать нового пользователя')
        register_parser.add_argument('--username', required=True,
            help='Имя пользователя')
        register_parser.add_argument('--password', required=True,
            help='Пароль')

        login_parser = self.subparsers.add_parser('login',
            help='Войти в систему')
        login_parser.add_argument('--username', required=True,
            help='Имя пользователя')
        login_parser.add_argument('--password', required=True,
            help='Пароль')

        portfolio_parser = self.subparsers.add_parser('show-portfolio',
            help='Показать портфель')
        portfolio_parser.add_argument('--base', default='USD',
            help='Базовая валюта (по умолчанию USD)')

        buy_parser = self.subparsers.add_parser('buy',
            help='Купить валюту')
        buy_parser.add_argument('--currency', required=True,
            help='Код валюты')
        buy_parser.add_argument('--amount', type=float, required=True,
            help='Количество валюты')

        sell_parser = self.subparsers.add_parser('sell',
            help='Продать валюту')
        sell_parser.add_argument('--currency', required=True,
            help='Код валюты')
        sell_parser.add_argument('--amount', type=float, required=True,
            help='Количество валюты')

        rate_parser = self.subparsers.add_parser('get-rate',
            help='Получить курс валюты')
        rate_parser.add_argument('--from', dest='from_currency',
            required=True, help='Исходная валюта')
        rate_parser.add_argument('--to', dest='to_currency',
            required=True, help='Целевая валюта')

        update_parser = self.subparsers.add_parser('update-rates',
            help='Обновить курсы валют')
        update_parser.add_argument('--source',
            choices=['coingecko', 'exchangerate'],
            help='Источник данных')

        show_rates_parser = self.subparsers.add_parser('show-rates',
            help='Показать актуальные курсы')
        show_rates_parser.add_argument('--currency',
            help='Фильтр по валюте')
        show_rates_parser.add_argument('--top', type=int,
            help='Показать N самых дорогих криптовалют')
        show_rates_parser.add_argument('--base', default='USD',
            help='Базовая валюта (по умолчанию USD)')
        self.subparsers.add_parser(
            "logout",
            help="Выйти из системы"
        )

    def run(self, args=None):
        """Запуск CLI"""
        parsed_args = self.parser.parse_args(args)

        if not parsed_args.command:
            self.parser.print_help()
            return

        command_handlers = {
            'register': lambda: self._register(
                parsed_args.username,
                parsed_args.password
            ),
            'login': lambda: self._login(
                parsed_args.username,
                parsed_args.password
            ),
            'show-portfolio': lambda: self._show_portfolio(parsed_args.base),
            'buy': lambda: self._buy(parsed_args.currency, parsed_args.amount),
            'sell': lambda: self._sell(parsed_args.currency, parsed_args.amount),
            'get-rate': lambda: self._get_rate(
                parsed_args.from_currency,
                parsed_args.to_currency
            ),
            'update-rates': lambda: self._update_rates(parsed_args.source),
            'show-rates': lambda: self._show_rates(
                parsed_args.currency,
                parsed_args.top,
                parsed_args.base
            ),
            "logout": lambda: self._logout(),
        }

        try:
            if parsed_args.command in command_handlers:
                command_handlers[parsed_args.command]()
        except Exception as e:
            self._handle_exception(e)

    def _handle_exception(self, e: Exception) -> None:
        """Обработка ошибок CLI"""
        if isinstance(e, InsufficientFundsError):
            print(f"Ошибка: {e}")
        elif isinstance(e, CurrencyNotFoundError):
            print(f"Ошибка: {e}")
            print("Поддерживаемые валюты: USD, EUR, RUB, JPY, GBP, "
                  "BTC, ETH, ADA, DOT, SOL")
            print("Используйте команду 'get-rate --from <код> --to <код>' "
                  "для проверки поддерживаемых пар.")
        elif isinstance(e, ApiRequestError):
            print(f"Ошибка: {e}")
            print(
                "Пожалуйста, повторите попытку позже или проверьте сетевое соединение."
            )
        else:
            print(f"Ошибка: {e}")

    def _register(self, username: str, password: str):
        """Регистрация нового пользователя"""
        try:
            user = UserUseCase.register_user(username, password)
            print(
                f"Пользователь '{username}' зарегистрирован "
                f"(id={user.user_id}). Войдите: login --username "
                f"{username} --password ****"
            )
        except ValueError as e:
            raise e
        except Exception as e:
            raise ApiRequestError(
                f"Ошибка при регистрации пользователя: {str(e)}"
            ) from e

    def _login(self, username: str, password: str):
        """Вход в систему"""
        try:
            user = UserUseCase.login_user(username, password)
            self.current_user = user
            self._save_session()
            print(f"Вы вошли как '{username}'")
        except ValueError as e:
            raise e
        except Exception as e:
            raise ApiRequestError(
                f"Ошибка при входе пользователя: {str(e)}"
            ) from e

    def _show_portfolio(self, base: str):
        """Показать портфель пользователя"""
        if not self.current_user:
            raise ValueError("Сначала выполните login")

        db = DatabaseManager()
        portfolios = db.load_data('portfolios.json')
        portfolio = next(
            (p for p in portfolios if p['user_id'] == self.current_user.user_id),
            None
        )

        if not portfolio or not portfolio['wallets']:
            print("У вас пока нет кошельков")
            return

        print(f"Портфель пользователя '{self.current_user.username}' (база: {base}):")

        total_value = 0.0
        for currency, balance in portfolio['wallets'].items():
            try:
                rate_data = RateUseCase.get_rate(currency, base)
                rate = rate_data['rate']
                value = balance * rate

                print(f"- {currency}: {balance:.4f}  → {value:.2f} {base}")
                total_value += value
            except Exception:
                print(f"- {currency}: {balance:.4f}  → 0.00 {base} (курс недоступен)")

        print("-" * 30)
        print(f"ИТОГО: {total_value:,.2f} {base}")

    def _buy(self, currency: str, amount: float):
        """Купить"""
        if not self.current_user:
            raise ValueError("Сначала выполните login")

        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        try:
            PortfolioUseCase.buy_currency(self.current_user.user_id, currency, amount)

            db = DatabaseManager()
            portfolios = db.load_data('portfolios.json')
            portfolio = next(
                (p for p in portfolios if p['user_id'] == self.current_user.user_id),
                None
            )

            if portfolio and currency in portfolio['wallets']:
                new_balance = portfolio['wallets'][currency]
                print(f"Покупка выполнена: {amount:.4f} {currency}")
                print(f"Новый баланс: {new_balance:.4f} {currency}")
            else:
                print(f"Покупка выполнена: {amount:.4f} {currency}")
                print("Ошибка при получении нового баланса")
        except CurrencyNotFoundError:
            raise CurrencyNotFoundError(currency) from None
        except Exception as e:
            raise ApiRequestError(
                f"Ошибка при покупке валюты: {str(e)}"
            ) from e

    def _sell(self, currency: str, amount: float):
        """Продать"""
        if not self.current_user:
            raise ValueError("Сначала выполните login")

        if amount <= 0:
            raise ValueError("'amount' должен быть положительным числом")

        try:
            PortfolioUseCase.sell_currency(self.current_user.user_id, currency, amount)

            db = DatabaseManager()
            portfolios = db.load_data('portfolios.json')
            portfolio = next(
                (p for p in portfolios if p['user_id'] == self.current_user.user_id),
                None
            )

            if portfolio and currency in portfolio['wallets']:
                new_balance = portfolio['wallets'][currency]
                print(f"Продажа выполнена: {amount:.4f} {currency}")
                print(f"Новый баланс: {new_balance:.4f} {currency}")
            elif portfolio:
                print(f"Продажа выполнена: {amount:.4f} {currency}")
                print(f"Валюта {currency} полностью продана")
            else:
                print(f"Продажа выполнена: {amount:.4f} {currency}")
                print("Ошибка при получении нового баланса")
        except InsufficientFundsError:
            raise
        except CurrencyNotFoundError:
            raise CurrencyNotFoundError(currency) from None
        except Exception as e:
            raise ApiRequestError(
                f"Ошибка при продаже валюты: {str(e)}"
            ) from e

    def _get_rate(self, from_currency: str, to_currency: str):
        """Курс"""
        if not from_currency or not to_currency:
            raise ValueError("Коды валют не могут быть пустыми")

        try:
            rate_data = RateUseCase.get_rate(from_currency, to_currency)
            rate = rate_data['rate']
            updated_at = rate_data['updated_at']

            print(f"Курс {from_currency}→{to_currency}: {rate:.8f}")
            print(f"Обратный курс {to_currency}→{from_currency}: {1/rate:.8f}")
            print(f"Обновлено: {updated_at}")
        except CurrencyNotFoundError:
            raise
        except Exception as e:
            raise ApiRequestError(
                f"Ошибка при получении курса: {str(e)}"
            ) from e

    def _update_rates(self, source: str = None):
        """Обновить курс"""
        print("Начало обновления курса")

        try:
            config = ParserConfig()

            coingecko_client = CoinGeckoClient(config)
            exchangerate_client = ExchangeRateApiClient(config)

            storage = RatesStorage(config)

            clients = {}
            if source is None or source == 'coingecko':
                clients['CoinGecko'] = coingecko_client
            if source is None or source == 'exchangerate':
                clients['ExchangeRate-API'] = exchangerate_client

            updater = RatesUpdater(config, clients, storage)

            result = updater.run_update()

            if result['success']:
                print(f"Обновление завершено успешно. "
                      f"Обновлено {result['rates_count']} курсов.")
                print(f"Последнее обновление: {result['timestamp']}")
            else:
                print(
                    "Обновление завершено с ошибками. "
                )

        except ParserApiRequestError as e:
            print(f"Ошибка при обновлении курсов: {str(e)}")
        except Exception as e:
            print(
                f"Неожиданная ошибка при обновлении курсов: {str(e)}"
            )

    def _show_rates(self, currency: str = None, top: int = None, base: str = 'USD'):
        """Показать актуальный курс"""
        try:
            config = ParserConfig()

            storage = RatesStorage(config)

            rates = storage.load_rates()

            if not rates:
                print(
                    "Локальный кэш курсов пуст. Выполните 'update-rates', "
                    "чтобы загрузить данные."
                )
                return

            if currency:
                filtered_rates = {k: v for k, v in rates.items() if currency in k}
                if not filtered_rates:
                    print(f"Курс для '{currency}' не найден в кэше.")
                    return
                rates = filtered_rates

            if top:
                crypto_rates = {
                    k: v for k, v in rates.items()
                    if any(crypto in k for crypto in config.CRYPTO_CURRENCIES)
                }
                sorted_rates = sorted(
                    crypto_rates.items(),
                    key=lambda x: x[1]['rate'],
                    reverse=True
                )
                sorted_rates = sorted_rates[:top]
                rates = dict(sorted_rates)

            print(
                f"Курсы из кэша (обновлено "
                f"{list(rates.values())[0]['updated_at'] if rates else 'неизвестно'}):"
            )
            for pair, data in rates.items():
                print(f"- {pair}: {data['rate']:.8f}")

        except Exception as e:
            print(f"Ошибка при показе курсов: {str(e)}")


def main():
    cli = CLIInterface()
    cli.run()


if __name__ == "__main__":
    main()
