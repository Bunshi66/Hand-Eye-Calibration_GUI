from __future__ import annotations

from struct import pack
from typing import TYPE_CHECKING, List, Optional, Tuple, cast

import API.source.features.mathematics.unit_convert as unit_c
from API.source.core.connection_state import (
    ConnectionState,
    handle_connection,
)
from API.source.core.exceptions.data_validation_error.argument_error import (
    validation,
)
from API.source.features.mathematics.coordinate_system import (
    convert_position_orientation,
)
from API.source.features.tools import (
    dataclass_to_tuple,
    set_position_orientation_units,
)
from API.source.models.classes.data_classes.command_templates import (
    MOTION_SETUP,
    InverseKinematicOptimalTemplate,
)
from API.source.models.classes.enum_classes.controller_commands import (
    Getters as Get,
)
from API.source.models.constants import (
    CTRLR_FKINE_CMD_PACK_FORMAT,
    CTRLR_FKINE_CMD_UNPACK_FORMAT,
    CTRLR_IKINE_CMD_PACK_FORMAT,
    CTRLR_IKINE_CMD_UNPACK_FORMAT,
    CTRLR_IKINE_OPTIMAL_CMD_PACK_FORMAT,
    CTRLR_IKINE_OPTIMAL_CMD_UNPACK_FORMAT,
    FKINE_IKINE_RESPONSE_JOINT_POSITION_SLICE,
    FKINE_SOLUTIONS_COUNT,
    JOINT_COUNT,
    ORIENTATION_SLICE,
    POSITION_ORIENTATION_LENGTH,
    POSITION_SLICE,
    PREVIOUS_FKINE_SOLUTION_OFFSET,
    RESPONSE_CODE_OFFSET,
)
from API.source.models.type_aliases import (
    AngleUnits,
    PositionOrientation,
)

if TYPE_CHECKING:
    from API.source.ap_interface.motion.coordinate_system import (
        CoordinateSystem,
    )
    from API.source.ap_interface.motion.joint_motion import (
        JointMotion,
    )
    from API.source.core.network.controller_socket import (
        Controller,
    )


_validate_length = validation.validate_length
_validate_literal = validation.validate_literal


