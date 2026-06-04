from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING, List, Optional, cast

import API.source.features.mathematics.unit_convert as math_s
from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.models.classes.data_classes.command_templates import (
    MOTION_SETUP,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Getters as Get,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Setters as Set,
)
from API.source.models.constants import (
    CTRLR_SET_GET_TOOL_PACK_UNPACK_FORMAT,
    ORIENTATION_SLICE,
    POSITION_ORIENTATION_LENGTH,
    POSITION_SLICE,
)
from API.source.models.type_aliases import (
    AngleUnits,
    PositionOrientation,
)

if TYPE_CHECKING:
    from API.source.core.network.controller_socket import (
        Controller,
    )


_validate_literal = validation.validate_literal
_validate_length = validation.validate_length


class Tool(object):
    """
    Класс для работы с инструментом робота.
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
        tool_end_point: PositionOrientation,
        units: Optional[AngleUnits] = None,
    ) -> bool:
        """Устанавливает положение и ориентацию конца инструмента (ЦТИ, TCP) относительно фланца робота.

        Метод задаёт смещение рабочей точки инструмента — например, кончика паяльника,
        сопла клеевого аппликатора или захвата манипулятора. Это позволяет роботу
        корректно управлять движением именно этой точки, а не центром фланца.

        Args:
            tool_end_point (PositionOrientation): Смещение TCP в формате
                `(X, Y, Z, Rx, Ry, Rz)`, где:
                - `X, Y, Z` — линейное смещение в метрах относительно фланца;
                - `Rx, Ry, Rz` — угловое смещение (вращение) вокруг осей X, Y, Z.
            units (Optional[AngleUnits]): Единицы измерения углов:
                - `'deg'` — градусы (используется по умолчанию, если `units=None`);
                - `'rad'` — радианы.

        Returns:
            bool: `True`, если команда успешно отправлена и TCP обновлён.

        Examples:
            >>> # Установить TCP: смещение 100 мм вперёд, без поворота (в градусах по умолчанию)
            >>> robot.tool.set((0.1, 0.0, 0.0, 0.0, 0.0, 0.0))

            >>> # Установить TCP с поворотом на 45 градусов вокруг Z
            >>> robot.tool.set((0.05, 0.0, 0.0, 0.0, 0.0, 45.0), 'deg')

            >>> # Установить TCP с углами в радианах
            >>> import math
            >>> robot.tool.set((0.0, 0.0, 0.05, 0.0, 0.0, math.pi / 4), 'rad')

        Notes:
            - Линейные компоненты (`X, Y, Z`) **всегда задаются в метрах**.
            - Угловые компоненты (`Rx, Ry, Rz`) интерпретируются в зависимости от `units`.
            - Если `units` не указан, углы считаются заданными в **градусах**.
            - После изменения TCP все последующие команды перемещения будут относиться
              именно к новой рабочей точке.
        """

        if units is None:
            units = MOTION_SETUP.units
        _validate_length(tool_end_point, POSITION_ORIENTATION_LENGTH)
        _validate_literal("angle", units)
        if units == "deg":
            tool_end_point = list(tool_end_point[POSITION_SLICE]) + cast(
                List,
                math_s.degrees_to_radians(*tool_end_point[ORIENTATION_SLICE]),
            )
        return self._controller.send(
            Set.ctrlr_coms_set_tool,
            pack(
                CTRLR_SET_GET_TOOL_PACK_UNPACK_FORMAT,
                *tool_end_point,
            ),
        )

    @handle_connection(available_in_read_only=False)
    def get(self, units: Optional[AngleUnits] = None) -> PositionOrientation:
        """Получает текущее смещение конца инструмента (TCP) относительно фланца робота.

        Метод возвращает координаты рабочей точки инструмента, заданные ранее
        через `set()`. Эти данные определяют, какая точка в пространстве считается
        «концом» инструмента при планировании и выполнении траекторий.

        Args:
            units (Optional[AngleUnits]): Единицы измерения угловых компонент:
                - `'deg'` — градусы (по умолчанию, если `units=None`);
                - `'rad'` — радианы.

        Returns:
            PositionOrientation: Кортеж вида `(X, Y, Z, Rx, Ry, Rz)`, где:
                - `X, Y, Z` — линейное смещение в **метрах**;
                - `Rx, Ry, Rz` — угловое смещение вокруг соответствующих осей
                  в указанных единицах (`'deg'` или `'rad'`).

        Examples:
            >>> # Получить TCP в градусах (по умолчанию)
            >>> tcp = robot.tool.get()
            >>> x, y, z, rx, ry, rz = tcp
            >>> print(f"TCP: ({x:.3f}, {y:.3f}, {z:.3f}) м, углы: ({rx:.1f}, {ry:.1f}, {rz:.1f})°")

            >>> # Получить TCP с углами в радианах
            >>> tcp_rad = robot.tool.get('rad')
            >>> _, _, _, rx, ry, rz = tcp_rad
            >>> print(f"Углы в радианах: ({rx:.3f}, {ry:.3f}, {rz:.3f})")

        Notes:
            - Линейные компоненты (`X, Y, Z`) всегда возвращаются в **метрах**.
            - Угловые компоненты преобразуются в указанные единицы при возврате.
            - Если TCP не был задан явно, метод может вернуть нулевое смещение
              `(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)`.
        """

        if units is None:
            units = MOTION_SETUP.units
        _validate_literal("angle", units)
        self._controller.send(Get.ctrlr_coms_get_tool)
        response = list(
            self._controller.receive(
                Get.ctrlr_coms_get_tool,
                CTRLR_SET_GET_TOOL_PACK_UNPACK_FORMAT,
            )
        )
        if units == "deg":
            response = response[POSITION_SLICE] + cast(
                List, math_s.radians_to_degrees(*response[ORIENTATION_SLICE])
            )
        return response
