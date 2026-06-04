from typing import Optional

from API.source.core.exceptions.base_api_error import ApiError


class ConnectionError(ApiError):
    def __init__(self, message: str = ""):
        super().__init__(message)


class ServerConnectionError(ApiError):
    def __init__(self, socket: Optional[int] = None):
        if socket:
            self.message = (
                "Server connection failed. Specified port is unavailable."
            )
        else:
            self.message = (
                f"Server connection failed. [{socket}] port is unavailable."
            )
        super().__init__(self.message)


class ServerPingError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Server access denied"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class BrokenConnectionError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Socket connection is broken"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class EmptyPackageError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Received empty package from server"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ClientDisconnectedError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Client has been disconnected"
        if message:
            self.message = self.message + f" ({message})"
        super().__init__(self.message)


class ReadOnlyConnectionError(ApiError):
    def __init__(self, message: Optional[str] = None):
        self.message = "Method is not available in read only connection mode"
        if message:
            self.message = self.message + f", ({message})"
        super().__init__(self.message)
