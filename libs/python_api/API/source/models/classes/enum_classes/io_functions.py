from API.source.models.classes.enum_classes.base_int_enum import (
    BaseIntEnum,
)


class InputFunction(BaseIntEnum):
    no_func = 0
    move = 1
    hold = 2
    pause = 3
    zero_gravity = 4
    run = 5
    move_to_home = 6
    ifunc_hold_io_dig_output = 200
    ifunc_trigger_io_dig_output = 300


class OutputFunction(BaseIntEnum):
    no_func = 0
    no_move_signal_false = 1
    no_move_signal_true = 2
    move_status_signal_true_false = 3
    run_signal_true = 4
    warning_signal_true = 5
    error_signal_true = 6


class SafetyInputFunctions(BaseIntEnum):
    di_type_input = 0
    di_type_emcy_input_stop_0_nc = 1
    di_type_emcy_input_stop_1_nc = 2
    di_type_sfgrd_stop_nc = 3
    di_type_sfgrd_release_no = 4
