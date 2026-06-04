from typing import Optional

from API.source.core.exceptions.base_api_error import ApiError


class ArgSignError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect sign selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgUnitsError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect units of measurement selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgPositionFormatError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect type of position format selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgValueError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect value selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgControllerStateError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect controller state selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgMotionModeError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect motion mode selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgSafetyStatusError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect safety status selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArrayLengthError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect array length"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgInputFunctionError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect input function selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgOutputFunctionError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect output function selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ArgToolModeError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect tool mode selected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class WristOutputActivationTypeError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Incorrect wrist output activation type"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)
