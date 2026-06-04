from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QFormLayout, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal

class SetupTab(QWidget):
    request_toggle_robot = pyqtSignal(str)
    request_toggle_camera = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._connect_internal_signals()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("Конфигурация оборудования")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Область настройки подключений (горизонтальная)
        conn_layout = QHBoxLayout()

        # --- Группа Камеры ---
        cam_group = QGroupBox("Сенсор / Камера")
        cam_form = QFormLayout()

        self.cam_type = QComboBox()
        self.cam_type.addItems(["SCAPE"])

        self.cam_id = QLineEdit("10.10.10.18")

        self.btn_connect_camera = QPushButton("Подключить камеру")
        self.btn_connect_camera.setStyleSheet("text-align: left; padding: 5px;")

        cam_form.addRow("Драйвер:", self.cam_type)
        cam_form.addRow("IP устройства:", self.cam_id)
        cam_form.addRow(self.btn_connect_camera)
        cam_group.setLayout(cam_form)

        conn_layout.addWidget(cam_group)

        # --- Группа Робота ---
        robot_group = QGroupBox("Робот / Манипулятор")
        robot_form = QFormLayout()

        self.robot_type = QComboBox()
        self.robot_type.addItems(["RC RoboPro"])

        self.robot_ip = QLineEdit("10.10.10.10")

        self.btn_connect_robot = QPushButton("Подключить робота")
        self.btn_connect_robot.setStyleSheet("text-align: left; padding: 5px;")

        robot_form.addRow("Модель:", self.robot_type)
        robot_form.addRow("IP адрес:", self.robot_ip)
        robot_form.addRow(self.btn_connect_robot)
        robot_group.setLayout(robot_form)

        conn_layout.addWidget(robot_group)

        layout.addLayout(conn_layout)
        layout.addStretch()  # Прижать всё вверх
        self.setLayout(layout)

    def _connect_internal_signals(self):
        self.btn_connect_robot.clicked.connect(self._on_robot_clicked)
        self.btn_connect_camera.clicked.connect(self._on_camera_clicked)

    def _on_robot_clicked(self):
        # Вкладка сама считывает свое текстовое поле
        ip = self.robot_ip.text()
        self.request_toggle_robot.emit(ip)

    def _on_camera_clicked(self):
        ip = self.cam_id.text()
        self.request_toggle_camera.emit(ip)

    def update_robot_status(self, is_connected: bool):
        """Обновляет UI группы робота в зависимости от статуса подключения"""
        if is_connected:
            self.btn_connect_robot.setText("Отключить робота")
            # Делаем кнопку зеленой
            self.btn_connect_robot.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
            # Блокируем поля ввода, чтобы пользователь не менял IP во время работы
            self.robot_ip.setEnabled(False)
            self.robot_type.setEnabled(False)
        else:
            self.btn_connect_robot.setText("Подключить робота")
            # Возвращаем стандартный стиль
            self.btn_connect_robot.setStyleSheet("text-align: left; padding: 5px;")
            self.robot_ip.setEnabled(True)
            self.robot_type.setEnabled(True)

    def update_camera_status(self, is_connected: bool):
        """Обновляет UI группы камеры в зависимости от статуса подключения"""
        if is_connected:
            self.btn_connect_camera.setText("Отключить камеру")
            self.btn_connect_camera.setStyleSheet("background-color: #4CAF50; color: white; padding: 5px;")
            self.cam_id.setEnabled(False)
            self.cam_type.setEnabled(False)
        else:
            self.btn_connect_camera.setText("Подключить камеру")
            self.btn_connect_camera.setStyleSheet("text-align: left; padding: 5px;")
            self.cam_id.setEnabled(True)
            self.cam_type.setEnabled(True)