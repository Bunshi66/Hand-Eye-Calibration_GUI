from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import logging
import time
#from src.utils.paths import *
import os
from PIL import Image
import open3d as o3d
import math

from PyCameraSDK.GenericError import *
from PyCameraSDK.Camera import *
from PyCameraSDK.Common import *
from API.rc_api import RobotApi
from API.source.models.classes.enum_classes.state_classes import (
    InComingControllerState as Ics, InComingSafetyStatus as Iss
)
from API.source.ap_interface.motion.coordinate_system import CoordinateSystem
from API.source.features.mathematics.coordinate_system import (
    convert_position_orientation,
)

logger = logging.getLogger(__name__)

class ScapeCamera():
    """Оболочка над SDK камеры SCAPE"""

    def __init__(self, connection_params: dict):
        """
            Инициализация камеры.

            Args:
                connection_params: {
                    'ip': str или None (None = первая найденная камера)
                }
            """
        connection_params = connection_params or {}
        self._camera_ip = connection_params.get('ip', None)
        self._cam = None  # объект Camera из SDK
        self._cam_info = None  # CameraInfo подключённой камеры
        self._cam_info_list = []  # список всех найденных камер
        self._connected = False

    def connect(self) -> bool:
        """Установить соединение с камерой."""
        logger = logging.getLogger(__name__)
        self._cam = Camera().CreateCamera()
        self._cam.RegisterErrorCodeHandler(PyErrorCodeHandler().__disown__())

        # Ищем камеры в сети
        ret, self._cam_info_list = self._cam.DiscoverCameras()
        if not self._cam_info_list:
            logger.error("Камеры SCAPE не обнаружены в сети")
            return False, CameraInfo()

        # Логируем найденные камеры
        for i, info in enumerate(self._cam_info_list):
            logger.info(
                f"[{i}] {info.cameraIP} "
                f"v{info.cameraSystemVersion} "
                f"(err={info.errorCode})"
            )

        # Подключаемся к нужной (или первой найденной)
        for info in self._cam_info_list:
            if self._camera_ip is not None and info.cameraIP != self._camera_ip:
                continue
            if self._cam.Open(info) == AC_OK:
                self._cam_info = info
                self._connected = True
                logger.info(f"Подключено к камере {info.cameraIP}")
                return True, info

        logger.error(f"Не удалось открыть камеру (ip={self._camera_ip})")
        return False, CameraInfo()

    def disconnect(self):
        """Отключиться от камеры и освободить ресурсы."""
        if self._cam:
            if self._connected and self._cam_info:
                # Закрываем соединение в C++
                self._cam.Close(self._cam_info)

            self._connected = False
            # ПРИНУДИТЕЛЬНО удаляем ссылку на C++ объект до завершения скрипта
            self._cam = None
            logger.info("Камера отключена и ресурсы освобождены.")

    def is_connected(self) -> bool:
        """Проверка состояния подключения."""
        return self._connected

    def get_frame(self) -> dict:
        """Делает снимок и возвращает сырые numpy-массивы."""
        if not self._connected or not self._cam_info:
            logger.error("Ошибка захвата: Камера не подключена")
            return None

        frame_data = FrameData()

        ret = self._cam.Capture(self._cam_info, frame_data)

        if ret != 0:
            logger.error(f"Ошибка SDK при захвате кадра: код {ret}")
            return None

        result = {}

        params = self._cam_info.camParam

        # Разрешение для цветной картинки
        tex_w = params.textureWidth
        tex_h = params.textureHeight

        # Разрешение для карты глубины (зависит от настроек SDK)
        if params.depthType == 1:  # DEPTH_MAP_ALIGN_RGB
            depth_w = params.textureWidth
            depth_h = params.textureHeight
        else:  # Выровнено по инфракрасной камере
            depth_w = params.irWidth
            depth_h = params.irHeight

        # ==========================================
        # ПАРСИНГ ДАННЫХ
        # ==========================================
        # 1. 2D Изображение (RGB или Mono)
        if frame_data.textureSize > 0:
            channels = frame_data.textureSize // (tex_w * tex_h)
            shape = (tex_h, tex_w, channels) if channels > 1 else (tex_h, tex_w)

            # Обязательно .copy() для безопасности памяти!
            result['image'] = frame_data.texture.reshape(shape).copy()

        # 2. Карта Глубины (TIFF)
        if frame_data.depthmapSize > 0:
            result['depth'] = frame_data.depthmap.reshape((depth_h, depth_w)).copy()

        # 3. Облако точек (N, 3)
        if frame_data.point3DSize > 0:
            # Здесь ширина и высота вообще не нужны,
            # reshape(-1, 3) сам разобьет плоский массив на тройки [X, Y, Z]
            result['points'] = frame_data.point3D.reshape((-1, 3)).copy()

        return result

    def _configure_output_settings(self, send_texture=True, send_point3d=True, send_depthmap=True):
        """Включает/выключает потоки данных для экономии трафика."""
        # Выключаем лишнее, чтобы работало быстрее
        self._cam_info.outputSettings.sendTriangleIndices = False
        self._cam_info.outputSettings.sendNormals = False
        self._cam_info.outputSettings.sendRemapTexture = False
        self._cam_info.outputSettings.sendPointColor = False

        # Включаем нужное
        self._cam_info.outputSettings.sendTexture = send_texture
        self._cam_info.outputSettings.sendPoint3D = send_point3d
        self._cam_info.outputSettings.sendDepthmap = send_depthmap

    def get_camera_info(self) -> dict:
        """Получить информацию о камере (модель, серийник, параметры)."""
        pass

    def get_intrinsic(self, cam_info, cam_position):
        """
                Получает матрицу внутренних параметров камеры (3x3).
                :param cam_info: Объект CameraInfo из SDK
                :param cam_position: CAMERA_POSITION.CAM_LEFT | CAM_RGB | CAM_RIGHT
                :return: np.ndarray shape (3,3) или None при ошибке
                """
        cam_enum = {'left': CAMERA_POSITION.CAM_LEFT,
                    'right': CAMERA_POSITION.CAM_RIGHT,
                    'rgb': CAMERA_POSITION.CAM_RGB}
        try:
            ret, intrinsic_list = self._cam.Get3DCameraIntrinsic(cam_info, cam_enum[cam_position])
            if ret != 0:  # 0 = AC_OK
                logger.error(f"❌ SDK вернул ошибку интринсиков: code={ret}")
                return None
            if len(intrinsic_list) != 9:
                logger.error(f"❌ Неверный размер интринсиков: {len(intrinsic_list)} (ожидается 9)")
                return None
            #print(f'Отладочная печать: {intrinsic_list}')
            return np.array(intrinsic_list).reshape(3, 3)
        except Exception as e:
            logger.error(f"❌ Исключение при получении интринсиков: {e}")
            return None

    def get_extrinsic(self, cam_info, extrinsic_type):
        """
        Получает матрицу преобразования из облака точек в СК целевой камеры (4x4).
        :param cam_info: Объект CameraInfo из SDK
        :param extrinsic_type: EXTRINSIC_TYPE.POINT_TO_CAM_LEFT | POINT_TO_CAM_RGB | POINT_TO_CAM_RIGHT
        :return: np.ndarray shape (4,4) или None при ошибке
        """
        cam_enum = {'left': EXTRINSIC_TYPE.POINT_TO_CAM_LEFT,
                    'right': EXTRINSIC_TYPE.POINT_TO_CAM_RIGHT,
                    'rgb': EXTRINSIC_TYPE.POINT_TO_CAM_RGB}
        try:
            ret, extrinsic_list = self._cam.Get3DCameraExtrinsic(cam_info, cam_enum[extrinsic_type])
            if ret != 0:
                logger.error(f"❌ SDK вернул ошибку эксттринсиков: code={ret}")
                return None
            if len(extrinsic_list) != 16:
                logger.error(f"❌ Неверный размер эксттринсиков: {len(extrinsic_list)} (ожидается 16)")
                return None
            #print(f'Отладочная печать: {extrinsic_list}')
            return np.array(extrinsic_list).reshape(4, 4)
        except Exception as e:
            logger.error(f"❌ Исключение при получении эксттринсиков: {e}")
            return None

    def set_exposure(self, value: float):
        """Настройка экспозиции."""
        pass


