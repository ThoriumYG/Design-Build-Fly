import math
import os
import sys

import numpy as np

# Go up one level from the subfolder to the main folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import initializations as init


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
    if battery is None:
        return 0
    s, Q, C = battery[0], battery[1], battery[2]
    R_i = (init.k_Ri_1 * C + init.k_Ri_2) / (C * Q / 3600)  # cell resistance, Q in Ah
    a, b = s * R_i, -s * init.U0_cell
    return (-b - math.sqrt(b**2 - 4 * a * P)) / (2 * a)  # smaller root = real one
