import logging
import struct
from dataclasses import fields
from threading import Lock, Thread, main_thread
from typing import Callable, Literal, Optional, Tuple

from API.source.core.exceptions.data_validation_error.parsing_error import (
    RTDParsingError,
)
from API.source.core.network.socket_wrapper import (
    SocketWrapper,
)
from API.source.models.classes.data_classes.rtd_structure import (
    RTD,
    STRUCT_FORMAT,
    RTDataPackageBorders,
)
from API.source.models.constants import RTD_PORT
from API.source.models.type_aliases import ExcInfoType


class RTDReceiver(object):
    """
    Класс-драйвер для приема RTD данных с робота.
    """

    _DATA_RECEIVE_TIMEOUT: float = 0.1  # sec

    def __init__(
        self, ip: str, timeout: float, logger: Optional[logging.Logger] = None
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
            ip=ip,
            port=RTD_PORT,
            connect_timeout=timeout,
            receive_timeout=self._DATA_RECEIVE_TIMEOUT,
        )
        self._struct_size = struct.calcsize(STRUCT_FORMAT)
        self._is_loop_running: bool = False
        self._is_connected: bool = False
        self._thread: Optional[Thread] = None
        self._lock = Lock()

        self._rt_data = RTD()

    def connect(self) -> bool:
        """
        Подключиться к RTD сокету робота.

        Returns:
            bool: True если подключение произведено успешно.
        """
        self._write_log("debug", "Connecting RTD receiver")
        if (
            self._socket.connect()
            and self._receive_rtd()
            and self._validate_rtd()
        ):
            self._is_connected = True
            return True
        self._is_connected = False
        return False

    def is_connected(self) -> bool:
        """
        Получить статус подключения к роботу.

        Returns:
            bool: True если подключение активно.
        """
        with self._lock:
            return self._is_connected and self._socket.is_connected()

    def get_data(self) -> RTD:
        """
        Получить текущие RTD данные.

        Returns:
            RTD: Дата класс с данными.
        """
        with self._lock:
            return self._rt_data

    def start_loop(
        self,
        error_callback: Optional[Callable[[ExcInfoType], None]] = None,
        thread_name: str = "RTD-Receiver-loop",
    ):
        """
        Запустить цикл приема RTD данных в отдельном потоке.

        Args:
            error_callback: функция, которая будет вызвана при возникновении
                исключения в цикле приема RTD данных;
            thread_name: имя потока, в котором будет запущен цикл приема.
        """
        self._write_log("debug", "Starting RTD receiving loop")
        self._thread = Thread(
            target=self._receiving_loop,
            args=(error_callback,),
            daemon=False,
            name=thread_name,
        )
        self._is_loop_running = True
        self._thread.start()

    def stop_loop(self):
        """
        Остановить цикл приема RTD данных.
        """
        if self._thread is None:
            return
        if not self._is_loop_running:
            return
        self._write_log("debug", "Stopping RTD receiving loop")
        with self._lock:
            self._is_loop_running = False
        try:
            self._thread.join(2)
        except Exception:
            pass

    def is_running(self) -> bool:
        """
        Получить статус работы цикла приема данных.

        Returns:
            bool: True если цикл запущен.
        """
        with self._lock:
            is_running = self._is_loop_running
        return is_running and self.is_connected()

    def _receiving_loop(
        self, error_callback: Optional[Callable[[ExcInfoType], None]]
    ):
        """
        Цикл приема данных.
        """
        self._is_loop_running = True
        self._write_log("debug", "RTD receiving loop was started")
        try:
            while (
                self._is_loop_running
                and self._socket.is_connected()
                and main_thread().is_alive()
            ):
                self._receive_rtd()
            self._is_loop_running = False
            self._write_log("debug", "RTD receiving loop was stopped")
        except Exception as error:
            self._write_log(
                "debug", f"RTD receiving loop failed with error: {error}"
            )
            self._is_loop_running = False
            if error_callback is not None:
                error_callback(error)

    def disconnect(self) -> None:
        """
        Отключиться от RTD сокета робота.
        """

        if self.is_running() or self.is_connected():
            self._write_log("debug", "Disconnecting RTD receiver")
            self.stop_loop()
            self._socket.disconnect()
        self._is_connected = False
        self._thread = None

    def _receive_rtd(self) -> bool:
        """
        Принять RTD данные один раз.
        """
        raw_data = self._socket.receive(self._struct_size)
        if raw_data is None:
            return False
        while len(raw_data) < self._struct_size:
            chunk = self._socket.receive(self._struct_size - len(raw_data))
            if chunk is None:
                return False
            raw_data += chunk
        unpack_data = struct.unpack(STRUCT_FORMAT, raw_data)
        n = 0
        for field in fields(RTD):
            data = getattr(RTD, field.name)
            if isinstance(data, Tuple):
                amount = len(data)
            else:
                amount = 1

            if amount == 1:
                setattr(
                    self._rt_data,
                    field.name,
                    unpack_data[n],
                )
            else:
                setattr(
                    self._rt_data,
                    field.name,
                    unpack_data[n : n + amount],
                )
            n += amount
        return True

    def _validate_rtd(self) -> bool:
        """
        Проверить формат структуры RTD данных.
        """
        if (
            self._rt_data.packet_begin == RTDataPackageBorders.rtd_packet_begin
            and self._rt_data.packet_end == RTDataPackageBorders.rtd_packet_end
        ):
            return True
        raise RTDParsingError("Most probably incorrect byte parsing")

    def _write_log(
        self, level: Literal["debug", "info", "warning", "error"], message: str
    ):
        """
        Обертка для логгера.
        """

        if self._logger is not None:
            log_method = getattr(self._logger, level, self._logger.error)
            log_method(message)

    def __del__(self):
        if self.is_connected():
            self.disconnect()
