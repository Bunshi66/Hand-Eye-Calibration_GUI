import logging
import struct
from typing import Any, Literal, Optional, Tuple

from API.source.core.exceptions.data_validation_error.parsing_error import (
    CommandTypeError,
    CorruptedPackageError,
)
from API.source.core.network.socket_wrapper import (
    SocketWrapper,
)
from API.source.models.constants import (
    CMD_PORT,
    CTRLR_CMD_DATA_PACK_UNPACK_FORMAT,
    CTRLR_CMD_PAYLOAD_LENGTH_SIZE,
    CTRLR_CMD_TYPE_LENGTH,
    EMPTY_BYTES,
)


class Controller(object):
    """
    Класс-драйвер для отправки/приема управляющих команд на/с робота.
    """

    _COMMAND_RECEIVE_TIMEOUT: float = 1  # sec

    def __init__(
        self, ip: str, timeout: int, logger: Optional[logging.Logger] = None
    ):
        """
        Создать новый объект класса.

        Args:
            ip (str): IPv4 адрес робота;
            timeout (float): максимальное время ожидания подключения к роботу;
            logger (optional, logging.Logger): если задан, то логи будут писаться.
        """
        self._ip: str = ip
        self._timeout: float = timeout
        self._logger: Optional[logging.Logger] = logger

        self._socket: SocketWrapper = SocketWrapper(
            ip=self._ip,
            port=CMD_PORT,
            connect_timeout=self._timeout,
            receive_timeout=self._COMMAND_RECEIVE_TIMEOUT,
        )
        self._is_connected: bool = False

    def connect(self) -> bool:
        """
        Подключиться к управляющему сокету робота.

        Returns:
            bool: True если подключение произведено успешно.
        """
        self._write_log("debug", "Connecting control socket")
        if self._socket.connect():
            self._is_connected = True
            return True
        self._is_connected = False
        return False

    def is_connected(self):
        """
        Получить статус подключения к роботу.

        Returns:
            bool: True если подключение активно.
        """
        return self._is_connected and self._socket.is_connected()

    def receive(self, command_type: int, struct_format: str) -> Tuple[Any, ...]:
        """
        Принять команду с робота.

        Args:
            command_type (int): ожидаемый тип команды;
            struct_format (str): ожидаемый формат данных.
        """
        cmd_length_data = self._socket.receive(CTRLR_CMD_PAYLOAD_LENGTH_SIZE)
        if cmd_length_data is None:
            return ()
        cmd_length = struct.unpack(
            CTRLR_CMD_DATA_PACK_UNPACK_FORMAT, cmd_length_data
        )
        if cmd_length[0] < CTRLR_CMD_PAYLOAD_LENGTH_SIZE:
            raise CorruptedPackageError(
                "Received data length less then expected"
            )

        cmd_type_data = self._socket.receive(CTRLR_CMD_TYPE_LENGTH)
        if cmd_type_data is None:
            raise CorruptedPackageError("Failed to receive command type")
        received_cmd_type = struct.unpack(
            CTRLR_CMD_DATA_PACK_UNPACK_FORMAT, cmd_type_data
        )
        self._write_log(
            "debug", f"Received response command-type: {received_cmd_type[0]}"
        )
        if received_cmd_type[0] != command_type:
            raise CommandTypeError("Received data for wrong command type")

        cmd_data = self._socket.receive(
            cmd_length[0] - CTRLR_CMD_PAYLOAD_LENGTH_SIZE
        )
        if cmd_data is None:
            raise CorruptedPackageError("Failed to receive command body data")
        return struct.unpack(struct_format, cmd_data)

    def send(self, command_type: int, payload: bytes = EMPTY_BYTES) -> bool:
        """
        Отправить команду роботу.

        Args:
            command_type (int): тип отправляемой команды;
            payload (bytes): тело отправляемой команды.
        """
        byte_message = struct.pack(
            CTRLR_CMD_DATA_PACK_UNPACK_FORMAT,
            len(payload) + CTRLR_CMD_PAYLOAD_LENGTH_SIZE,
        ) + struct.pack(CTRLR_CMD_DATA_PACK_UNPACK_FORMAT, command_type)
        if len(payload) > 0:
            byte_message = byte_message + payload
        self._socket.send(byte_message)
        self._write_log("debug", f"Sent command-type: {command_type}")
        return True

    def disconnect(self):
        """
        Отключиться от управляющего сокета робота.
        """
        if self.is_connected():
            self._write_log("debug", "Disconnecting control socket")
            self._socket.disconnect()
        self._is_connected = False

    def __del__(self):
        if self.is_connected():
            self.disconnect()

    def _write_log(
        self, level: Literal["debug", "info", "warning", "error"], message: str
    ):
        """
        Обертка для логгера.
        """

        if self._logger is not None:
            log_method = getattr(self._logger, level, self._logger.error)
            log_method(message)
