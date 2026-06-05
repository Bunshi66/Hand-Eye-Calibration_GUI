from PyQt5.QtCore import QObject

from source.models.hardware_model import RobotModel, CameraModel
from source.models.data_model import DataModel
from source.models.auth_model import AuthModel, UserRole
from source.models.calibration_model import CalibrationModel

from source.controllers.hardware_controller import HardwareController
from source.controllers.data_controller import DataController

from source.views.main_window import MainWindow



class AppController(QObject):
    def __init__(self):
        super().__init__()

        # 1. Инициализируем Модели
        self.auth_model = AuthModel(initial_role=UserRole.ENGINEER)
        self.robot_model = RobotModel()
        self.camera_model = CameraModel()
        self.data_model = DataModel()
        self.calib_model = CalibrationModel()

        # 2. Инициализируем Контроллеры, передаем им модели
        self.hw_controller = HardwareController(self.robot_model, self.camera_model)
        self.data_controller = DataController(self.data_model, self.hw_controller, self.calib_model)

        # 3. Инициализируем View
        self.main_view = MainWindow()

        # 4. Связываем всё сигналами
        self._connect_signals()

    def _connect_signals(self):
        # ====== SETUP TAB ======
        # --- UI -> КОНТРОЛЛЕР (Действия пользователя) ---
        # Предположим, во View есть кнопка и поле ввода IP
        self.main_view.tab_setup.request_toggle_robot.connect(self.hw_controller.toggle_robot_connection)
        self.main_view.tab_setup.request_toggle_camera.connect(self.hw_controller.toggle_camera_connection)

        self.main_view.viewport_panel.request_test_shot.connect(self.hw_controller.trigger_test_shot)
        self.main_view.viewport_panel.request_show_cad.connect(self.data_controller.show_cad_pcd)
        self.main_view.viewport_panel.request_show_cad_mesh.connect(self.data_controller.show_cad_mesh)
        # --- МОДЕЛЬ -> UI (Реакция на изменение состояния железа) ---
        self.robot_model.connected.connect(self.main_view.tab_setup.update_robot_status)
        self.camera_model.connected.connect(self.main_view.tab_setup.update_camera_status)

        # --- ОБРАБОТКА ОШИБОК -> UI ---
        self.robot_model.error_occurred.connect(self.main_view.show_error)
        self.camera_model.error_occurred.connect(self.main_view.show_error)

        # ====== DATA TAB ======
        # UI -> DataController
        self.main_view.tab_data.request_add_pose.connect(self.data_controller.record_current_pose)
        self.main_view.tab_data.request_update_pose.connect(self.data_controller.update_current_pose)
        self.main_view.tab_data.request_move_to.connect(self.data_controller.move_to_waypoint)
        self.main_view.tab_data.request_clear.connect(self.data_controller.clear_waypoints)
        self.main_view.tab_data.request_save_poses.connect(self.data_controller.save_poses)
        self.main_view.tab_data.request_load_poses.connect(self.data_controller.load_poses)
        self.main_view.tab_data.request_start_collect_data.connect(self.data_controller.start_collecting_data)
        self.main_view.tab_data.request_run_calibration.connect(self.data_controller.start_calibration)
        self.main_view.tab_data.request_set_cad_path.connect(self.data_controller.set_cad_path)

        # DataModel -> UI (Обновление таблицы)
        self.data_model.waypoint_added.connect(
            lambda wp: self.main_view.tab_data.add_waypoint_row(wp.id, wp.tcp_pose)
        )
        self.data_model.waypoint_updated.connect(
            lambda idx: self.main_view.tab_data.update_waypoint_row(
                idx, self.data_model.get_all_waypoints()[idx]
            )
        )
        self.data_model.waypoints_cleared.connect(self.main_view.tab_data.clear_table)
        self.data_model.error_occurred.connect(self.main_view.show_error)

        self.data_controller.progress_update.connect(self.main_view.tab_data.update_progress)
        self.data_controller.error_occurred.connect(self.main_view.tab_data.show_error)
        self.data_controller.progress_finished.connect(self.main_view.tab_data.finished_progress)
        self.data_controller.calib_success.connect(self.main_view.tab_data.success_calib)

        self.camera_model.frame_received.connect(self.main_view.viewport_panel.gl_widget.display_point_cloud)
        self.calib_model.cad_model_recieved.connect(self.main_view.viewport_panel.gl_widget.display_point_cloud)
        self.calib_model.cad_model_mesh_recieved.connect(self.main_view.viewport_panel.gl_widget.display_mesh)


    def run(self):
        self.main_view.show()