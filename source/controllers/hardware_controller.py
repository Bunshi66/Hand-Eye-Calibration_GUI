from Cython.Plex.Actions import Return
from PyQt5.QtCore import QObject
import numpy as np
import open3d as o3d
# Импортируйте ваши низкоуровневые классы
from source.hardware.robot_interface import RobotInterface
from source.hardware.scape_camera import ScapeCamera

class HardwareController(QObject):
    def __init__(self, robot_model, camera_model):
        super().__init__()
        self.robot_model = robot_model
        self.camera_model = camera_model

        # Экземпляры низкоуровневых драйверов
        self.robot_interface = RobotInterface()
        self.camera_interface = ScapeCamera()

    def connect_robot(self, ip_address: str):
        """Вызывается из UI, когда пользователь жмет 'Подключить робота'"""
        try:
            ret = self.robot_interface.connect(ip_address) # Ваш низкоуровневый вызов

            if ret:
                self.robot_model.ip = ip_address
                self.robot_model.is_connected = True  # Это автоматически вызовет emit(True)
                print(f"Робот подключен по IP: {ip_address}")
            else:
                raise ConnectionError(f"Робот IP {ip_address} не ответил или отклонил запрос.")
        except Exception as e:
            self.robot_model.error_occurred.emit(f"Ошибка подключения робота: {str(e)}")
            self.robot_model.is_connected = False

    def connect_camera(self, ip_address):
        """Вызывается из UI для подключения 3D камеры"""
        try:
            ret, camera_info = self.camera_interface.connect(ip_address)

            if ret:
                self.camera_model.camera_info = camera_info
                self.camera_model.is_connected = True  # Вызовет emit(True)
                print("3D Камера подключена")
            else:
                raise ConnectionError(f"Камера IP {ip_address} не ответила или отклонила запрос.")
        except Exception as e:
            self.camera_model.error_occurred.emit(f"Ошибка камеры: {str(e)}")
            self.camera_model.is_connected = False

    def disconnect_robot(self):
        """Вызывается из UI, когда пользователь жмет 'Подключить робота'"""
        try:
            #TODO: Отключаемся от робота, без конкретного ip
            self.robot_interface.disconnect()

            self.robot_model.ip = None
            self.robot_model.is_connected = False
            print(f"Робот отключен")

        except Exception as e:
            self.robot_model.error_occurred.emit(f"Ошибка отключения робота: {str(e)}")
            #self.robot_model.is_connected = False

    def disconnect_camera(self):
        """Вызывается из UI для подключения 3D камеры"""
        try:
            self.camera_interface.disconnect()

            self.camera_model.camera_info = None
            self.camera_model.is_connected = False
            print("3D Камера отключена")

        except Exception as e:
            self.camera_model.error_occurred.emit(f"Ошибка камеры: {str(e)}")
            #self.camera_model.is_connected = False

    def move_to_joints(self, joints):
        #return
        if not self.is_robot_connected():
            raise ConnectionError("Робот отключен во время движения")
        try:
            self.robot_interface.move_to_joints_deg(joints)
        except Exception as e:
            raise RuntimeError(f"Ошибка движения: {e}")

    def capture_frame(self):
        #return
        if not self.is_camera_connected():
            raise ConnectionError("Камера отключена во время сканирования")
        try:
            return self.camera_interface.get_frame()['points']
        except Exception as e:
            raise RuntimeError(f"Ошибка захвата: {e}")

    def get_current_pose_joints(self):
        return self.robot_interface.get_joint_angles()

    def get_current_pose_linear(self):
        return self.robot_interface.get_tcp_pose()

    def toggle_robot_connection(self, ip_address: str):
        """Решает, что делать с роботом, в зависимости от текущего статуса"""
        if self.robot_model.is_connected:
            self.disconnect_robot()
        else:
            self.connect_robot(ip_address)

    def toggle_camera_connection(self, ip_address: str):
        if self.camera_model.is_connected:
            self.disconnect_camera()
        else:
            self.connect_camera(ip_address)

    def trigger_test_shot(self):
        """Запрос скана от камеры, с отображением ТОЛЬКО облака точек в UI"""

        if not self.camera_model.is_connected:
            self.camera_model.error_occurred.emit("Камера не подключена!")
            return

        try:
            # --- ВАРИАНТ 1: Загрузка реального файла PLY/PCD ---
            #print("Выполняется тестовый скан (заглушка)...")
            # file_path = r"D:\Viacheslav\PycharmProjects\Hand-Eye-Calibration_GUI\src\data\LOCAL_data_2026-05-10_14-29-56\camera_scans\step_000_points.ply"
            # pcd = o3d.io.read_point_cloud(file_path)
            # pcd = pcd.voxel_down_sample(voxel_size=1.0)
            # points = np.asarray(pcd.points)

            frame_data = self.camera_interface.get_frame()

            self.camera_model.frame_received.emit(frame_data)

        except Exception as e:
            self.camera_model.error_occurred.emit(f"Ошибка тестового скана: {str(e)}")

    def is_robot_connected(self):
        return self.robot_model.is_connected

    def is_camera_connected(self):
        return self.camera_model.is_connected