class Kinematics:
    """
    Класс для получения решения прямой и обратной задач кинематики.
    """

    _controller: Controller
    _joint: JointMotion

    def __init__(
        self,
        controller: Controller,
        joint: JointMotion,
        connection_state: ConnectionState,
    ) -> None:
        self._controller = controller
        self._joint = joint
        self._connection_state = connection_state

    @handle_connection(available_in_read_only=False)
    def get_forward(
        self,
        angle_pose: PositionOrientation,
        units: Optional[AngleUnits] = None,
        coordinate_system: Optional[CoordinateSystem] = None,
    ) -> PositionOrientation | None:
        """Решает прямую задачу кинематики (Forward Kinematics).

        Получает решение прямой задачи кинематики в пользовательской системе
        координат. Если система координат не была задана, то будет
        использована система координат основания робота.

        Args:
            joints_angles: 6 углов поворота моторов, от основания до фланца
                робота ('units').
            units: Единицы измерения. По-умолчанию градусы.
                'deg' — градусы.
                'rad' — радианы.
            coordinate_system: Выбранная система координат. По-умолчанию
                используется система координат основания робота.

        Returns:
            PositionOrientation | None:
                - `(X, Y, Z, Rx, Ry, Rz)` — позиция TCP в метрах и углах
                  в указанной системе координат;
                - `None`, если не удалось получить решение.

        Examples:
            >>> # Получить TCP-позицию для заданных углов (в глобальной СК)
            >>> angles = [10.0, -50.0, 0.0, 0.0, 0.0, 0.0]
            >>> tcp_pose = robot.motion.kinematics.get_forward(angle_pose=angles)
            >>> if tcp_pose:
            ...     x, y, z, rx, ry, rz = tcp_pose
            ...     print(f"TCP: X={x:.3f} м, Y={y:.3f} м, Z={z:.3f} м")

            >>> # Получить позицию в пользовательской СК
            >>> from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
            >>> user_cs = CoordinateSystem((0.5, 0, 0.2, 0, 0, 0))
            >>> tcp_local = robot.motion.kinematics.get_forward(
            ...     angle_pose=angles,
            ...     coordinate_system=user_cs
            ... )
        """

        if units is None:
            units = MOTION_SETUP.units
        _validate_literal("angle", units)
        _validate_length(angle_pose, JOINT_COUNT)
        if units == "deg":
            angle_pose = cast(
                List[float], unit_c.degrees_to_radians(*angle_pose)
            )
        self._controller.send(
            Get.ctrlr_coms_fkine,
            pack(CTRLR_FKINE_CMD_PACK_FORMAT, *angle_pose),
        )
        response = self._controller.receive(
            Get.ctrlr_coms_fkine,
            CTRLR_FKINE_CMD_UNPACK_FORMAT,
        )
        tcp_pose = list(response[FKINE_IKINE_RESPONSE_JOINT_POSITION_SLICE])

        if not response and response[0] != 0:
            return None
        if coordinate_system:
            tcp_pose = convert_position_orientation(
                coordinate_system,
                tcp_pose,
                orientation_units="rad",
                to_local=True,
            )
        tcp_pose = cast(List[float], tcp_pose)
        if units == "rad":
            return tcp_pose
        return cast(
            PositionOrientation,
            tcp_pose[POSITION_SLICE]
            + cast(
                List[float],
                unit_c.radians_to_degrees(*tcp_pose[ORIENTATION_SLICE]),
            ),
        )

    @handle_connection(available_in_read_only=False)
    def get_inverse(
        self,
        tcp_pose: PositionOrientation,
        angle_pose: Optional[PositionOrientation] = None,
        orientation_units: Optional[AngleUnits] = None,
        get_all: bool = False,
    ) -> PositionOrientation | Tuple[PositionOrientation, ...] | None:
        """Решает обратную задачу кинематики (Inverse Kinematics).

        Получает решение обратной задачи кинематики. Конвертация позиции и
        ориентации из локальной (пользовательской) в глобальную производится
        при передаче аргументов с помощью функции
        convert_position_orientation, переданные при этом единицы измерения
        должны совпадать с единицами измерения данного метода.

        Args:
            tcp_pose: Позиция и ориентация ЦТИ в глобальной
                системе координат (система координат основания робота) в
                формате:
                (X, Y, Z, Rx, Ry, Rz), где (X, Y, Z) — м,
                (Rx, Ry,Rz) — 'orientation_units'.
            angle_pose: Положение углов поворота моторов, относительно которого
                будет рассчитано ближайшее решение обратной задачи кинематики.
                По-умолчанию текущее значение, полученное из RTD.
            orientation_units: Единицы измерения. По-умолчанию градусы.
                'deg' — градусы.
                'rad' — радианы.
            get_all: Получить ли все решения или только оптимальное.
        Returns:
            PositionOrientation: Оптимальное решение задачи.
            Tuple[PositionOrientation, ...]: 8 решений задачи в формате 6
                углов поворотов моторов, от основания до фланца робота
                ('units').
            None: В случае ошибки в расчетах в контроллере.

        Examples:
            >>> # Получить одно решение, ближайшее к текущей позиции
            >>> target = (0.4, 0.0, 0.5, 0.0, 3.14, 0.0)
            >>> angles = robot.motion.kinematics.get_inverse(tcp_pose=target)
            >>> if angles:
            ...     robot.motion.joint.add_new_waypoint(angle_pose=angles)

            >>> # Получить все возможные решения
            >>> all_solutions = robot.motion.kinematics.get_inverse(
            ...     tcp_pose=target,
            ...     get_all=True
            ... )
            >>> if all_solutions:
            ...     # Выбрать решение с наименьшим сгибом локтя
            ...     best = min(all_solutions, key=lambda j: abs(j[2]))
            ...     robot.motion.joint.add_new_waypoint(angle_pose=best)

            >>> # Указать опорную позицию для выбора решения
            >>> reference = (0, -90, 0, -90, 0, 0)
            >>> angles = robot.motion.kinematics.get_inverse(
            ...     tcp_pose=target,
            ...     angle_pose=reference,
            ...     orientation_units='deg'
            ... )

        Notes:
            - Обратная задача может иметь **до 8 решений** для стандартного
              6-осного манипулятора.
            - Если `angle_pose` не задан, в качестве опорной используется
              **текущая позиция робота** (из RTD).
            - Все решения возвращаются в **тех же единицах**, что указаны
              в `orientation_units`.
            - Позиции вне досягаемости или ведущие к самостолкновению
              возвращают `None`.
            - Этот метод **недоступен в режиме read-only**.
        """
        if orientation_units is None:
            orientation_units = MOTION_SETUP.units
        if angle_pose is None:
            angle_pose = self._joint._rtd_receiver.get_data().act_q
        _validate_literal("angle", orientation_units)
        _validate_length(tcp_pose, POSITION_ORIENTATION_LENGTH)
        _validate_length(angle_pose, POSITION_ORIENTATION_LENGTH)
        tcp_pose = set_position_orientation_units(tcp_pose, orientation_units)
        if get_all:
            self._controller.send(
                Get.ctrlr_coms_ikine,
                pack(CTRLR_IKINE_CMD_PACK_FORMAT, *tcp_pose),
            )
            response = self._controller.receive(
                Get.ctrlr_coms_ikine,
                CTRLR_IKINE_CMD_UNPACK_FORMAT,
            )
            if orientation_units == "deg":
                response = cast(
                    List[float], unit_c.radians_to_degrees(*response)
                )
            return tuple(
                response[
                    i * POSITION_ORIENTATION_LENGTH + RESPONSE_CODE_OFFSET : i
                    * POSITION_ORIENTATION_LENGTH
                    + PREVIOUS_FKINE_SOLUTION_OFFSET
                ]
                for i in range(FKINE_SOLUTIONS_COUNT)
            )
        ikine_template = InverseKinematicOptimalTemplate(
            target=list(tcp_pose), base_q=list(angle_pose)
        )
        self._controller.send(
            Get.ctrlr_coms_ikine_optimal,
            pack(
                CTRLR_IKINE_OPTIMAL_CMD_PACK_FORMAT,
                *dataclass_to_tuple(ikine_template),
            ),
        )
        response = self._controller.receive(
            Get.ctrlr_coms_ikine_optimal,
            CTRLR_IKINE_OPTIMAL_CMD_UNPACK_FORMAT,
        )
        inverse_solution = list(
            response[FKINE_IKINE_RESPONSE_JOINT_POSITION_SLICE]
        )
        if response and response[0] == 0:
            if orientation_units == "deg":
                inverse_solution = cast(
                    List[float], unit_c.radians_to_degrees(*inverse_solution)
                )
            return inverse_solution
        return None
