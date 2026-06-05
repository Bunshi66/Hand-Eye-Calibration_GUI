from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMessageBox, QHBoxLayout, QSplitter
from PyQt5.QtCore import Qt

from source.views.tabs.setup_tab import SetupTab
from source.views.tabs.data_tab import DataTab
from source.views.tabs.result_tab import ResultTab
from source.views.viewport_opengl import ViewportPanel

from source.models.auth_model import UserRole
from source.views.tabs.bin_picking_tab import BinPickingTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle(f"Hand-Eye Calibration & Bin-picking SOFTWARE")
        self._init_ui()
        self.showMaximized()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        self.splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.splitter)

        self.viewport_panel = ViewportPanel()
        self.splitter.addWidget(self.viewport_panel)

        self.right_panel = QWidget()
        right_layout = QHBoxLayout(self.right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        self.tabs_widget = QTabWidget()
        self.tabs_widget.setStyleSheet("""QTabBar::tab { padding: 10px; font-weight: bold; width: 100}""")

        self.tab_setup = SetupTab()
        self.tab_data = DataTab()
        self.tab_result = ResultTab()
        self.tab_bin_picking = BinPickingTab()

        self.tabs_widget.addTab(self.tab_setup, "Setup Control")
        self.tabs_widget.addTab(self.tab_data, "Data Collect")
        self.tabs_widget.addTab(self.tab_result, "Calibration")
        self.tabs_widget.addTab(self.tab_bin_picking, "Bin-picking")

        right_layout.addWidget(self.tabs_widget)

        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([1000, 500])

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)



    # --- СЛОТ ДЛЯ КОНТРОЛЛЕРА ---
    def apply_access_level(self, role: UserRole):
        """Этот метод будет вызываться при старте и при смене пользователя"""
        self.setWindowTitle(f"Hand Eye Calibration System - {role.name}")
        self.status_bar.showMessage(f"System Ready. Mode: {role.name}")

        if role == UserRole.OPERATOR:
            # Оператору нельзя калибровать
            self.tabs.setTabEnabled(2, False)
        elif role in (UserRole.ENGINEER, UserRole.ADMIN):
            # Инженеру и Админу можно
            self.tabs.setTabEnabled(2, True)

    def show_error(self, message: str):
        """Выводит всплывающее окно с ошибкой"""
        QMessageBox.critical(self, "Ошибка оборудования", message)