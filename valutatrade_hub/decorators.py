import functools
import logging
from typing import Any, Callable


def _extract_user_info(args):
    """Получение информации о пользователе"""
    if args and hasattr(args[0], '__class__'):
        if hasattr(args[0], 'user_id'):
            return args[0].user_id
        elif hasattr(args[0], 'username'):
            return args[0].username
    return None

def _extract_currency_code(args, kwargs):
    """Получение кода валюты"""
    if 'currency_code' in kwargs:
        return kwargs['currency_code']
    elif 'currency' in kwargs:
        return kwargs['currency']

    for _, arg in enumerate(args[1:], 1):  
        if (
            isinstance(arg, str) and len(arg) <= 10
        ):  
            return arg
    return None

def _extract_amount(args, kwargs):
    """Получение количества"""
    if 'amount' in kwargs:
        return kwargs['amount']
    elif len(args) > 2 and isinstance(args[2], (int, float)):
        return args[2]
    return None

def _extract_additional_params(args, kwargs):
    """Получение дополнительных параметров"""
    log_params = {}

    user_info = _extract_user_info(args)
    if user_info:
        log_params['username'] = user_info

    currency_code = _extract_currency_code(args, kwargs)
    if currency_code:
        log_params['currency_code'] = currency_code

    amount = _extract_amount(args, kwargs)
    if amount is not None:
        log_params['amount'] = amount

    if 'rate' in kwargs:
        log_params['rate'] = kwargs['rate']
    if 'base' in kwargs:
        log_params['base'] = kwargs['base']

    return log_params

def log_action(action_name: str, verbose: bool = False) -> Callable:
    """Логирование операций"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            logger = logging.getLogger('valutatrade.actions')

            log_params = {
                'action': action_name,
                'result': 'OK'
            }

            try:
                additional_params = _extract_additional_params(args, kwargs)
                log_params.update(additional_params)
            except Exception:
                pass

            try:
                result = func(*args, **kwargs)

                logger.info(f"{action_name} operation completed", extra=log_params)

                return result
            except Exception as e:
                log_params['result'] = 'ERROR'
                log_params['error_type'] = type(e).__name__
                log_params['error_message'] = str(e)

                logger.error(
                    f"{action_name} operation failed: {str(e)}",
                    extra=log_params
                )

                raise

        return wrapper
    return decorator
