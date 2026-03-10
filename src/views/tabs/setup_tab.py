from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QFormLayout, QLineEdit)
from PyQt5.QtCore import Qt


class SetupTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

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
        self.cam_type.addItems(["SCAPE", "Hikrobot"])

        self.cam_id = QLineEdit("0")
        #self.cam_id.setPlaceholderText("IP")

        self.btn_connect_cam = QPushButton("Подключить камеру")
        self.btn_connect_cam.setStyleSheet("text-align: left; padding: 5px;")

        cam_form.addRow("Драйвер:", self.cam_type)
        cam_form.addRow("IP устройства:", self.cam_id)
        cam_form.addRow(self.btn_connect_cam)
        cam_group.setLayout(cam_form)

        conn_layout.addWidget(cam_group)

        # --- Группа Робота ---
        robot_group = QGroupBox("Робот / Манипулятор")
        robot_form = QFormLayout()

        self.robot_type = QComboBox()
        self.robot_type.addItems(["RC RoboPro"])

        self.robot_ip = QLineEdit("192.168.1.10")

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