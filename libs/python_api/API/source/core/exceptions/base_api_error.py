class ApiError(Exception):
    """
    Базовое исключение API. Все остальные исключения наследуются от него.
    """

    def __init__(self, message: str = ""):
        self._message = message
        super().__init__(self._message)

    def get_message(self) -> str:
        return self._message
