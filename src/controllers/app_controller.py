import sys
from PyQt5.QtWidgets import QApplication
from src.views.login_dialog import LoginDialog
from src.views.main_window import MainWindow
from src.models.auth_model import CurrentUser
# Импортируем наши контроллеры
from src.controllers.hardware_controller import HardwareController
from src.controllers.calibration_controller import CalibrationController


class AppController:
    def __init__(self):
        # 1. Инициализация Qt Application
        self.app = QApplication(sys.argv)

        # 2. Переменные состояния
        self.current_user = None
        self.main_window = None

        # 3. Создаем "железный" контроллер сразу,
        # чтобы он мог инициализировать драйверы в фоне, если надо
        self.hw_controller = HardwareController()

        # 4. Контроллер логики пока пустой, создадим после запуска окна
        self.calib_controller = None

    def run(self):
        """Запуск цикла приложения."""
        # ШАГ 1: Показываем окно входа
        if self._show_login():
            # ШАГ 2: Если вошли успешно -> Запускаем основное приложение
            self._start_main_application()
            # ШАГ 3: Запускаем Event Loop
            sys.exit(self.app.exec_())
        else:
            # Если нажали "Отмена" или крестик
            sys.exit(0)

    def _show_login(self) -> bool:
        """Показывает диалог входа. Возвращает True, если вход успешен."""
        login_dialog = LoginDialog()
        if login_dialog.exec_():
            # Создаем объект пользователя на основе данных из диалога
            self.current_user = CurrentUser(role=login_dialog.selected_role)
            return True
        return False

    def _start_main_application(self):
        """Инициализирует и показывает главное окно."""
        self.main_window = MainWindow(self.current_user)

        # Контроллер бизнес-логики
        self.calib_controller = CalibrationController(
            self.main_window,
            self.hw_controller
        )

        # === СВЯЗЫВАНИЕ (BINDING) ===

        # 1. Setup Tab: Только кнопки подключения
        self.main_window.tab_setup.btn_connect_cam.clicked.connect(
            self.hw_controller.connect_camera
        )

        self.main_window.tab_setup.btn_connect_robot.clicked.connect(
            self.hw_controller.connect_robot
        )

        # 2. ВИДЕОПОТОК: Теперь шлем его в DATA TAB (Вкладка 2), а не в Setup
        # Обращаемся к tab_data.view_label
        self.hw_controller.on_frame_received.connect(
            self.main_window.tab_data.view_label.setPixmap
        )

        self.main_window.show()