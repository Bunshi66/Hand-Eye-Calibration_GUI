from PyQt5.QtCore import QObject, pyqtSignal
import numpy as np
import open3d as o3d

class CalibrationModel(QObject):
    # Сигналы для UI
    calculation_started = pyqtSignal()
    calculation_finished = pyqtSignal(object, dict) # Передает (Матрицу 4x4, общие метрики)
    error_occurred = pyqtSignal(str)
    cad_model_recieved = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.transformation_matrix = np.eye(4)
        self.is_calibrated = False
        self._cad_path = None
        self._cad_mesh = None
        self._cad_pcd = None

    def set_results(self, matrix: np.ndarray, metrics: dict):
        self.transformation_matrix = matrix
        self.is_calibrated = True
        self.calculation_finished.emit(self.transformation_matrix, metrics)

    def set_cad_path(self, path: str):
        self._cad_path = path

        mesh = o3d.io.read_triangle_mesh(self._cad_path)

        if mesh.is_empty():
            # Если не меш, пробуем как облако точек (PLY/PCD)
            self._cad_pcd = o3d.io.read_point_cloud(self._cad_path)
            self._cad_mesh = None  # Для облака точек треугольников нет

            if self._cad_pcd.is_empty():
                raise RuntimeError(f"Не удалось загрузить CAD модель: {self._cad_path}")
        else:
            self._cad_mesh = mesh
            # Сэмплим точки для ICP сразу при загрузке
            self._cad_pcd = mesh.sample_points_uniformly(number_of_points=50000)

        self._cad_pcd.estimate_normals()

        points_np = np.asarray(self._cad_pcd.points)

        # 2. Извлекаем цвета, если они есть (например, формат PLY поддерживает цвета)
        if self._cad_pcd.has_colors():
            # Open3D хранит цвета в формате RGB от 0.0 до 1.0
            colors_np = np.asarray(self._cad_pcd.colors)
        else:
            colors_np = None

        result = {
            'points': points_np,
            'colors': colors_np
        }

        # Эмитим сигнал (кстати, грамматически правильно received, а не recieved,
        # но если сигнал назван так, оставляем твое название)
        self.cad_model_recieved.emit(result)
        # print("CAD модель загружена и отправлена в UI.")

    def get_cad_path(self):
        return self._cad_path

    # def get_render_data(self):
    #     """Отдает вершины и полигоны для pyqtgraph (UI)"""
    #     if self._cad_mesh is not None:
    #         # Преобразуем векторы Open3D в массивы numpy, понятные для pyqtgraph
    #         vertices = np.asarray(self._cad_mesh.vertices)
    #         faces = np.asarray(self._cad_mesh.triangles)
    #         return vertices, faces
    #     return None, None

    def get_render_data(self):
        points_np = np.asarray(self._cad_pcd.points)

        # 2. Извлекаем цвета, если они есть (например, формат PLY поддерживает цвета)
        if self._cad_pcd.has_colors():
            # Open3D хранит цвета в формате RGB от 0.0 до 1.0
            colors_np = np.asarray(self._cad_pcd.colors)
        else:
            colors_np = None

        result = {
            'points': points_np,
            'colors': colors_np
        }

        self.cad_model_recieved.emit(result)
        # print("CAD модель отправлена в UI (Show CAD).")

    def get_cad_pcd(self):
        """Отдает готовое облако точек для Worker'a"""
        return self._cad_pcd