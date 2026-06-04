from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING, Tuple, cast

from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Getters as Get,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Setters as Set,
)
from API.source.models.constants import (
    CTRLR_SET_GET_PAYLOAD_PACK_UNPACK_FORMAT,
    TCP_POSITION_COUNT,
)

if TYPE_CHECKING:
    from API.source.core.network.controller_socket import (
        Controller,
    )


_validate_length = validation.validate_length


class PayLoad(object):
    """
    Класс для работы с полезной нагрузкой робота.
    """

    _controller: Controller

    def __init__(
        self,
        controller: Controller,
        connection_state: ConnectionState,
    ) -> None:
        self._controller = controller
        self._connection_state = connection_state

    @handle_connection(available_in_read_only=False)
    def set(
        self,
        mass: float,
        tcp_mass_center: Tuple[float, float, float],
    ) -> bool:
        """Устанавливает массу и положение центра масс полезной нагрузки робота.

        Метод позволяет задать физические параметры устанавливаемого на фланец
        инструмента или груза. Эти данные используются системой управления для
        корректного расчёта моментов, компенсации инерции и обеспечения
        стабильного движения.

        Args:
            mass (float): Масса полезной нагрузки в килограммах.
            tcp_mass_center (tuple[float, float, float]): Координаты центра масс
                относительно системы координат фланца, в метрах. Формат: `(X, Y, Z)`, где:
                - `X` — смещение вдоль оси фланца (обычно вперёд/назад),
                - `Y` — смещение влево/вправо,
                - `Z` — смещение вверх/вниз.

        Returns:
            bool: `True`, если параметры успешно переданы в контроллер робота.

        Examples:
            >>> # Установить массу 2.5 кг с центром масс в центре фланца
            >>> robot.payload.set(2.5, (0.0, 0.0, 0.0))

            >>> # Установить длинный инструмент: масса 1.8 кг, центр масс смещён на 80 мм вперёд
            >>> robot.payload.set(1.8, (0.08, 0.0, 0.0))

            >>> # Лёгкий датчик с центром масс чуть вниз и вправо
            >>> robot.payload.set(0.3, (0.01, -0.02, -0.015))

        Notes:
            - Значения центра масс задаются **в метрах**, а не в миллиметрах.
            - Рекомендуется устанавливать эти параметры **до** запуска движения.
        """

        _validate_length(tcp_mass_center, TCP_POSITION_COUNT)
        return self._controller.send(
            Set.ctrlr_coms_set_payload,
            pack(
                CTRLR_SET_GET_PAYLOAD_PACK_UNPACK_FORMAT,
                mass,
                *tcp_mass_center,
            ),
        )

    @handle_connection(available_in_read_only=False)
    def get(
        self,
    ) -> Tuple[float, Tuple[float, float, float]]:
        """Получает текущие параметры массы и центра масс полезной нагрузки робота.

        Метод возвращает ранее установленные (или используемые по умолчанию) значения
        массы и положения центра масс инструмента или груза, закреплённого на фланце.
        Эти данные используются системой управления для расчёта динамики и компенсации
        инерционных эффектов при движении.

        Returns:
            Tuple[float, Tuple[float, float, float]]: Кортеж вида `(масса, (X, Y, Z))`, где:
                - `масса` — масса полезной нагрузки в килограммах (float);
                - `(X, Y, Z)` — координаты центра масс в метрах относительно
                  системы координат фланца;

        Examples:
            >>> payload = robot.payload.get()
            ... mass, (x, y, z) = payload
            ... print(f"Масса: {mass} кг, ЦМ: ({x:.3f}, {y:.3f}, {z:.3f}) м")

            >>> # Проверить, совпадает ли центр масс с центром фланца
            >>> _, (x, y, z) = robot.payload.get()
            >>> if abs(x) < 0.001 and abs(y) < 0.001 and abs(z) < 0.001:
            ...     print("ЦМ в центре фланца")

        Notes:
            - Значения возвращаются в **метрах** и **килограммах**.
        """

        self._controller.send(Get.ctrlr_coms_get_payload)
        response = self._controller.receive(
            Get.ctrlr_coms_get_payload,
            CTRLR_SET_GET_PAYLOAD_PACK_UNPACK_FORMAT,
        )
        return cast(
            tuple[float, tuple[float, float, float]],
            (response[0], response[1:]),
        )
