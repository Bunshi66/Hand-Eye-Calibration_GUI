from API.rc_api import RobotApi
from API.source.models.classes.enum_classes.state_classes import (
    InComingControllerState as Ics, InComingSafetyStatus as Iss
)
from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
from API.source.features.mathematics.coordinate_system import (
    convert_position_orientation,
)

import logging

logger = logging.getLogger(__name__)

class RobotInterface():

    def __init__(self):
        self._ip = None #ip_address
        self._robot = None
        self._connected = False

    def connect(self, ip_address) -> bool:
        """Устанавливает соединение с роботом."""

        self._ip = ip_address

        logger.info(f"Подключение к роботу RC по IP: {self._ip}...")
        try:
            # Инициализация с автоподключением (как в вашем примере)
            self._robot = RobotApi(ip=self._ip, show_std_traceback=True, autoconnect=True)

            if (
                    self._robot.safety_status.get() == Iss.fault.name
                    or self._robot.controller_state.get() == Ics.failure.name
            ):
                self._robot.controller_state.set('off')

            self._robot.tool.set((0, 0, 0, 0, 0, 0), units='deg')
            self._robot.payload.set(mass=2.2, tcp_mass_center=(-0.009, 0, -0.04))
            self._robot.motion.scale_setup.set(velocity=1, acceleration=1)
            self._robot.controller_state.set("run", await_sec=120)
            self._connected = True

            logger.info("Робот успешно подключен.")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к роботу RC: {e}")
            return False

    def disconnect(self):
        """Отключается от робота."""
        self._robot.disconnect()
        self._connected = False
        print("Отключено от робота RC.")

        # if self._connected:
        #     self._robot = None
        #     self._connected = False
        #     print("Отключено от робота RC.")

    def robot_tool_set(self, tool_end_point):
        self._robot.tool.set(tool_end_point, units='deg')
        logger.info(f"Установлены параметры инструмента: {tool_end_point}")

    def move_linear_trajectory(self, pose_list, velocity: float, acceleration: float, num_slow_pose):
        try:
            for i, pose in enumerate(pose_list):

                logger.info(f"Добавлена линейная поза (м, гр): {pose}")

                if i in num_slow_pose:
                    self._robot.motion.linear.add_new_waypoint(
                        tcp_pose=pose,
                        speed=velocity / 2,
                        accel=acceleration / 2,
                        orientation_units="deg"
                    )
                else:
                    self._robot.motion.linear.add_new_waypoint(
                        tcp_pose=pose,
                        speed=velocity,
                        accel=acceleration,
                        orientation_units="deg"
                    )
            # 2. Запускаем движение
            self._robot.motion.mode.set('move')

            # 3. Блокируем код, пока робот физически не доедет
            self._robot.motion.wait_waypoint_completion(0)

            logger.info("Линейное движение завершено.")
            return True

        except Exception as e:
            logger.error(f"Сбой при линейном движении робота: {e}", exc_info=True)
            return False

    def move_linear_pose(self, pose: tuple, velocity: float, acceleration: float) -> bool:
        """
        Выполняет ЛИНЕЙНОЕ перемещение в заданную декартову позу.

        Args:
            pose: Целевая поза (X, Y, Z, Rx, Ry, Rz).
                  X,Y,Z должны быть в МЕТРАХ.
                  Rx,Ry,Rz должны быть в ГРАДУСАХ.
            velocity: Скорость движения в м/с.
            acceleration: Ускорение в м/с^2.

        Returns:
            True в случае успеха, False в случае ошибки.
        """
        if not self._connected or not self._robot:
            logger.error("Ошибка (move_linear_pose): Попытка двигать неподключенного робота.")
            return False

        try:
            logger.info(f"Линейное движение в позу (м, гр): {pose} со скоростью {velocity} м/с...")

            # 1. Задаем целевую точку для линейного движения
            self._robot.motion.linear.add_new_waypoint(
                tcp_pose=pose,
                speed=velocity,
                accel=acceleration,
                # blend=0.0, # Уточнить, нужен ли этот параметр для linear
                orientation_units="deg"
            )

            # 2. Запускаем движение
            self._robot.motion.mode.set('move')

            # 3. Блокируем код, пока робот физически не доедет
            self._robot.motion.wait_waypoint_completion(0)

            logger.info("Линейное движение завершено.")
            return True

        except Exception as e:
            logger.error(f"Сбой при линейном движении робота: {e}", exc_info=True)
            return False

    def move_to_joints_deg(self, target_pose: tuple, speed: int = 20, accel: int = 20) -> bool:
        """
        Перемещает робота по заданным углам сочленений (в градусах).
        Автоматически дожидается окончания движения и гасит вибрации.

        Args:
            target_pose: кортеж из 6 углов (J1, J2, J3, J4, J5, J6)
            speed: скорость
            accel: ускорение
        """
        if not self._connected or not self._robot:
            logger.error("Ошибка: Попытка двигать неподключенного робота.")
            return False

        try:
            print(f"Движение в точку: {target_pose}...")

            # 1. Задаем целевую точку (waypoint)
            self._robot.motion.joint.add_new_waypoint(
                angle_pose=target_pose,
                speed=speed,
                accel=accel,
                blend=0,
                units='deg'
            )

            # 2. Запускаем движение
            self._robot.motion.mode.set('move')

            # 3. Блокируем код, пока робот физически не доедет
            self._robot.motion.wait_waypoint_completion(0)

            # 4. Гасим вибрации конструкции
            #time.sleep(1)

            return True

        except Exception as e:
            logger.error(f"Сбой при движении робота: {e}")
            return False

    def get_tcp_pose(self) -> dict:
        """
        Запрашивает декартову позу TCP за ОДИН сетевой запрос.

        Returns:
            dict: {
                "pose_radians": [X, Y, Z, Rx_rad, Ry_rad, Rz_rad],
                "pose_degrees": [X, Y, Z, Rx_deg, Ry_deg, Rz_deg]
            }
        """
        if not self._connected or not self._robot:
            logger.error("Ошибка: Попытка запросить позу у неподключенного робота.")
            return None

        try:
            x_m, y_m, z_m, rx_deg, ry_deg, rz_deg = self._robot.motion.get_actual_position(
                position_format="tcp",
                orientation_units="deg"
            ) # H_gripper2base

            # 1. Переводим трансляцию в миллиметры
            x_mm, y_mm, z_mm = x_m * 1000.0, y_m * 1000.0, z_m * 1000.0

            # 2. Формируем список в радианах (идеальный слепок времени)
            pose_deg = [x_mm, y_mm, z_mm, rx_deg, ry_deg, rz_deg]

            # return {
            #     "pose_degrees": pose_deg
            # }
            return pose_deg

        except Exception as e:
            logger.error(f"Ошибка при чтении позы робота: {e}")
            return None

    def get_joint_angles(self) -> dict:
        """
        Получить текущие углы сочленений (пригодится для отладки).

        Returns:
            dict: {
                "joints_radians": [J1...J6],
                "joints_degrees": [J1...J6]
            }
        """
        if not self._connected or not self._robot:
            logger.error("Попытка запросить углы: робот не подключен!")
            return None

        try:
            joints_deg = self._robot.motion.get_actual_position(
                position_format="joints",
                orientation_units="deg"
            )

            # return {
            #     "joints_degrees": joints_deg
            # }
            return joints_deg

        except Exception as e:
            logger.error(f"Ошибка чтения углов сочленений: {e}")
            return None

    def set_DO_true(self):
        self._robot.io.digital.set_output(index=23, value=True)

    def set_DO_false(self):
        self._robot.io.digital.set_output(index=23, value=False)