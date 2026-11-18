# initializations.py
"""
Shared start values for the TUM Design/Build/Fly WS 2026/27 design program.
Sources: RFP V1 (28.10.2026) and the input presentations (Introduction,
Performance, Aerodynamics, Propulsion, Structure).

All values in SI units (m, kg, s, N, W, V, A, rad). Costs in EUR.
x positions are measured from the wing spar/joiner, negative = forward.
Import with:  import initializations as init   (then use init.g, init.rho, ...)
"""
import math

# ============================================================================
# constants
# ============================================================================
g = 9.81                      # gravitational acceleration                [m/s^2]
rho = 1.225                   # air density, ISA sea level                [kg/m^3]
T0 = 288.15                   # air temperature, ISA sea level            [K]
p0 = 101325.0                 # air pressure, ISA sea level               [Pa]
R_air = 287.05                # specific gas constant of air              [J/(kg K)]
kappa = 1.4                   # ratio of specific heats of air            [-]
mu = 1.81e-5                  # dynamic viscosity of air at T0            [Pa s]
nu = mu / rho                 # kinematic viscosity of air                [m^2/s]
a0 = math.sqrt(kappa * R_air * T0)  # speed of sound                      [m/s]

# --- 3D printing (Prusa PETG), Structure slides 22-23 / RFP p. 8 ---
rho_PETG = 1270.0             # density of printed material               [kg/m^3]
t_shell = 0.4e-3              # shell thickness per wall (x2 in formula)  [m]
infill = 0.08                 # infill volume fraction                    [-]
print_rate = 20e-6 / 3600.0   # printing speed 20 cm^3/h                  [m^3/s]
print_cost_rate = 10.0 / 3600.0  # printing cost 10 EUR/h                 [EUR/s]
T_print_free = 30.0 * 3600.0  # print time before penalty starts          [s]
k_print_penalty = 0.4 / 3600.0   # exponent factor, cost_pen = e^(k(T-T_free)) [1/s]

# --- spar caps (CFRP rods 1.0 mm) ---
d_CFRP_rod = 1.0e-3           # rod diameter                              [m]
m_per_l_CFRP = 1.2e-3         # rod mass per length                       [kg/m]
cost_per_l_CFRP = 2.0         # rod cost per length                       [EUR/m]

# --- nose landing gear (wire, sold per length) ---
m_per_l_nose_gear = 91.7e-3   # mass per length                           [kg/m]
cost_per_l_nose_gear = 3.0    # cost per length                           [EUR/m]

# --- battery model (Propulsion slide 20) ---
U0_cell = 3.7                 # nominal cell voltage                      [V]
k_Ri_1 = 3.367e-3             # R_i,cell = (k_Ri_1*C + k_Ri_2)/(C*Q)      [-]
k_Ri_2 = 0.4097               #                                           [-]

# --- ESC model (Propulsion slide 16): eta = a + b*theta, theta <= 1 ---
eta_ESC_a = 0.75              #                                           [-]
eta_ESC_b = 0.20              #                                           [-]

# ============================================================================
# RFP parameters
# ============================================================================
# --- geometry limits ---
b_max = 2.0                   # maximum wingspan                          [m]
l_boom = 1.0                  # tail boom length (fixed, not shortened)   [m]
d_boom = 0.012                # tail boom diameter                        [m]
l_spar_cap_max = 1.0          # maximum length of one spar cap            [m]
washout_tip_max = math.radians(-1.0)  # wing tip washout, at least -1 deg [rad]
x_batt_min = -0.220           # battery body must lie within [min, max]   [m]
x_batt_max = -0.040           #   (relative to wing joiner)               [m]
n_actuators = 2               # exactly two actuators                     [-]

# --- stability & aerodynamics ---
SM_min = 0.18                 # static margin, -dCm/dCL >= 18 %           [-]
ncrit = 7                     # XFOIL transition parameter                [-]

