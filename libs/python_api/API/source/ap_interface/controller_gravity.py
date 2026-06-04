from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING, Tuple, cast

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
    CTRLR_SET_GET_GRAVITY_PACK_UNPACK_FORMAT,
    GRAVITY_VECTOR_COUNT,
)

if TYPE_CHECKING:
    from API.source.core.network.controller_socket import (
        Controller,
    )

from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)

_validate_length = validation.validate_length


class ControllerGravity(object):
    """
    Класс для управления ориентацией контроллера через задание вектора
    гравитации. Изменяет физическое положение/ориентацию контроллера путем
    имитации заданного вектора гравитационного воздействия.
    """

    _controller: Controller
    _connection_state: ConnectionState

    def __init__(
        self,
        controller: Controller,
        connection_state: ConnectionState,
    ) -> None:
        self._controller = controller
        self._connection_state = connection_state

    @handle_connection(available_in_read_only=False)
    def set(self, gravity_vector: Tuple[float, float, float]) -> bool:
        """Устанавливает вектор гравитации для коррекции ориентации контроллера.

        Метод задаёт направление имитируемого гравитационного воздействия,
        используемого системой управления для адаптации к физической ориентации
        робота (например, при установке на наклонной поверхности или вверх ногами).

        Вектор **должен быть предварительно нормирован** пользователем:
        его длина должна соответствовать ускорению свободного падения ||v|| ≈ 1.0.
        API не выполняет автоматическую нормировку.

        Args:
            gravity_vector: Вектор гравитации,в формате (X, Y, Z),
                где (X, Y, Z) — ориентация вектора, нормированная на g≈9.81 м/с².
        Returns:
            True: В случае успешной отправки команды, иначе False

        Examples:
            >>> # Стандартная ориентация (в единицах g)
            >>> robot.controller_gravity.set((0.0, 0.0, -1.0))

            >>> # Робот установлен "вверх ногами"
            >>> robot.controller_gravity.set((0.0, 0.0, 1.0))

            >>> # Наклон на 45 градусов вперёд
            >>> import math
            >>> angle = math.radians(45)
            >>> robot.controller_gravity.set((0.0, -math.sin(angle), -math.cos(angle)))

        Notes:
            - Убедитесь, что вектор **нормирован** перед передачей — иначе
              поведение робота может быть непредсказуемым.
            - Неправильная ориентация гравитации может привести к ошибкам
              позиционирования или срабатыванию защиты по усилию.
        """

        _validate_length(gravity_vector, GRAVITY_VECTOR_COUNT)
        inverted_vector = (
            -gravity_vector[0],
            -gravity_vector[1],
            -gravity_vector[2],
        )
        return self._controller.send(
            Set.ctrlr_coms_set_gravity,
            pack(
                CTRLR_SET_GET_GRAVITY_PACK_UNPACK_FORMAT,
                *inverted_vector,
            ),
        )

    @handle_connection(available_in_read_only=False)
    def get(self) -> Tuple[float, float, float] | None:
        """Возвращает текущий активный вектор гравитации, применяемый к контроллеру.

        Вектор отражает имитацию гравитационного воздействия, используемую
        для коррекции ориентации контроллера. Значения нормированы относительно
        стандартного ускорения свободного падения: g = -9.81 м/с².
        Например, значение `(0.0, 0.0, -1.0)` соответствует стандартной
        ориентации с гравитацией, направленной вниз по оси Z.

        Returns:
            Tuple[float, float, float] | None: Трёхмерный вектор гравитации
                в формате (X, Y, Z), выраженный в **единицах g** (безразмерный
                вектор, где 1.0 ≈ 9.81 м/с²).
                Пример: (0.0, 0.0, -1.0) — стандартная ориентация.
                Возвращает `None`, если получить заданный вектор гравитации не удалось.

        Examples:
            >>> gravity = robot.controller_gravity.get()
            >>> if gravity is not None:
            ...     x, y, z = gravity
            ...     print(f"Вектор гравитации: X={x:.2f}, Y={y:.2f}, Z={z:.2f}")
            ... else:
            ...     print("Не удалось получить вектор гравитации")

        Notes:
            - Возвращаемый вектор **безразмерный**: он показывает направление
              и относительную величину гравитации в единицах стандартного g.
            - Ось Z обычно направлена вниз при стандартной установке робота.
        """

        self._controller.send(Get.ctrlr_coms_get_gravity)
        response = self._controller.receive(
            Get.ctrlr_coms_get_gravity,
            CTRLR_SET_GET_GRAVITY_PACK_UNPACK_FORMAT,
        )
        inverted_response = (
            -response[0],
            -response[1],
            -response[2],
        )
        return cast(tuple[float, float, float], inverted_response)
