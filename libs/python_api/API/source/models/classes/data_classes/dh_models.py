import re
from typing import Dict

from API.source.models.classes.data_classes.service_types import DhModelParams


class DhParamsManager(object):
    """
    Класс для хранения идеальных DH параметров для каждой модели робота.
    """

    _RC3_DH_PARAMS = DhModelParams(
        alpha=(1.570796, 0, 0, 1.570796, -1.570796, 0),
        a=(0, -0.35, -0.334, 0, 0, 0),
        d=(0.1765, 0.1445, -0.1398, 0.127, 0.127, 0.133),
        theta=(0, 0, 0, 0, 0, 0),
        offset=(0, 0, 0, 0, 0, 0),
    )

    _RC5_DH_PARAMS = DhModelParams(
        alpha=(1.570796, 0, 0, 1.570796, -1.570796, 0),
        a=(0, -0.405, -0.3722, 0, 0, 0),
        d=(0.1725, 0.156, -0.1485, 0.1398, 0.1398, 0.1398),
        theta=(0, 0, 0, 0, 0, 0),
        offset=(0, 0, 0, 0, 0, 0),
    )

    _RC10_DH_PARAMS = DhModelParams(
        alpha=(1.570796, 0, 0, 1.570796, -1.570796, 0),
        a=(0, -0.61, -0.5502, 0, 0, 0),
        d=(0.1685, 0.174, -0.1485, 0.1398, 0.1398, 0.1398),
        theta=(0, 0, 0, 0, 0, 0),
        offset=(0, 0, 0, 0, 0, 0),
    )

    _RC16_DH_PARAMS = DhModelParams(
        alpha=(1.570796, 0, 0, 1.570796, -1.570796, 0),
        a=(0, -0.47, -0.3402, 0, 0, 0),
        d=(0.1685, 0.174, -0.1485, 0.1398, 0.1398, 0.1398),
        theta=(0, 0, 0, 0, 0, 0),
        offset=(0, 0, 0, 0, 0, 0),
    )

    _MODEL_2_DH: Dict[str, DhModelParams] = {
        "rc3": _RC3_DH_PARAMS,
        "rc5": _RC5_DH_PARAMS,
        "rc10": _RC10_DH_PARAMS,
        "rc16": _RC16_DH_PARAMS,
    }

    @classmethod
    def get(cls, robot_model: str) -> DhModelParams:
        """
        ПОлучить DH параметры для указанной модели робота.
        """
        model = cls._get_robot_model_by_regex(robot_model)
        params = cls._MODEL_2_DH.get(model, DhModelParams())
        return params

    @staticmethod
    def _get_robot_model_by_regex(text: str) -> str:
        pattern = r"(rc3|rc5|rc10|rc16)"
        match = re.search(pattern, text)
        return match.group(0) if match else ""
