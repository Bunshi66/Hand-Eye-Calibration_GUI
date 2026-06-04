from dataclasses import dataclass, field
from typing import List, Tuple, Union

from API.source.models.constants import (
    CTRLR_MAX_AN_OUT,
    CTRLR_MAX_DIG_OUT_BYTES,
    WRIST_MAX_AN_IN,
)
from API.source.models.type_aliases import (
    AngleUnits,
    PositionOrientation,
)


@dataclass
class RPMPCartesianWayPointTemplate:
    tr_position: Tuple[float, ...] = (0.0,) * 3
    rot_position: Tuple[float, ...] = (0.0,) * 3
    tr_velocity: float = 0.0
    rot_velocity: float = 0.0
    tr_acceleration: float = 0.0
    rot_acceleration: float = 0.0


@dataclass
class RPMPJointWayPointTemplate:
    q: Tuple[float, ...] = (0.0,) * 6
    qd: Tuple[float, ...] = (0.0,) * 6
    qdd: Tuple[float, ...] = (0.0,) * 6


@dataclass
class RPMPMoveLWayPointTemplate:
    cart_wp: RPMPCartesianWayPointTemplate = field(
        default_factory=RPMPCartesianWayPointTemplate
    )


@dataclass
class RPMPMovePWayPointTemplate:
    cart_wp: RPMPCartesianWayPointTemplate = field(
        default_factory=RPMPCartesianWayPointTemplate
    )


@dataclass
class RPMPMoveCWayPointTemplate:
    cart_wp_1: RPMPCartesianWayPointTemplate = field(
        default_factory=RPMPCartesianWayPointTemplate
    )
    cart_wp_2: RPMPCartesianWayPointTemplate = field(
        default_factory=RPMPCartesianWayPointTemplate
    )


@dataclass
class RPMPMoveJWayPointTemplate:
    joint_wp: RPMPJointWayPointTemplate = field(
        default_factory=RPMPJointWayPointTemplate
    )


@dataclass
class RPMPMoveCommandTemplate:
    type: int = 0
    blend_radius: float = 0.0
    wp: Union[
        RPMPMoveLWayPointTemplate,
        RPMPMovePWayPointTemplate,
        RPMPMoveCWayPointTemplate,
        RPMPMoveJWayPointTemplate,
    ] = field(default_factory=RPMPMoveJWayPointTemplate)


@dataclass
class MoveCommandTemplate:
    t: int = 0
    des_q: PositionOrientation = (0,) * 6
    des_x: PositionOrientation = (0,) * 6
    force: Tuple[float, ...] = (0,) * 6
    force_en: Tuple[float, ...] = (0,) * 6
    in_tcp: float = 0
    v_max_t: float = 0
    v_max_r: float = 0
    a_max_t: float = 0
    a_max_r: float = 0
    v_max_j: float = 0
    a_max_j: float = 0
    r_blend: float = 0
    pseg: int = -1


@dataclass
class JogCommandParametersTemplate:
    in_tcp: int = 0
    force_en: List[float] = field(default_factory=lambda: [0] * 6)
    force: List[float] = field(default_factory=lambda: [0] * 6)
    speed_max: List[float] = field(
        default_factory=lambda: [0.2] * 3 + [0.5] * 3
    )
    accel: List[float] = field(default_factory=lambda: [0.1] * 3 + [0.25] * 3)
    decel: List[float] = field(default_factory=lambda: [2.0] * 3 + [2.5] * 3)


@dataclass
class JogCommandTemplate:
    mode: int = 0
    force_en: List[float] = field(default_factory=lambda: [0] * 6)
    force_max: List[float] = field(default_factory=lambda: [0] * 6)
    force_const: List[float] = field(default_factory=lambda: [0] * 6)
    stiff: List[float] = field(default_factory=lambda: [0] * 6)
    var: List[float] = field(default_factory=lambda: [0] * 6)


@dataclass
class JointJogCommandTemplate:
    mode: int = 0
    joints_rotation_directions: List[float] = field(
        default_factory=lambda: [0] * 6
    )


@dataclass
class SetOutputTemplate:
    dig_out_mask: List[int] = field(
        default_factory=lambda: [0] * CTRLR_MAX_DIG_OUT_BYTES
    )
    dig_out: List[int] = field(
        default_factory=lambda: [0] * CTRLR_MAX_DIG_OUT_BYTES
    )
    an_out_mask: List[int] = field(
        default_factory=lambda: [0] * CTRLR_MAX_AN_OUT
    )
    an_out_curr_mode: List[int] = field(
        default_factory=lambda: [0] * CTRLR_MAX_AN_OUT
    )
    an_out_value: List[float] = field(
        default_factory=lambda: [0] * CTRLR_MAX_AN_OUT
    )


@dataclass
class InverseKinematicOptimalTemplate:
    target: List[float] = field(default_factory=lambda: [0] * 6)
    base_q: List[float] = field(default_factory=lambda: [0] * 6)


@dataclass
class MotionSetup:
    units: AngleUnits = "deg"

    joint_speed: float = 60
    joint_acceleration: float = 80

    linear_speed: float = 0.25
    linear_acceleration: float = 0.25

    blend: float = 0


MOTION_SETUP: MotionSetup = MotionSetup()


@dataclass
class RPMPMotionSetup:
    units: AngleUnits = "deg"

    linear_speed: float = 0.25
    linear_acceleration: float = 1

    rotation_speed: float = 45
    rotation_acceleration: float = 90

    joints_speed: PositionOrientation = (60,) * 6
    joints_accel: PositionOrientation = (120,) * 6

    blend: float = 0


RPMP_MOTION_SETUP: RPMPMotionSetup = RPMPMotionSetup()


@dataclass
class SetWristInputOutputTemplate:
    dig_out_mask: int = 0
    dig_out: int = 0
    an_in_mask: List[int] = field(default_factory=lambda: [0] * WRIST_MAX_AN_IN)
    an_in_mode: List[int] = field(default_factory=lambda: [0] * WRIST_MAX_AN_IN)
    mux_mode: int = 0
