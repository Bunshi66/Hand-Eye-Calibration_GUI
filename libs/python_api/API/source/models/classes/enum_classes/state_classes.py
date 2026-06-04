from API.source.models.classes.enum_classes.base_int_enum import (
    BaseIntEnum,
)


class InComingSafetyStatus(BaseIntEnum):
    """
    Класс входящих состояний безопасности.
    Значения класса используются только для сравнения значений с rt_data.
    В остальной логике программы используются только имена полей.
    """

    deinit = 0
    recovery = 1
    normal = 2
    reduced = 3
    safeguard_stop = 4
    emergency_stop = 5
    fault = 6
    violation = 7


class InComingMotionMode(BaseIntEnum):
    """
    Класс входящих режимов движения.
    Значения класса используются только для сравнения значений с rt_data.
    В остальной логике программы используются только имена полей.
    """

    hold = 0
    pause = 5
    move = 4
    move_adv = 6
    zero_gravity = 1
    jog = 2
    joint_jog = 3


class OutComingMotionMode(BaseIntEnum):
    """
    Класс исходящих режимов движения.
    Значения класса используются только для отправки команд.
    В остальной логике программы используются только имена полей.
    """

    hold = 0
    pause = 4
    move = 2
    move_adv = 11
    zero_gravity = 15
    jog = 8
    joint_jog = 10


class InComingControllerState(BaseIntEnum):
    """
    Класс входящих состояний контроллера.
    Значения класса используются только для сравнения значений с rt_data.
    В остальной логике программы используются только имена полей.
    """

    idle = 0
    off = 1
    stby = 2
    on = 3
    run = 4
    calibration = 5
    failure = 6
    force_exit = 7


class OutComingControllerState(BaseIntEnum):
    """
    Класс исходящих состояний контроллера.
    Значения класса используются только для отправки команд.
    В остальной логике программы используются только имена полей.
    """

    # command
    power = 5
    # states
    off = 0
    stby = 1
    on = 2
    run = 3
    confirm_position = 16


class WristMode(BaseIntEnum):
    """
    Класс режимов инструмента.
    Значения класса используются только для сравнения значений с rt_data.
    В остальной логике программы используются только имена полей.
    """

    off = 0
    rs485 = 1
    analog_in = 2
    nc = 3
    gnd = 4


class MotionWarning(BaseIntEnum):
    """
    Класс статусов предупреждения о состоянии робота
    Значения класса используются только для сравнения значений с rt_data.
    В остальной логике программы используются только имена полей.
    """

    no_warning = 0
    protective_stop = 1
    self_collision = 2
