from PyQt5.QtCore import QObject, Qt
from PyQt5.QtWidgets import QTableWidgetItem, QFileDialog, QMessageBox
import json
import dataclasses

from src.models.calibration_data import CalibrationDataset, RobotPose, PointStatus
from src.views.main_window import MainWindow


class CalibrationController(QObject):
    def __init__(self, main_window: MainWindow, hardware_controller):
        super().__init__()
        self.view = main_window.tab_data  # Ссылка на вкладку DataTab
        self.hw = hardware_controller  # Ссылка на HardwareController

        # Наша модель данных
        self.dataset = CalibrationDataset()

        self._bind_signals()

    def _bind_signals(self):
        """Привязываем кнопки UI к методам контроллера."""
        # Кнопки управления списком
        self.view.btn_add_pose.clicked.connect(self.add_current_pose)
        self.view.btn_clear.clicked.connect(self.clear_table)
        self.view.btn_save.clicked.connect(self.save_dataset)
        # self.view.btn_load.clicked.connect(self.load_dataset) # Реализуем позже

    def add_current_pose(self):
        """Добавляет текущую позицию робота в список."""
        # 1. Получаем сырые данные [x, y, z, rx, ry, rz] от HardwareController
        raw_pose = self.hw.get_robot_pose()

        # 2. Конвертируем в dataclass RobotPose
        # Распаковка списка через *args
        pose_obj = RobotPose(*raw_pose)

        # 3. Добавляем в Модель
        self.dataset.add_point(pose_obj)

        # 4. Обновляем Вид (Таблицу)
        self._refresh_table_row(len(self.dataset.points) - 1)

    def clear_table(self):
        self.dataset.points.clear()
        self.view.table.setRowCount(0)

    def _refresh_table_row(self, row_index: int):
        """Рисует или обновляет конкретную строку таблицы на основе Модели."""
        point = self.dataset.points[row_index]
        table = self.view.table

        # Если строки еще нет, создаем
        if table.rowCount() <= row_index:
            table.insertRow(row_index)

        # Колонка ID
        item_id = QTableWidgetItem(str(point.id))
        item_id.setTextAlignment(Qt.AlignCenter)
        table.setItem(row_index, 0, item_id)

        # Колонка Status
        status_str = point.status.value
        item_status = QTableWidgetItem(status_str)
        item_status.setTextAlignment(Qt.AlignCenter)

        # Раскраска статуса
        if point.status == PointStatus.EMPTY:
            item_status.setForeground(Qt.gray)
        elif point.status == PointStatus.CAPTURED:
            item_status.setForeground(Qt.green)

        table.setItem(row_index, 1, item_status)

        # Колонка Pose Data (красивый вывод)
        pose_str = str(point.target_pose)
        item_pose = QTableWidgetItem(pose_str)
        table.setItem(row_index, 2, item_pose)

    def save_dataset(self):
        """Сохранение маршрута в JSON."""
        # Открываем диалог сохранения
        file_path, _ = QFileDialog.getSaveFileName(
            self.view, "Save Calibration Path", "", "JSON Files (*.json)"
        )

        if file_path:
            try:
                data = self.dataset.to_dict()
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"Saved to {file_path}")
            except Exception as e:
                QMessageBox.critical(self.view, "Error", f"Failed to save: {str(e)}")