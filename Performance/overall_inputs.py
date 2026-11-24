# overall_inputs.py
"""
OVERALL INPUTS: values that no sub-team calculates. We (team lead / optimiser)
choose them, or the RFP fixes them.

WHAT IS `design_variables`?
---------------------------
Every function in every team file takes ONE argument: `design_variables`.
It is a Python dictionary that describes ONE aircraft configuration, i.e. the
numbers WE choose (wing span, wing area, cruise speed, battery, ...).
The optimiser changes these numbers in every iteration to find the best
aircraft. All teams get the same dictionary, so all teams calculate the SAME
aircraft. Each team reads only the keys it needs.

When your team needs a new design variable: add it to DESIGN_VARIABLES_EXAMPLE
below, with unit and meaning, so everybody knows it exists.

Units: always SI (m, kg, s, N, W, V, A, rad), costs in EUR.
"""

import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")  # repo root
sys.path.extend([ROOT] + [os.path.join(ROOT, folder) for folder in
                          ("Aerodynamics", "Structure", "Propulsion", "Performance")])
import initializations as init

# One example aircraft. Copy it, change the numbers, pass it to any function.
DESIGN_VARIABLES_EXAMPLE = {
    # --- flight ---
    "cruise_speed": 14.0,       # climb + 4 cruise laps [m/s]; RFP: whole number
                                # (14.0 ok, 14.5 not allowed), >= v_stall + 3 m/s
    "max_velocity": 25.0,       # highest level-flight speed [m/s]; RFP: >= 25
    # --- wing (Aerodynamics) ---
    "wing_span": 1.8,           # tip to tip [m]; RFP: <= 2.0
    "wing_area": 0.40,          # wing reference area [m^2]
    "wing_taper_ratio": 0.6,    # tip chord / root chord [-]
    # --- components (Propulsion) ---
    "battery": "3S_2200_20C",   # key of init.batteries (text)
    "motor": "A30-22S",         # key of init.motors (text)
    "propeller": "APC_9x6",     # key of init.propellers (text)
}


def cruise_speed(design_variables):
    """Airspeed of the climb and the 4 cruise laps [m/s].
    RFP: whole number (14.0 ok, 14.5 not), at least stall speed + 3 m/s."""
    return float(design_variables.get("cruise_speed", 14.0))


def mission_velocity(design_variables):
    """Airspeed of the recon (mission) phase [m/s]. Fixed by the RFP: 20 m/s."""
    return init.v_recon


def max_velocity(design_variables):
    """Highest level-flight speed the aircraft must reach [m/s]. RFP: >= 25 m/s."""
    return float(design_variables.get("max_velocity", init.v_max_min))


def air_density(design_variables):
    """Air density [kg/m^3]. Sea level standard atmosphere: 1.225."""
    return float(design_variables.get("air_density", init.rho))
