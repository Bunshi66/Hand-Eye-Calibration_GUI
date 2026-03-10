from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QTextEdit, QLabel)
from PyQt5.QtCore import Qt


class ResultTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout()

        # --- ЛЕВАЯ: Настройки алгоритма и Лог ---
        left_layout = QVBoxLayout()

        # Настройки
        settings_group = QGroupBox("Параметры алгоритма")
        # Тут будут поля ввода (Square Size и т.д.)
        settings_group.setMinimumHeight(150)
        left_layout.addWidget(settings_group)

        # Кнопка расчета
        self.btn_calc = QPushButton("CALIBRATE NOW")
        self.btn_calc.setMinimumHeight(40)
        self.btn_calc.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        left_layout.addWidget(self.btn_calc)

        # Текстовый вывод
        self.log_area = QTextEdit()
        self.log_area.setPlaceholderText("Здесь будет выведена матрица трансформации...")
        self.log_area.setReadOnly(True)
        left_layout.addWidget(self.log_area)

        main_layout.addLayout(left_layout, 1)

        # --- ПРАВАЯ: 3D Визуализация ---
        # В будущем сюда внедрим Open3D окно
        self.visualizer_frame = QLabel("3D VISUALIZATION (Open3D)")
        self.visualizer_frame.setAlignment(Qt.AlignCenter)
        self.visualizer_frame.setStyleSheet("background-color: #111; color: cyan; font-size: 16px;")

        main_layout.addWidget(self.visualizer_frame, 2)

        self.setLayout(main_layout)