# --- speeds ---
v_max_min = 25.0              # max level-flight speed must reach this    [m/s]
v_recon = 20.0                # fixed speed in reconnaissance phase       [m/s]
dv_stall_margin = 3.0         # every flight speed >= v_stall + 3 m/s     [m/s]
v_stall_ref = 9.5             # f_stall = 0.5 at this stall speed         [m/s]
# (flight speeds may only be set as whole numbers)

# --- mission ---
h_cruise = 70.0               # climb altitude                            [m]
vz_climb = 2.0                # vertical speed during climb               [m/s]
n_laps = 4                    # cruise laps                               [-]
s_cruise_total = 3570.0       # total distance of the 4 laps (approx.)    [m]
l_cruise_straight = 320.0     # cruise lap straight                       [m]
r_cruise_turn = 40.0          # cruise lap turn radius                    [m]
l_recon_straight = 350.0      # recon pattern straight                    [m]
r_recon_turn = 50.0           # recon pattern turn radius                 [m]
battery_use = 0.70            # mission ends at 70 % capacity used        [-]

# --- structure ---
n_z = 6.0                     # max load factor for bending               [-]
SF = 1.5                      # safety factor, all structure calcs        [-]
SF_print = 2.0                # printed parts in bending w/o CFRP         [-]
twist_tip_max = math.radians(4.0)  # max torsional tip deformation        [rad]
v_torsion = 25.0              #   ... checked at this speed               [m/s]
tail_area_ratio_max = 0.20    # "normal" tail: S_tail < 20 % S_wing       [-]
tail_spar_span = 0.80         # tail spar cap runs to 80 % of tail span   [-]

# --- scoring (RFP section 5) ---
k_mission = 200.0             # P_mission = 200 * T_mission[s] / cost_AC  [-]
d_TO_ref = 45.0               # f_TO = 1/(1+e^(d_TO-45 m))                [m]
k_stall = 6.0                 # f_stall = 1/(1+e^(6(v_stall-9.5)))        [s/m]
P_prediction_max = 20.0       # precise prediction bonus                  [-]

# --- fixed components: name: (x_CG [m], mass [kg], cost [EUR]) ---
fixed_components = {
    "flight_controller": (0.030, 0.007, 138.0),
    "gnss_sensor":       (0.030, 0.012,  50.0),
    "airspeed_sensor":   (0.080, 0.005,  70.0),
    "receiver":          (0.088, 0.007,  75.0),
    "esc":               (-0.130, 0.010, 30.0),
    "actuator_left":     (0.081, 0.027,  35.0),
    "actuator_right":    (0.092, 0.027,  35.0),
    "dronetag":          (0.030, 0.005,  50.0),
    "camera_system":     (0.030, 0.055, 170.0),
    "telemetry_modem":   (0.800, 0.005,  21.0),
    "telemetry_cable":   (0.400, 0.007,   5.0),
    "fuselage":          (-0.025, 0.420, 50.0),
    "tail_boom":         (0.300, 0.055,  16.0),
    "wing_joiner":       (0.000, 0.025,   5.0),
    "spinner":           (-0.300, 0.025, 11.0),
}
# gear parts with variable x_CG: name: (mass [kg], cost [EUR])
main_gear_adaptor = (0.010, 5.0)
wheel = (0.006, 3.0)          # 63 mm x 12 mm
nose_gear_adaptor = (0.010, 8.0)
x_gear_options = [-0.200, -0.160, -0.120, 0.040, 0.080, 0.120]  # [m]

