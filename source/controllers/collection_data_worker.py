# controllers/calibration_worker.py

from PyQt5.QtCore import QObject, pyqtSignal, QThread
import time

class CollectionDataWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, waypoints, hardware_controller, data_model):
        super().__init__()
        self._waypoints = waypoints
        self._hardware = hardware_controller
        self._data_model = data_model
        self._is_running = True

    def stop(self):
        self._is_running = False

    def run(self):
        try:
            total = len(self._waypoints)

            for i, waypoint in enumerate(self._waypoints):

                if not self._is_running:
                    self.error.emit("Калибровка остановлена пользователем")
                    return

                # 1️⃣ Движение робота
                print(f'ЗАГЛУШКА: Движение робота в точку {waypoint.joints}')
                self._hardware.move_to_joints(waypoint.joints)

                # 2️⃣ Сканирование
                print(f'ЗАГЛУШКА: Снимок камеры')
                point_cloud = self._hardware.capture_frame()

                # 3️⃣ Сохранение в модель
                waypoint.point_cloud = point_cloud

                # 4️⃣ Обновление прогресса
                percent = int((i + 1) / total * 100)
                #QThread.msleep(1000)
                self.progress.emit(percent)

            self.progress.emit(100)
            self.finished.emit()

        except Exception as e:
            self.finished.emit()
            self.error.emit(str(e))