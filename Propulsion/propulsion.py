# propulsion.py
"""
=============================================================================
 PROPULSION TEMPLATE  (TUM Design/Build/Fly WS 2026/27)
=============================================================================

HOW THIS FILE WORKS
-------------------
Part A  OUTPUTS       Functions the other teams call. Keep NAME, ARGUMENT,
                      RETURN TYPE and UNIT exactly as they are. Replace the
                      PLACEHOLDER body with a call to your calculation steps.
Part B  STEPS         The calculations you need, with the lecture equation in
                      each docstring (Propulsion input presentation).
                      Simple equations are already written; "TODO" is yours.

Component chain (lecture):  battery -> ESC -> motor -> propeller
    P_el (battery)  ->  P_el (motor)  ->  P_mech (shaft)  ->  T * v (flight)

WHAT WE NEED FROM OTHER TEAMS
-----------------------------
  nothing for now: the thrust demand T and the airspeed v come as arguments
  from Performance.

WHAT WE GIVE TO OTHER TEAMS (Part A)
------------------------------------
  max_thrust, battery_power_over_thrust, battery   -> Performance
  propulsion_weight                                -> Structures
  total_component_cost                             -> Performance (score)

Components may only be chosen from the RFP tables (init.propellers,
init.motors, init.batteries). Units: SI (N, m/s, W, V, A, rad/s).
"""

import math
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")  # repo root
sys.path.extend(
    [ROOT]
    + [
        os.path.join(ROOT, folder)
        for folder in ("Aerodynamics", "Structure", "Propulsion", "Performance")
    ]
)
import initializations as init


# ============================================================================
# PART A - OUTPUTS (other teams call these)
# ============================================================================
def max_thrust(design_variables):
    """Thrust at full throttle, standing still (v = 0)  [N].
    Used by: Performance (take-off at full thrust, climb + 25 m/s checks).
    Status: PLACEHOLDER (12 N). Later: propeller_thrust() at max rpm."""
    return 12.0


def battery_power_over_thrust(design_variables, T, v):
    """Electrical power the battery must deliver for thrust T [N] at airspeed
    v [m/s]. Returns float [W]. Used by: Performance in every phase.
    Status: PLACEHOLDER P = T v / 0.55 (constant efficiency).
    Later: solve the chain propeller -> motor -> ESC for this T and v."""
    powertrain_efficiency_placeholder = 0.55  # Miro note: constant for now (lecture 50-70 %)
    return T * v / powertrain_efficiency_placeholder


def battery(design_variables):
    """Selected battery: tuple (s, Q_batt [A s], C_rate [1/h], mass [kg], cost [EUR]),
    same format as init.batteries. Used by: Performance (70 % charge budget)."""
    return init.batteries[design_variables.get("battery", "3S_2200_20C")]


def propulsion_weight(design_variables):
    """Mass of motor + propeller + battery + ESC  [kg].  Used by: Structures."""
    m_motor = init.motors[design_variables.get("motor", "A30-22S")][0]
    m_prop = init.propellers[design_variables.get("propeller", "APC_9x6")][2]
    m_batt = battery(design_variables)[3]
    m_esc = init.fixed_components["esc"][1]
    return m_motor + m_prop + m_batt + m_esc


def total_component_cost(design_variables):
    """Price of all BOUGHT components (fixed RFP parts + motor, propeller,
    battery, gear, CFRP rods ...)  [EUR]. Printing cost NOT included
    (score_calculation adds it from structures.printing_time()).
    Status: PLACEHOLDER (500 EUR). Later: sum of the component costs."""
    total_component_cost_placeholder = 500.0  # [EUR], first rough estimate
    return total_component_cost_placeholder


# ============================================================================
# PART B - CALCULATION STEPS
# ============================================================================
# --- step 1: propeller ----------------------------------------------------------
def advance_ratio(v, n, D):
    """J = v / (n * D)  [-]; n in revolutions per second, D diameter [m]."""
    return v / (n * D)


def propeller_coefficients(propeller_name, J):
    """CT(J) and CP(J) of the chosen APC propeller, from measured data
    (UIUC propeller database).  TODO."""
    raise NotImplementedError("Propulsion: CT/CP data")


def propeller_thrust(CT, n, D, rho=init.rho):
    """T = CT * rho * n^2 * D^4  [N]."""
    return CT * rho * n**2 * D**4


def propeller_torque(CP, n, D, rho=init.rho):
    """Q = CP * rho * n^2 * D^5 / (2 pi)  [N m]."""
    return CP * rho * n**2 * D**5 / (2 * math.pi)


def propeller_efficiency(CT, CP, J):
    """eta_prop = T v / P = CT * J / CP  [-]."""
    return CT * J / CP


# --- step 2: motor (4 constants: KV, R_i, I0, U0 from the data sheet) --------
def motor_current(Q_tq, KV, I0):
    """I = Q * KV + I0  [A]  (Drela first-order model; KV in rad/(s V))."""
    return Q_tq * KV + I0


def motor_voltage(omega, I, KV, R_i):
    """U = omega / KV + I * R_i  [V]  (back-EMF + resistive loss)."""
    return omega / KV + I * R_i


# --- step 3: ESC ------------------------------------------------------------------
def esc_efficiency(U_out, U_in):
    """eta_ESC = 0.75 + 0.2 * theta,  theta = U_out / U_in <= 1  [-]."""
    theta = min(U_out / U_in, 1.0)
    return init.eta_ESC_a + init.eta_ESC_b * theta


# --- step 4: battery -----------------------------------------------------------------
def battery_voltage(battery_data, I):
    """U = s * (U0 - R_i,cell * I),  R_i,cell = (3.367e-3 C + 0.4097) / (C Q[Ah])  [V]."""
    s, Q, C = battery_data[0], battery_data[1], battery_data[2]
    R_i_cell = (init.k_Ri_1 * C + init.k_Ri_2) / (C * Q / 3600)
    return s * (init.U0_cell - R_i_cell * I)
