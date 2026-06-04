from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING, Optional, Tuple

from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.core.exceptions.data_validation_error.generic_error import (
    WristAIOUnitsNotSet,
    WristStateError,
)
from API.source.features.tools import dataclass_to_tuple, sleep
from API.source.models.classes.data_classes.command_templates import (
    SetWristInputOutputTemplate,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Setters as Set,
)
from API.source.models.classes.enum_classes.state_classes import (
    WristMode as Wm,
)
from API.source.models.classes.enum_classes.various_types import (
    PowerUnitsCode,
)
from API.source.models.constants import (
    AMPERAGE_VALUES_RANGE,
    AVAILABLE_WRIST_AN_IN_INDEX_COUNT,
    CHECK_FREQUENCY_SEC,
    CTRLR_WRIST_IO_SET_VALUE_PACK_FORMAT,
    SET_WRIST_MODE_AWAIT_SEC,
    VOLTAGE_INPUT_INDEXES_RANGE,
    VOLTAGE_VALUES_RANGE,
)
from API.source.models.type_aliases import (
    AnalogIndex,
    CompareSigns,
    PowerUnits,
)

if TYPE_CHECKING:
    from logging import Logger

    from API.source.core.network.controller_socket import (
        Controller,
    )
    from API.source.core.network.rtd_receiver_socket import (
        RTDReceiver,
    )


_validate_index = validation.validate_index
_validate_literal = validation.validate_literal
_validate_value = validation.validate_value


