from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING, Callable, Optional, cast

import API.source.features.mathematics.unit_convert as unit_c
from API.source.ap_interface.motion.coordinate_system import (
    CoordinateSystem,
)
from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.features.tools import (
    dataclass_to_tuple,
    literal_to_int,
    set_position_orientation_units,
)
from API.source.models.classes.data_classes.command_templates import (
    MOTION_SETUP,
    JointJogCommandTemplate,
    MoveCommandTemplate,
)
from API.source.models.classes.enum_classes.controller_commands import (
    AddWayPointCommand as Awp,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Getters as Get,
)
from API.source.models.classes.enum_classes.controller_commands import (
    JointJogModes as Jm,
)
from API.source.models.classes.enum_classes.state_classes import (
    OutComingMotionMode as Omm,
)
from API.source.models.constants import (
    BLEND_LIMITS,
    CTRLR_GET_LAST_POSITION_UNPACK_FORMAT,
    CTRLR_JOINT_JOG_CMD_PACK_FORMAT,
    JOINT_ACCEL_LIMITS_DEG_SEC,
    JOINT_ACCEL_LIMITS_RAD_SEC,
    JOINT_COUNT,
    JOINT_SPEED_LIMITS_DEG_SEC,
    JOINT_SPEED_LIMITS_RAD_SEC,
    POSITION_ORIENTATION_LENGTH,
)
from API.source.models.type_aliases import (
    AngleUnits,
    JogDirection,
    JointIndex,
    PositionFormat,
    PositionOrientation,
)

if TYPE_CHECKING:
    from API.source.core.network.controller_socket import (
        Controller,
    )
    from API.source.core.network.rtd_receiver_socket import (
        RTDReceiver,
    )


_validate_index = validation.validate_index
_validate_length = validation.validate_length
_validate_literal = validation.validate_literal
_validate_value = validation.validate_value


