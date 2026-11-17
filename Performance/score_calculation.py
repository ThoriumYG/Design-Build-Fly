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

# Constants
G = 9.80665
RHO = 1.225

def calc_v_stall(m, cl_max, wing_area):
    v_stall = np.sqrt((2 * m * G) / (RHO * wing_area * cl_max))
    print(f"v_stall = {v_stall:.3f} m/s")
    return v_stall

def calc_f_stall(v_stall):
    f_stall = 1 / (1 + np.exp(6 * (v_stall - 9.5)))
    return f_stall

def calc_d_to(m, cl_max, wing_area, max_thrust):
    """
    INSERT CORRECT CALCULATION METHOD HERE
    """
    d_to = 45 # Placeholder
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
    cl_max = 2
    wing_area = 0.4
    max_thrust = 10
    t_mission = 2000
    cost = 500

    print("Hello there!")

    f_stall = calc_f_stall(calc_v_stall(m, cl_max, wing_area))
    print(f"f_stall = {f_stall}")
    f_to = calc_f_to(calc_d_to(m, cl_max, wing_area, max_thrust))
    print(f"f_to = {f_to}")
    score = calc_score(t_mission, cost, f_stall, f_to)
    print(f"Mission points (knockdown factors included): {score}")