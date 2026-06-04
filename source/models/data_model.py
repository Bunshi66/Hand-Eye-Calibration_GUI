from PyQt5.QtCore import QObject, pyqtSignal
from dataclasses import dataclass
import numpy as np
import json

@dataclass
class Waypoint:
    id: int
    joints: np.ndarray          # Суставные углы (массив)
    tcp_pose: np.ndarray        # Декартовы координаты (массив X, Y, Z, Rx, Ry, Rz)
    point_cloud: object = None  # Сюда позже будем сохранять 3D скан
    detect_error = None
    fitness = None
    enabled = True

class DataModel(QObject):
    # Сигналы для обновления интерфейса
    waypoint_added = pyqtSignal(object)  # Передаем весь объект Waypoint
    waypoint_updated = pyqtSignal(int)   # Передаем индекс (номер строки)
    waypoints_cleared = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._waypoints = []  # Список объектов Waypoint

    def add_waypoint(self, joints, tcp_pose):
        new_id = len(self._waypoints) + 1
        wp = Waypoint(id=new_id, joints=joints, tcp_pose=tcp_pose)
        self._waypoints.append(wp)
        self.waypoint_added.emit(wp)  # Кричим интерфейсу: "Отрисуй новую строку!"

    def update_waypoint_pose(self, row_index: int, new_joints, new_tcp_pose):
        """Вызывается, когда пользователь перезаписывает позу робота"""
        if 0 <= row_index < len(self._waypoints):
            # Обновляем координаты
            self._waypoints[row_index].joints = new_joints
            self._waypoints[row_index].tcp_pose = new_tcp_pose

            # ВАЖНО: Сбрасываем RMSE и скан, так как позиция изменилась!
            self._waypoints[row_index].detect_error = None
            self._waypoints[row_index].point_cloud = None

            # Сигналим интерфейсу: "Перерисуй эту строку!"
            self.waypoint_updated.emit(row_index)

    def update_detect_error_from_worker(self, wp_tuple):
        wp_index, detect_error = wp_tuple
        wp_index -= 1
        if 0 <= wp_index < len(self._waypoints):
            # 1. Изменяем объект
            self._waypoints[wp_index].detect_error = detect_error

            # 2. Оповещаем UI, что объект изменился. waypoint_id начинается с 1, row_id начинается с 0
            self.waypoint_updated.emit(wp_index)

    def get_all_waypoints(self):
        return self._waypoints

    def clear(self):
        self._waypoints.clear()
        self.waypoints_cleared.emit()

    def save_to_json(self, filepath: str):
        """Сохраняет текущие точки в JSON файл"""
        data_list = []
        for wp in self._waypoints:
            wp_dict = {
                "id": wp.id,
                "joints": wp.joints if wp.joints is not None else [],
                "tcp_pose": wp.tcp_pose if wp.tcp_pose is not None else []
            }
            data_list.append(wp_dict)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, indent=4)  # indent=4 делает файл красивым и читаемым

    def load_from_json(self, filepath: str):
        """Загружает точки из JSON файла"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data_list = json.load(f)

        # Очищаем текущую таблицу и список точек перед загрузкой новых
        self.clear()

        for item in data_list:
            # Превращаем списки обратно в массивы NumPy
            joints = np.array(item.get("joints", []))
            tcp_pose = np.array(item.get("tcp_pose", []))

            # Используем уже готовый метод add_waypoint,
            # который сам добавит точку и дернет сигнал для обновления UI
            self.add_waypoint(joints, tcp_pose)