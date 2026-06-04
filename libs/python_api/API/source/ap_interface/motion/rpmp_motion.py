from __future__ import annotations

import logging
from struct import pack
from typing import TYPE_CHECKING, Optional, cast

import API.source.features.mathematics.unit_convert as unit_c
from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.features.tools import (
    dataclass_to_tuple_recursive,
    set_position_orientation_units,
    sleep,
)
from API.source.models.classes.data_classes.command_templates import (
    RPMP_MOTION_SETUP,
    RPMPCartesianWayPointTemplate,
    RPMPMoveCommandTemplate,
    RPMPMoveCWayPointTemplate,
    RPMPMoveLWayPointTemplate,
    RPMPMovePWayPointTemplate,
)
from API.source.models.classes.enum_classes.controller_commands import (
    RPMPAddWayPointCommand,
    RPMPMoveWayPointType,
)
from API.source.models.constants import (
    ACCEL_LIMITS,
    BLEND_LIMITS,
    CHECK_FREQUENCY_SEC,
    CTRLR_RPMP_ADD_WP_MOVEC_CMD_PACK_FORMAT,
    CTRLR_RPMP_ADD_WP_MOVEL_CMD_PACK_FORMAT,
    CTRLR_RPMP_ADD_WP_MOVEP_CMD_PACK_FORMAT,
    ORIENTATION_SLICE,
    POSITION_ORIENTATION_LENGTH,
    POSITION_SLICE,
    RPMP_ROTATION_ACCEL_LIMITS,
    RPMP_ROTATION_SPEED_LIMITS,
    SPEED_LIMITS,
    WP_ADD_TIMEOUT,
    WP_COUNTER_MAX_VALUE,
)
from API.source.models.type_aliases import (
    AngleUnits,
    PositionOrientation,
)

if TYPE_CHECKING:
    from API.source.core.network.controller_socket import (
        Controller,
    )
    from API.source.core.network.rtd_receiver_socket import (
        RTDReceiver,
    )


_validate_length = validation.validate_length
_validate_literal = validation.validate_literal
_validate_value = validation.validate_value


