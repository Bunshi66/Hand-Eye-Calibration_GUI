from enum import Enum, auto
from PyQt5.QtCore import QObject, pyqtSignal

class UserRole(Enum):
    OPERATOR = auto()
    ENGINEER = auto()
    ADMIN = auto()

class AuthModel(QObject):
    # Сигнал: испускается, когда роль изменилась
    role_changed = pyqtSignal(UserRole)

    def __init__(self, initial_role=UserRole.OPERATOR):
        super().__init__()
        self._role = initial_role

    @property
    def role(self) -> UserRole:
        return self._role

    @role.setter
    def role(self, new_role: UserRole):
        if self._role != new_role:
            self._role = new_role
            # Уведомляем весь код, что права изменились
            self.role_changed.emit(self._role)