class WristAnalogIO(object):
    """
    Класс для работы с аналоговыми входами/выходами платы запястья робота.
    """

    _controller: Controller
    _rtd_receiver: RTDReceiver
    _logger: Logger

    def __init__(
        self,
        controller: Controller,
        rtd_receiver: RTDReceiver,
        connection_state: ConnectionState,
        logger: Logger,
    ):
        self._controller = controller
        self._rtd_receiver = rtd_receiver
        self._connection_state = connection_state
        self._logger = logger

    @handle_connection(available_in_read_only=True)
    def check_wrist_enable(self) -> bool:
        """Проверяет, подключена ли и активна ли плата запястья робота.

        Метод служит для быстрой валидации наличия платы запястья: если плата
        отсутствует (режим `'off'`), выбрасывается исключение. В противном случае
        возвращается подтверждение доступности.
        Метод доступен в режиме «read only».

        Returns:
            bool: `True`, если плата запястья подключена и не находится в состоянии `'off'`.

        Raises:
            WristStateError: Если плата запястья отсутствует (находится в режиме `'off'`).

        Examples:
            >>> try:
            ...     robot.wrist.analog.check_wrist_enable()
            ...     print("Плата запястья доступна")
            ... except WristStateError:
            ...     print("Плата запястья не обнаружена")

        Notes:
            - Используется вспомогательно перед операциями, требующими наличия платы запястья.
        """
        if self._rtd_receiver.get_data().wrist_mode == Wm.off:
            raise WristStateError()
        return True

    @handle_connection(available_in_read_only=True)
    def get_input(
        self, index: AnalogIndex, units: PowerUnits
    ) -> Optional[Tuple[int, float]]:
        """Считывает текущее аналоговое значение с указанного входа платы запястья.

        Метод позволяет получить мгновенное значение напряжения или тока с одного
        из аналоговых входов — например, для считывания показаний датчиков давления,
        уровня, температуры или других устройств с аналоговым выходом.

        Метод доступен в режиме «read only».

        Args:
            index (AnalogIndex): Индекс аналогового входа. Допустимые значения: `0`–`1`.
            units (PowerUnits): Единицы измерения сигнала:
                - `'V'` — ожидается напряжение (вход должен быть подключен к источнику 0–10 В);
                - `'mA'` — ожидается ток (вход должен быть подключен к источнику 4–20 мА).

        Returns:
            Optional[Tuple[int, float]]:
                - Кортеж `(индекс, значение)`, если чтение успешно:
                    - для `'V'`: значение в диапазоне **0.0 – 10.0 В**;
                    - для `'mA'`: значение в диапазоне **4.0 – 20.0 мА**.
                - `None`, если плата запястья отсутствует, вход недоступен или произошла ошибка связи.

        Examples:
            >>> # Считать напряжение с входа 0
            >>> result = robot.wrist.analog.get_input(0, 'V')
            >>> if result:
            ...     idx, voltage = result
            ...     print(f"Вход {idx}: {voltage:.2f} В")

            >>> # Считать ток с входа 1
            >>> idx, current = robot.wrist.analog.get_input(1, 'mA') or (1, 0.0)
            >>> if current >= 12.0:
            ...     print("Сигнал выше порога")

        Notes:
            - Метод не блокирует выполнение и возвращает мгновенное значение.
            - Возвращаемый `None` может указывать на отсутствие платы запястья
              (режим `'off'`) или временную ошибку связи.
        """
        if self.check_wrist_enable():
            if self._set_input_units(index, units):
                return (
                    index,
                    self._rtd_receiver.get_data().wrist_an_in_value[index],
                )
            else:
                raise WristAIOUnitsNotSet()
        return None

    def _set_input_units(
        self,
        index: AnalogIndex,
        units: PowerUnits,
        await_sec: int = SET_WRIST_MODE_AWAIT_SEC,
    ) -> bool:
        """
        Установить единицы измерения, снимаемые на 'index' аналоговом входе
        платы запястья. Тип устанавливаемого значения зависит от переменной
        units.

        Args:
            index: Индекс выхода (0-1).
            units: Единицы измерения. 'mA' - сила тока. 'V' - напряжение.
        Returns:
            True: В случае успешной отправки команды.
            False: В случае таймаута или неудачной отправки команды.
        """
        if self._rtd_receiver.get_data().wrist_mode == Wm.off:
            raise WristStateError(
                f"Can not set input units, when wrist mode is {Wm.off}"
            )
        _validate_literal("power", units)
        _validate_index(index, range(AVAILABLE_WRIST_AN_IN_INDEX_COUNT))
        set_input_output_template = SetWristInputOutputTemplate()
        set_input_output_template.an_in_mask[index] = 1
        set_input_output_template.an_in_mode[index] = PowerUnitsCode[units]
        set_input_output_template.mux_mode = Wm.analog_in
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
                    "Failed to set input units - connection was lost"
                )
                return False
            if (
                self._rtd_receiver.get_data().wrist_an_in_curr_mode[index]
                == PowerUnitsCode[units]
            ):
                return res
        return False

    @handle_connection(available_in_read_only=True)
    def wait_input(
        self,
        index: AnalogIndex,
        threshold_value: float,
        units: PowerUnits,
        greater_or_less: CompareSigns,
        await_sec: int = -1,
    ) -> bool:
        """Ожидает, пока аналоговый вход платы запястья не преодолеет заданное пороговое значение.

        Метод позволяет синхронизировать выполнение программы с внешними аналоговыми
        сигналами — например, дождаться, пока датчик давления (4–20 мА) не достигнет
        заданного уровня или пока управляющее напряжение (0–10 В) не упадёт ниже порога.

        Метод доступен в режиме «read only».

        Args:
            index (AnalogIndex): Индекс аналогового входа. Допустимые значения: `0`–`1`.
            threshold_value (float): Пороговое значение:
                - при `units='V'`: от **0.0 до 10.0 В**;
                - при `units='mA'`: от **4.0 до 20.0 мА**.
            units (PowerUnits): Тип измеряемого сигнала:
                - `'V'` — напряжение (вход должен быть подключён к источнику 0–10 В);
                - `'mA'` — сила тока (вход должен быть подключён к источнику 4–20 мА).
            greater_or_less (CompareSigns): Условие ожидания:
                - `'>'` — ждать, пока значение **станет больше** порога;
                - `'<'` — ждать, пока значение **станет меньше** порога.
            await_sec (int): Лимит времени ожидания в секундах:
                - `-1` — ожидание без ограничения (по умолчанию);
                - `0` — однократная проверка без блокировки;
                - положительное число — максимальное время ожидания в секундах.

        Returns:
            bool:
                - `True`, если пороговое значение было преодолено в течение указанного времени;
                - `False`, если произошёл тайм-аут (только при `await_sec >= 0`).

        Raises:
            ArgIndexError: Если `index` выходит за допустимый диапазон (0–1).
            ArgComparisonError: Если `greater_or_less` не равен `'>'` или `'<'`.

        Examples:
            >>> # Дождаться, пока напряжение на входе 0 превысит 7.5 В (макс. 10 сек)
            >>> if robot.wrist.analog.wait_input(0, 7.5, 'V', '>', await_sec=10):
            ...     print("Уровень напряжения достигнут")

            >>> # Проверить однократно, упало ли значение тока на входе 1 ниже 8 мА
            >>> is_low = robot.wrist.analog.wait_input(1, 8.0, 'mA', '<', await_sec=0)

            >>> # Бесконечно ждать, пока ток не поднимется выше 16 мА
            >>> robot.wrist.analog.wait_input(0, 16.0, 'mA', '>')

        Notes:
            - Метод блокирует выполнение программы.
            - Убедитесь, что тип сигнала (`units`) соответствует реальному подключению:
        """
        if self._rtd_receiver.get_data().wrist_mode == Wm.off:
            raise WristStateError(
                f"Can not wait input value, when wrist mode is {Wm.off}"
            )
        _validate_literal("power", units)
        _validate_index(index, range(AVAILABLE_WRIST_AN_IN_INDEX_COUNT))
        _validate_value(
            threshold_value,
            (
                VOLTAGE_VALUES_RANGE
                if index in range(VOLTAGE_INPUT_INDEXES_RANGE)
                else AMPERAGE_VALUES_RANGE
            ),
        )
        _validate_literal("compare", greater_or_less)
        self._logger.info(f"Waiting analog signal on {index} wrist input...")
        for _ in sleep(
            await_sec=await_sec,
            frequency=CHECK_FREQUENCY_SEC,
        ):
            if not self._connection_state.is_connected():
                self._logger.error(
                    "Failed to wait wrist analog input - connection was lost"
                )
                return False
            actual_value = self.get_input(index, units)
            if actual_value is None:
                continue
            actual_value = actual_value[1]
            match greater_or_less:
                case "<":
                    if actual_value <= threshold_value:
                        self._logger.info(
                            (
                                f"Analog signal on wrist {index}: "
                                f"{actual_value} < "
                                f"{threshold_value}"
                            )
                        )
                        return True
                case ">":
                    if actual_value >= threshold_value:
                        self._logger.info(
                            (
                                f"Analog signal on wrist {index}: "
                                f"{actual_value} > "
                                f"{threshold_value}"
                            )
                        )
                        return True
        self._logger.info(f"Analog signal on {index} wrist input timeout")
        return False