class RPMPMotion(object):
    """
    Класс для работы типом движения 'Advanced'.
    """

    _controller: Controller
    _rtd_receiver: RTDReceiver

    def __init__(
        self,
        controller: Controller,
        rtd_receiver: RTDReceiver,
        connection_state: ConnectionState,
        logger: logging.Logger,
    ) -> None:
        self._controller = controller
        self._rtd_receiver = rtd_receiver
        self._connection_state = connection_state
        self._waypoint_counter: Optional[int] = None
        self._logger = logger

    @handle_connection(available_in_read_only=False)
    def add_movel_waypoint(
        self,
        tcp_pose: PositionOrientation,
        translation_speed: Optional[float] = None,
        translation_accel: Optional[float] = None,
        rotation_speed: Optional[float] = None,
        rotation_accel: Optional[float] = None,
        blend: Optional[float] = None,
        orientation_units: Optional[AngleUnits] = None,
    ) -> bool:
        """Добавляет точку линейного движения (MoveL) в буфер точек Advanced-движения.

        Добавить целевую точку типа 'linear' для типа движения 'Advanced' в
        глобальной системе координат (система координат основания робота).
        Конвертация позиции и ориентации из локальной СК (пользовательской) в
        глобальную производится при передаче аргументов с помощью функции
        'convert_position_orientation', переданные при этом единицы измерения
        должны совпадать с единицами измерения данного метода.

        Добавление точки типа 'linear' задает движение от предыдущей добавленной
        точки к текущей по линейной траектории с соответствующими ограничениями
        и параметрами.

        Args:
            tcp_pose: Позиция ЦТИ в формате (X, Y, Z, Rx, Ry, Rz),
                где (X, Y, Z) — м, (Rx, Ry,Rz) — 'orientation_units'.
            translation_speed: Желаемая скорость поступательного перемещения
                точки по траектории (0 - 3 м/с).
            translation_accel: Желаемое ускорение поступательного перемещения
                точки по траектории (0 - 15 м/c^2).
            rotation_speed: Желаемая скорость вращательного перемещения
                точки ('orientation_units'/c) (0 - 360 deg/с / 0 - 6.28 rad/с).
            rotation_accel: Желаемое ускорение вращательного перемещения
                точки ('orientation_units'/c^2) (0 - 720 deg/с^2 / 0 - 12.56 rad/с^2).
            blend: Радиус сглаживания движения (м).
                (Радиус вокруг точки, при пересечении которого траекторией
                движения робота начинается/заканчивается сглаживание).
            orientation_units: Единицы измерения. По-умолчанию градусы.
                'deg' — градусы.
                'rad' — радианы.

        Returns:
            True: В случае успешной отправки команды.

        Examples:
            >>> # Добавить MoveL-точку
            >>> pose = (0.4, 0.0, 0.6, 0.0, 3.14, 0.0)
            >>> robot.motion.advanced.add_movel_waypoint(
            ...     tcp_pose=pose,
            ...     translation_speed=0.5,
            ...     rotation_speed=90.0,  # град/с
            ...     blend=0.02
            ... )

        Notes:
            - Все точки добавляются в **очередь** и выполняются после вызова
              `robot.motion.mode.set('move_adv')`.
            - Убедитесь, что единицы измерения углов в `tcp_pose` совпадают с
              `orientation_units`.
            - MoveL гарантирует **прямолинейную траекторию TCP**, но не гарантирует
              постоянную скорость движения.
        """
        if orientation_units is None:
            orientation_units = RPMP_MOTION_SETUP.units
        if translation_speed is None:
            translation_speed = RPMP_MOTION_SETUP.linear_speed
        if rotation_speed is None:
            rotation_speed = RPMP_MOTION_SETUP.rotation_speed
            if orientation_units == "rad":
                rotation_speed = cast(
                    float, unit_c.degrees_to_radians(rotation_speed)
                )
        if translation_accel is None:
            translation_accel = RPMP_MOTION_SETUP.linear_acceleration
        if rotation_accel is None:
            rotation_accel = RPMP_MOTION_SETUP.rotation_acceleration
            if orientation_units == "rad":
                rotation_accel = cast(
                    float, unit_c.degrees_to_radians(rotation_accel)
                )
        if blend is None:
            blend = RPMP_MOTION_SETUP.blend

        _validate_literal("angle", orientation_units)
        _validate_value(blend, BLEND_LIMITS)
        _validate_value(translation_speed, SPEED_LIMITS)
        _validate_value(translation_accel, ACCEL_LIMITS)

        if orientation_units == "deg":
            rotation_speed = cast(
                float, unit_c.degrees_to_radians(rotation_speed)
            )
            rotation_accel = cast(
                float, unit_c.degrees_to_radians(rotation_accel)
            )
        _validate_value(rotation_speed, RPMP_ROTATION_SPEED_LIMITS)
        _validate_value(rotation_accel, RPMP_ROTATION_ACCEL_LIMITS)

        _validate_length(tcp_pose, POSITION_ORIENTATION_LENGTH)
        tcp_pose = set_position_orientation_units(tcp_pose, orientation_units)

        cart_wp = RPMPCartesianWayPointTemplate(
            tr_position=tuple(tcp_pose[POSITION_SLICE]),
            rot_position=tuple(tcp_pose[ORIENTATION_SLICE]),
            tr_velocity=translation_speed,
            rot_velocity=rotation_speed,
            tr_acceleration=translation_accel,
            rot_acceleration=rotation_accel,
        )
        command = RPMPMoveCommandTemplate(
            type=RPMPMoveWayPointType.rpmp_move_wp_type_movel,
            blend_radius=blend,
            wp=RPMPMoveLWayPointTemplate(cart_wp=cart_wp),
        )
        return self._add_waypoint(
            CTRLR_RPMP_ADD_WP_MOVEL_CMD_PACK_FORMAT, command
        )

    @handle_connection(available_in_read_only=False)
    def add_movep_waypoint(
        self,
        tcp_pose: PositionOrientation,
        translation_speed: Optional[float] = None,
        rotation_speed: Optional[float] = None,
        translation_accel: Optional[float] = None,
        rotation_accel: Optional[float] = None,
        blend: Optional[float] = None,
        orientation_units: Optional[AngleUnits] = None,
    ) -> bool:
        """Добавляет точку процессного движения (MoveP) в буфер точек Advanced-движения.

        Добавить целевую точку типа 'process' для типа движения 'Advanced' в
        глобальной системе координат (система координат основания робота).
        Конвертация позиции и ориентации из локальной СК (пользовательской) в
        глобальную производится при передаче аргументов с помощью функции
        'convert_position_orientation', переданные при этом единицы измерения
        должны совпадать с единицами измерения данного метода.

        Args:
            tcp_pose: Позиция ЦТИ в формате (X, Y, Z, Rx, Ry, Rz),
                где (X, Y, Z) — м, (Rx, Ry,Rz) — 'orientation_units'.
            translation_speed: Желаемая скорость поступательного перемещения
                точки по траектории (0 - 3 м/с).
            translation_accel: Желаемое ускорение поступательного перемещения
                точки по траектории (0 - 15 м/c^2).
            rotation_speed: Желаемая скорость вращательного перемещения
                точки ('orientation_units'/c) (0 - 360 deg/с / 0 - 6.28 rad/с).
            rotation_accel: Желаемое ускорение вращательного перемещения
                точки ('orientation_units'/c^2)(0 - 720 deg/с^2 / 0 - 12.56 rad/с^2).
            blend: Радиус сглаживания движения (м).
                (Радиус вокруг точки, при пересечении которого траекторией
                движения робота начинается/заканчивается сглаживание).
            orientation_units: Единицы измерения. По-умолчанию градусы.
                'deg' — градусы.
                'rad' — радианы.

        Returns:
            True: В случае успешной отправки команды.

        Examples:
            >>> # Добавить MoveL-точку
            >>> pose = (0.4, 0.0, 0.6, 0.0, 3.14, 0.0)
            >>> robot.motion.advanced.add_movep_waypoint(
            ...     tcp_pose=pose,
            ...     translation_speed=0.5,
            ...     rotation_speed=90.0,  # град/с
            ...     blend=0.02
            ... )

        Notes:
            - Все точки добавляются в **очередь** и выполняются после вызова
              `robot.motion.mode.set('move_adv')`.
            - Убедитесь, что единицы измерения углов в `tcp_pose` совпадают с
              `orientation_units`.
            - MoveP гарантирует прямолинейную траекторию TCP и постоянную скорость
                движения.
            - Задаваемые скорости и ускорения (за исключением скорости
                поступательного движения) являются желаемыми и могут
                автоматически уменьшаться во время реализации траектории
                (но не увеличиваться).
        """
        if orientation_units is None:
            orientation_units = RPMP_MOTION_SETUP.units
        if translation_speed is None:
            translation_speed = RPMP_MOTION_SETUP.linear_speed
        if rotation_speed is None:
            rotation_speed = RPMP_MOTION_SETUP.rotation_speed
            if orientation_units == "rad":
                rotation_speed = cast(
                    float, unit_c.degrees_to_radians(rotation_speed)
                )
        if translation_accel is None:
            translation_accel = RPMP_MOTION_SETUP.linear_acceleration
        if rotation_accel is None:
            rotation_accel = RPMP_MOTION_SETUP.rotation_acceleration
            if orientation_units == "rad":
                rotation_accel = cast(
                    float, unit_c.degrees_to_radians(rotation_accel)
                )
        if blend is None:
            blend = RPMP_MOTION_SETUP.blend

        _validate_literal("angle", orientation_units)
        _validate_value(blend, BLEND_LIMITS)
        _validate_value(translation_speed, SPEED_LIMITS)
        _validate_value(translation_accel, ACCEL_LIMITS)

        if orientation_units == "deg":
            rotation_speed = cast(
                float, unit_c.degrees_to_radians(rotation_speed)
            )
            rotation_accel = cast(
                float, unit_c.degrees_to_radians(rotation_accel)
            )
        _validate_value(rotation_speed, RPMP_ROTATION_SPEED_LIMITS)
        _validate_value(rotation_accel, RPMP_ROTATION_ACCEL_LIMITS)

        _validate_length(tcp_pose, POSITION_ORIENTATION_LENGTH)
        tcp_pose = set_position_orientation_units(tcp_pose, orientation_units)

        cart_wp = RPMPCartesianWayPointTemplate(
            tr_position=tuple(tcp_pose[POSITION_SLICE]),
            rot_position=tuple(tcp_pose[ORIENTATION_SLICE]),
            tr_velocity=translation_speed,
            rot_velocity=rotation_speed,
            tr_acceleration=translation_accel,
            rot_acceleration=rotation_accel,
        )

        command = RPMPMoveCommandTemplate(
            type=RPMPMoveWayPointType.rpmp_move_wp_type_movep,
            blend_radius=blend,
            wp=RPMPMovePWayPointTemplate(cart_wp=cart_wp),
        )
        return self._add_waypoint(
            CTRLR_RPMP_ADD_WP_MOVEP_CMD_PACK_FORMAT, command
        )

    @handle_connection(available_in_read_only=False)
    def add_movec_waypoint(
        self,
        tcp_pose_1: PositionOrientation,
        tcp_pose_2: PositionOrientation,
        translation_speed: Optional[float] = None,
        rotation_speed: Optional[float] = None,
        translation_accel: Optional[float] = None,
        rotation_accel: Optional[float] = None,
        blend: Optional[float] = None,
        orientation_units: Optional[AngleUnits] = None,
    ) -> bool:
        """Добавляет сегмент круговой траектории (MoveC) в буфер Advanced-движения.

        MoveC (Circular Move) определяет **дугу**, проходящую через три точки:
        1. Текущая позиция робота (перед вызовом метода);
        2. `tcp_pose_1` — промежуточная точка на дуге;
        3. `tcp_pose_2` — конечная точка дуги.

        Таким образом, один вызов `add_movec_waypoint` добавляет **одну дугу**
        (две новые точки), а не одну точку. Траектория строится в декартовом
        пространстве с сохранением постоянной ориентации или её плавным изменением.

        Конвертация позиции и ориентации из локальной СК (пользовательской) в
        глобальную производится при передаче аргументов с помощью функции
        'convert_position_orientation', переданные при этом единицы измерения
        должны совпадать с единицами измерения данного метода.

        Args:
            tcp_pose_1: Первая позиция ЦТИ в формате (X, Y, Z, Rx, Ry, Rz),
                где (X, Y, Z) — м, (Rx, Ry,Rz) — 'orientation_units'.
            tcp_pose_2: Вторая позиция ЦТИ в формате (X, Y, Z, Rx, Ry, Rz),
                где (X, Y, Z) — м, (Rx, Ry,Rz) — 'orientation_units'.
            translation_speed: Желаемая скорость поступательного перемещения
                точки по траектории (0 - 3 м/с).
            translation_accel: Желаемое ускорение поступательного перемещения
                точки по траектории (0 - 15 м/c^2).
            rotation_speed: Желаемая скорость вращательного перемещения
                точки ('orientation_units'/c) (0 - 360 deg/с / 0 - 6.28 rad/с).
            rotation_accel: Желаемое ускорение вращательного перемещения
                точки ('orientation_units'/c^2)(0 - 720 deg/с^2 / 0 - 12.56 rad/с^2).
            blend: Радиус сглаживания движения (м).
                (Радиус вокруг точки, при пересечении которого траекторией
                движения робота начинается/заканчивается сглаживание).
            orientation_units: Единицы измерения. По-умолчанию градусы.
                'deg' — градусы.
                'rad' — радианы.

        Returns:
            True: В случае успешной отправки команды.

        Examples:
            >>> # Выполнить полукруг в плоскости XY
            >>> start = robot.motion.linear.get_actual_position()
            >>> robot.motion.advanced.add_movec_waypoint(start)
            >>> mid = (0.3, 0.1, 0.5, 0, 3.14, 0)    # промежуточная
            >>> end = (0.3, 0.2, 0.5, 0, 3.14, 0)    # конечная
            >>> robot.motion.advanced.add_movec_waypoint(mid, end, translation_speed=0.3)

        Notes:
            - Если три точки (текущая, `tcp_pose_1`, `tcp_pose_2`) коллинеарными
              — дуга вырождается в линию, происходит линейное движение.
            - Если две из трех точек совпадают — дуга вырождается в линию,
                происходит линейное движение.
            - После добавления сегмента движение запускается через
              `robot.motion.mode.set('move_adv')`.
            - Убедитесь, что единицы измерения углов в обеих позициях совпадают
              с `orientation_units`.
            - Задаваемые скорости и ускорения являются желаемыми и могут
                автоматически уменьшаться во время реализации траектории
                (но не увеличиваться)
        """
        if orientation_units is None:
            orientation_units = RPMP_MOTION_SETUP.units
        if translation_speed is None:
            translation_speed = RPMP_MOTION_SETUP.linear_speed
        if rotation_speed is None:
            rotation_speed = RPMP_MOTION_SETUP.rotation_speed
            if orientation_units == "rad":
                rotation_speed = cast(
                    float, unit_c.degrees_to_radians(rotation_speed)
                )
        if translation_accel is None:
            translation_accel = RPMP_MOTION_SETUP.linear_acceleration
        if rotation_accel is None:
            rotation_accel = RPMP_MOTION_SETUP.rotation_acceleration
            if orientation_units == "rad":
                rotation_accel = cast(
                    float, unit_c.degrees_to_radians(rotation_accel)
                )
        if blend is None:
            blend = RPMP_MOTION_SETUP.blend

        _validate_literal("angle", orientation_units)
        _validate_value(blend, BLEND_LIMITS)
        _validate_value(translation_speed, SPEED_LIMITS)
        _validate_value(translation_accel, ACCEL_LIMITS)

        if orientation_units == "deg":
            rotation_speed = cast(
                float, unit_c.degrees_to_radians(rotation_speed)
            )
            rotation_accel = cast(
                float, unit_c.degrees_to_radians(rotation_accel)
            )
        _validate_value(rotation_speed, RPMP_ROTATION_SPEED_LIMITS)
        _validate_value(rotation_accel, RPMP_ROTATION_ACCEL_LIMITS)

        _validate_length(tcp_pose_1, POSITION_ORIENTATION_LENGTH)
        _validate_length(tcp_pose_2, POSITION_ORIENTATION_LENGTH)
        tcp_pose_1 = set_position_orientation_units(
            tcp_pose_1, orientation_units
        )
        tcp_pose_2 = set_position_orientation_units(
            tcp_pose_2, orientation_units
        )

        cart_wp_1 = RPMPCartesianWayPointTemplate(
            tr_position=tuple(tcp_pose_1[POSITION_SLICE]),
            rot_position=tuple(tcp_pose_1[ORIENTATION_SLICE]),
            tr_velocity=translation_speed,
            rot_velocity=rotation_speed,
            tr_acceleration=translation_accel,
            rot_acceleration=rotation_accel,
        )
        cart_wp_2 = RPMPCartesianWayPointTemplate(
            tr_position=tuple(tcp_pose_2[POSITION_SLICE]),
            rot_position=tuple(tcp_pose_2[ORIENTATION_SLICE]),
            tr_velocity=translation_speed,
            rot_velocity=rotation_speed,
            tr_acceleration=translation_accel,
            rot_acceleration=rotation_accel,
        )

        command = RPMPMoveCommandTemplate(
            type=RPMPMoveWayPointType.rpmp_move_wp_type_movec,
            blend_radius=blend,
            wp=RPMPMoveCWayPointTemplate(
                cart_wp_1=cart_wp_1, cart_wp_2=cart_wp_2
            ),
        )
        return self._add_waypoint(
            CTRLR_RPMP_ADD_WP_MOVEC_CMD_PACK_FORMAT,
            command,
            num_of_points=2,
        )

    def _add_waypoint(
        self,
        pack_format: str,
        command_template: RPMPMoveCommandTemplate,
        num_of_points: int = 1,
    ) -> bool:
        """
        Вспомогательная команда отправки сообщения добавления новой 'RPMP' точки.

        Returns:
            True: В случае успешного добавления точки.
        """
        self._waypoint_counter = int(self._rtd_receiver.get_data().wp_cntr)
        self._waypoint_counter = (
            self._waypoint_counter + num_of_points
        ) & WP_COUNTER_MAX_VALUE

        self._controller.send(
            RPMPAddWayPointCommand.ctrlr_coms_rpmp_move_add_wp,
            pack(
                pack_format,
                *dataclass_to_tuple_recursive(command_template),
            ),
        )

        for _ in sleep(
            await_sec=WP_ADD_TIMEOUT,
            frequency=CHECK_FREQUENCY_SEC,
        ):
            if not self._connection_state.is_connected():
                self._logger.error(
                    "Failed to add waypoint - connection was lost"
                )
                return False
            if self._rtd_receiver.get_data().wp_cntr == self._waypoint_counter:
                return True
        self._waypoint_counter = None
        return False
