from PyQt5.QtCore import QObject, pyqtSignal, QThread
import numpy as np
import cv2
from scipy.spatial.transform import Rotation as R
import open3d as o3d

class CalibrationWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)
    # Теперь success возвращает словарь: {"TSAI": np.array(4x4), "PARK": np.array(4x4), ...}
    success = pyqtSignal(dict)
    detect_error = pyqtSignal(tuple)


    def __init__(self, waypoints, calib_type, calib_model):
        super().__init__()
        self._calib_model = calib_model
        self._waypoints = waypoints
        self._calib_type = calib_type
        self._cad_pcd = None
        self._cad_path = None

    def _prepare_cad_model(self):
        """Просто забирает готовое облако точек из Модели"""
        self._cad_pcd = self._calib_model.get_cad_pcd()

        if self._cad_pcd is None or self._cad_pcd.is_empty():
            raise ValueError("CAD модель не загружена. Пожалуйста, выберите файл.")

        # Нормали и даунсэмплинг уже сделаны в CalibModel при загрузке!
        print("Воркер получил CAD модель из памяти.")

    # def _load_cad_model(self):
    #     """Загружает CAD файл и готовит его для ICP"""
    #     self._cad_path = self._calib_model.get_cad_path()
    #
    #     if not self._cad_path:
    #         raise ValueError("Путь к CAD файлу не указан.")
    #
    #     # Загружаем меш (STL/OBJ/PLY)
    #     mesh = o3d.io.read_triangle_mesh(self._cad_path)
    #     if mesh.is_empty():
    #         # Если не меш, пробуем загрузить как облако точек (PLY/PCD)
    #         self._cad_pcd = o3d.io.read_point_cloud(self._cad_path)
    #     else:
    #         # Если это меш, сэмплим из него облако точек (например, 10 000 точек)
    #         self._cad_pcd = mesh.sample_points_uniformly(number_of_points=10000)
    #
    #     if self._cad_pcd.is_empty():
    #         raise RuntimeError(f"Не удалось загрузить CAD модель из {self._cad_path}")
    #
    #     # Полезно сделать предварительную обработку (нормали, даунсэмплинг)
    #     self._cad_pcd.estimate_normals()
    #     print("CAD модель успешно загружена и подготовлена.")

    def run(self):
        try:
            self.progress.emit(0)
            self._prepare_cad_model()
            self.progress.emit(10)

            # Списки для OpenCV
            R_gripper2base, t_gripper2base = [], []
            R_target2cam, t_target2cam = [], []

            total = len(self._waypoints)

            for i, wp in enumerate(self._waypoints):
                print(f'[DEBUG] Обрабатываю точку {wp.id}. Проверка наличия точек в облаке ')
                # if wp.point_cloud is None:
                #     print(f'Облако не содержит точек')
                #     continue

                # ----------------------------------------------------
                # 1. Пытаемся найти паттерн (target2cam)
                # ----------------------------------------------------
                H_target2cam = self._compute_target2cam(wp)
                QThread.msleep(1000)

                # Если алгоритм не нашел шаблон (засветка, обрезано) - ПРОПУСКАЕМ ЭТУ ПОЗУ
                if H_target2cam is None:
                    print(f"Паттерн не найден на позе ID: {wp.id}. Точка исключена.")
                    continue

                    # ----------------------------------------------------
                # 2. Если шаблон найден, берем позу робота (gripper2base)
                # ----------------------------------------------------
                H_robot = self._compute_robot_pose(wp.tcp_pose)

                # ----------------------------------------------------
                # 3. Конвертируем в векторы для OpenCV и добавляем в списки
                # ----------------------------------------------------
                # Камера
                r_cam, _ = cv2.Rodrigues(H_target2cam[:3, :3])
                R_target2cam.append(r_cam)
                t_target2cam.append(H_target2cam[:3, 3].reshape(3, 1))

                # Робот
                r_rob, _ = cv2.Rodrigues(H_robot[:3, :3])
                R_gripper2base.append(r_rob)
                t_gripper2base.append(H_robot[:3, 3].reshape(3, 1))

                percent = int((i + 1) / total * 80)
                self.progress.emit(percent)

            # Проверка, что точек достаточно
            valid_points = len(R_target2cam)
            if valid_points < 3:
                raise ValueError(
                    f"Запустите сбор калибрвоочных данных!\n Собрано поз ({valid_points} из {len(self._waypoints)}). Нужно минимум 3.")

            self.progress.emit(90)

            # ----------------------------------------------------
            # 4. Запуск всех методов калибровки
            # ----------------------------------------------------
            calibration_methods = {
                'TSAI': cv2.CALIB_HAND_EYE_TSAI,
                'PARK': cv2.CALIB_HAND_EYE_PARK,
                'HORAUD': cv2.CALIB_HAND_EYE_HORAUD,
                'ANDREFF': cv2.CALIB_HAND_EYE_ANDREFF,
                'DANIILIDIS': cv2.CALIB_HAND_EYE_DANIILIDIS
            }

            all_results = {}

            for method_name, method_code in calibration_methods.items():
                try:
                    # Для Eye-in-Hand: R_gripper2base, R_target2cam
                    # Для Eye-to-Hand: R_base2gripper, R_target2cam
                    # (Инверсия для Eye-to-Hand уже сделана в методе _compute_robot_pose!)
                    R_res, t_res = cv2.calibrateHandEye(
                        R_gripper2base, t_gripper2base,
                        R_target2cam, t_target2cam,
                        method=method_code
                    )

                    # Собираем гомогенную матрицу 4x4
                    T_res = np.identity(4)
                    T_res[:3, :3] = R_res
                    T_res[:3, 3] = t_res.flatten()

                    all_results[method_name] = T_res

                except cv2.error as e:
                    print(f"ОШИБКА OpenCV при калибровке {method_name}: {e}")
                    # Не прерываем цикл, просто не добавляем этот метод в словарь

            if not all_results:
                raise RuntimeError("Все методы OpenCV завершились с ошибкой.")

            self.progress.emit(100)
            self.success.emit(all_results)  # Возвращаем словарь со всеми матрицами!
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit()

    # ====================================================
    # Вспомогательные математические методы
    # ====================================================

    def _compute_robot_pose(self, tcp_pose: np.ndarray) -> np.ndarray:
        """Переводит TCP [X,Y,Z, Rx,Ry,Rz] в матрицу 4x4 с учетом типа калибровки"""
        x, y, z, rx, ry, rz = tcp_pose
        #TODO: Проверить что [x, y, z] в мм

        # ВНИМАНИЕ: Проверьте порядок углов вашего робота (например 'xyz', 'zyx')
        rot_matrix = R.from_euler('xyz', [rx, ry, rz], degrees=True).as_matrix()

        H = np.eye(4)
        H[:3, :3] = rot_matrix
        H[:3, 3] = [x, y, z]

        if self._calib_type == "Eye-to-Hand":
            # Для Eye-to-Hand OpenCV ожидает R_base2gripper (инверсия)
            return np.linalg.inv(H)

        # Для Eye-in-Hand отдаем как есть (R_gripper2base)
        return H

    def _compute_target2cam(self, waypoint):
        """
        Сопоставляет скан со сканера (scan_array) с CAD-моделью (self._cad_pc)
        """
        print(f'ЗАШЛУШКА! вычисление позы шаблона для точки {waypoint.id}')
        import random
        self.detect_error.emit((waypoint.id, random.uniform(0.01, 0.3)))

        return np.eye(4)
        try:
            # 1. Конвертируем numpy скан в объект Open3D
            point_cloud = waypoint.point_cloud
            scan_pcd = o3d.geometry.PointCloud()
            scan_pcd.points = o3d.utility.Vector3dVector(point_cloud)

            # Предварительная обработка скана
            scan_pcd.estimate_normals()
            print('Предобработка скана завершена')

            # 2. Грубое совмещение (Global Registration / RANSAC)
            # Здесь вы вставите свой вызов RANSAC.
            # Для примера возьмем начальное предположение (Identity)
            initial_trans = np.eye(4)

            # 3. Тонкое совмещение (ICP)
            # threshold - максимальное расстояние между точками для соответствия
            threshold = 10.0 # мм
            print('Пытаюсь выполнить ICP регистрацию')
            reg_p2p = o3d.pipelines.registration.registration_icp(
                self._cad_pcd, scan_pcd, threshold, initial_trans,
                o3d.pipelines.registration.TransformationEstimationPointToPlane()
            )
            print(f'Выполнена ICP регистрация: fitness ({reg_p2p.fitness})')
            # 4. Проверка качества (Fitness)
            # Если совпадение меньше, например, 60%, считаем, что деталь не найдена
            if reg_p2p.fitness < 0.6:
                print(f'ICP регистрация: не пройден порог fitness')
                return None

            return reg_p2p.transformation

        except Exception as e:
            print(f"Ошибка ICP: {e}")
            return None

    def remove_table_plane(pcd: o3d.geometry.PointCloud,
                           dist_threshold=0.003,
                           ransac_n=3,
                           num_iterations=2000,
                           above_eps=4.5,
                           container_band_min=68.5,
                           container_band_max=71.5):
        # --- 1. Находим плоскость ---
        plane_model, inliers = pcd.segment_plane(
            distance_threshold=dist_threshold,
            ransac_n=ransac_n,
            num_iterations=num_iterations
        )

        a, b, c, d = plane_model
        normal = np.array([a, b, c])
        normal = normal / np.linalg.norm(normal)

        print(
            f"Найдена плоскость: {a:.4f}x + {b:.4f}y + {c:.4f}z + {d:.4f} = 0"
        )

        # --- 2. Разворачиваем нормаль к камере ---
        camera_origin = np.array([0.0, 0.0, 0.0])

        if (camera_origin @ normal + d) < 0:
            normal = -normal
            d = -d

        print(
            f"Стол: нормаль = [{normal[0]:.4f}, "
            f"{normal[1]:.4f}, {normal[2]:.4f}], d = {d:.4f}"
        )

        # --- 3. Высоты над столом ---
        points = np.asarray(pcd.points)
        distances = points @ normal + d  # высота точки над столом

        # --- 4. Всё над столом ---
        mask_above = distances > above_eps
        indices_above = np.where(mask_above)[0]
        pcd_above_table = pcd.select_by_index(indices_above)

        print(
            f"Удалено точек стола и ниже: "
            f"{len(points) - len(indices_above)}"
        )

        # --- 5. Формируем облако контейнерного диапазона ---
        pcd_container_band = None

        if container_band_max is not None:
            mask_band = (
                    (distances > container_band_min) &
                    (distances < container_band_max)
            )

            indices_band = np.where(mask_band)[0]
            pcd_container_band = pcd.select_by_index(indices_band)

            print(
                f"Точек в контейнерном диапазоне: {len(indices_band)}"
            )
        print(f'pcd_above_table - {type(pcd_above_table)}; pcd_container_band - {type(pcd_container_band)}')

        # geom = [pcd_above_table, pcd_container_band]
        # vizu = RegistrationVisualizer(geometries=geom)
        # vizu.run()

    def estimate_calib_plate_pose(self):
        H = np.eye(4)
        return H