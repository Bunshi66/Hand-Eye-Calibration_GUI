from dataclasses import dataclass
from typing import NamedTuple, Tuple


class JointAngleDiscrepancy(NamedTuple):
    """
    Класс для передачи информации о расхождении сохраненного положения звена с
    реальным положением.

    Args:
        joint_number: номер звена считая от основания;
        allowed_discrepancy: допустимое рассогласование углов (deg);
        actual_position: снимаемое с привода положение (deg);
        saved_position: сохраненная в контроллере позиция (deg).
    """

    joint_number: int = 0
    allowed_discrepancy: float = 0
    actual_position: float = 0
    saved_position: float = 0


@dataclass
class DhModelParams:
    """
    Класс для представления информации о DH параметрах робота.

    Args:
        alpha: угол скручивания (rad);
        a: длина звена (m);
        d: смещение звена (m);
        theta: угол сочленения (rad);
        offset: смещение нулевого положения звена (rad).
    """

    alpha: Tuple[float, ...] = (0,) * 6
    a: Tuple[float, ...] = (0,) * 6
    d: Tuple[float, ...] = (0,) * 6
    theta: Tuple[float, ...] = (0,) * 6
    offset: Tuple[float, ...] = (0,) * 6
