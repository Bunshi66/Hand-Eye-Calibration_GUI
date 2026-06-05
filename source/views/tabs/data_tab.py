from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
                             QPushButton, QLabel, QComboBox, QFormLayout,
                             QLineEdit, QTableWidget, QHeaderView, QProgressBar,
                             QDoubleSpinBox, QAbstractItemView, QMessageBox,
                             QTableWidgetItem, QFileDialog)
from PyQt5.QtCore import Qt, pyqtSignal
import pyqtgraph.opengl as gl
import numpy as np
import pyqtgraph as pg
import os

class DataTab(QWidget):
    request_add_pose = pyqtSignal()  # Запросить текущие joint angles и добавить в таблицу
    request_update_pose = pyqtSignal(int)  # Перезаписать позу с индексом (int) текущими координатами
    request_move_to = pyqtSignal(int)  # Отправить робота к позе с индексом (int)
    request_clear = pyqtSignal()
    request_save_poses = pyqtSignal(str)
    request_load_poses = pyqtSignal(str)
    request_start_collect_data = pyqtSignal()
    request_run_calibration = pyqtSignal(str)
    request_set_cad_path = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._connect_internal_signals()

    def _init_ui(self):
        main_layout = QVBoxLayout()

        # ================== ЛЕВАЯ ПАНЕЛЬ (ПОЗЫ) ==================
        up_layout = QVBoxLayout()
        # left_layout.addWidget(QLabel("<b>1. Маршрут калибровки (Waypoints)</b>"))

        self.table = QTableWidget(0, 8)
        headers = [
            "X", "Y", "Z",
            "Rx", "Ry", "Rz",
            "Detect\nError", "RMSE"
        ]
        self.table.setHorizontalHeaderLabels(headers)
        header = self.table.horizontalHeader()

        # Растягиваем все колонки равномерно
        for i in range(8):
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        up_layout.addWidget(self.table)

        # Управление списком
        btn_grid = QHBoxLayout()
        self.btn_load = QPushButton("Load")
        self.btn_save = QPushButton("Save")
        self.btn_clear = QPushButton("Clear")
        btn_grid.addWidget(self.btn_load)
        btn_grid.addWidget(self.btn_save)
        btn_grid.addWidget(self.btn_clear)
        up_layout.addLayout(btn_grid)

        # Добавляем левую панель в главное окно (занимает ~35% ширины)
        main_layout.addLayout(up_layout, 80)

        bottom_layout = QHBoxLayout()

        # ------------------ НИЗ ПРАВОЙ ЧАСТИ (TOOLS) ------------------
        bottom_tools_layout = QHBoxLayout()

        # --- ОБЪЕДИНЕННАЯ ГРУППА: Сцена и Сбор данных ---
        # data_group = QGroupBox("2. Настройка и Сбор данных")
        data_group = QGroupBox()
        data_group.setStyleSheet("QGroupBox { border: 1px solid #2196F3; font-weight: bold; }")

        data_layout = QHBoxLayout()

        # Левая колонка группы: Камера и Робот
        scene_layout = QVBoxLayout()
        cam_form = QFormLayout()

        teach_btns = QHBoxLayout()

        btn_style = "background-color: #555; color: white; border-radius: 4px; padding: 5px;"

        self.btn_add_pose = QPushButton("Add Pose")
        self.btn_add_pose.setStyleSheet(btn_style)
        self.btn_update_pose = QPushButton("Upd Pose")
        self.btn_update_pose.setStyleSheet(btn_style)
        self.btn_move_to = QPushButton("Move To")
        self.btn_move_to.setStyleSheet(btn_style)
        teach_btns.addWidget(self.btn_add_pose)
        teach_btns.addWidget(self.btn_update_pose)
        teach_btns.addWidget(self.btn_move_to)

        scene_layout.addLayout(cam_form)
        scene_layout.addLayout(teach_btns)

        # Собираем левую (Сцена) и правую (Батч) колонки в одну группу
        data_layout.addLayout(scene_layout, 50)
        data_group.setLayout(data_layout)

        # --- НОВАЯ ГРУППА: Вычисление Hand-Eye ---
        # calib_group = QGroupBox("3. Hand-Eye Calibration")
        calib_group = QGroupBox()
        calib_group.setStyleSheet("QGroupBox { border: 1px solid #2196F3; font-weight: bold; }")
        calib_layout = QVBoxLayout()

        calib_form = QFormLayout()
        self.combo_calib_type = QComboBox()
        self.combo_calib_type.addItems(["Eye-in-Hand", "Eye-to-Hand"])
        calib_form.addRow("Тип:", self.combo_calib_type)
        calib_layout.addLayout(calib_form)

        self.btn_load_CAD_file = QPushButton("Load CAD model")
        self.btn_load_CAD_file.setFixedHeight(35)
        calib_layout.addWidget(self.btn_load_CAD_file)

        self.btn_start_collect_data = QPushButton("START DATA COLLECTION")
        self.btn_start_collect_data.setFixedHeight(35)
        self.btn_start_collect_data.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; font-size: 13px;")
        calib_layout.addWidget(self.btn_start_collect_data)

        self.btn_run_calib = QPushButton("RUN CALIBRATION")
        self.btn_run_calib.setFixedHeight(35)
        self.btn_run_calib.setStyleSheet("background-color: #9C27B0; color: white; font-weight: bold; font-size: 13px;")
        calib_layout.addWidget(self.btn_run_calib)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        calib_layout.addWidget(self.progress_bar)

        calib_layout.addStretch()  # Прижимаем кнопку вниз
        calib_group.setLayout(calib_layout)

        bottom_tools_layout.addWidget(data_group, 50)
        bottom_tools_layout.addWidget(calib_group, 50)

        # Добавляем нижнюю панель в правую часть (занимает ~30% ВЫСОТЫ)
        bottom_layout.addLayout(bottom_tools_layout, 30)

        # ================== ФИНАЛЬНАЯ СБОРКА ==================
        # Добавляем правую часть в главное окно (занимает ~65% ширины)
        main_layout.addLayout(bottom_layout, 20)

        self.setLayout(main_layout)

    def _connect_internal_signals(self):
        """
        Связываем клики кнопок с нашими кастомными сигналами.
        Логика выбора строки таблицы тоже здесь.
        """
        self.btn_add_pose.clicked.connect(self.request_add_pose.emit)
        self.btn_clear.clicked.connect(self.request_clear.emit)

        self.btn_update_pose.clicked.connect(self._on_update_pose_clicked)
        self.btn_move_to.clicked.connect(self._on_move_to_clicked)
        self.btn_save.clicked.connect(self._on_save_clicked)
        self.btn_load.clicked.connect(self._on_load_clicked)
        self.btn_start_collect_data.clicked.connect(self._on_start_calibration_clicked)
        self.btn_run_calib.clicked.connect(self._on_run_calib_clicked)
        self.btn_load_CAD_file.clicked.connect(self._on_load_CAD_clicked)

    def _on_run_calib_clicked(self):
        calib_type = self.combo_calib_type.currentText()
        self.request_run_calibration.emit(calib_type)

    def _on_start_calibration_clicked(self):
        self.calibration_button_control(False)
        self.request_start_collect_data.emit()

    def calibration_button_control(self, flag):
        if flag:
            self.btn_start_collect_data.setText("START DATA COLLECTION")
        else:
            self.btn_start_collect_data.setText("COLLECTING...")

        self.btn_start_collect_data.setEnabled(flag)
        self.btn_add_pose.setEnabled(flag)
        self.btn_update_pose.setEnabled(flag)
        self.btn_move_to.setEnabled(flag)
        self.btn_load.setEnabled(flag)
        self.btn_save.setEnabled(flag)
        self.btn_clear.setEnabled(flag)

    def success_calib(self, calib_dict):
        # TODO написать обработку результатов калибровки для UI
        print(calib_dict)

    def update_progress(self, value):
        """Обновление прогресс-бара"""
        self.progress_bar.setValue(value)

        # Если достигнут 100%, разблокируем кнопку
        if value >= 100:
            self.calibration_button_control(False)

    def show_error(self, error_msg):
        """Показ ошибки"""
        QMessageBox.critical(self, "Ошибка", error_msg)
        # Разблокируем кнопку в случае ошибки
        self.calibration_button_control(True)
        self.progress_bar.setValue(0)

    def finished_progress(self):
        self.calibration_button_control(True)

    def _get_selected_row(self) -> int:
        """
        Возвращает индекс выбранной строки или -1, если ничего не выбрано.
        Показывает предупреждение пользователю если строка не выбрана.
        """
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "Нет выбора", "Пожалуйста, выберите позу в таблице.")
            return -1
        return self.table.currentRow()

    def _on_update_pose_clicked(self):
        row = self._get_selected_row()
        #print(f'row: {row}')
        if row != -1:
            self.request_update_pose.emit(row)

    def _on_move_to_clicked(self):
        row = self._get_selected_row()
        if row != -1:
            self.request_move_to.emit(row)

    def _on_save_clicked(self):
        """Открывает диалог сохранения файла"""
        # Проверяем, есть ли вообще данные в таблице
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "Пусто", "Нет позы для сохранения!")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить маршрут (Poses)", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.request_save_poses.emit(file_path)

    def _on_load_clicked(self):
        """Открывает диалог выбора файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить маршрут (Poses)", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.request_load_poses.emit(file_path)

    def _on_load_CAD_clicked(self):
        """Открывает диалог выбора файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать CAD модель шаблона", "", "CAD Files (*.stl *.obj *.ply)"
        )
        if file_path:
            self.btn_load_CAD_file.setText(os.path.basename(file_path))
            self.request_set_cad_path.emit(file_path)

    def _create_item(self, text: str) -> QTableWidgetItem:
        """Вспомогательный метод для создания нередактируемой ячейки по центру"""
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        return item

    def add_waypoint_row(self, waypoint_id: int, tcp_pose):
        """Добавляет новую позу (раскладывая координаты по колонкам)"""
        #print(f'Попытка отрисовать новую позу: {tcp_pose}')
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 1-3: Translation (X, Y, Z)
        self.table.setItem(row, 0, self._create_item(f"{tcp_pose[0]:.2f}"))
        self.table.setItem(row, 1, self._create_item(f"{tcp_pose[1]:.2f}"))
        self.table.setItem(row, 2, self._create_item(f"{tcp_pose[2]:.2f}"))

        # 4-6: Rotation (Rx, Ry, Rz)
        self.table.setItem(row, 3, self._create_item(f"{tcp_pose[3]:.3f}"))
        self.table.setItem(row, 4, self._create_item(f"{tcp_pose[4]:.3f}"))
        self.table.setItem(row, 5, self._create_item(f"{tcp_pose[5]:.3f}"))

        # 7-8: Ошибки (Пока данных нет, ставим прочерки)
        self.table.setItem(row, 6, self._create_item("—"))
        self.table.setItem(row, 7, self._create_item("—"))

        # Прокручиваем вниз
        self.table.scrollToBottom()

    def update_waypoint_row(self, row_index: int, waypoint):
        """Полностью перерисовывает строку на основе объекта Waypoint"""
        if row_index >= self.table.rowCount():
            return

        # 1. Обновляем координаты (X, Y, Z, Rx, Ry, Rz)
        self.table.item(row_index, 0).setText(f"{waypoint.tcp_pose[0]:.2f}")
        self.table.item(row_index, 1).setText(f"{waypoint.tcp_pose[1]:.2f}")
        self.table.item(row_index, 2).setText(f"{waypoint.tcp_pose[2]:.2f}")
        self.table.item(row_index, 3).setText(f"{waypoint.tcp_pose[3]:.3f}")
        self.table.item(row_index, 4).setText(f"{waypoint.tcp_pose[4]:.3f}")
        self.table.item(row_index, 5).setText(f"{waypoint.tcp_pose[5]:.3f}")

        # 2. Обновляем detect_error
        detect_error_text = f"{waypoint.detect_error:.4f}" if waypoint.detect_error is not None else "—"
        self.table.item(row_index, 6).setText(detect_error_text)

        # 3. Обновляем Fitness
        # TODO Добавить передачу аргумента fitness из data_model
        # fitness_text = f"{waypoint.fitness:.4f}" if waypoint.fitness is not None else "—"
        # self.table.item(row_index, 7).setText(fitness_text)

        # # 3. Обновляем визуальный статус (включен/выключен)
        # color = Qt.black if waypoint.enabled else Qt.gray
        # for col in range(8):
        #     item = self.table.item(row_index, col)
        #     if item:
        #         item.setForeground(color)

    def mark_waypoint_scanned(self, row_index: int, success: bool):
        """Отмечает строку после Batch Collection"""
        if 0 <= row_index < self.table.rowCount():
            symbol = "✅" if success else "❌"
            self.table.item(row_index, 1).setText(symbol)

    def clear_table(self):
        """Очищает таблицу"""
        self.table.setRowCount(0)