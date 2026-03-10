from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QTableWidget, QHeaderView,
                             QDoubleSpinBox, QFormLayout, QProgressBar, QMessageBox)
from PyQt5.QtCore import Qt


class DataTab(QWidget):
    def __init__(self):
        super().__init__()
        self._init_ui()

    def _init_ui(self):
        main_layout = QHBoxLayout()

        # ================== ЛЕВАЯ ПАНЕЛЬ (ПОЗЫ) ==================
        left_layout = QVBoxLayout()

        left_layout.addWidget(QLabel("<b>1. Маршрут калибровки (Waypoints)</b>"))

        # Таблица
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["ID", "Data", "Robot Pose"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Есть картинка или нет
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        # Выделение всей строки
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        left_layout.addWidget(self.table)

        # Управление списком
        btn_grid = QHBoxLayout()
        self.btn_load = QPushButton("Load")
        self.btn_save = QPushButton("Save")
        self.btn_clear = QPushButton("Clear")
        btn_grid.addWidget(self.btn_load)
        btn_grid.addWidget(self.btn_save)
        btn_grid.addWidget(self.btn_clear)
        left_layout.addLayout(btn_grid)

        main_layout.addLayout(left_layout, 3)  # 30%

        # ================== ЦЕНТР (VIEWPORT) ==================
        viewport_layout = QVBoxLayout()
        '''
        # Заголовок меняется: Live View или Review Image
        self.lbl_view_mode = QLabel("LIVE VIEW")
        self.lbl_view_mode.setStyleSheet(
            "background-color: #4CAF50; color: white; padding: 2px 5px; border-radius: 3px;")
        self.lbl_view_mode.setAlignment(Qt.AlignCenter)
        self.lbl_view_mode.setFixedWidth(100)
        viewport_layout.addWidget(self.lbl_view_mode, alignment=Qt.AlignRight)
        '''

        self.view_label = QLabel("Viewport")
        self.view_label.setAlignment(Qt.AlignCenter)
        self.view_label.setStyleSheet("background-color: #222; color: #888; border: 2px solid #555;")
        viewport_layout.addWidget(self.view_label)

        main_layout.addLayout(viewport_layout, 5)  # 50%

        # ================== ПРАВАЯ ПАНЕЛЬ (TOOLS) ==================
        right_layout = QVBoxLayout()

        # --- Группа 1: Настройка Сцены ---
        setup_group = QGroupBox("2. Настройка сцены")
        setup_layout = QVBoxLayout()

        # Камера
        cam_form = QFormLayout()
        self.spin_exposure = QDoubleSpinBox()
        self.spin_exposure.setRange(0, 100000)
        self.spin_gain = QDoubleSpinBox()
        cam_form.addRow("Exposure:", self.spin_exposure)
        cam_form.addRow("Gain:", self.spin_gain)
        setup_layout.addLayout(cam_form)

        # Робот (Teaching)
        teach_layout = QHBoxLayout()
        self.btn_add_pose = QPushButton("Add Pose")
        self.btn_update_pose = QPushButton("Upd Pose")
        self.btn_move_to = QPushButton("Move To")
        teach_layout.addWidget(self.btn_add_pose)
        teach_layout.addWidget(self.btn_update_pose)
        teach_layout.addWidget(self.btn_move_to)
        setup_layout.addLayout(teach_layout)

        # Test Shot
        self.btn_test_shot = QPushButton("Test Shot (Preview)")
        setup_layout.addWidget(self.btn_test_shot)

        setup_group.setLayout(setup_layout)
        right_layout.addWidget(setup_group)

        right_layout.addStretch()

        # --- Группа 2: Сбор Данных ---
        run_group = QGroupBox("3. Сбор данных")
        run_group.setStyleSheet("QGroupBox { border: 2px solid #2196F3; font-weight: bold; }")
        run_layout = QVBoxLayout()

        self.lbl_info = QLabel("Все настройки камеры будут заблокированы во время сбора.")
        self.lbl_info.setWordWrap(True)
        self.lbl_info.setStyleSheet("font-size: 10px; color: gray;")
        run_layout.addWidget(self.lbl_info)

        self.btn_start_batch = QPushButton("START BATCH\nCOLLECTION")
        self.btn_start_batch.setMinimumHeight(60)
        self.btn_start_batch.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        run_layout.addWidget(self.btn_start_batch)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        run_layout.addWidget(self.progress_bar)

        run_group.setLayout(run_layout)
        right_layout.addWidget(run_group)

        main_layout.addLayout(right_layout, 2)  # 20%

        self.setLayout(main_layout)