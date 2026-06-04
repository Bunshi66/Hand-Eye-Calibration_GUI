from typing import Optional, Tuple

from API.source.core.exceptions.base_api_error import ApiError
from API.source.models.classes.data_classes.service_types import (
    JointAngleDiscrepancy,
)
from API.source.models.constants import TAB, TNL


class RobotCalibrationPositionError(ApiError):
    def __init__(self, pos_info: Tuple[JointAngleDiscrepancy]):
        """
        Ошибка рассогласования углов поворотов моторов.

        Args:
            pos_info: Информация о позициях звеньев, представленная в виде кортежа
                из объектов дата-класса JointAngleDiscrepancy.
        """

        self.message = "Robot position discrepancy. Manual calibration needed"
        rows = []
        for joint in pos_info:
            rows.append(
                f"{TNL}    Joint {joint.joint_number}: [Saved: {joint.saved_position:.3f},"
                f"{TAB}Actual:{joint.actual_position:.3f}]"
            )
        self.message += (
            f"{TNL}Discrepancy between the current and last saved positions "
            f"is more than {pos_info[0].allowed_discrepancy:.1f} degrees:\n"
            f"{''.join(rows)}"
        )

        super().__init__(self.message)


class SavedPositionError(ApiError):
    def __init__(self, message: str = ""):
        super().__init__(message)


class CalculatePlaneError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Failed to calculate plane using three points"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class FunctionTimeOutError(ApiError):
    def __init__(
        self,
        error_target: str = "",
        timeout_sec: float = 0,
        message: Optional[str] = None,
    ):
        self.message = f"{error_target} did not change in {timeout_sec} sec"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class AddWaypointError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Failed to add the waypoint"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class WristStateError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Wrist in off state. Check connection"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class WristAIOUnitsNotSet(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Failed to set analog inputs units"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)
