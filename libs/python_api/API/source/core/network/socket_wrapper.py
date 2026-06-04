import socket
from typing import Optional

from API.source.core.exceptions.connection_error import (
    BrokenConnectionError,
    ClientDisconnectedError,
    ConnectionError,
    EmptyPackageError,
    ServerConnectionError,
)
from API.source.models.constants import EMPTY_BYTES


class SocketWrapper(object):
    """
    Обертка для сокета.
    """

    _RECEIVE_TIMEOUT: float = 0.5  # sec

    def __init__(
        self,
        ip: str,
        port: int,
        connect_timeout: float,
        receive_timeout: float = _RECEIVE_TIMEOUT,
    ):
        """
        Создать новый объект класса.

        Args:
            ip (str): IPv4 адрес целевого подключения;
            port (int): порт целевого подключения;
            connect_timeout (float): максимальное время ожидания при подключении;
            receive_timeout (float): максимальное время ожидания при
                приеме/отправке данных.
        """
        self._ip: str = ip
        self._port: int = port
        self._connect_timeout: float = connect_timeout
        self._receive_timeout: float = receive_timeout
        self._socket: Optional[socket.socket] = None
        self._is_connected: bool = False

    def connect(self) -> bool:
        """
        Установить соединение.
        """
        try:
            self._socket = socket.create_connection(
                address=(self._ip, self._port),
                timeout=self._connect_timeout,
            )
            self._socket.settimeout(self._receive_timeout)
            self._set_is_connected(True)
        except Exception as e:
            raise ServerConnectionError(self._port) from e

        return True

    def receive(self, message_length: int) -> Optional[bytes]:
        """
        Принять данные.
        """
        if self._socket is None:
            raise ConnectionError(
                "Failed to receive package from server - socket is not connected"
            )
        try:
            chunk = self._socket.recv(message_length)
            if chunk == EMPTY_BYTES:
                raise EmptyPackageError
            return chunk
        except socket.timeout:
            return None
        except Exception as e:
            raise ClientDisconnectedError(
                "Failed to receive package from server"
            ) from e

    def send(self, package: bytes):
        """
        Отправить данные.
        """
        if self._socket is None:
            raise ConnectionError(
                "Failed to send package to server - socket is not connected"
            )
        try:
            sent = self._socket.send(package)
            if sent == 0:
                raise BrokenConnectionError
        except socket.timeout:
            pass
        except Exception as e:
            raise ClientDisconnectedError(
                "Failed to send package to server"
            ) from e

    def disconnect(self):
        """
        Разорвать соединение.
        """
        self._set_is_connected(False)
        if self._socket is not None:
            self._socket.close()
        self._socket = None

    def is_connected(self) -> bool:
        """
        Получить статус подключения.
        """
        return self._is_connected

    def _set_is_connected(self, state: bool):
        self._is_connected = state

    def __del__(self):
        self.disconnect()
