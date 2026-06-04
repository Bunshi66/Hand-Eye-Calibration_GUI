import threading
from functools import wraps
from typing import Callable, Optional

from API.source.core.exceptions.base_api_error import ApiError
from API.source.core.exceptions.connection_error import (
    ConnectionError,
    ReadOnlyConnectionError,
)


def handle_connection(
    _func: Optional[Callable] = None, *, available_in_read_only: bool = False
):
    """
    Декоратор, проверяющий возможность вызова функции в зависимости от состояния
    подключения к роботу. Для работы декоратора класс, методом которого является
    декорируемая функция, должен иметь приватное поле '_connection_state',
    хранящее объект или ссылку на объект типа ConnectionState.

    Keyword Args:
        available_in_read_only (bool): флаг, указывающий возможность использования
            декорируемой функции в режиме подключения 'read only'.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            connection_state = getattr(self, "_connection_state", None)
            if connection_state is None or not isinstance(
                connection_state, ConnectionState
            ):
                raise ApiError(
                    f"Class {self.__class__.__name__} must have a '_connection_state' "
                    f"attribute of type ConnectionState to use @handle_connection."
                )

            if not connection_state.is_connected():
                raise ConnectionError(
                    f"Can't process method {self.__class__.__name__}.{func.__name__} "
                    f"- robot is not connected"
                )

            if not available_in_read_only and connection_state.is_read_only():
                raise ReadOnlyConnectionError(
                    f"method: {self.__class__.__name__}.{func.__name__}"
                )

            return func(self, *args, **kwargs)

        return wrapper

    if _func is not None:
        return decorator(_func)
    else:
        return decorator


class ConnectionState(object):
    """
    Класс для индикации режима подключения к роботу.
    """

    _is_connected: bool = False
    _is_read_only: bool = False

    def __init__(self, is_connected: bool = False, is_read_only: bool = False):
        self._is_connected = is_connected
        self._is_read_only = is_read_only
        self._lock = threading.Lock()

    def connect(self):
        """
        Установить состояние подключения 'Подключено'.
        """
        with self._lock:
            self._is_connected = True

    def disconnect(self):
        """
        Установить состояние подключения 'Отключено'.
        """
        with self._lock:
            self._is_connected = False

    def is_connected(self) -> bool:
        """
        Получить состояние подключения.

        Returns:
            bool: True если подключение активно.
        """
        with self._lock:
            return self._is_connected

    def read_only(self):
        """
        Установить режим подключения 'read only'.
        """
        with self._lock:
            self._is_read_only = True

    def full(self):
        """
        Установить режим подключения 'full'.
        """
        with self._lock:
            self._is_read_only = False

    def is_read_only(self) -> bool:
        """
        Получить режим подключения.

        Returns:
            bool: True если подключение установлено в режиме 'read only'.
        """
        with self._lock:
            return self._is_read_only
