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
import sys
import os

# Go up one level from the subfolder to the main folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import initializations as init

# To be moved into initializations.py
c = 1.20 # liftoff speed 20% higher than stall speed
mu_f = 0.35 # should be reevaluated (range from 0.25 to 0.45 possible)
e = 0.85

def calc_v_stall(m, cl_max, wing_area):
    v_stall = np.sqrt((2 * m * init.g) / (init.rho * wing_area * cl_max))
    print(f"v_stall = {v_stall:.3f} m/s")
    return v_stall

def calc_f_stall(v_stall):
    f_stall = 1 / (1 + np.exp(6 * (v_stall - 9.5)))
    return f_stall

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

def calc_f_to(d_to):
    f_to = 1 / (1 + np.exp(d_to - 45))
    return f_to

def calc_score(t_mission, cost, f_stall, f_to):
    p_mission = 200 * t_mission / cost
    score = p_mission * f_to * f_stall
    return score

if __name__ == "__main__":
    # Test values
    m = 2
    cl_max = 1.3
    wing_area = 0.4
    max_thrust = 10
    cd_0 = 0.02
    AR = 10
    t_mission = 2000
    cost = 500

    print("Hello there!")

    f_stall = calc_f_stall(calc_v_stall(m, cl_max, wing_area))
    print(f"f_stall = {f_stall}")
    f_to = calc_f_to(calc_d_to(m, cl_max, wing_area, max_thrust, cd_0, AR))
    print(f"f_to = {f_to}")
    score = calc_score(t_mission, cost, f_stall, f_to)
    print(f"Mission points (knockdown factors included): {score}")