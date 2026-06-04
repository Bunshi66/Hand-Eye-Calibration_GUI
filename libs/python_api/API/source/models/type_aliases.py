from types import TracebackType
from typing import List, Literal, Tuple, TypeAlias, Union

# IO
max_dig_in_index_count = 24  # real count
max_dig_out_index_count = 24  # real count

AnalogIndex: TypeAlias = Literal[0, 1, 2, 3]
DigitalIndex: TypeAlias = Literal[
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
    21,
    22,
    23,
]
DigitalSafetyIndex: TypeAlias = Literal[0, 1, 2, 3, 4, 5, 6, 7]
DigitalWristIndex: TypeAlias = Literal[0, 1]

# Logger
_SysExcInfoType: TypeAlias = Union[
    Tuple[
        type[BaseException],
        BaseException,
        TracebackType | None,
    ],
    Tuple[None, None, None],
]
ExcInfoType: TypeAlias = None | bool | _SysExcInfoType | BaseException

# Diff args
JointIndex: TypeAlias = Literal[0, 1, 2, 3, 4, 5]
PositionOrientation: TypeAlias = List[float] | Tuple[float, ...]


LiteralType: TypeAlias = Literal[
    "compare",
    "math",
    "angle",
    "position",
    "power",
    "axis",
    "reference_frame",
    "activation_type",
    "cs",
    "mm",
    "ss",
    "in_f",
    "out_f",
    "Wm",
]
CompareSigns: TypeAlias = Literal[">", "<"]
JogDirection: TypeAlias = Literal["+", "-"]
ReferenceFrame: TypeAlias = Literal["base", "tcp"]
AngleUnits: TypeAlias = Literal["rad", "deg"]
PositionFormat: TypeAlias = Literal["joints", "tcp"]
PowerUnits: TypeAlias = Literal["mA", "V"]
JogAxis: TypeAlias = Literal["X", "Y", "Z", "Rx", "Ry", "Rz"]
ControllerState_: TypeAlias = Literal["on", "off", "run"]
MotionMode_: TypeAlias = Literal["move", "move_adv", "pause", "hold"]
SafetyStatus_: TypeAlias = Literal[
    "recovery", "normal", "reduced", "safeguard_stop"
]
InputFunction_: TypeAlias = Literal[
    "no_func",
    "move",
    "move_advhold",
    "pause",
    "zero_gravity",
    "run",
    "move_to_home",
]
OutputFunction_: TypeAlias = Literal[
    "no_func",
    "no_move_signal_false",
    "no_move_signal_true",
    "move_status_signal_true_false",
    "run_signal_true",
    "warning_signal_true",
    "error_signal_true",
]
WristMode_: TypeAlias = Literal["off", "rs485", "analog_in", "nc", "gnd"]
WristInputActivationType_ = Literal["hold", "trigger"]
