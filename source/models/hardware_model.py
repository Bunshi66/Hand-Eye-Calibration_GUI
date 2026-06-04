from PyQt5.QtCore import QObject, pyqtSignal

class RobotModel(QObject):
    connected = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_connected = False
        self._ip = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @is_connected.setter
    def is_connected(self, state: bool):
        if self._is_connected != state:
            self._is_connected = state
            # Автоматически оповещаем UI об изменении статуса
            self.connected.emit(self._is_connected)

    @property
    def ip(self) -> str:
        return self._ip

    @ip.setter
    def ip(self, value: str):
        self._ip = value


class CameraModel(QObject):
    connected = pyqtSignal(bool)
    frame_received = pyqtSignal(object)   # numpy.ndarray
    error_occurred = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._is_connected = False
        self._camera_info = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @is_connected.setter
    def is_connected(self, state: bool):
        if self._is_connected != state:
            self._is_connected = state
            self.connected.emit(self._is_connected)

    @property
    def camera_info(self):
        return self._camera_info

    @camera_info.setter
    def camera_info(self, info):
        self._camera_info = info