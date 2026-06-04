from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar, QMessageBox

# Импортируем наши новые вкладки
from source.views.tabs.setup_tab import SetupTab
from source.views.tabs.data_tab import DataTab
from source.views.tabs.result_tab import ResultTab

from source.models.auth_model import UserRole
# Импорт ваших вкладок...

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1200, 800)
        self.setWindowTitle(f"Hand-Eye Calibration & Bin-picking SOFTWARE")
        self._init_ui()
        self.showMaximized()

    def _init_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_setup = SetupTab()
        self.tab_data = DataTab()
        self.tab_result = ResultTab()

        self.tabs.addTab(self.tab_setup, "1. Setup Control")
        self.tabs.addTab(self.tab_data, "2. Data Acquisition")
        self.tabs.addTab(self.tab_result, "3. Calibration Results")

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