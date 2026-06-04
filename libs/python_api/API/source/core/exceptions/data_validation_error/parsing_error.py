from typing import Optional

from API.source.core.exceptions.base_api_error import ApiError


class CorruptedPackageError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Received corrupted package from server"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class CommandTypeError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Server command type validation failed"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class RTDParsingError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Can not parse RT data package"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)
