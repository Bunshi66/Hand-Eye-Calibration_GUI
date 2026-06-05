from PyQt5.QtCore import QObject, QThread, pyqtSignal

import numpy as np
import json

from source.controllers.collection_data_worker import CollectionDataWorker
from source.controllers.calibration_worker import CalibrationWorker

class DataController(QObject):
    progress_update = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    progress_finished = pyqtSignal()
    calib_success = pyqtSignal(dict)
    #detect_error_calculated = pyqtSignal(tuple)

    def __init__(self, data_model, hw_controller, calib_model):
        super().__init__()
        self.data_model = data_model
        self.hw_controller = hw_controller
        self.calib_model = calib_model
        self._thread = None
        self._worker = None

    def set_cad_path(self, cad_path):
        self.calib_model.set_cad_path(cad_path)


    def show_cad_pcd(self):
        if not self.calib_model.get_cad_path():
            self.error_occurred.emit("CAD модель не загружена")
            return

        try:
            self.calib_model.get_pcd_data()
        except Exception as e:
            self.error_occurred.emit("Ошибка при отображении CAD модели")

    def show_cad_mesh(self):
        if not self.calib_model.get_cad_path():
            self.error_occurred.emit("CAD модель не загружена")
            return

        try:
            self.calib_model.get_mesh_data()
        except Exception as e:
            self.error_occurred.emit("Ошибка при отображении CAD модели")

    def start_calibration(self, calib_type):
        waypoints = self.data_model.get_all_waypoints()

        if not waypoints:
            self.error_occurred.emit(f"Невозможно начать калибровку {calib_type}: Недостаточное кол-во поз!")
            return

        self._thread = QThread()
        self._worker = CalibrationWorker(
            waypoints=waypoints,
            calib_type=calib_type,
            calib_model=self.calib_model
        )
        self._worker.moveToThread(self._thread)

        # signals
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._worker.progress.connect(self.progress_update)
        self._worker.error.connect(self.error_occurred)
        self._worker.finished.connect(self.progress_finished)
        self._worker.success.connect(self.calib_success)
        self._worker.detect_error.connect(self.data_model.update_detect_error_from_worker)

        self._thread.start()

    def start_collecting_data(self):

        if not self.hw_controller.is_robot_connected():
            self.error_occurred.emit("Невозможно начать калибровку: Робот не подключен!")
            return

        if not self.hw_controller.is_camera_connected():
            self.error_occurred.emit("Невозможно начать калибровку: Камера не подключена!")
            return

        # 2️⃣ Проверка наличия поз
        waypoints = self.data_model.get_all_waypoints()

        if not waypoints:
            self.error_occurred.emit("Невозможно начать калибровку: Недостаточное кол-во поз!")
            return

        self._thread = QThread()
        self._worker = CollectionDataWorker(
            waypoints,
            self.hw_controller,
            self.data_model
        )

        self._worker.moveToThread(self._thread)

        # signals
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._worker.progress.connect(self.progress_update)
        self._worker.error.connect(self.error_occurred)
        self._worker.finished.connect(self.progress_finished)

        self._thread.start()

    def stop_collecting_data(self):
        if self._worker:
            self._worker.stop()

    def record_current_pose(self):
        """Считывает текущую позицию робота и добавляет новую позу"""
        if not self.hw_controller.is_robot_connected():
            self.data_model.error_occurred.emit("Невозможно добавить позу: Робот не подключен!")
            return

        try:
            joints = self.hw_controller.get_current_pose_joints()
            tcp_pose = self.hw_controller.get_current_pose_linear()

            # joints = np.array([0.0, -90.0, 90.0, 0.0, 90.0, 0.0])
            # tcp_pose = np.array([400.0, 100.5, 300.0, 180.0, 0.0, 45.0])

            self.data_model.add_waypoint(joints, tcp_pose)

        except Exception as e:
            self.data_model.error_occurred.emit(f"Ошибка при чтении позы: {str(e)}")

    def update_current_pose(self, row_index: int):
        """Перезаписывает выбранную позу текущими координатами робота"""
        if not self.hw_controller.is_robot_connected():
            self.data_model.error_occurred.emit("Робот не подключен!")
            return

        try:
            # ЗАМЕНИТЕ НА РЕАЛЬНЫЕ МЕТОДЫ
            joints = self.hw_controller.get_current_pose_joints()
            tcp_pose = self.hw_controller.get_current_pose_linear()

            # Эмуляция:
            # joints = np.array([10.0, -80.0, 80.0, 0.0, 90.0, 0.0])
            # tcp_pose = np.array([410.0, 120.0, 310.0, 180.0, 0.0, 45.0])

            self.data_model.update_waypoint_pose(row_index, joints, tcp_pose)
        except Exception as e:
            self.data_model.error_occurred.emit(f"Ошибка обновления позы: {str(e)}")

    def move_to_waypoint(self, row_index: int):
        """Отправляет робота в ранее сохраненную позицию"""
        if not self.hw_controller.is_robot_connected():
            self.data_model.error_occurred.emit("Робот не подключен!")
            return

        waypoints = self.data_model.get_all_waypoints()
        if 0 <= row_index < len(waypoints):
            target_joints = waypoints[row_index].joints

            try:
                # ЗАМЕНИТЕ НА РЕАЛЬНЫЙ МЕТОД ДВИЖЕНИЯ ВАШЕГО РОБОТА
                # Внимание: для реальной работы нужен отдельный поток (QThread)
                self.hw_controller.move_to_joints(target_joints)
                print(f"Робот поехал к точке: {row_index}")
            except Exception as e:
                self.data_model.error_occurred.emit(f"Ошибка движения: {str(e)}")

    def clear_waypoints(self):
        self.data_model.clear()

    def save_poses(self, filepath: str):
        try:
            self.data_model.save_to_json(filepath)
            print(f"Маршрут успешно сохранен в: {filepath}")
        except Exception as e:
            self.data_model.error_occurred.emit(f"Ошибка при сохранении файла: {str(e)}")

    def load_poses(self, filepath: str):
        try:
            self.data_model.load_from_json(filepath)
            print(f"Маршрут успешно загружен из: {filepath}")
        except json.JSONDecodeError:
            self.data_model.error_occurred.emit("Файл поврежден или не является валидным JSON.")
        except Exception as e:
            self.data_model.error_occurred.emit(f"Ошибка при загрузке файла: {str(e)}")