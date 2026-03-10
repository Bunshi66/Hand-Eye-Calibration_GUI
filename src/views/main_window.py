from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QStatusBar
from src.models.auth_model import UserRole, CurrentUser

# Импортируем наши новые вкладки
from src.views.tabs.setup_tab import SetupTab
from src.views.tabs.data_tab import DataTab
from src.views.tabs.result_tab import ResultTab

class MainWindow(QMainWindow):
    def __init__(self, user: CurrentUser):
        super().__init__()
        self.user = user
        self.setWindowTitle(f"Hand Eye Calibration System - {user.role.name}")
        self.resize(1200, 800) # Сделаем окно побольше

        self._init_ui()

    def _init_ui(self):
        # Центральный виджет теперь содержит Табы
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Создаем экземпляры вкладок
        self.tab_setup = SetupTab()
        self.tab_data = DataTab()
        self.tab_result = ResultTab()

        # Добавляем их в контейнер
        self.tabs.addTab(self.tab_setup, "1. Setup & Control")
        self.tabs.addTab(self.tab_data, "2. Data Acquisition")
        self.tabs.addTab(self.tab_result, "3. Calibration & Results")

        # Настройка доступа (Пример: Оператору нельзя в настройки калибровки)
        if self.user.role == UserRole.OPERATOR:
            # Например, выключаем вкладку результатов или делаем её read-only
            # self.tabs.setTabEnabled(2, False)
            pass

        # Статус бар
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(f"System Ready. Mode: {self.user.role.name}")