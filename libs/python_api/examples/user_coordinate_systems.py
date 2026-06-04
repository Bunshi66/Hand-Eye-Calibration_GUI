"""
Использование локальной системы координат для задания целевых точек.
"""

from API.rc_api import RobotApi
from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
from API.source.features.mathematics.coordinate_system import (
    convert_position_orientation,
)

# IPv4 адрес целевого робота
ROBOT_IP: str = "127.0.0.1"


def create_user_coordinate_system(robot_ip: str):
    """
    Перемещение робота в глобальной и локальной системах координат.

    Args:
        robot_ip: IPv4 адрес робота.
    """
    # Подключение к роботу
    robot = RobotApi(ip=robot_ip, show_std_traceback=True, autoconnect=True)
    robot.controller_state.set("off")

    # Настройка параметров нагрузки
    robot.payload.set(mass=0, tcp_mass_center=(0, 0, 0))

    # Настройка параметров движения
    robot.motion.scale_setup.set(velocity=0.4, acceleration=0.4)

    # Настройка параметров инструмента
    robot.tool.set(tool_end_point=(0, 0, 0.14329, 0, 0, 0))

    # Запуск робота
    robot.controller_state.set("run", await_sec=120)

    # Определение локальной системы координат
    local_coord_system = CoordinateSystem(
        position_orientation=((-0.3332, -0.1838, -0.0198, 3.138, 0, 0.8195)),
        orientation_units="deg",
    )
    target_point = (-0.45, -0.1, 0.2, -135, 15, 45)

    # Перемещение робота в рабочее положение
    robot.motion.joint.add_new_waypoint(
        angle_pose=(0, -115, 120, -100, -90, 0),
        speed=70,
        accel=70,
        blend=0,
        units="deg",
    )
    robot.motion.mode.set("move")
    robot.motion.wait_waypoint_completion(0)

    # Перемещение в целевую точку, заданную в глобальной системе координат
    robot.motion.joint.add_new_waypoint(
        tcp_pose=target_point,
        speed=30,
        accel=30,
        units="deg",
    )
    robot.motion.mode.set("move")
    robot.motion.wait_waypoint_completion(0)

    global_pose = robot.motion.get_actual_position(
        orientation_units="deg", position_format="tcp"
    )
    local_pose = robot.motion.get_actual_position(
        orientation_units="deg",
        position_format="tcp",
        coordinate_system=local_coord_system,
    )
    print(
        "Положение робота: ",
        f"\tв глобальной системе координат: {global_pose}",
        f"\tв локальной системе координат: {local_pose}",
        sep="\n",
    )

    # Определение положения точки локальной системы координат в глобальной
    target_point = convert_position_orientation(
        coordinate_system=local_coord_system,
        position_orientation=target_point,
        orientation_units="deg",
    )

    # Перемещение в целевую точку, заданную в локальной системе координат
    robot.motion.joint.add_new_waypoint(
        tcp_pose=target_point,
        speed=30,
        accel=30,
        units="deg",
    )
    robot.motion.mode.set("move")
    robot.motion.wait_waypoint_completion(0)

    global_pose = robot.motion.get_actual_position(
        orientation_units="deg", position_format="tcp"
    )
    local_pose = robot.motion.get_actual_position(
        orientation_units="deg",
        position_format="tcp",
        coordinate_system=local_coord_system,
    )
    print(
        "Положение робота: ",
        f"\tв глобальной системе координат: {global_pose}",
        f"\tв локальной системе координат: {local_pose}",
        sep="\n",
    )


if __name__ == "__main__":
    # Запуск определенной выше функции
    create_user_coordinate_system(ROBOT_IP)
