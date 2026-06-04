import logging
from threading import Lock, Thread, main_thread
from time import sleep
from typing import Callable, Literal, Optional

from API.source.core.exceptions.status_error.controller_state_error import (
    ControllerFailureError,
)
from API.source.core.exceptions.status_error.safety_status_error import (
    ControllerFaultError,
    EmergencyStopError,
    SafetyViolationError,
)
from API.source.core.network.rtd_receiver_socket import (
    RTDReceiver,
)
from API.source.models.classes.enum_classes.state_classes import (
    InComingControllerState as Ics,
)
from API.source.models.classes.enum_classes.state_classes import (
    InComingMotionMode as Imm,
)
from API.source.models.classes.enum_classes.state_classes import (
    InComingSafetyStatus as Iss,
)
from API.source.models.classes.enum_classes.state_classes import (
    MotionWarning as Mw,
)
from API.source.models.classes.enum_classes.state_classes import (
    WristMode as Wm,
)
from API.source.models.type_aliases import ExcInfoType


class StateHandler(object):
    """
    Класс, реализующий проверку состояния контроллера робота.
    """

    _CYCLE_TIME: float = 0.01  # sec
    _rtd_receiver: RTDReceiver
    _logger: Optional[logging.Logger]

    def __init__(
        self,
        rtd_receiver: RTDReceiver,
        ignore_errors: bool,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Создать новый объект класса.

        Args:
            rtd_receiver (RTDReceiver): объект класса RTDReceiver;
            ignore_errors (bool): флаг игнорирования ошибок контроллера;
            logger (optional, logging.Logger): если задан, то логи будут писаться.
        """
        self._rtd_receiver: RTDReceiver = rtd_receiver
        self._ignore_errors: bool = ignore_errors
        self._logger: Optional[logging.Logger] = logger

        self._controller_state = -1
        self._motion_mode = -1
        self._safety_status = -1
        self._safety_warning = False
        self._controller_warning = False
        self._wrist_mode = -1

        self._thread: Optional[Thread] = None
        self._lock = Lock()

        self._is_running: bool = False

    def start(
        self,
        error_callback: Optional[Callable[[ExcInfoType], None]] = None,
        thread_name: str = "StateHandler-loop",
    ):
        """
        Запустить цикл проверки состояния контроллера в отдельном потоке.

        Args:
            error_callback: функция, которая будет вызвана при возникновении
                недопустимого состояния контроллера или ошибки при приеме данных;
            thread_name: имя потока, в котором будет запущен цикл проверки
                состояния.
        """
        self._write_log("debug", "Starting state controller checker loop")
        self._thread = Thread(
            target=self._checking_loop,
            args=(error_callback,),
            daemon=False,
            name=thread_name,
        )
        self._thread.start()

    def stop(self):
        """
        Остановить цикл проверки состояния контроллера.
        """
        self._write_log("debug", "Stopping state controller checker loop")
        if self._thread is None:
            return
        with self._lock:
            self._is_running = False
        try:
            self._thread.join(2)
        except Exception:
            pass

    def is_running(self) -> bool:
        """
        Получить статус работы цикла приема данных.

        Returns:
            bool: True если цикл запущен.
        """
        with self._lock:
            is_running = self._is_running
        return is_running and self._rtd_receiver.is_connected()

    def _checking_loop(
        self, error_callback: Optional[Callable[[ExcInfoType], None]]
    ):
        self._is_running = True
        self._write_log("debug", "State handler loop was started")

        try:
            while (
                self._is_running
                and self._rtd_receiver.is_connected()
                and main_thread().is_alive()
            ):
                try:
                    self._check_all()
                    sleep(self._CYCLE_TIME)
                except (
                    ControllerFailureError,
                    ControllerFaultError,
                    EmergencyStopError,
                    SafetyViolationError,
                ) as error:
                    if not self._ignore_errors:
                        raise error
                    sleep(self._CYCLE_TIME)

            self._is_running = False
            self._write_log("debug", "State handler loop was stopped")
        except Exception as error:
            self._write_log(
                "debug", f"State handler loop failed with error: {error}"
            )
            self._is_running = False
            if error_callback is not None:
                error_callback(error)

    def _check_all(self):
        self._check_controller_state()
        self._check_motion_mode()
        self._check_safety_status()
        self._check_wrist_mode()

    def _check_wrist_mode(self):
        if self._rtd_receiver.get_data().wrist_mode != self._wrist_mode:
            self._write_log(
                "info",
                f"Robot wrist-mode: "
                f"{Wm(int(self._rtd_receiver.get_data().wrist_mode)).name}",
            )
            self._wrist_mode = self._rtd_receiver.get_data().wrist_mode

    def _check_motion_mode(self):
        if self._rtd_receiver.get_data().motion_mode != self._motion_mode:
            self._write_log(
                "info",
                f"Robot motion-mode: "
                f"{Imm(int(self._rtd_receiver.get_data().motion_mode)).name}",
            )
            self._motion_mode = self._rtd_receiver.get_data().motion_mode
            if self._motion_mode == Imm.pause:
                if self._rtd_receiver.get_data().state_flags:
                    self._write_log(
                        "warning",
                        f"Robot motion warning: "
                        f"{Mw(int(self._rtd_receiver.get_data().state_flags)).name}",
                    )

    def _check_controller_state(self):
        if self._rtd_receiver.get_data().state != self._controller_state:
            state = int(self._rtd_receiver.get_data().state)
            if self._controller_state != -1:
                self._write_log(
                    "info", f"Robot controller-state: {Ics(state).name}"
                )
            if state == Ics.failure:
                if self._controller_state == -1:
                    if self._controller_warning:
                        return
                    else:
                        self._controller_warning = True
                        return self._write_log(
                            "warning",
                            "Controller inner error happened. Controller reboot needed.",
                        )
                else:
                    raise ControllerFailureError
            if self._controller_warning:
                self._controller_warning = False
            self._controller_state = self._rtd_receiver.get_data().state

    def _check_safety_status(self):  # noqa: C901
        if self._rtd_receiver.get_data().safety != self._safety_status:
            status = int(self._rtd_receiver.get_data().safety)
            match status:
                case Iss.emergency_stop:
                    if self._safety_status == -1:
                        if self._safety_warning:
                            return
                        else:
                            self._safety_warning = True
                            return self._write_log(
                                "warning",
                                "Robot emergency stop (1-category stop event)",
                            )
                    else:
                        raise EmergencyStopError
                case Iss.fault:
                    if self._safety_status == -1:
                        if self._safety_warning:
                            return
                        else:
                            self._safety_warning = True
                            return self._write_log(
                                "warning",
                                "Robot software fault (0-category stop event)."
                                " Check core log-files",
                            )
                    else:
                        raise ControllerFaultError
                case Iss.violation:
                    if self._safety_status == -1:
                        if self._safety_warning:
                            return
                        else:
                            self._safety_warning = True
                            return self._write_log(
                                "warning",
                                "Robot safety violation (0-category stop event)",
                            )

                    else:
                        raise SafetyViolationError
            if self._safety_warning:
                self._safety_warning = False
            self._write_log("info", f"Robot safety-status: {Iss(status).name}")
            self._safety_status = self._rtd_receiver.get_data().safety

    def _write_log(
        self, level: Literal["debug", "info", "warning", "error"], message: str
    ):
        """
        Обертка для логгера.
        """

        if self._logger is not None:
            log_method = getattr(self._logger, level, self._logger.error)
            log_method(message)

    def __del__(self):
        if self.is_running():
            self.stop()
