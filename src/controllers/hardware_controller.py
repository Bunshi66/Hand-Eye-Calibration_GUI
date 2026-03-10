from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
import cv2
from src.models.hardware_interfaces import ICamera, ScapeCamera, IRobot, MockRobot


class HardwareController(QObject):
    # Сигналы для обновления UI
    on_frame_received = pyqtSignal(QPixmap)  # Готовая картинка для QLabel
    on_robot_status_changed = pyqtSignal(bool)
    on_camera_status_changed = pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.camera: ICamera = None
        self.robot: IRobot = None

        # Таймер для опроса камеры (30 FPS)
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_loop)

        # Пока используем заглушки
        self.camera = ScapeCamera()
        self.robot = MockRobot()

    def connect_camera(self):
        # Тут логика выбора реальной камеры, пока Mock
        if self.camera.connect():
            self.on_camera_status_changed.emit(True)
            self.timer.start(33)  # ~30 FPS

    def connect_robot(self):
        # Тут логика выбора реального робота, пока Mock
        if self.robot.connect("127.0.0.1"):
            self.on_robot_status_changed.emit(True)

    def _update_loop(self):
        """Вызывается по таймеру."""
        if self.camera:
            frame = self.camera.get_frame()
            if frame is not None:
                # Конвертация CV2 (BGR) -> Qt (RGB)
                rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgb_image.shape
                bytes_per_line = ch * w
                qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
                self.on_frame_received.emit(QPixmap.fromImage(qt_img))

    def get_robot_pose(self):
        if self.robot:
            return self.robot.get_pose()
        return [0] * 6