class JointMotion:
    """
    Класс для работы с моторным типом движения.
    """

    _controller: Controller
    _rtd_receiver: RTDReceiver

    def __init__(
        self,
        controller: Controller,
        rtd_receiver: RTDReceiver,
        connection_state: ConnectionState,
        add_wp: Callable[[MoveCommandTemplate], bool],
        get_position: Callable[
            [AngleUnits, PositionFormat, Optional[CoordinateSystem]],
            PositionOrientation,
        ],
    ) -> None:
        self._controller = controller
        self._rtd_receiver = rtd_receiver
        self._connection_state = connection_state
        self._add_waypoint = add_wp
        self._get_position = get_position

    @handle_connection(available_in_read_only=False)
    def add_new_waypoint(
        self,
        angle_pose: Optional[PositionOrientation] = None,
        tcp_pose: Optional[PositionOrientation] = None,
        speed: Optional[float] = None,
        accel: Optional[float] = None,
        blend: Optional[float] = None,
        units: Optional[AngleUnits] = None,
    ) -> bool:
        """Добавляет точку движения по сочленениям (Joint) в буфер точек.

        Метод позволяет задать целевую конфигурацию робота одним из трёх способов:
        1. **Только углы сочленений** (`angle_pose`) — прямое указание позиции;
        2. **Только TCP-позиция** (`tcp_pose`) — система решит обратную задачу
           кинематики и вычислит углы;
        3. **Оба параметра** — используется `tcp_pose`, а `angle_pose` позволяет
            указать желаемое положение робота в этой точке.

        Результирующее движение выполняется по кратчайшей траектории в пространстве
        сочленений с учётом заданных скорости и ускорения.

        Args:
            angle_pose (PositionOrientation, optional): Углы сочленений
                `(J1, J2, J3, J4, J5, J6)` в указанных единицах (`units`).
            tcp_pose (PositionOrientation, optional): Позиция TCP
                `(X, Y, Z, Rx, Ry, Rz)`, где линейные компоненты — в метрах,
                угловые — в тех же единицах, что и `units`.
            speed (float, optional): Скорость сочленений:
                - в градусах: 0–180 °/с;
                - в радианах: 0–3.14 рад/с.
                По умолчанию — из глобальной конфигурации (`set_motion_config`).
            accel (float, optional): Ускорение сочленений:
                - в градусах: 0–1500 °/с²;
                - в радианах: 0–26.18 рад/с².
                По умолчанию — из глобальной конфигурации.
            blend (float, optional): Радиус сглаживания в метрах.
                При приближении к точке на расстояние ≤ `blend` робот плавно
                переходит к следующему сегменту. Значение `0` отключает сглаживание.
            units (AngleUnits, optional): Единицы измерения углов:
                - `'deg'` — градусы (по умолчанию);
                - `'rad'` — радианы.
        Returns:
            True: В случае успешного добавления точки.

        Examples:
            >>> # Задать движение по углам
            >>> angles = (0.0, -90.0, 0.0, -90.0, 0.0, 0.0)
            >>> robot.motion.joint.add_new_waypoint(angle_pose=angles)

            >>> # Задать движение через TCP (углы будут вычислены автоматически)
            >>> pose = (0.3, 0.0, 0.5, 0.0, 3.14, 0.0)
            >>> robot.motion.joint.add_new_waypoint(tcp_pose=pose, units='rad')

        Notes:
            - Если указан только `tcp_pose`, решается **обратная задача кинематики**.
              При неоднозначности (несколько решений) выбирается ближайшее
              к текущей конфигурации.
            - Все углы должны быть в **одних и тех же единицах**, что указано в `units`.
            - Добавление точки **не запускает движение** — требуется явный запуск
              через `robot.motion.mode.set('move')`.
        """
        if speed is None:
            speed = MOTION_SETUP.joint_speed
        if accel is None:
            accel = MOTION_SETUP.joint_acceleration
        if blend is None:
            blend = MOTION_SETUP.blend
        if units is None:
            units = MOTION_SETUP.units
        _validate_literal("angle", units)
        _validate_value(blend, BLEND_LIMITS)
        _validate_value(
            speed,
            (
                JOINT_SPEED_LIMITS_DEG_SEC
                if units == "deg"
                else JOINT_SPEED_LIMITS_RAD_SEC
            ),
        )
        _validate_value(
            accel,
            (
                JOINT_ACCEL_LIMITS_DEG_SEC
                if units == "deg"
                else JOINT_ACCEL_LIMITS_RAD_SEC
            ),
        )
        if units == "deg":
            speed = cast(float, unit_c.degrees_to_radians(speed))
            accel = cast(float, unit_c.degrees_to_radians(accel))
            if angle_pose is not None:
                _validate_length(angle_pose, POSITION_ORIENTATION_LENGTH)
                angle_pose = cast(
                    PositionOrientation, unit_c.degrees_to_radians(*angle_pose)
                )
        if angle_pose is not None and tcp_pose is not None:
            _validate_length(tcp_pose, POSITION_ORIENTATION_LENGTH)
            tcp_pose = set_position_orientation_units(tcp_pose, units)
            command = MoveCommandTemplate(
                t=Awp.move_wp_type_tcp_pose,
                des_x=tcp_pose,
                des_q=angle_pose,
                v_max_j=speed,
                a_max_j=accel,
                r_blend=blend,
            )
        elif tcp_pose is not None:
            _validate_length(tcp_pose, POSITION_ORIENTATION_LENGTH)
            tcp_pose = set_position_orientation_units(tcp_pose, units)
            command = MoveCommandTemplate(
                t=Awp.move_wp_type_tcp_pose,
                des_x=tcp_pose,
                des_q=self._rtd_receiver.get_data().act_q,
                v_max_j=speed,
                a_max_j=accel,
                r_blend=blend,
            )
        elif angle_pose is not None:
            command = MoveCommandTemplate(
                t=Awp.move_wp_type_joint,
                des_q=angle_pose,
                v_max_j=speed,
                a_max_j=accel,
                r_blend=blend,
            )
        else:
            return False
        return self._add_waypoint(command)

    @handle_connection(available_in_read_only=True)
    def get_actual_position(
        self, units: Optional[AngleUnits] = None
    ) -> PositionOrientation:
        """Возвращает текущие углы сочленений робота (Joint-space).

        Метод предоставляет мгновенные значения углов поворота всех шести
        моторов (от основания до фланца) в указанной системе единиц.
        Результат отражает **фактическое физическое положение** робота
        на момент вызова.

        Метод доступен в режиме «read only».

        Args:
            units (AngleUnits, optional): Единицы измерения углов:
                - `'deg'` — градусы (по умолчанию);
                - `'rad'` — радианы.

        Returns:
            PositionOrientation: Кортеж из 6 чисел:
                `(J1, J2, J3, J4, J5, J6)`, где `Ji` — угол поворота i-го
                сочленения от основания к фланцу, в указанных единицах.

        Examples:
            >>> # Получить углы в градусах
            >>> joints = robot.motion.joint.get_actual_position()
            >>> print(f"Текущие углы: {joints}")

            >>> # Получить углы в радианах
            >>> joints_rad = robot.motion.joint.get_actual_position(units='rad')
        """

        if units is None:
            units = MOTION_SETUP.units
        _validate_literal("angle", units)
        return self._get_position(units, "joints", None)

    @handle_connection(available_in_read_only=False)
    def get_last_saved_position(
        self, units: Optional[AngleUnits] = None
    ) -> PositionOrientation | None:
        """Возвращает последнюю сохранённую позицию робота в формате углов сочленений.

        Args:
            units (AngleUnits, optional): Единицы измерения углов:
                - `'deg'` — градусы (по умолчанию);
                - `'rad'` — радианы.

        Returns:
            PositionOrientation | None:
                - Объект с 6 углами `(J1, J2, J3, J4, J5, J6)` в указанных единицах

        Examples:
            >>> # Получить последнюю сохранённую позицию (или текущую, если в 'run')
            >>> pos = robot.motion.joint.get_last_saved_position()
            >>> if pos is not None:
            ...     print(f"Сохраненные углы: {pos}")

        Notes:
            - Эта функция **не эквивалентна** `get_actual_position()` — только в
              состоянии 'run' они совпадают.
            - Используйте этот метод, например, для восстановления позиции
              после перезапуска или для сравнения с текущим положением
              в безопасном состоянии.
        """
        if units is None:
            units = MOTION_SETUP.units
        _validate_literal("angle", units)
        self._controller.send(Get.ctrlr_coms_get_last_pos)
        response = self._controller.receive(
            Get.ctrlr_coms_get_last_pos,
            CTRLR_GET_LAST_POSITION_UNPACK_FORMAT,
        )
        if units == "deg":
            return cast(
                PositionOrientation,
                unit_c.radians_to_degrees(*response),
            )
        return cast(PositionOrientation, response)

    @handle_connection(available_in_read_only=False)
    def jog_once(
        self,
        joint_index: JointIndex,
        jog_direction: JogDirection,
    ) -> bool:
        """Выполняет кратковременный шаг джоггинга по указанному сочленению.

        Метод предназначен для ручного управления отдельными моторами робота
        в реальном времени. Это **один цикл управления** — для непрерывного вращения
        метод должен вызываться **циклически с частотой не менее 100 Гц** (каждые ≤10 мс).

        Args:
            joint_index (JointIndex): Индекс сочленения (мотора):
                - `0` — первое звено от основания (J1),
                - `1` — второе звено (J2),
                - ...
                - `5` — последнее звено (J6).
            jog_direction (JogDirection): Направление вращения:
                - `'+'` — по часовой стрелке (в системе отсчёта сочленения);
                - `'-'` — против часовой стрелки.

        Returns:
            True: В случае успешной отправки команды.

        Examples:
            >>> # Непрерывное вращение J2 по часовой стрелке в течение 1.5 сек
            >>> import time
            >>> start = time.time()
            >>> while time.time() - start < 1.5:
            ...     robot.motion.joint.jog_once(joint_index=1, jog_direction='+')
            ...     time.sleep(0.005)  # 200 Гц — надёжная частота

        Notes:
            - Направление `'+'`/`'-'` определяется направлением вращения часовой стрелки.
            - Скорость и ускорение джоггинга можно настроить с помощью scale_setup.
        """

        _validate_index(joint_index, range(JOINT_COUNT))
        _validate_literal("math", jog_direction)
        jog_template = JointJogCommandTemplate()
        jog_template.joints_rotation_directions[joint_index] = literal_to_int(
            jog_direction
        )
        jog_template.mode = Jm.ctrlr_coms_joint_jog_mode_on
        return self._controller.send(
            Omm.joint_jog,
            pack(
                CTRLR_JOINT_JOG_CMD_PACK_FORMAT,
                *dataclass_to_tuple(jog_template),
            ),
        )
