"""
mission_sim.py

Simulates the mission for a given configuration and returns T_mission.

1. Takeoff
2a. Set v_cruise = v_stall + 3 m/s
2b. Climb + 4 cruise laps with v_cruise
3. Mission -> Loop until 70% of capacity used
4a. Store T_mission for current cruise speed.
4b. If not iterated through all v_cruise, continue with next at 2b.
5. Pick best cruise speed for current config (= max T_mission).
6. Return T_mission.
"""

import initializations as init
from Aerodynamics import aerodynamics
from Performance import mission_phases as phases
from Propulsion import propulsion
from Structure import structures


def mission_sim(design_variables, verbose=False):
    """Simulate the whole mission and return T_mission [s]."""
    dv = design_variables

    # Inputs from the team files
    m = structures.aircraft_mass(dv)
    S = aerodynamics.wing_area(dv)
    CL_max = aerodynamics.CL_max(dv)
    polar = aerodynamics.CLCD_polar(dv)
    T_max = propulsion.max_thrust(dv)
    battery = propulsion.battery(dv)
    v_cruise = dv["cruise_speed"]  # array of cruise speeds to try [m/s]

    def power(T, v):  # battery power [W] for thrust T at speed v
        return propulsion.battery_power_over_thrust(dv, T, v)

    # Mission
    charge_budget = init.battery_use * battery[1]  # 70 % of capacity [A s]

    # Takeoff
    t_to, d_to, q_to = phases.takeoff(m, S, CL_max, T_max, polar, battery)

    # Loop through all cruise speeds
    max_T_mission = 0
    v_cruise_max_T = 0
    for v_c in v_cruise:
        # Climb
        t_cl, q_cl = phases.climb(m, S, v_c, polar, battery, power)
        # Cruise
        t_cr, q_cr = phases.cruise(m, S, v_c, polar, battery, power)

        # Check if enough charge available before going into reconnaissance
        charge_left = charge_budget - (q_to + q_cl + q_cr)
        if charge_left <= 0:  # 70 % used before the recon starts
            T_mission, q_re = 0.0, 0.0  # -> design not valid
        else:
            # Reconnaissance
            T_mission, q_re = phases.recon(m, S, charge_left, polar, battery, power)

        # Store highest mission time and corresponding cruise velocity
        if T_mission > max_T_mission:
            max_T_mission = T_mission
            v_cruise_max_T = v_c

    if verbose:
        print(f"{'phase':<10}{'time [s]':>10}{'charge [mAh]':>14}")
        for name, t, q in [
            ("take-off", t_to, q_to),
            ("climb", t_cl, q_cl),
            ("cruise", t_cr, q_cr),
            ("recon", max_T_mission, q_re),
        ]:
            print(f"{name:<10}{t:10.1f}{q / 3.6:14.0f}")
        print(
            f"T_mission = {max_T_mission:.0f} s ({max_T_mission / 60:.1f} min) at v_cruise = {v_cruise_max_T} m/s"
        )

    return max_T_mission, d_to


# Test run with the placeholder values of the team files
if __name__ == "__main__":
    from Analysis_and_Optimization.baseline_design import BASELINE_DESIGN

    mission_sim(BASELINE_DESIGN, verbose=True)
