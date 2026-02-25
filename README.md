# ValutaTrade Hub

Комплексная платформа для управления виртуальным портфелем фиатных и криптовалют.

## Структура проекта


finalproject
│  
├── data/
│    ├── users.json
│    │── session.json     
│    ├── portfolios.json       
│    ├── rates.json               # локальный кэш для Core Service
│    └── exchange_rates.json      # хранилище Parser Service (исторические данные).json            
├── valutatrade_hub/
│    ├── __init__.py
│    ├── logging_config.py         
│    ├── decorators.py            
│    ├── core/
│    │    ├── __init__.py
│    │    ├── currencies.py         
│    │    ├── exceptions.py         
│    │    ├── models.py           
│    │    ├── usecases.py          
│    │    └── utils.py             
│    ├── infra/
│    │    ├─ __init__.py
│    │    ├── settings.py           
│    │    └── database.py          
│    ├── parser_service/
│    │    ├── __init__.py
│    │    ├── config.py             # конфигурация API и параметров обновления
│    │    ├── api_clients.py        # работа с внешними API
│    │    ├── updater.py            # основной модуль обновления курсов
│    │    ├── storage.py            # операции чтения/записи exchange_rates.json
│    │    └── scheduler.py          # планировщик периодического обновления
│    └── cli/
│         ├─ __init__.py
│         └─ interface.py     
│
├── main.py
├── Makefile
├── poetry.lock
├── pyproject.toml
├── README.md
└── .gitignore               

## Установка

poetry install


## Запуск CLI

poetry run valutatrade

или

make project


## Основные компоненты

1. **Сервис Парсинга (Parser Service)**: Отдельное приложение, которое по запросу или расписанию обращается к публичным API, получает актуальные курсы, сравнивает их с предыдущими значениями и сохраняет историю в базу данных.

2. **Основной Сервис (Core Service)**: Главное приложение, которое предоставляет пользовательский интерфейс (CLI), управляет пользователями, их кошельками, историей транзакций и взаимодействует с сервисом парсинга для получения актуальных курсов.

## Класс User

Реализован класс `User` со следующими атрибутами и методами:

### Атрибуты:
- `_user_id`: int — уникальный идентификатор пользователя.
- `_username`: str — имя пользователя.
- `_hashed_password`: str — пароль в зашифрованном виде.
- `_salt`: str — уникальная соль для пользователя.
- `_registration_date`: datetime — дата регистрации пользователя.

### Методы:
- `get_user_info()` — выводит информацию о пользователе (без пароля).
- `change_password(new_password: str)` — изменяет пароль пользователя, с хешированием нового пароля.
- `verify_password(password: str)` — проверяет введённый пароль на совпадение.

## Сервис Парсинга

Сервис парсинга отвечает за получение актуальных курсов валют из внешних источников и сохранение их в локальное хранилище.

### Источники данных

1. **CoinGecko** — для криптовалют (BTC, ETH, SOL, и т.д.)
2. **ExchangeRate-API** — для фиатных валют (USD, EUR, GBP, RUB, и т.д.)

### Компоненты Parser Service

- **config.py** — конфигурация сервиса, включая API ключи и списки валют
- **api_clients.py** — клиенты для работы с внешними API
- **updater.py** — координатор обновления курсов
- **storage.py** — работа с файлами данных
- **scheduler.py** — планировщик периодического обновления

### Файлы данных

- **data/rates.json** — кэш актуальных курсов для Core Service
- **data/exchange_rates.json** — история курсов с метаданными

### CLI команды Parser Service

1. **update-rates** — обновить курсы валют
   - `--source` — обновить данные только из указанного источника (coingecko или exchangerate)

2. **show-rates** — показать список актуальных курсов из локального кэша
   - `--currency` — показать курс только для указанной валюты
   - `--top` — показать N самых дорогих криптовалют
   - `--base` — показать все курсы относительно указанной базы


### Asciinema


https://asciinema.org/a/AzjXXNIkciOyThHN
