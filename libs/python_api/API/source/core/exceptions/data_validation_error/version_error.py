from typing import Optional

from API.source.core.exceptions.base_api_error import ApiError


class VersionError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "The client does not match the server version"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ControllerUnlockError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Server access denied"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)
