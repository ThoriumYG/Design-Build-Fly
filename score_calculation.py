"""
Inputs:
- Aircraft Mass
- CL_max
- Wing Area
- Max Thrust
- t_mission
- cost
Output:
- Score
"""

import numpy as np
import mission_sim as msim
import initializations as init
from Performance import overall_inputs

"""
def calc_d_to(m, cl_max, wing_area, max_thrust, cd_0, AR):
    W = m * init.g
    cl_to = (1 / c ** 2) * cl_max
    # Takeoff acceleration distance formula from Aircraft Design Basics
    d_to = (c ** 2 * (W / wing_area)) / (init.rho * init.g 
                                         * (cl_max * (max_thrust / W - mu_f)
                                            - (c ** 2 / 2) * (cd_0 + (cl_to ** 2) / (3 * np.pi * AR * e) - mu_f * cl_to)
                                            )
                                        )
    # Simplified formula
    # d_to = (c ** 2 * (W / wing_area)) / (init.rho * init.g * cl_max * (max_thrust / W))
    print(f"d_to = {d_to:.3f} m")
    return d_to
"""


def calc_score(t_mission, cost, v_stall, d_to, verbose=False):
    f_stall = 1 / (1 + np.exp(6 * (v_stall - 9.5)))
    f_to = 1 / (1 + np.exp(d_to - 45))

    p_mission = 200 * t_mission / cost
    score = p_mission * f_to * f_stall

    if verbose:
        print(f"f_stall = {f_stall}")
        print(f"f_to = {f_to}")
        print(f"Mission points (without knockdown factors) = {p_mission}")
        print(f"Mission points (knockdown factors included) = {score}")
    return score


# Test run with the placeholder values of the team files
if __name__ == "__main__":
    T_mission, d_to = msim.mission_sim(overall_inputs.DESIGN_VARIABLES_EXAMPLE, verbose=True)
    cost = 500
    v_stall = 8
    calc_score(T_mission, cost, v_stall, d_to, verbose=True)
