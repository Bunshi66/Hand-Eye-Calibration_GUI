import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
import json
import os

try:
    import open3d as o3d
except ImportError:
    o3d = None


class PointStatus(Enum):
    EMPTY = "Empty"
    CAPTURED = "Captured"
    ERROR = "Error"
    DISABLED = "Disabled"


@dataclass
class RobotPose:
    """Хранит координаты робота (Euler angles convention)."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    rx: float = 0.0  # Rotation X (Roll)
    ry: float = 0.0  # Rotation Y (Pitch)
    rz: float = 0.0  # Rotation Z (Yaw)

    def to_array(self) -> List[float]:
        return [self.x, self.y, self.z, self.rx, self.ry, self.rz]

    def __str__(self):
        return f"[{self.x:.2f}, {self.y:.2f}, {self.z:.2f}, {self.rx:.2f}, {self.ry:.2f}, {self.rz:.2f}]"


@dataclass
class CalibrationPoint:
    """
    Единица данных для калибровки.
    Управляет жизненным циклом данных (RAM vs Disk).
    """
    id: int
    target_pose: RobotPose  # Плановая поза

    # Фактические данные (заполняются после снимка)
    actual_pose: Optional[RobotPose] = None
    status: PointStatus = PointStatus.EMPTY

    # --- 2D Данные ---
    image_path: Optional[str] = None

    # --- 3D Данные ---
    point_cloud_path: Optional[str] = None

    # Поля для хранения ВРЕМЕННЫХ тяжелых объектов в памяти.
    # Они не должны попадать в JSON при сохранении проекта.
    _cached_image: Optional[np.ndarray] = field(default=None, repr=False)
    _cached_pcd: Optional[object] = field(default=None, repr=False)

    def is_captured(self) -> bool:
        return self.status == PointStatus.CAPTURED

    def clear_heavy_data(self):
        """Очищает оперативную память, оставляя только пути к файлам."""
        self._cached_image = None
        self._cached_pcd = None


@dataclass
class CalibrationDataset:
    points: List[CalibrationPoint] = field(default_factory=list)

    # Глобальные настройки, с которыми снимался этот датасет
    camera_settings: dict = field(default_factory=dict)

    def add_point(self, pose: RobotPose):
        new_id = len(self.points) + 1
        self.points.append(CalibrationPoint(id=new_id, target_pose=pose))

    def get_captured_points(self) -> List[CalibrationPoint]:
        return [p for p in self.points if p.status == PointStatus.CAPTURED]

    def clear_all_heavy_data(self):
        """Экстренная очистка памяти для всех точек."""
        for p in self.points:
            p.clear_heavy_data()