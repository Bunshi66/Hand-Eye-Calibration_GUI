from typing import List, Optional, Tuple, cast

import numpy as np
import numpy.typing as npt
from scipy.spatial.transform import Rotation

from API.source.ap_interface.motion.coordinate_system import (
    CoordinateSystem,
)
from API.source.core.exceptions.data_validation_error.generic_error import (
    CalculatePlaneError,
)
from API.source.models.classes.data_classes.command_templates import (
    MOTION_SETUP,
)
from API.source.models.classes.enum_classes.various_types import (
    CoordinateSystemInfoType,
)
from API.source.models.constants import (
    ORIENTATION_SLICE,
    POSITION_SLICE,
)
from API.source.models.type_aliases import (
    AngleUnits,
    PositionOrientation,
)


def get_transformation_parameters(
    coordinate_system: CoordinateSystem,
) -> Tuple[npt.NDArray, Rotation]:
    """
    Вычисление вектора трансляции и матрицы поворота.

    Args:
        coordinate_system: Выбранная система координат.
    Returns:
        tuple: Вектор перемещения и Матрица поворота.
    """

    coordinate_system_position_orientation = np.array(
        coordinate_system.get(CoordinateSystemInfoType.POSITION_ORIENTATION)
    )
    return (
        np.array(coordinate_system_position_orientation[POSITION_SLICE]),
        Rotation.from_euler(
            "xyz",
            coordinate_system_position_orientation[ORIENTATION_SLICE],
            degrees=coordinate_system.get(
                CoordinateSystemInfoType.ORIENTATION_UNITS
            )
            == "deg",
        ),
    )


def calculate_plane_from_points(
    pO: List[float] | Tuple[float, float, float],
    pX: List[float] | Tuple[float, float, float],
    pY: List[float] | Tuple[float, float, float],
    orientation_units: Optional[AngleUnits] = None,
) -> PositionOrientation:
    """Вычисляет позицию и ориентацию пользовательской системы координат по трём точкам.

    На основе трёх точек в пространстве строится локальная система координат:
    - `pO` — начало системы (origin);
    - вектор `pX - pO` задаёт направление **оси X**;
    - вектор `pY - pO` участвует в построении **оси Y**;
    - ось **Z** вычисляется как векторное произведение X × Y.

    Результат — позиция и ориентация этой системы в глобальной СК основания робота,
    в формате `(X, Y, Z, Rx, Ry, Rz)`.

    Эта функция **не требует подключения к роботу** — она выполняет чисто
    геометрические вычисления.

    Args:
        pO (List[float] | Tuple[float, float, float]): Точка начала координат плоскости
            в формате `(x, y, z)` в метрах.
        pX (List[float] | Tuple[float, float, float]): Точка, задающая направление оси X,
            в формате `(x, y, z)` в метрах. Должна отличаться от `pO`.
        pY (List[float] | Tuple[float, float, float]): Точка, лежащая в плоскости XY,
            в формате `(x, y, z)` в метрах. Не должна лежать на прямой `pO–pX`.
        orientation_units (AngleUnits, optional): Единицы измерения углов в результате:
            - `'deg'` — градусы (по умолчанию);
            - `'rad'` — радианы.

    Returns:
        PositionOrientation: Позиция и ориентация системы координат в формате
        `(X, Y, Z, Rx, Ry, Rz)`, где:
        - `(X, Y, Z)` — координаты точки `pO` в метрах;
        - `(Rx, Ry, Rz)` — углы поворота в указанных единицах,
          представляющие ориентацию осей X, Y, Z.

    Examples:
        >>> # Определить СК по трём точкам на поверхности стола
        >>> from API.source.features.mathematics.coordinate_system import (
        ...     calculate_plane_from_points,
        ... )
        >>> origin = (0.3, 0.0, 0.8)      # угол стола
        >>> x_point = (0.4, 0.0, 0.8)     # 10 см вдоль края
        >>> y_point = (0.3, 0.1, 0.8)     # 10 см поперёк
        >>> pose = calculate_plane_from_points(origin, x_point, y_point)
        >>> print(f"СК стола: {pose}")

        >>> # Использовать для создания пользовательской СК
        >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
        >>> table_cs = CoordinateSystem(pose)

    Notes:
        - Точки `pO`, `pX`, `pY` **должны быть неколлинеарны**, иначе ось Z
          не определится (функция может вернуть некорректную ориентацию).
    """

    if orientation_units is None:
        orientation_units = MOTION_SETUP.units
    point_O = np.array(pO)
    point_X = np.array(pX)
    point_Y = np.array(pY)
    if (
        np.array_equal(point_O, point_X)
        or np.array_equal(point_O, point_Y)
        or np.array_equal(point_X, point_Y)
    ):
        raise CalculatePlaneError(
            "Two or more points defining the direction of the coordinate axes "
            "of the plane coincide, the coordinates of the points must "
            "be unique."
        )
    vecX = point_X - point_O
    vecY = point_Y - point_O
    vecX_norm = vecX / np.linalg.norm(vecX)
    vecY_norm = vecY / np.linalg.norm(vecY)
    vecZ = np.cross(vecX_norm, vecY_norm)
    if np.linalg.norm(vecZ) == 0:
        raise CalculatePlaneError(
            f"The vectors {vecX} and {vecY} are collinear."
        )
    vecZ_norm = vecZ / np.linalg.norm(vecZ)
    rotation_matrix = np.array(
        [
            vecX_norm,
            np.cross(vecZ_norm, vecX_norm),
            vecZ_norm,
        ]
    ).T
    rotation = Rotation.from_matrix(rotation_matrix)
    rpy = rotation.as_euler("xyz", degrees=orientation_units == "deg")
    return point_O.tolist() + rpy.tolist()