# --- variable components ---
# main landing gear: (wheelbase [m], height [m], mass [kg], cost [EUR])
main_gears = {
    "190x95":  (0.190, 0.095, 0.018, 16.0),
    "245x110": (0.245, 0.110, 0.029, 28.0),
    "300x140": (0.300, 0.140, 0.054, 32.0),
}
# propellers APC Thin Electric: (D [m], pitch [m], mass [kg], cost [EUR]), x_CG = -0.300 m
x_prop = -0.300
propellers = {
    "APC_8x6":   (8 * 0.0254, 6.0 * 0.0254, 0.015, 4.0),
    "APC_8x8":   (8 * 0.0254, 8.0 * 0.0254, 0.015, 4.0),
    "APC_9x6":   (9 * 0.0254, 6.0 * 0.0254, 0.019, 4.0),
    "APC_9x7.5": (9 * 0.0254, 7.5 * 0.0254, 0.019, 5.0),
    "APC_9x9":   (9 * 0.0254, 9.0 * 0.0254, 0.019, 5.0),
}
# motors Hacker: (mass [kg], cost [EUR]), x_CG = -0.260 m
# (KV, R_i, I0, U0 still to be taken from the manufacturer data sheets)
x_motor = -0.260
motors = {
    "A30-22S": (0.083, 76.0),
    "A30-28S": (0.083, 76.0),
    "A30-12M": (0.113, 83.0),
    "A30-16M": (0.113, 83.0),
    "A30-14L": (0.143, 89.0),
}
# batteries XTRON 3S1P: (cells in series s, capacity Q [As], C-rate [1/h], mass [kg], cost [EUR])
batteries = {
    "3S_1800_50C": (3, 1.8 * 3600, 50, 0.158, 30.0),
    "3S_2200_20C": (3, 2.2 * 3600, 20, 0.167, 23.0),
    "3S_2200_50C": (3, 2.2 * 3600, 50, 0.181, 35.0),
}

'''
Further variable names (use these in every module)
----------------------------------------------------------------------------
m           total aircraft mass                         [kg]
W           weight, m*g                                 [N]
S           wing reference area                         [m^2]
b           wingspan                                    [m]
AR          aspect ratio, b^2/S                         [-]
lam         taper ratio, c_tip/c_root                   [-]
c_root      root chord                                  [m]
c_tip       tip chord                                   [m]
c_mac       mean aerodynamic chord                      [m]
S_wet       wetted surface                              [m^2]
V_wing      wing volume                                 [m^3]
Re          Reynolds number, v*c/nu                     [-]
alpha       angle of attack                             [rad]
CL          lift coefficient                            [-]
CD          drag coefficient                            [-]
CD0         zero-lift drag coefficient                  [-]
CM          pitching moment coefficient                 [-]
e           Oswald efficiency factor                    [-]
L           lift                                        [N]
D           drag                                        [N]
x_NP        neutral point (from wing root LE)           [m]
x_CG        centre of gravity (from wing root LE)       [m]
SM          static margin                               [-]
S_HT        horizontal tail area                        [m^2]
v           true airspeed                               [m/s]
v_stall     stall speed                                 [m/s]
T           thrust                                      [N]
Q_tq        propeller/motor torque                      [N m]
n           propeller speed                             [1/s]
D_prop      propeller diameter                          [m]
J           advance ratio, v/(n*D_prop)                 [-]
CT          thrust coefficient                          [-]
CP          power coefficient                           [-]
eta_prop    propeller efficiency                        [-]
eta_motor   motor efficiency                            [-]
eta_ESC     ESC efficiency                              [-]
KV          motor speed constant                        [rad/(s V)]
R_i         motor inner resistance                      [Ohm]
I0          motor zero-torque current                   [A]
U           voltage                                     [V]
I           current                                     [A]
P_el        electrical power                            [W]
P_mech      mechanical (shaft) power                    [W]
E_batt      battery energy                              [J]
Q_batt      battery capacity                            [A s]
M_b         bending moment                              [N m]
M_t         torsional moment                            [N m]
Temp        temperature                                 [K]
T_print     printing time                               [s]
cost_AC     total aircraft cost                         [EUR]
T_mission   recon mission time                          [s]
d_TO        take-off distance                           [m]
'''
