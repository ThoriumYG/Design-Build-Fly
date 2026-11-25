# mission_performance_v2.py
"""
Calculates T_mission: how long the aircraft can fly the recon phase.

Mission (RFP section 3):
  1. Take-off  : full thrust, standing start on grass
  2. Climb     : to 70 m, at cruise speed, 2 m/s vertical speed
  3. Cruise    : 4 laps (320 m straights, 40 m turn radius), at cruise speed
  4. Recon     : 20 m/s (fixed), until 70 % of the battery charge is used
                 -> T_mission = duration of this phase

Idea: every phase uses some battery charge. Take-off, climb and cruise come
first; whatever is left of the 70 % is used in the recon phase.

All inputs come from the team files (aerodynamics.py, structures.py,
propulsion.py) and overall_inputs.py. Units: SI (m, kg, s, N, W, A).
Usage:  T_mission = mission_time(design_variables)
"""

import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")  # repo root
sys.path.extend(
    [ROOT]
    + [
        os.path.join(ROOT, folder)
        for folder in ("Aerodynamics", "Structure", "Propulsion", "Performance")
    ]
)
import initializations as init
import overall_inputs
import aerodynamics
import propulsion
import structures


# ============================================================================
# Physics helpers
# ============================================================================
def drag_force(m, S, v, polar, rho, load_factor=1.0):
    """Drag [N] in steady flight. load_factor > 1 in turns."""
    CL = 2 * load_factor * m * init.g / (rho * v**2 * S)  # lift = weight * n
    CD = np.interp(CL, polar[0], polar[1])  # read CD from polar
    return 0.5 * rho * v**2 * S * CD


def turn_load_factor(v, R):
    """Load factor n in a level turn with radius R [m]: n = 1 / cos(bank)."""
    bank = math.atan(v**2 / (init.g * R))
    return 1 / math.cos(bank)


def battery_current(P, battery):
    """Battery current [A] for power P [W] (battery model, Propulsion lecture).

    U = s * (U0 - R_i * I) and P = U * I  ->  solve the quadratic for I.
    """
    s, Q, C = battery[0], battery[1], battery[2]
    R_i = (init.k_Ri_1 * C + init.k_Ri_2) / (C * Q / 3600)  # cell resistance, Q in Ah
    a, b = s * R_i, -s * init.U0_cell
    return (-b - math.sqrt(b**2 - 4 * a * P)) / (2 * a)  # smaller root = real one


# ============================================================================
# Mission phases: each returns (duration [s], charge used [A s])
# ============================================================================
def takeoff(m, S, CL_max, T_max, polar, rho, battery, power):
    """Ground roll at full thrust until lift-off speed (1.2 * stall speed)."""
    mu_grass = 0.08  # rolling friction, short grass
    v_liftoff = 1.2 * math.sqrt(2 * m * init.g / (rho * S * CL_max))
    CD_roll = np.interp(0.3, polar[0], polar[1])  # CL ~ 0.3 while on the wheels

    v, t, dt = 0.0, 0.0, 0.01
    while v < v_liftoff:  # step through the ground roll
        drag = 0.5 * rho * v**2 * S * CD_roll
        acceleration = (T_max - drag - mu_grass * m * init.g) / m
        v += acceleration * dt
        t += dt

    # Power at average roll speed (0.7 * v_liftoff); P = T*v would give 0 at v = 0.
    I = battery_current(power(T_max, 0.7 * v_liftoff), battery)
    return t, I * t


def climb(m, S, v, polar, rho, battery, power):
    """Climb to 70 m with 2 m/s vertical speed: thrust = drag + weight * sin(angle)."""
    angle = math.asin(init.vz_climb / v)
    thrust = drag_force(m, S, v, polar, rho) + m * init.g * math.sin(angle)
    t = init.h_cruise / init.vz_climb  # 70 m / 2 m/s = 35 s
    I = battery_current(power(thrust, v), battery)
    return t, I * t


def pattern_lap(m, S, v, straight, radius, polar, rho, battery, power):
    """One racetrack lap (2 straights + 2 half circles): returns (time, charge)."""
    # straights
    t_straight = 2 * straight / v
    I_straight = battery_current(power(drag_force(m, S, v, polar, rho), v), battery)
    # turns: more lift needed -> more drag
    n = turn_load_factor(v, radius)
    t_turn = 2 * math.pi * radius / v
    I_turn = battery_current(power(drag_force(m, S, v, polar, rho, n), v), battery)
    return t_straight + t_turn, I_straight * t_straight + I_turn * t_turn


def cruise(m, S, v, polar, rho, battery, power):
    """4 laps of the cruise pattern (4 * 891 m = 3565 m, RFP: approx. 3570 m)."""
    t_lap, q_lap = pattern_lap(
        m, S, v, init.l_cruise_straight, init.r_cruise_turn, polar, rho, battery, power
    )
    return init.n_laps * t_lap, init.n_laps * q_lap


def recon(m, S, charge_left, polar, rho, battery, power):
    """Fly the recon pattern at 20 m/s until the remaining charge is used."""
    t_lap, q_lap = pattern_lap(
        m, S, init.v_recon, init.l_recon_straight, init.r_recon_turn, polar, rho, battery, power
    )
    t = charge_left / (q_lap / t_lap)  # remaining charge / average current
    return t, charge_left


# ============================================================================
# Main function
# ============================================================================
def mission_time(design_variables, verbose=False):
    """Simulate the whole mission and return T_mission [s]."""
    dv = design_variables

    # --- inputs from the team files ---
    m = structures.aircraft_mass(dv)
    S = aerodynamics.wing_area(dv)
    CL_max = aerodynamics.CL_max(dv)
    polar = aerodynamics.CLCD_polar(dv)
    T_max = propulsion.max_thrust(dv)
    battery = propulsion.battery(dv)
    v_cruise = overall_inputs.cruise_speed(dv)
    rho = overall_inputs.air_density(dv)

    def power(T, v):  # battery power [W] for thrust T at speed v
        return propulsion.battery_power_over_thrust(dv, T, v)

    # --- fly the mission ---
    charge_budget = init.battery_use * battery[1]  # 70 % of capacity [A s]

    t_to, q_to = takeoff(m, S, CL_max, T_max, polar, rho, battery, power)
    t_cl, q_cl = climb(m, S, v_cruise, polar, rho, battery, power)
    t_cr, q_cr = cruise(m, S, v_cruise, polar, rho, battery, power)

    charge_left = charge_budget - (q_to + q_cl + q_cr)
    if charge_left <= 0:  # 70 % used before the recon starts
        T_mission, q_re = 0.0, 0.0  # -> design not valid
    else:
        T_mission, q_re = recon(m, S, charge_left, polar, rho, battery, power)

    if verbose:
        print(f"{'phase':<10}{'time [s]':>10}{'charge [mAh]':>14}")
        for name, t, q in [
            ("take-off", t_to, q_to),
            ("climb", t_cl, q_cl),
            ("cruise", t_cr, q_cr),
            ("recon", T_mission, q_re),
        ]:
            print(f"{name:<10}{t:10.1f}{q / 3.6:14.0f}")
        print(f"T_mission = {T_mission:.0f} s ({T_mission / 60:.1f} min)")

    return T_mission


# ============================================================================
# Test run with the placeholder values of the team files
# ============================================================================
if __name__ == "__main__":
    mission_time(overall_inputs.DESIGN_VARIABLES_EXAMPLE, verbose=True)
