from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING

from API.source.ap_interface.wrist.analog_io import (
    WristAnalogIO,
)
from API.source.ap_interface.wrist.digital_io import (
    WristDigitalIO,
)
from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.core.exceptions.data_validation_error.generic_error import (
    FunctionTimeOutError,
)
from API.source.features.tools import (
    dataclass_to_tuple,
    sleep,
)
from API.source.models.classes.data_classes.command_templates import (
    SetWristInputOutputTemplate,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Setters as Set,
)
from API.source.models.classes.enum_classes.state_classes import (
    WristMode as Wm,
)
from API.source.models.constants import (
    CHECK_FREQUENCY_SEC,
    CTRLR_WRIST_IO_SET_VALUE_PACK_FORMAT,
    SET_WRIST_MODE_AWAIT_SEC,
)
from API.source.models.type_aliases import WristMode_

if TYPE_CHECKING:
    from logging import Logger

    from API.source.core.network.controller_socket import (
        Controller,
    )
    from API.source.core.network.rtd_receiver_socket import (
        RTDReceiver,
    )


_validate_literal = validation.validate_literal


class Wrist(object):
    """
    Класс для работы с платой запястья робота.
    Доступные состояния платы запястья:
        'off' — Плата запястья отсутствует.
        'rs485' — Плата запястья найдена и работает в режиме rs485 (обмен
            данными по протоколу modbus).
        'analog_in' — Плата запястья найдена и находится в режиме работы
            с аналоговыми входами.
        'nc' — Плата запястья найдена но не сконфигурирована для работы с
            внешними устройствами.
        'gnd' — Плата запястья найдена и находится в режиме общей 'земли'
    """

    digital: WristDigitalIO
    """Подкласс для работы с цифровыми входами/выходами."""
    analog: WristAnalogIO
    """Подкласс для работы с аналоговыми входами/выходами."""
    _rtd_receiver: RTDReceiver
    _controller: Controller

    def __init__(
        self,
        controller: Controller,
        rtd_receiver: RTDReceiver,
        connection_state: ConnectionState,
        logger: Logger,
    ) -> None:
        self._rtd_receiver = rtd_receiver
        self._controller = controller
        self._connection_state = connection_state
        self._logger = logger
        self.digital = WristDigitalIO(
            controller=controller,
            rtd_receiver=rtd_receiver,
            connection_state=self._connection_state,
            logger=logger,
        )
        self.analog = WristAnalogIO(
            controller=controller,
            rtd_receiver=rtd_receiver,
            connection_state=self._connection_state,
            logger=logger,
        )

    @handle_connection(available_in_read_only=True)
    def get(self) -> Wm:
        """Получает текущее состояние платы запястья робота.

        Метод возвращает режим, в котором в данный момент работает плата запястья.
        Метод доступен в режиме «read only»

        Returns:
            str: Текущее состояние платы запястья. Возможные значения:
                - 'off' — плата запястья отсутствует;
                - 'rs485' — плата подключена и работает в режиме Modbus RTU по RS-485;
                - 'analog_in' — плата подключена и настроена на работу с аналоговыми входами;
                - 'nc' — плата подключена, но не сконфигурирована для работы с внешними устройствами;
                - 'gnd' — плата подключена и находится в режиме общей «земли»

        Examples:
            >>> state = robot.wrist.get()
            >>> if state == 'analog_in':
            ...     print("Плата запястья готова к чтению аналоговых сигналов")
            >>> elif state == 'off':
            ...     print("Плата запястья не выключена")
        """
        return Wm(int(self._rtd_receiver.get_data().wrist_mode))

    @handle_connection(available_in_read_only=False)
    def set(
        self,
        mode: WristMode_,
        await_sec: int = SET_WRIST_MODE_AWAIT_SEC,
    ) -> bool:
        """Устанавливает рабочий режим платы запястья робота.

        Метод позволяет переключить плату запястья в требуемое состояние:
        отключить её, перевести в режим аналоговых входов, настроить для обмена
        по RS-485 или оставить в нейтральном состоянии.

        Args:
            mode (WristMode_): Целевой режим платы. Допустимые значения:
                - `'off'` — отключить плату запястья;
                - `'rs485'` — включить режим Modbus RTU по RS-485;
                - `'analog_in'` — настроить плату для работы с аналоговыми входами;
                - `'nc'` — оставить плату подключённой, но неактивной;
                - `'gnd'` — перевести плату в режим общей «земли»
            await_sec (int): Максимальное время ожидания подтверждения смены режима (в секундах):
                - `-1` — ожидание без ограничения;
                - `0` — проверка выполняется один раз без блокировки;
                - положительное значение — лимит времени ожидания в секундах
                  (по умолчанию используется 60).

        Returns:
            bool:
                - `True`, если режим успешно установлен и подтверждён платой;
                - `False`, если смена режима не подтверждена в течение указанного времени.

        Examples:
            >>> # Перевести плату запястья в режим аналоговых входов с таймаутом 5 сек
            >>> robot.wrist.set('analog_in', await_sec=5)

            >>> # Отключить плату запястья (используется значение по умолчанию для await_sec)
            >>> robot.wrist.set('off')

            >>> # Попытаться установить режим RS-485
            >>> success = robot.wrist.set('rs485', await_sec=10)
            >>> if not success:
            ...     print("Не удалось перевести плату в режим RS-485")
        """
        _validate_literal("Wm", mode)
        set_input_output_template = SetWristInputOutputTemplate()
        set_input_output_template.mux_mode = Wm[mode].value
        res = self._controller.send(
            Set.ctrlr_coms_set_wrist_io,
            pack(
                CTRLR_WRIST_IO_SET_VALUE_PACK_FORMAT,
                *dataclass_to_tuple(set_input_output_template),
            ),
        )
        for _ in sleep(
            await_sec=await_sec,
            frequency=CHECK_FREQUENCY_SEC,
        ):
            if not self._connection_state.is_connected():
                self._logger.error(
                    "Failed to set wrist mode - connection was lost"
                )
                return False
            if self.get() == Wm[mode].value:
                return res
        raise FunctionTimeOutError("Wrist mode", await_sec)
