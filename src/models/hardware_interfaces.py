from abc import ABC, abstractmethod
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import ctypes
import logging
import json
import time
from src.utils.paths import *

from PyCameraSDK.GenericError import *
from PyCameraSDK.Camera import *
from PyCameraSDK.Common import *


# --- ИНТЕРФЕЙСЫ ---
class   ICamera(ABC):
    @abstractmethod
    def connect(self) -> bool: pass

    @abstractmethod
    def disconnect(self): pass

    @abstractmethod
    def capture(self) -> np.ndarray: pass


class IRobot(ABC):
    @abstractmethod
    def connect(self, ip: str) -> bool: pass

    @abstractmethod
    def get_pose(self) -> list: pass

    @abstractmethod
    def move_to(self, pose: list): pass


class ScapeCamera(ICamera):
    """Оболочка над SDK камеры SCAPE"""

    def __init__(self, connection_params: dict):
        """Инициализация и подключение к камере."""
        pass

    def connect(self) -> bool:
        """Установить соединение с камерой."""
        pass

    def disconnect(self):
        """Отключиться от камеры."""
        pass

    def is_connected(self) -> bool:
        """Проверка состояния подключения."""
        pass

    def capture(self) -> dict:
        """
        Returns: {
            'point_cloud': ...,  # numpy array Nx3 или Nx6 (с цветом)
            'image_2d': ...,     # numpy array HxWx3
            'depth_map': ...,    # numpy array HxW
            'timestamp': ...,
        }
        """
        pass

    def get_camera_info(self) -> dict:
        """Получить информацию о камере (модель, серийник, параметры)."""
        pass

    def get_intrinsics(self) -> dict:
        """Получить внутренние параметры камеры (матрица, дисторсия)."""
        pass

    def set_exposure(self, value: float):
        """Настройка экспозиции."""
        pass


class MockRobot(IRobot):
    def __init__(self):
        self._pose = [0, 0, 0, 0, 0, 0]

    def connect(self, ip: str) -> bool:
        print(f"Mock Robot connected at {ip}")
        return True

    def get_pose(self) -> list:
        # Эмуляция дрожания координат
        return [x + np.random.normal(0, 0.1) for x in self._pose]

    def move_to(self, pose: list):
        print(f"Robot moving to {pose}...")
        time.sleep(0.5)  # Имитация движения
        self._pose = pose


if __name__ == "__main__":
    pass