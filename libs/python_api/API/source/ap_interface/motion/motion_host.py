from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING, List, Optional, cast

import API.source.features.mathematics.unit_convert as unit_c
from API.source.ap_interface.motion.joint_motion import (
    JointMotion,
)
from API.source.ap_interface.motion.kinematics_solution import (
    Kinematics,
)
from API.source.ap_interface.motion.linear_motion import (
    LinearMotion,
)
from API.source.ap_interface.motion.motion_mode import (
    MotionMode,
)
from API.source.ap_interface.motion.move_scaling import (
    MoveScaling,
)
from API.source.ap_interface.motion.rpmp_motion import (
    RPMPMotion,
)
from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.base_api_error import ApiError
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.core.exceptions.data_validation_error.generic_error import (
    AddWaypointError,
)
from API.source.features.mathematics.coordinate_system import (
    convert_position_orientation,
)
from API.source.features.tools import (
    dataclass_to_tuple,
    sleep,
)
from API.source.models.classes.data_classes.command_templates import (
    MOTION_SETUP,
    MoveCommandTemplate,
)
from API.source.models.classes.enum_classes.controller_commands import (
    AddWayPointCommand as Awp,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Getters as Get,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Setters as Set,
)
from API.source.models.classes.enum_classes.state_classes import (
    OutComingMotionMode as Omm,
)
from API.source.models.classes.enum_classes.various_types import (
    AddWayPointErrorCode as AwpErr,
)
from API.source.models.constants import (
    ADD_WAY_POINT_ERROR_DESCRIPTION,
    CHECK_FREQUENCY_SEC,
    CTRLR_ADD_WP_CMD_PACK_FORMAT,
    CTRLR_COMS_ADD_WP_RES_FORMAT,
    CTRLR_FKINE_CMD_PACK_FORMAT,
    CTRLR_FKINE_CMD_UNPACK_FORMAT,
    CTRLR_GET_LAST_POSITION_UNPACK_FORMAT,
    CTRLR_GET_SET_HOME_POSE_PACK_UNPACK_FORMAT,
    FKINE_IKINE_RESPONSE_JOINT_POSITION_SLICE,
    MOVE_TO_HOME_POSE_ACCEL,
    MOVE_TO_HOME_POSE_SPEED,
    OMM_ENABLE_DISABLE_PACK_FORMAT,
    ORIENTATION_SLICE,
    POSITION_ORIENTATION_LENGTH,
    POSITION_SLICE,
    WP_ADD_TIMEOUT,
    WP_COUNT_LIMITS,
    WP_COUNTER_MAX_VALUE,
)
from API.source.models.type_aliases import (
    AngleUnits,
    PositionFormat,
    PositionOrientation,
)

if TYPE_CHECKING:
    from logging import Logger

    from API.source.ap_interface.motion.coordinate_system import (
        CoordinateSystem,
    )
    from API.source.core.network.controller_socket import (
        Controller,
    )
    from API.source.core.network.rtd_receiver_socket import (
        RTDReceiver,
    )


_validate_length = validation.validate_length
_validate_literal = validation.validate_literal
_validate_value = validation.validate_value


