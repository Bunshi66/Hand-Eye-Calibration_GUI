from typing import Optional

from API.source.core.exceptions.base_api_error import ApiError


class FunctionTimeOutError(ApiError):
    def __init__(
        self,
        error_target: str = "",
        timeout_sec: float = 0,
        message: Optional[str] = None,
    ):
        self.message = f"{error_target} did not change in {timeout_sec} sec. "
        if message:
            self.message += message
        super().__init__(self.message)
