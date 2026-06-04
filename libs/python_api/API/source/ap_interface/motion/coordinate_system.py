from typing import Optional

from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.models.classes.data_classes.command_templates import (
    MOTION_SETUP,
)
from API.source.models.classes.enum_classes.various_types import (
    CoordinateSystemInfoType,
)
from API.source.models.constants import (
    POSITION_ORIENTATION_LENGTH,
)
from API.source.models.type_aliases import (
    AngleUnits,
    PositionOrientation,
)

_validate_length = validation.validate_length
_validate_literal = validation.validate_literal


class CoordinateSystem(object):
    """
    Класс для работы с координатными системами робота.
    """

    _position_orientation: PositionOrientation
    _orientation_units: AngleUnits

    def __init__(
        self,
        position_orientation: PositionOrientation,
        orientation_units: Optional[AngleUnits] = None,
    ) -> None:
        """Создаёт пользовательскую систему координат (СК), заданную относительно основания робота.

        Пользовательская СК определяется своей нулевой точкой и ориентацией
        в глобальной системе координат робота. После создания её можно
        использовать для:
        - задания точек движения в локальных координатах,
        - преобразования позиций между системами,
        - упрощения логики управления (например, относительно детали или инструмента).

        Этот класс **не требует подключения к роботу** — он является чисто
        вычислительным инструментом API.

        Args:
            position_orientation (PositionOrientation): Позиция и ориентация
                начала пользовательской СК в формате '(X, Y, Z, Rx, Ry, Rz)', где:
                - '(X, Y, Z)' — координаты в метрах;
                - '(Rx, Ry, Rz)' — углы поворота в указанных единицах.
                Задаётся в **глобальной системе координат основания робота**.
            orientation_units (AngleUnits, optional): Единицы измерения углов:
                - 'deg' — градусы (по умолчанию);
                - 'rad' — радианы.
        Examples:
            >>> # Создать СК, смещённую на 0.5 м по X и повёрнутую вокруг Z на 90°
            >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
            >>> local_cs = CoordinateSystem(
            ...     position_orientation=(0.5, 0.0, 0.0, 0.0, 0.0, 90.0),
            ...     orientation_units='deg'
            ... )

        Notes:
            - Все преобразования позиций между СК выполняются локально на стороне клиента.
        """
        if orientation_units is None:
            orientation_units = MOTION_SETUP.units
        self._set_coordinate_system(position_orientation, orientation_units)

    def set(
        self,
        position_orientation: PositionOrientation,
        orientation_units: Optional[AngleUnits] = None,
    ) -> None:
        """Обновляет параметры существующей пользовательской системы координат.

        Позволяет динамически изменить положение и ориентацию СК без создания
        нового объекта. Новые значения задаются относительно глобальной системы
        координат основания робота.

        Этот метод **не требует подключения к роботу** — он работает локально
        в памяти приложения.

        Args:
            position_orientation (PositionOrientation): Новое положение начала СК
                в формате '(X, Y, Z, Rx, Ry, Rz)', где:
                - '(X, Y, Z)' — координаты в метрах;
                - '(Rx, Ry, Rz)' — углы поворота в указанных единицах.
                Задаётся в **глобальной системе координат основания робота**.
            orientation_units (AngleUnits, optional): Единицы измерения углов:
                - 'deg' — градусы (по умолчанию);
                - 'rad' — радианы.

        Examples:
            >>> # Изначально СК задана относительно первой детали
            >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
            >>> cs = CoordinateSystem((0.3, 0.0, 0.2, 0, 0, 0))
            >>> # После замены детали — обновить СК
            >>> cs.set((0.35, 0.02, 0.21, 0, 0, 2.5))  # небольшой сдвиг и поворот

        Notes:
            - Обновление СК **не влияет на уже добавленные в буфер точки** — они
              остаются в той системе, в которой были заданы.
        """

        if orientation_units is None:
            orientation_units = MOTION_SETUP.units
        self._set_coordinate_system(position_orientation, orientation_units)

    def get(
        self, info_type: CoordinateSystemInfoType
    ) -> PositionOrientation | AngleUnits | None:
        """Возвращает запрошенную информацию о пользовательской системе координат.

        Метод позволяет получить либо полную позицию и ориентацию начала СК,
        либо только единицы измерения углов, в зависимости от переданного типа.

        Этот метод **не требует подключения к роботу** — все данные хранятся локально.

        Args:
            info_type (CoordinateSystemInfoType): Тип запрашиваемой информации:
                - `CoordinateSystemInfoType.POSITION_ORIENTATION` — вернуть
                  `(X, Y, Z, Rx, Ry, Rz)` в метрах и указанных единицах углов;
                - `CoordinateSystemInfoType.ORIENTATION_UNITS` — вернуть
                  текущие единицы измерения углов (`'deg'` или `'rad'`).

        Returns:
            PositionOrientation | AngleUnits:

                - Если `info_type == POSITION_ORIENTATION`: кортеж из 6 чисел
                  `(X, Y, Z, Rx, Ry, Rz)`, где:
                    * `(X, Y, Z)` — координаты в метрах;
                    * `(Rx, Ry, Rz)` — углы в текущих единицах измерения.
                - Если `info_type == ORIENTATION_UNITS`: строка `'deg'` или `'rad'`.

        Examples:
            >>> from API.source.models.classes.enum_classes.various_types import (
            ...     CoordinateSystemInfoType,
            ... )
            >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
            >>> cs = CoordinateSystem((0.5, 0.0, 0.3, 0, 0, 90), orientation_units='deg')

            >>> # Получить позицию и ориентацию
            >>> pose = cs.get(CoordinateSystemInfoType.POSITION_ORIENTATION)
            >>> print(f"Начало СК: {pose}")

            >>> # Получить единицы измерения
            >>> units = cs.get(CoordinateSystemInfoType.ORIENTATION_UNITS)
            >>> print(f"Единицы углов: {units}")  # Вывод: deg

        Notes:
            - Возвращаемая позиция всегда задана **в глобальной системе координат
              основания робота**, даже если сама СК — пользовательская.
            - Этот метод **не взаимодействует с контроллером робота** — он просто
              возвращает локально сохранённые данные.
            - Используйте этот метод, например, для логирования или отладки
              текущей конфигурации СК.
        """

        if info_type == CoordinateSystemInfoType.POSITION_ORIENTATION:
            return self._position_orientation
        if info_type == CoordinateSystemInfoType.ORIENTATION_UNITS:
            return self._orientation_units
        return None

    def _set_coordinate_system(
        self,
        position_orientation: PositionOrientation,
        orientation_units: AngleUnits,
    ) -> None:
        """
        Метод для установки системы координат и единиц измерения с валидацией
        входных данных.

        Args:
            position_orientation: Система координат в формате
                (X, Y, Z, Rx, Ry, Rz).
            orientation_units: Единицы измерения углов.
        """

        _validate_literal("angle", orientation_units)
        _validate_length(
            position_orientation,
            POSITION_ORIENTATION_LENGTH,
        )
        self._position_orientation = position_orientation
        self._orientation_units = orientation_units

    def __str__(self) -> str:
        return f"Coordinate System: {self._position_orientation} (3*m, 3*{self._orientation_units})"
