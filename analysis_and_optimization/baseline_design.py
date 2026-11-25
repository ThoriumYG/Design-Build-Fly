"""
baseline_design.py

BASELINE_DESIGN: the reference aircraft every analysis starts from. These are
the values that no sub-team calculates. We (team lead / optimiser) choose them,
within the limits the RFP sets.

WHAT IS `design_variables`?
---------------------------
Every function in every team file takes ONE argument: `design_variables`.
It is a Python dictionary that describes ONE aircraft configuration, i.e. the
numbers WE choose (wing span, wing area, cruise speed, battery, ...).
An analysis changes some of these numbers (e.g. sweeps the wing span) and
keeps the rest from BASELINE_DESIGN. All teams get the same dictionary, so all
teams calculate the SAME aircraft. Each team reads only the keys it needs.

Rules:
- Team files and Performance functions never import BASELINE_DESIGN; they only
  use the `design_variables` they are given. Only analyses, `__main__` test
  blocks and tests import it.
- Analyses never modify BASELINE_DESIGN; they work on a copy:
      dv = {**BASELINE_DESIGN, "wing_span": 1.6}
- When your team needs a new design variable: add it here, with unit and
  meaning, so everybody knows it exists.
- Fixed RFP values (recon speed 20 m/s, minimum max speed 25 m/s, ...) are
  not design variables; they live in initializations.py.

Units: always SI (m, kg, s, N, W, V, A, rad), costs in EUR.
"""

import numpy as np

BASELINE_DESIGN = {
    # --- flight ---
    "cruise_speed": np.arange(11, 26),  # climb + 4 cruise laps [m/s]; RFP: whole number
    # (14.0 ok, 14.5 not allowed), >= v_stall + 3 m/s
    "max_velocity": 25.0,  # highest level-flight speed [m/s]; RFP: >= 25
    # --- wing (Aerodynamics) ---
    "wing_span": 1.8,  # tip to tip [m]; RFP: <= 2.0
    "wing_area": 0.40,  # wing reference area [m^2]
    "wing_taper_ratio": 0.6,  # tip chord / root chord [-]
    # --- components (Propulsion) ---
    "battery": "3S_2200_20C",  # key of init.batteries (text)
    "motor": "A30-22S",  # key of init.motors (text)
    "propeller": "APC_9x6",  # key of init.propellers (text)
}
