"""
Перевод робота в положение 'семерка' (положение, в котором робот напоминает
цифру 7).
"""

from API.rc_api import RobotApi

# IPv4 адрес целевого робота
ROBOT_IP: str = "10.10.10.10"


def move_to_7_pose(robot_ip: str):
    """
    Переместить робота в положение 'семерка'.

    Args:
        robot_ip: IPv4 адрес робота.
    """
    # Подключение к роботу
    robot = RobotApi(ip=robot_ip, show_std_traceback=True, autoconnect=True)
    #robot.controller_state.set("off")

    # Настройка параметров нагрузки
    #robot.payload.set(mass=0.3, tcp_mass_center=(0, 0, 0))

    # Настройка параметров движения
    #robot.motion.scale_setup.set(velocity=1, acceleration=1)

    # Запуск робота
    robot.controller_state.set("run", await_sec=120)

    # Добавление положения 'семерка'
    '''robot.motion.joint.add_new_waypoint(
        angle_pose=(0, -120, 120, -90, -90, 0),
        speed=100,
        accel=10,
        blend=0,
        
        units="deg",
    )'''
    tcp_pose = robot.motion.joint.get_actual_position('deg')
    print(tcp_pose)

    # robot.motion.joint.add_new_waypoint(
    #     angle_pose=(-5.76, -88.77, 65.48, -66.51, -90.05, 39.08),
    #     speed=100,
    #     accel=10,
    #     blend=0,
    #     units="deg",
    # )
    # # Запуск движения и ожидание его завершения
    # robot.motion.mode.set("move")
    # robot.motion.wait_waypoint_completion(0)
    tcp_pose = robot.motion.linear.get_actual_position(orientation_units='deg')
    print(tcp_pose)

if __name__ == "__main__":
    # Запуск определенной выше функции
    move_to_7_pose(ROBOT_IP)
