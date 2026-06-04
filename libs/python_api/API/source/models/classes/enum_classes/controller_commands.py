from enum import IntEnum


class AddWayPointCommand(IntEnum):
    # command
    ctrlr_coms_move_add_wp = 1
    # motion types for waypoints
    move_wp_type_joint = 0
    move_wp_type_linear_cart = 1
    move_wp_type_tcp_pose = 2


class RPMPAddWayPointCommand(IntEnum):
    ctrlr_coms_rpmp_move_add_wp = 18


class RPMPMoveWayPointType(IntEnum):
    # motion types for waypoints
    rpmp_move_wp_type_movel = 0
    rpmp_move_wp_type_movep = 1
    rpmp_move_wp_type_movec = 2
    rpmp_move_wp_type_movej = 3


class ControllerUnlockCommand(IntEnum):
    ctrlr_coms_unlock = 100


class JogModes(IntEnum):
    ctrlr_coms_jog_mode_off = 0
    ctrlr_coms_jog_mode_force = 1
    ctrlr_coms_jog_mode_velocity = 2
    ctrlr_coms_jog_mode_position = 3


class JointJogModes(IntEnum):
    ctrlr_coms_joint_jog_mode_off = 0
    ctrlr_coms_joint_jog_mode_on = 1


class Getters(IntEnum):
    ctrlr_coms_get_last_pos = 901
    ctrlr_coms_get_move_scale = 1115
    ctrlr_coms_get_gravity = 1116
    ctrlr_coms_get_zero_gravity_fscale = 1117
    ctrlr_coms_get_payload = 1121
    ctrlr_coms_get_tool = 1122
    ctrlr_coms_get_jog_param = 1123
    ctrlr_coms_get_force_param = 1124
    ctrlr_coms_get_tool_capsule_count = 1127
    ctrlr_coms_get_tool_capsule = 1128
    ctrlr_coms_get_link_capsule_count = 1129
    ctrlr_coms_get_link_capsule = 1130
    ctrlr_coms_get_home_pose = 1150
    ctrlr_coms_get_robot_view_info = 4000
    ctrlr_coms_get_sw_version = 3000
    ctrlr_coms_get_proto_version = 3001
    # get kinematics
    ctrlr_coms_fkine = 2000
    ctrlr_coms_ikine = 2001
    ctrlr_coms_ikine_optimal = 2002
    # io func
    ctrlr_coms_get_dig_input_func = 1132
    ctrlr_coms_get_dig_output_func = 1133
    ctrlr_coms_cbox_get_sfty_input_func = 1601


class Setters(IntEnum):
    ctrlr_coms_set_force_param = 1024
    ctrlr_coms_set_jog_param = 1023
    ctrlr_coms_set_home_pose = 1050
    ctrlr_coms_set_move_scale = 1015
    ctrlr_coms_set_gravity = 1016
    ctrlr_coms_set_outputs = 14
    ctrlr_coms_set_payload = 1021
    ctrlr_coms_store_settings = 1300
    ctrlr_coms_set_tool = 1022
    # io func
    ctrlr_coms_set_dig_input_func = 1032
    ctrlr_coms_set_dig_output_func = 1033
    # wrist func
    ctrlr_coms_set_wrist_io = 17
    ctrlr_coms_set_wrist_dig_input_func = 1053
    ctrlr_coms_set_wrist_dig_output_func = 1054
