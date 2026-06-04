"""
Подключение к роботу.
"""

from API.rc_api import RobotApi

# IPv4 адрес целевого робота
ROBOT_IP: str = "127.0.0.1"


def autoconnect_to_robot(robot_ip: str):
    """
    Подключение к роботу при создании экземпляра класса API.

    Args:
        robot_ip: IPv4 адрес робота.
    """
    # Подключение к роботу при создании экземпляра класса
    robot = RobotApi(ip=robot_ip, show_std_traceback=True)
    print(
        "Подключение с роботом установлено: ", robot.is_connected()
    )  # Будет выведено True

    # Отключение от робота
    robot.disconnect()
    print(
        "Подключение с роботом установлено: ", robot.is_connected()
    )  # Будет выведено False

    # Повторное подключение без создания нового экземпляра класса
    robot.connect()
    print(
        "Подключение с роботом установлено: ", robot.is_connected()
    )  # Будет выведено True

    # Отключение от робота
    robot.disconnect()


def advanced_connect_to_robot(robot_ip: str):
    """
    Управление подключением к роботу.

    Args:
        robot_ip: IPv4 адрес робота.
    """
    # Создание экземпляра класса
    robot = RobotApi(ip=robot_ip, show_std_traceback=True, autoconnect=False)
    print(
        "Подключение с роботом установлено: ", robot.is_connected()
    )  # Будет выведено False

    # Подключение к роботу
    robot.connect()
    print(
        "Подключение с роботом установлено: ", robot.is_connected()
    )  # Будет выведено True

    # Отключение от робота
    robot.disconnect()
    print(
        "Подключение с роботом установлено: ", robot.is_connected()
    )  # Будет выведено False

    # Повторное подключение к роботу в режиме "read only"
    robot.connect(read_only=True)
    print(
        "Подключение с роботом установлено: ", robot.is_connected()
    )  # Будет выведено True

    print(
        "Текущее положение робота: ",
        robot.motion.get_actual_position(
            orientation_units="deg", position_format="joints"
        ),
    )
    # Отключение от робота
    robot.disconnect()


if __name__ == "__main__":
    # Запуск определенных выше функции
    autoconnect_to_robot(ROBOT_IP)
    advanced_connect_to_robot(ROBOT_IP)
