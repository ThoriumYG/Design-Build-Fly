"""
takeoff.py

Calculates takeoff distance and energy/charge consumed during takeoff.
"""
import numpy as np
import math

import sys
import os

import helpers

# Go up one level from the subfolder to the main folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import initializations as init

def takeoff(m, S, CL_max, T_static, polar, battery, A_prop=0.03, eta=0.6,
            mu=0.08, CL_roll=0.3, dCD_gear=0.0, t_max=60.0):
    """Ground roll at full throttle until lift-off speed (1.2 * v_stall).
    Returns roll time [s], roll distance [m], consumed charge [As]."""
    g = init.g
    rho = init.rho
    v_lo = 1.2 * math.sqrt(2 * m * g / (rho * S * CL_max)) # 1.2*v_stall (conservative)
    
    if polar is not None:
        CD_roll = np.interp(CL_roll, polar[0], polar[1]) + dCD_gear
    else:
        cd_0 = 0.03
        k_ground = 3
        AR = 10
        e = 0.85
        CD_roll = cd_0 + CL_roll ** 2 / (k_ground * np.pi * AR * e)

    s = v = t = Q = 0.0
    dt = 0.01
    while v < v_lo:
        T = T_static                     # optional: T(v) from propeller data
        q = 0.5 * rho * v**2 * S
        D = q * CD_roll
        L = q * CL_roll
        a = (T - D - mu * max(m * g - L, 0.0)) / m

        # Shaft power
        P_shaft = T * (v / 2 + math.sqrt(v**2 / 4 + T / (2 * rho * A_prop))) / eta
        Q += helpers.battery_current(P_shaft, battery) * dt

        v += a * dt
        s += v * dt
        t += dt
        if t > t_max or a <= 0 and v < v_lo:
            raise ValueError("Insufficient thrust.")

    return t, s, Q


def climb(m, S, v, polar, battery, power):
    """Climb to 70 m with 2 m/s vertical speed: thrust = drag + weight * sin(angle)."""
    angle = math.asin(init.vz_climb / v)
    thrust = helpers.drag_force(m, S, v, polar, init.rho) + m * init.g * math.sin(angle)     # additional thrust needed to compensate climb
    t = init.h_cruise / init.vz_climb                 # 70 m / 2 m/s = 35 s
    I = helpers.battery_current(power(thrust, v), battery)
    Q = I * t
    return t, Q


def pattern_lap(m, S, v, straight, radius, polar, battery, power):
    """One lap (2 straights + 2 half circles): returns (time, charge)."""
    # straights
    t_straight = 2 * straight / v
    I_straight = helpers.battery_current(power(helpers.drag_force(m, S, v, polar, init.rho), v), battery)
    # turns: more lift needed -> more drag
    n = helpers.turn_load_factor(v, radius)
    t_turn = 2 * math.pi * radius / v
    I_turn = helpers.battery_current(power(helpers.drag_force(m, S, v, polar, init.rho, n), v), battery)
    return t_straight + t_turn, I_straight * t_straight + I_turn * t_turn


def cruise(m, S, v, polar, battery, power):
    """4 laps of the cruise pattern (4 * 891 m = 3565 m, RFP: approx. 3570 m)."""
    t_lap, q_lap = pattern_lap(m, S, v, init.l_cruise_straight, init.r_cruise_turn,
                               polar, battery, power)
    return init.n_laps * t_lap, init.n_laps * q_lap


def recon(m, S, charge_left, polar, rho, battery, power):
    """Fly the recon pattern at 20 m/s until the remaining charge is used."""
    t_lap, q_lap = pattern_lap(m, S, init.v_recon, init.l_recon_straight,
                               init.r_recon_turn, polar, battery, power)
    t = charge_left / (q_lap / t_lap)                 # remaining charge / average current
    return t, charge_left


if __name__ == "__main__":
    # Test data
    m = 2
    S = 0.4
    v_cruise = 14
    CL_max = 1.3
    AR = 7
    polar = np.array([
    # CL
    [-0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3, 0.4, 0.5,
      0.6,  0.7,  0.8,  0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
    # CD
    [0.0505, 0.0442, 0.0391, 0.0351, 0.0323, 0.0306, 0.0300, 0.0306, 0.0323, 0.0351,
     0.0391, 0.0442, 0.0505, 0.0579, 0.0664, 0.0760, 0.0869, 0.1098, 0.1519],
    ])

    print(takeoff(m, S, CL_max, AR, polar))
    print(climb(m, S, v_cruise, polar))