class Motion:
    """
    Класс для управления движением робота.
    """

    _controller: Controller
    _rtd_receiver: RTDReceiver
    _connection_state: ConnectionState

    joint: JointMotion
    """Подкласс для работы с движением типа 'joint'."""
    linear: LinearMotion
    """Подкласс для работы с движением типа 'linear'."""
    advanced: RPMPMotion
    """Подкласс для работы с движением типа 'advanced'."""
    scale_setup: MoveScaling
    """Подкласс для работы с настройками параметров движения."""
    mode: MotionMode
    """Подкласс для работы с режимами движения."""
    kinematics: Kinematics
    """Подкласс для получения решений задач кинематики."""

    def __init__(
        self,
        controller: Controller,
        rtd_receiver: RTDReceiver,
        connection_state: ConnectionState,
        logger: Logger,
    ) -> None:
        self._logger = logger
        self._controller = controller
        self._connection_state = connection_state
        self._rtd_receiver = rtd_receiver

        self.joint = JointMotion(
            controller=self._controller,
            rtd_receiver=rtd_receiver,
            connection_state=self._connection_state,
            add_wp=self._add_waypoint,
            get_position=self.get_actual_position,
        )
        self.linear = LinearMotion(
            controller=self._controller,
            rtd_receiver=rtd_receiver,
            connection_state=self._connection_state,
            add_wp=self._add_waypoint,
            get_position=self.get_actual_position,
        )
        self.advanced = RPMPMotion(
            controller=self._controller,
            rtd_receiver=rtd_receiver,
            connection_state=self._connection_state,
            logger=self._logger,
        )

        self.scale_setup = MoveScaling(
            controller=self._controller, connection_state=self._connection_state
        )
        self.mode = MotionMode(
            controller=self._controller,
            rtd_receiver=rtd_receiver,
            connection_state=self._connection_state,
            logger=self._logger,
        )
        self.kinematics = Kinematics(
            controller=self._controller,
            joint=self.joint,
            connection_state=self._connection_state,
        )
        self._waypoint_counter = None

    @handle_connection(available_in_read_only=False)
    def _add_waypoint(self, command_template: MoveCommandTemplate) -> bool:
        """
        Полный функционал добавления целевой точки (рад, м, с) в системе
        координат основания робота.

        Args:
            command_template: Предзаполненный объект дата-класса, содержащий
            все необходимые поля для команды.

        Returns:
            True: В случае успешного добавления точки.

        Raises:
            AddWaypointError: В случае таймаута ожидания добавления точки.
        """

        self._waypoint_counter = self._rtd_receiver.get_data().wp_cntr
        self._waypoint_counter = (
            self._waypoint_counter + 1
        ) & WP_COUNTER_MAX_VALUE
        self._controller.send(
            Awp.ctrlr_coms_move_add_wp,
            pack(
                CTRLR_ADD_WP_CMD_PACK_FORMAT,
                *dataclass_to_tuple(command_template),
            ),
        )
        response = self._controller.receive(
            Awp.ctrlr_coms_move_add_wp,
            CTRLR_COMS_ADD_WP_RES_FORMAT,
        )
        if response[0] != AwpErr.success:
            self._waypoint_counter = None
            raise AddWaypointError(ADD_WAY_POINT_ERROR_DESCRIPTION[response[0]])
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
        raise AddWaypointError

    @staticmethod
    def set_motion_config(
        units: Optional[AngleUnits] = None,
        joint_speed: Optional[float] = None,
        joint_acceleration: Optional[float] = None,
        linear_speed: Optional[float] = None,
        linear_acceleration: Optional[float] = None,
        blend: Optional[float] = None,
    ):
        """Устанавливает глобальные параметры движения для всех последующих команд.

        Настройки применяются к линейным и угловым (по сочленениям) движениям
        и влияют на скорость, ускорение и плавность траекторий.
        Параметры, переданные как `None` **не изменяются**.

        Метод доступен в режиме «read only», так как не запускает движение,
        а только конфигурирует его параметры.

        Args:
            units (AngleUnits, optional): Единицы измерения углов.
                - `'deg'` — градусы (диапазон: 0–180 °/с для скорости);
                - `'rad'` — радианы (диапазон: 0–3.14 рад/с).
                По умолчанию сохраняется текущая настройка.
            joint_speed (float, optional): Максимальная скорость сочленений.
                - В градусах: 0–180 °/с;
                - В радианах: 0–3.14 рад/с.
            joint_acceleration (float, optional): Максимальное ускорение сочленений.
                - В градусах: 0–1500 °/с²;
                - В радианах: 0–26.18 рад/с².
            linear_speed (float, optional): Максимальная линейная скорость
                конечного звена (TCP). Диапазон: 0–3 м/с.
            linear_acceleration (float, optional): Максимальное линейное ускорение
                TCP. Диапазон: 0–15 м/с².
            blend (float, optional): Радиус сглаживания траектории в метрах.
                При приближении к точке на расстояние ≤ `blend` робот начинает
                плавный переход к следующему сегменту траектории, не останавливаясь.
                Значение `0` отключает сглаживание (движение по точкам с остановкой).

        Examples:
            >>> # Установить умеренные параметры движения в градусах
            >>> robot.motion.set_motion_config(
            ...     units='deg',
            ...     joint_speed=30,
            ...     joint_acceleration=300,
            ...     linear_speed=0.5,
            ...     linear_acceleration=2.0,
            ...     blend=0.05  # 5 см сглаживания
            ... )

            >>> # Только изменить скорость, остальное оставить как есть
            >>> robot.motion.set_motion_config(linear_speed=1.0)

        Notes:
            - Изменения применяются **глобально** и влияют на все будущие движения,
              пока не будут изменены снова или в команде движения явно не указано другое.
        """

        if units:
            MOTION_SETUP.units = units
        if joint_speed:
            MOTION_SETUP.joint_speed = joint_speed
        if joint_acceleration:
            MOTION_SETUP.joint_acceleration = joint_acceleration
        if linear_speed:
            MOTION_SETUP.linear_speed = linear_speed
        if linear_acceleration:
            MOTION_SETUP.linear_acceleration = linear_acceleration
        if blend:
            MOTION_SETUP.blend = blend

    @handle_connection(available_in_read_only=True)
    def get_actual_position(
        self,
        orientation_units: Optional[AngleUnits] = None,
        position_format: PositionFormat = "tcp",
        coordinate_system: Optional[CoordinateSystem] = None,
    ) -> PositionOrientation:
        """Возвращает текущее положение робота в заданном формате и системе координат.

        Метод позволяет получить либо углы сочленений (joint-space),
        либо декартову позицию и ориентацию конечного инструмента (TCP)
        в линейном пространстве (task-space).

        Метод доступен в режиме «read only».

        Args:
            orientation_units (AngleUnits, optional): Единицы измерения углов
                ориентации. Допустимые значения:
                - `'deg'` — градусы (по умолчанию);
                - `'rad'` — радианы.
            position_format (PositionFormat, optional): Формат выходных данных.
                - `'tcp'` — возвращает позицию и ориентацию TCP в виде
                  `(X, Y, Z, Rx, Ry, Rz)`, где:
                    * `(X, Y, Z)` — координаты в метрах,
                    * `(Rx, Ry, Rz)` — углы поворота вокруг осей в указанных
                      единицах (`orientation_units`);
                - `'joints'` — возвращает углы сочленений в виде
                  `(J1, J2, J3, J4, J5, J6)`, где `Ji` — угол поворота i-го
                  звена от основания. Углы возвращаются в тех же единицах,
                  что указаны в `orientation_units`.
                По умолчанию: `'tcp'`.
            coordinate_system (CoordinateSystem, optional): Система координат,
                в которой возвращается TCP. Если не задана, используется
                глобальная система координат основания робота.
                Может быть пользовательской системой, заданной через
                `robot.coordinate_system`.
        Returns:
            PositionOrientation: кортеж, содержащий 6 чисел:
                - для `'tcp'`: `(X, Y, Z, Rx, Ry, Rz)`;
                - для `'joints'`: `(J1, J2, J3, J4, J5, J6)`.

        Examples:
            >>> # Получить углы сочленений в градусах
            >>> joints = robot.motion.get_actual_position(position_format='joints')
            >>> print(f"Углы: {joints}")

            >>> # Получить позицию TCP в пользовательской системе координат
            >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
            >>> local_coord_system = CoordinateSystem(
            ...     position_orientation=((-0.3332, -0.1838, -0.0198, 3.138, 0, 0.8195)),
            ...     orientation_units="deg",
            ... )
            >>> pose = robot.motion.get_actual_position(
            ...     coordinate_system=local_coord_system,
            ...     orientation_units='deg'
            ... )
            >>> x, y, z, rx, ry, rz = pose

        Notes:
            - При `position_format='joints'` параметр `coordinate_system`
              игнорируется.
            - Ориентация `(Rx, Ry, Rz)` задана в формате **поворотов вокруг
              неподвижных осей (extrinsic XYZ)** — уточните документацию
              кинематики, если используется другой формат (например, Euler ZYX).
            - Все линейные значения возвращаются в **метрах**.
        """

        if orientation_units is None:
            orientation_units = MOTION_SETUP.units
        _validate_literal("angle", orientation_units)
        _validate_literal("position", position_format)

        if position_format == "joints":
            joints_pose = list(self._rtd_receiver.get_data().act_q)
            if orientation_units == "rad":
                return joints_pose
            return cast(
                PositionOrientation,
                unit_c.radians_to_degrees(*joints_pose),
            )
        tcp_pose = list(self._rtd_receiver.get_data().act_tcp_x)
        if coordinate_system:
            tcp_pose = list(
                convert_position_orientation(
                    coordinate_system,
                    tcp_pose,
                    orientation_units="rad",
                    to_local=True,
                )
            )
        if orientation_units == "rad":
            return tcp_pose
        pose = tcp_pose[POSITION_SLICE] + cast(
            List, unit_c.radians_to_degrees(*tcp_pose[ORIENTATION_SLICE])
        )
        return pose

    @handle_connection(available_in_read_only=False)
    def get_last_saved_position(
        self,
        orientation_units: Optional[AngleUnits] = None,
        position_format: PositionFormat = "joints",
        coordinate_system: Optional[CoordinateSystem] = None,
    ) -> PositionOrientation | None:
        """Возвращает последнюю сохранённую позицию робота в заданном формате.

        Сохранённая позиция — это состояние, зафиксированное в памяти контроллера.
        Метод позволяет получить её либо в виде углов сочленений, либо в виде
        декартовой позиции и ориентации TCP.

        Args:
            orientation_units (AngleUnits, optional): Единицы измерения углов.
                - `'deg'` — градусы (по умолчанию);
                - `'rad'` — радианы.
            position_format (PositionFormat, optional): Формат вывода:
                - `'joints'` — возвращает углы сочленений `(J1, J2, ..., J6)`
                  в указанных единицах;
                - `'tcp'` — возвращает позицию и ориентацию конечного инструмента
                  `(X, Y, Z, Rx, Ry, Rz)`, где линейные координаты в метрах,
                  углы — в `orientation_units`.
                По умолчанию: `'joints'`.
            coordinate_system (CoordinateSystem, optional): Система координат
                для формата `'tcp'`. Если не указана, используется система
                координат основания робота. Игнорируется при `position_format='joints'`.

        Returns:
            PositionOrientation | None:
                - Объект с 6 значениями (в зависимости от `position_format`),
                  соответствующий последней сохранённой позиции;
                - `None`, если получить позицию не удалось.

        Examples:
            >>> # Получить последнюю сохранённую позицию в углах сочленений (градусы)
            >>> last_joints = robot.motion.get_last_saved_position()
            >>> if last_joints:
            ...     print(f"Последняя позиция: {last_joints}")

            >>> # Получить в TCP-формате в радианах
            >>> last_pose = robot.motion.get_last_saved_position(
            ...     position_format='tcp',
            ...     orientation_units='rad'
            ... )

        Notes:
            - Возвращаемая позиция **не обязательно совпадает** с текущей
                фактической позицией робота — она отражает состояние на момент
                последнего сохранения.
            - При `position_format='joints'` параметр `coordinate_system` игнорируется.
        """
        if orientation_units is None:
            orientation_units = MOTION_SETUP.units
        _validate_literal("angle", orientation_units)
        _validate_literal("position", position_format)

        self._controller.send(Get.ctrlr_coms_get_last_pos)
        last_pose = self._controller.receive(
            Get.ctrlr_coms_get_last_pos,
            CTRLR_GET_LAST_POSITION_UNPACK_FORMAT,
        )
        if len(last_pose) != 6:
            return None

        if position_format == "joints":
            if orientation_units == "deg":
                return cast(
                    PositionOrientation,
                    unit_c.radians_to_degrees(*last_pose),
                )
            return last_pose

        self._controller.send(
            Get.ctrlr_coms_fkine,
            pack(CTRLR_FKINE_CMD_PACK_FORMAT, *last_pose),
        )
        response = self._controller.receive(
            Get.ctrlr_coms_fkine,
            CTRLR_FKINE_CMD_UNPACK_FORMAT,
        )
        tcp_pose = list(response[FKINE_IKINE_RESPONSE_JOINT_POSITION_SLICE])

        if not response or response[0] != 0:
            return None
        if coordinate_system:
            tcp_pose = convert_position_orientation(
                coordinate_system,
                tcp_pose,
                orientation_units="rad",
                to_local=True,
            )
        if orientation_units == "deg":
            tcp_pose = cast(List[float], tcp_pose[POSITION_SLICE]) + cast(
                List[float],
                unit_c.radians_to_degrees(*tcp_pose[ORIENTATION_SLICE]),
            )
        return tcp_pose

    @handle_connection(available_in_read_only=True)
    def check_waypoint_completion(self, waypoint_count: int = 0) -> bool:
        """Проверяет, завершено ли выполнение текущих целевых точек — без блокировки.

        Метод сравнивает количество оставшихся невыполненных точек в буфере
        контроллера с заданным порогом `waypoint_count`. Возвращает `True`,
        если точек **осталось не более**, чем указано.

        Метод доступен в режиме «read only».

        Проверить состояние исполнения текущих заданных целевых точек
        (без ожидания).

        Args:
            waypoint_count (int, optional): Пороговое количество точек в буфере.
                По умолчанию `0` — проверяется полное прохождение всех точек.

        Returns:
            True: Если точки исполнены (целевых точек в буфере меньше, чем
                `waypoint_count`).
            False: Если точки не исполнены (точек в буфере больше, чем
                `waypoint_count`).

        Examples:
            >>> # Проверить, пройдены ли все точки
            >>> if robot.motion.check_waypoint_completion():
            ...     print("Все точки пройдены")
        """

        _validate_value(waypoint_count, WP_COUNT_LIMITS)
        return self._rtd_receiver.get_data().buff_fill <= waypoint_count

    @handle_connection(available_in_read_only=False)
    def get_home_pose(
        self, units: Optional[AngleUnits] = None
    ) -> PositionOrientation:
        """Возвращает текущую домашнюю позицию робота.

        Домашняя позиция — это позиция, которая считается "начальной" для робота.

        Args:
            units (AngleUnits, optional): Единицы измерения углов сочленений:
                - `'deg'` — градусы (по умолчанию);
                - `'rad'` — радианы.

        Returns:
            PositionOrientation: Объект, содержащий 6 углов сочленений
                `(J1, J2, J3, J4, J5, J6)` в указанных единицах,
                представляющих домашнюю позицию от основания до фланца робота.

        Examples:
            >>> # Получить домашнюю позицию в градусах
            >>> home = robot.motion.get_home_pose()
            >>> print(f"Домашняя позиция: {home}")

            >>> # Получить в радианах
            >>> home_rad = robot.motion.get_home_pose(units='rad')

        Notes:
            - Возвращаемая позиция **не обязательно совпадает** с текущей
              фактической позицией робота.
            - Для перемещения робота в домашнюю позицию используйте метод
              `move_to_home_pose()`.
        """
        if units is None:
            units = MOTION_SETUP.units
        _validate_literal("angle", units)
        self._controller.send(Get.ctrlr_coms_get_home_pose)
        response = self._controller.receive(
            Get.ctrlr_coms_get_home_pose,
            CTRLR_GET_SET_HOME_POSE_PACK_UNPACK_FORMAT,
        )
        if units == "deg":
            return cast(
                PositionOrientation,
                unit_c.radians_to_degrees(*response),
            )
        return cast(PositionOrientation, response)

    @handle_connection(available_in_read_only=False)
    def free_drive(self, enable: bool = True) -> bool:
        """Активирует режим ручного перемещения «Free Drive».

        В этом режиме оператор может физически перемещать руку робота,
        а система управления компенсирует гравитацию и минимизирует сопротивление.
        Режим предназначен для ручного позиционирования, обучения или настройки.

        Команда **требует циклического подтверждения**. Для корректной
        работы метод должен вызываться **не реже 100 Гц** (каждые 10 мс),
        пока режим активен. Если вызовы прекращаются, контроллер автоматически
        выходит из режима Free Drive.

        Args:
            enable (bool, optional):
                - `True` — активировать режим Free Drive;
                - `False` — деактивировать.
                По умолчанию: `True`.

        Returns:
            True: В случае успешной отправки команды.

        Examples:
            >>> # Активировать Free Drive на 5 секунд
            >>> import time
            >>> start = time.time()
            >>> while time.time() - start < 5.0:
            ...     robot.motion.free_drive(True)  # вызывать ≥100 Гц
            ...     time.sleep(0.005)  # 200 Гц — безопасная частота
            >>> robot.motion.free_drive(False)  # явное отключение
        """

        return self._controller.send(
            Omm.zero_gravity,
            pack(OMM_ENABLE_DISABLE_PACK_FORMAT, bool(enable)),
        )

    @handle_connection(available_in_read_only=False)
    def move_to_home_pose(self):
        """Перемещает робота в домашнюю позицию.

        Перед началом движения метод автоматически:
        1. Останавливает любое текущее движение;
        2. Очищает буфер целевых точек;
        3. Инициирует перемещение к домашней позиции.

        Returns:
            True: В случае начала перемещения в домашнюю позицию.

        Examples:
            >>> # Переместиться в домашнюю позицию
            >>> if robot.motion.move_to_home_pose():
            ...     print("Начато перемещение домой")
            ... else:
            ...     print("Не удалось инициировать движение")

            >>> # Дождаться завершения (опционально)
            >>> robot.motion.wait_waypoint_completion()

        Notes:
            - Метод **не ждёт завершения движения** — он только запускает его.
              Используйте `wait_waypoint_completion()`, если требуется синхронное выполнение.
            - Домашняя позиция должна быть предварительно задана (через
              `set_home_pose`) или определена по умолчанию.
        """
        return (
            self.mode.set("hold")
            and self.joint.add_new_waypoint(
                angle_pose=self.get_home_pose(units="rad"),
                speed=MOVE_TO_HOME_POSE_SPEED,
                accel=MOVE_TO_HOME_POSE_ACCEL,
                units="rad",
            )
            and self.mode.set("move")
        )

    @handle_connection(available_in_read_only=False)
    def set_home_pose(
        self,
        angle_pose: PositionOrientation,
        units: Optional[AngleUnits] = None,
    ) -> bool:
        """Устанавливает новую домашнюю позицию робота.

        Домашняя позиция — это "исходной" положение, используемое для возврата
        робота в исходное положение (например, через `move_to_home_pose`).
        Эта позиция сохраняется в памяти контроллера и может быть восстановлена
        после перезапуска.

        Args:
            angle_pose (PositionOrientation): Последовательность из 6 углов
                сочленений `(J1, J2, J3, J4, J5, J6)`, представляющих желаемую
                домашнюю позицию от основания до фланца робота.
            units (AngleUnits, optional): Единицы измерения углов в `angle_pose`:
                - `'deg'` — градусы (по умолчанию);
                - `'rad'` — радианы.
                Если не указано, предполагаются градусы.

        Returns:
            bool: True — если домашняя позиция успешно установлена в контроллере;

        Examples:
            >>> # Установить домашнюю позицию в градусах
            >>> home_angles = (0.0, -90.0, 0.0, -90.0, 0.0, 0.0)
            >>> robot.motion.set_home_pose(home_angles)

            >>> # Установить в радианах
            >>> import math
            >>> home_rad = (0.0, -math.pi/2, 0.0, -math.pi/2, 0.0, 0.0)
            >>> robot.motion.set_home_pose(home_rad, units='rad')

        Notes:
            - Рекомендуется устанавливать домашнюю позицию в безопасной,
              легко достижимой конфигурации (например, в центре рабочей зоны).
        """
        if units is None:
            units = MOTION_SETUP.units
        _validate_literal("angle", units)
        _validate_length(angle_pose, POSITION_ORIENTATION_LENGTH)
        if units == "deg":
            angle_pose = cast(
                PositionOrientation, unit_c.degrees_to_radians(*angle_pose)
            )
        return self._controller.send(
            Set.ctrlr_coms_set_home_pose,
            pack(
                CTRLR_GET_SET_HOME_POSE_PACK_UNPACK_FORMAT,
                *angle_pose,
            ),
        )

    @handle_connection(available_in_read_only=False)
    def simple_joystick(
        self, coordinate_system: Optional[CoordinateSystem] = None
    ) -> bool:
        """Запускает встроенный графический интерфейс для ручного джоггинга (Jogging).

        Интерфейс позволяет управлять роботом в реальном времени с помощью
        виртуального джойстика: перемещать TCP по осям или вращать сочленения.
        Реализован на основе методов `jog_once` и предоставляет базовые функции
        позиционирования, калибровки и переключения режимов.

        Метод **блокирующий**: выполнение программы приостанавливается до тех пор,
        пока пользователь не закроет окно интерфейса.

        Args:
            coordinate_system (CoordinateSystem, optional): Пользовательская система
                координат для джоггинга в режиме TCP. Если не задана,
                используется система координат основания робота.

        Returns:
            bool: True — после корректного завершения работы интерфейса
                  (пользователь закрыл окно). В случае исключения (например,
                  отсутствие tkinter) метод выбросит ошибку.

        Examples:
            >>> # Запустить джойстик в глобальной СК
            >>> robot.motion.simple_joystick()

            >>> # Запустить в пользовательской системе координат
            >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
            >>> local_coord_system = CoordinateSystem(
            ...     position_orientation=((-0.3332, -0.1838, -0.0198, 0.138, 0, 0.8195)),
            ...     orientation_units="rad",
            ... )
            >>> robot.motion.simple_joystick(coordinate_system=local_coord_system)

        Notes:
            - Интерфейс предназначен для отладки и ручного управления —
              не рекомендуется для использования в промышленных автоматизированных сценариях.
        """

        try:
            # Безопасный импорт GUI. Используется для совместимости основной
            # части API с системами, не имеющими установленный tkinter.
            from API.source.features.gui.ui_controller import (
                SimpleJoystickUI,
            )

            SimpleJoystickUI(
                self.linear.jog_once,
                self.joint.jog_once,
                self.linear.set_jog_param_in_tcp,
                self.linear.get_actual_position,
                self.joint.get_actual_position,
                self.free_drive,
                self.mode.set,
                self.joint.add_new_waypoint,
                self.linear.add_new_offset,
                self.scale_setup.set,
                coordinate_system,
            )
            return True

        except ImportError as e:
            self._logger.error(f"Failed to start simple joystick, error: {e}")
            raise ApiError(
                "Tkinter is needed to use this method, probably your python "
                "installation or system doesn't contain it"
            )

    @handle_connection(available_in_read_only=True)
    def wait_waypoint_completion(
        self, waypoint_count: int = 0, await_sec: int = -1
    ) -> bool:
        """Ожидает завершения выполнения целевых точек в буфере.

        Метод блокирует выполнение программы до тех пор, пока количество
        оставшихся невыполненных точек в буфере контроллера не станет
        **меньше или равно** `waypoint_count`, либо не истечёт заданное
        время ожидания.

        Метод доступен в режиме «read only».

        Args:
            waypoint_count (int, optional): Пороговое значение количества точек.
                Ожидание завершается, когда в буфере остаётся ≤ `waypoint_count` точек.
                По умолчанию `0` — ожидается полное выполнение всех точек.
            await_sec (int, optional): Максимальное время ожидания в секундах:
                - `-1` — ожидание без ограничения по времени (по умолчанию);
                - `0` — неблокирующая проверка: выполнить одну итерацию и вернуться;
                - `> 0` — ожидать не более указанного числа секунд.

        Returns:
            bool: True — если количество точек в буфере стало ≤ `waypoint_count`
                  в течение заданного времени;
                  False — если произошёл таймаут (`await_sec >= 0` и условие не выполнено).

        Examples:
            >>> # Дождаться полного выполнения всех точек (без таймаута)
            >>> robot.motion.wait_waypoint_completion()

            >>> # Дождаться, пока не останется ≤ 1 точки, максимум 10 секунд
            >>> if robot.motion.wait_waypoint_completion(waypoint_count=1, await_sec=10):
            ...     print("Готов к следующему действию")
            ... else:
            ...     print("Таймаут: движение не завершено")

            >>> # Неблокирующая проверка (аналог check_waypoint_completion)
            >>> done = robot.motion.wait_waypoint_completion(await_sec=0)

        Notes:
            - При `await_sec = -1` вызов может блокировать программу неограниченно —
              используйте с осторожностью в автоматизированных системах.
            - Этот метод часто используется после добавления серии точек.
        """

        _validate_value(waypoint_count, WP_COUNT_LIMITS)
        waypoint_amount = 0
        for _ in sleep(
            await_sec=await_sec,
            frequency=CHECK_FREQUENCY_SEC,
        ):
            if not self._connection_state.is_connected():
                self._logger.error(
                    "Failed to wait waypoint completion - connection was lost"
                )
                return False
            if waypoint_amount != self._rtd_receiver.get_data().buff_fill:
                self._logger.debug(
                    (
                        f"Waypoint in queue: "
                        f"{self._rtd_receiver.get_data().buff_fill}"
                    )
                )
                waypoint_amount = self._rtd_receiver.get_data().buff_fill
            if waypoint_count >= self._rtd_receiver.get_data().buff_fill:
                self._logger.debug(f"Waypoint queue is equals {waypoint_count}")
                return True
        return False
