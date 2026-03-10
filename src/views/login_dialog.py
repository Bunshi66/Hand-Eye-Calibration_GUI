from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QComboBox,
                             QPushButton, QLineEdit, QMessageBox)
from src.models.auth_model import UserRole


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Выбор режима работы")
        self.setFixedSize(300, 180)
        self.selected_role = None

        # Простая база паролей для примера
        self._passwords = {
            UserRole.OPERATOR: "",  # Без пароля
            UserRole.ENGINEER: "123",
            UserRole.ADMIN: "admin"
        }

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()

        # Выбор роли
        layout.addWidget(QLabel("Режим доступа:"))
        self.role_combo = QComboBox()
        for role in UserRole:
            self.role_combo.addItem(role.name, role)

        self.role_combo.currentIndexChanged.connect(self._on_role_changed)
        layout.addWidget(self.role_combo)

        # Поле пароля
        layout.addWidget(QLabel("Пароль:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)  # Скрываем символы
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEnabled(False)  # Для оператора сразу выключено
        layout.addWidget(self.password_input)

        # Кнопка входа
        self.login_btn = QPushButton("Войти")
        self.login_btn.clicked.connect(self._on_login_clicked)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def _on_role_changed(self):
        """Включает или выключает поле пароля в зависимости от роли."""
        role = self.role_combo.currentData()
        # Если пароль требуется (не пустая строка в словаре), включаем поле
        if self._passwords[role]:
            self.password_input.setEnabled(True)
            self.password_input.clear()
            self.password_input.setFocus()
        else:
            self.password_input.setEnabled(False)
            self.password_input.clear()

    def _on_login_clicked(self):
        role = self.role_combo.currentData()
        entered_password = self.password_input.text()
        required_password = self._passwords[role]

        if entered_password == required_password:
            self.selected_role = role
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
            self.password_input.selectAll()