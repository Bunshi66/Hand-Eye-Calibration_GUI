from __future__ import annotations

from typing import TYPE_CHECKING

from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.features.tools import sleep
from API.source.models.classes.enum_classes.state_classes import (
    InComingSafetyStatus as Iss,
)
from API.source.models.constants import CHECK_FREQUENCY_SEC
from API.source.models.type_aliases import SafetyStatus_

if TYPE_CHECKING:
    from logging import Logger

    from API.source.core.network.rtd_receiver_socket import (
        RTDReceiver,
    )
from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)

_validate_literal = validation.validate_literal


class SafetyStatus(object):
    """
    Класс для работы с текущими статусами безопасности.
    """

    def __init__(
        self,
        rtd_receiver: RTDReceiver,
        connection_state: ConnectionState,
        logger: Logger,
    ) -> None:
        self._rtd_receiver = rtd_receiver
        self._connection_state = connection_state
        self._logger = logger

    @handle_connection(available_in_read_only=True)
    def get(self) -> str:
        """Возвращает текущий статус безопасности робота.

        Статус отражает состояние системы безопасности и определяет,
        какие операции в данный момент разрешены. Метод доступен
        в режиме «read only».

        Возможные значения:

            - 'deinit': Робот не инициализирован. Операции недоступны.
            - 'recovery': Нарушение ограничений при старте. Доступны только
                FreeDrive и Jogging.
            - 'normal': Рабочее состояние с базовыми ограничениями безопасности.
            - 'reduced': Рабочее состояние с повышенными ограничениями
                (например, сниженная скорость, уменьшенная рабочая зона).
            - 'safeguard_stop': Экстренный останов 2-й категории (по кнопке
                безопасности). Торможение без обрыва питания, траектория сохраняется.
            - 'emergency_stop': Экстренный останов 1-й категории (кнопка E-Stop).
                Активируются тормоза, траектория не сохраняется.
            - 'fault': Экстренный останов 0-й категории из-за внутренней ошибки.
                Отключение питания.
            - 'violation': Экстренный останов 0-й категории из-за нарушения
                пределов безопасности (например, превышение скорости или усилия).
                Отключение питания.

        Returns:
            str: Текущий статус безопасности. Значение всегда одно из
                перечисленных выше.

        Examples:
            >>> status = robot.safety_status.get()
            >>> if status == 'emergency_stop':
            ...     print("Требуется сброс кнопки аварийного останова!")
            ... elif status in ('normal', 'reduced'):
            ...     print("Робот готов к работе")
        """

        return Iss(self._rtd_receiver.get_data().safety).name

    @handle_connection(available_in_read_only=True)
    def wait(self, status: SafetyStatus_, await_sec: int = -1) -> bool:
        """Ожидает перехода системы безопасности робота в заданный статус.

        Метод блокирует выполнение до тех пор, пока текущий статус безопасности
        не станет равным указанному `status`, либо не истечёт заданное время
        ожидания. Поддерживает как ограниченное, так и бесконечное ожидание.

        Доступен в режиме «read only».

        Args:
            status: Ожидаемый статус безопасности —
                ('recovery', 'normal', 'reduced', 'safeguard_stop').
            await_sec (int, optional): Максимальное время ожидания в секундах.
                - `-1` — ожидание без ограничения по времени (по умолчанию);
                - `0` — выполнить одну проверку (неблокирующий вызов);
                - `> 0` — ожидать не более указанного числа секунд.

        Returns:
            True: В случае успешной смены режима безопасности.
            False: В случае таймаута (если await_sec >= 0).

        Examples:
            >>> # Ждать переход в режим 'normal' (до 10 секунд)
            >>> if not robot.safety_status.wait('normal', await_sec=10):
            ...     print("Робот не перешёл в режим 'normal'")

            >>> # Неблокирующая проверка
            >>> if not robot.safety_status.wait('normal', await_sec=0):
            ...     print("Робот находится не в режиме 'normal'")

        Notes:
            - При `await_sec = -1` вызов может блокировать программу неограниченно —
              используйте с осторожностью.
            - Если текущий статус уже совпадает с `status`, метод немедленно
              вернёт `True`.
        """

        _validate_literal("ss", status)
        for _ in sleep(
            await_sec=await_sec,
            frequency=CHECK_FREQUENCY_SEC,
        ):
            if not self._connection_state.is_connected():
                self._logger.error(
                    "Failed to wait safety status - connection was lost"
                )
                return False
            if self.get() == status:
                return True
        return False