def convert_position_orientation(
    coordinate_system: CoordinateSystem,
    position_orientation: PositionOrientation,
    orientation_units: Optional[AngleUnits] = None,
    to_local: bool = False,
) -> PositionOrientation:
    """Преобразует позицию и ориентацию между глобальной и пользовательской системой координат.

    Функция выполняет двунаправленное преобразование:
    - если `to_local=True`: из **глобальной СК (основания робота)**
       в **локальную СК** (заданную объектом `coordinate_system`);
    - если `to_local=False` (по умолчанию): из **локальной СК**
       в **глобальную СК**.

    Это чисто вычислительная функция — **не требует подключения к роботу**.

    Args:
        coordinate_system: Выбранная система координат.
        position_orientation: Конвертируемые позиция и ориентация в единицах
            измерения выбранной системы координат.
        orientation_units: Переданные единицы измерения. По-умолчанию градусы.
            'deg' — градусы.
            'rad' — радианы.
        to_local: Флаг переключения для конвертации из глобальной системы
            координат (основание робота) в локальную (пользовательскую).

    Returns:
        PositionOrientation: Преобразованная позиция и ориентация в том же формате
        `(X, Y, Z, Rx, Ry, Rz)`, в указанных единицах измерения.

    Examples:
        >>> # Создать пользовательскую СК (смещение + поворот)
        >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
        ... from API.source.features.mathematics.coordinate_system import (
        ...     convert_position_orientation,
        ... )
        >>> user_cs = CoordinateSystem((0.5, 0.0, 0.0, 0.0, 0.0, 90.0))

        >>> # Преобразовать точку из локальной СК в глобальную (по умолчанию)
        >>> local_point = (0.1, 0.0, 0.0, 0, 0, 0)  # 10 см вперёд от детали
        >>> global_point = convert_position_orientation(user_cs, local_point)
        >>> print(f"Глобальная позиция: {global_point}")

        >>> # Преобразовать текущую позицию робота в локальную СК
        >>> current_global = robot.motion.linear.get_actual_position()
        >>> current_local = convert_position_orientation(
        ...     user_cs,
        ...     current_global,
        ...     to_local=True
        ... )
        >>> print(f"Позиция относительно детали: {current_local}")

    Notes:
        - Углы должны быть в **тех же единицах**, что указаны в `orientation_units`.
        - Функция **не проверяет достижимость** результирующей позиции —
          это чисто геометрическое преобразование.
    """
    if orientation_units is None:
        orientation_units = MOTION_SETUP.units
    position = np.array(position_orientation[POSITION_SLICE])
    r = Rotation.from_euler(
        "xyz",
        position_orientation[ORIENTATION_SLICE],
        degrees=orientation_units == "deg",
    )
    translation, rotation = get_transformation_parameters(coordinate_system)
    if to_local:
        position_transformed = rotation.inv().apply(position - translation)
        orientation_transformed = (rotation.inv() * r).as_euler(
            "xyz", degrees=orientation_units == "deg"
        )
    else:
        position_transformed = rotation.apply(position) + translation
        orientation_transformed = (rotation * r).as_euler(
            "xyz", degrees=orientation_units == "deg"
        )
    return cast(
        PositionOrientation,
        position_transformed.tolist() + orientation_transformed.tolist(),
    )
