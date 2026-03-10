from abc import ABC, abstractmethod
import numpy as np
import time


# --- ИНТЕРФЕЙСЫ ---
class   ICamera(ABC):
    @abstractmethod
    def connect(self) -> bool: pass

    @abstractmethod
    def disconnect(self): pass

    @abstractmethod
    def get_frame(self) -> np.ndarray: pass


class IRobot(ABC):
    @abstractmethod
    def connect(self, ip: str) -> bool: pass

    @abstractmethod
    def get_pose(self) -> list: pass

    @abstractmethod
    def move_to(self, pose: list): pass


# --- ЗАГЛУШКИ (MOCKS) ---
class ScapeCamera(ICamera):
    def connect(self) -> bool:
        print("Mock Camera Connected")
        return True

    def disconnect(self):
        print("Mock Camera Disconnected")

    def get_frame(self) -> np.ndarray:
        # Генерируем шум или градиент для теста
        # Возвращаем черную картинку 640x480 с бегущей полосой
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        t = int(time.time() * 100) % 640
        img[:, t:t + 10] = (0, 255, 0)  # Зеленая полоса
        return img


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