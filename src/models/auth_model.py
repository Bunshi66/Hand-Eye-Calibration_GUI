from enum import Enum, auto

class UserRole(Enum):
    OPERATOR = auto()
    ENGINEER = auto()
    ADMIN = auto()

class CurrentUser:
    """Хранит состояние текущего уровня доступа."""
    def __init__(self, role: UserRole):
        self.role = role

    def __repr__(self):
        return f"AccessLevel({self.role.name})"