class RobotInterface():

    def __init__(self, ip_address: str):
        self._ip = ip_address
        self._robot = None
        self._connected = False

    def connect(self) -> bool:
        """Устанавливает соединение с роботом."""
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
        if self._connected:
            self._robot = None
            self._connected = False
            logger.info("Отключено от робота RC.")

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
            logger.info(f"Движение в точку: {target_pose}...")

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

            return {
                "pose_degrees": pose_deg
            }

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
            joints_rad = self._robot.motion.get_actual_position(
                position_format="joints",
                orientation_units="rad"
            )

            joints_deg = [math.degrees(j) for j in joints_rad]

            return {
                "joints_radians": list(joints_rad),
                "joints_degrees": joints_deg
            }

        except Exception as e:
            logger.error(f"Ошибка чтения углов сочленений: {e}")
            return None

    def set_DO_true(self):
        self._robot.io.digital.set_output(index=23, value=True)

    def set_DO_false(self):
        self._robot.io.digital.set_output(index=23, value=False)

    def set_DO_16_true(self):
        self._robot.io.digital.set_output(index=16, value=True)

    def set_DO_16_false(self):
        self._robot.io.digital.set_output(index=16, value=False)

    def set_DO_17_true(self):
        self._robot.io.digital.set_output(index=17, value=True)
        time.sleep(0.2)

    def set_DO_17_false(self):
        self._robot.io.digital.set_output(index=17, value=False)
        time.sleep(0.2)


if __name__ == "__main__":
    try:
        # --- ТЕСТ РОБОТА ---
        robot = RobotInterface('10.10.10.10')
        if robot.connect():
            # Тестируем чтение позы
            pose = robot.get_tcp_pose()
            print(f"Текущая поза робота: {pose}")

        else:
            print('Не удалось подключиться к роботу')

        print("-" * 40)

        # --- ТЕСТ КАМЕРЫ ---
        cam = ScapeCamera({'ip': None})

        # Сначала пытаемся подключиться
        ret, cam_info = cam.connect()
        if ret:
            # Если подключились, берем инфо
            print('cam_info:', cam_info)
        else:
            print('Не удалось подключиться к камере')

        robot.set_DO_17_true()
        time.sleep(3)
        robot.set_DO_17_false()

        cam_in_left = cam.get_intrinsic(cam_info, 'left')
        print(f'Внутренняя матрица (левая камера):\n {cam_in_left}')
        cam_in_right = cam.get_intrinsic(cam_info, 'right')
        print(f'Внутренняя матрица (правая камера):\n {cam_in_right}')
        cam_in_rgb = cam.get_intrinsic(cam_info, 'rgb')
        print(f'Внутренняя матрица (RGB камера):\n {cam_in_rgb}')

        cam_ex_left = cam.get_extrinsic(cam_info, 'left')
        print(f'Внешняя матрица (левая камера):\n {cam_ex_left}')
        cam_ex_right = cam.get_extrinsic(cam_info, 'right')
        print(f'Внешняя матрица (правая камера):\n {cam_ex_right}')
        cam_ex_rgb = cam.get_extrinsic(cam_info, 'rgb')
        print(f'Внешняя матрица (RGB камера):\n {cam_ex_rgb}')

        # save_dir = r"D:\Viacheslav\PycharmProjects\Hand-Eye-Calibration_GUI\src\model_segmentation"
        # os.makedirs(save_dir, exist_ok=True)
        # filename = "camera_calibration.npz"  # постоянное имя
        # # filename = f"camera_calibration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.npz"  # с временем
        #
        # filepath = os.path.join(save_dir, filename)
        #
        # # Собираем все матрицы
        # calibration_data = {
        #     'intrinsic_left': cam_in_left,
        #     'intrinsic_right': cam_in_right,
        #     'intrinsic_rgb': cam_in_rgb,
        #     'extrinsic_left': cam_ex_left,
        #     'extrinsic_right': cam_ex_right,
        #     'extrinsic_rgb': cam_ex_rgb,
        # }
        #
        # calibration_data = {k: v for k, v in calibration_data.items() if v is not None}
        #
        # # Сохраняем
        # np.savez(filepath, **calibration_data)
        #
        # print(f"✅ Все матрицы успешно сохранены в один файл:")
        # print(f"   → {filepath}")
        # print(f"   Ключей: {len(calibration_data)}")

    finally:
        cam.disconnect()
        robot.disconnect()
