# interfaces.py
"""
=============================================================================
 INTERFACES BETWEEN THE SUB-TEAMS  (TUM Design/Build/Fly WS 2026/27)
=============================================================================

WHAT IS THIS FILE?
------------------
This file is the "contract" between the four sub-teams:
Aerodynamics, Structures, Propulsion and Performance.

Whenever one team needs a value from another team (for example Performance
needs the wing area from Aerodynamics), it gets that value by calling ONE
function in this file, e.g.

        S = interfaces.wing_area(design_variables)

Nobody imports another team's code directly. Everything goes through here.


THE THREE RULES
---------------
1. If you PROVIDE a value: write your code inside the body of your function
   in this file (usually one line that calls your own module).
2. NEVER change the function NAME, the ARGUMENTS, the RETURN TYPE or the UNIT.
   Other teams rely on them. If a change is really needed, tell the team lead
   first, so every team can update at the same time.
3. If you NEED a value: only call the function here. Do not copy numbers by
   hand and do not import another team's module.

Why: every team can rewrite its own code as often as it wants. As long as the
functions below keep their name, arguments and unit, nothing else breaks.


WHAT IS `design_variables`?
---------------------------
Every function takes ONE argument called `design_variables`.

`design_variables` is a Python dictionary that describes ONE aircraft
configuration: the numbers WE choose (wing span, wing area, cruise speed,
battery type, ...). The optimiser (Orchestrator.py) changes these numbers
in every iteration to find the best aircraft.

Why every function gets it: all teams must calculate the SAME aircraft at the
same time. If Aero used a 1.8 m wing span and Structures used 2.0 m, the
results would not fit together. Passing one shared dictionary prevents this.

Each team only reads the keys it needs and ignores the others.
A full example with all keys and their meaning is DESIGN_VARIABLES_EXAMPLE
below. When your team needs a new design variable, add it there (with unit
and description) so everybody knows it exists.


WHAT DO "PLACEHOLDER" AND "NotImplementedError" MEAN?
------------------------------------------------------
* PLACEHOLDER: the providing team has not connected its code yet. The function
  returns a rough test value so the whole program can already run.
  The value is NOT a design result. The providing team replaces it.
* NotImplementedError: nobody needs this value for the mission calculation
  yet, so there is not even a test value. Calling it stops the program with a
  message that says which team has to fill it in.


UNITS AND TYPES
---------------
* Always SI units: m, kg, s, N, W, V, A, rad. Costs in EUR.
  (So time is in SECONDS, not hours; angles in RADIANS, not degrees.)
* Default type: float (a number like 0.40). Other types are written in the
  function's description.


OVERVIEW: WHO GIVES WHAT TO WHOM  (from the Miro board)
-------------------------------------------------------
  Provided by     Function                      Used by
  --------------  ----------------------------  ------------------------------
  Overall input   cruise_speed                  Performance, Aerodynamics
                  mission_velocity              Performance, Aerodynamics
                  max_velocity                  Aerodynamics, Structures
                  air_density                   all teams
  Aerodynamics    wing_area                     Performance, Structures
                  CL_max                        Performance
                  CLCD_polar                    Performance
                  wing_planform                 Structures
                  lift_dist_stall_speed         Structures
                  lift_dist_max_speed           Structures
                  NP_position                   Performance (stability check)
                  static_margin                 Performance (stability check)
  Structures      aircraft_mass                 Performance, Aerodynamics
                  CG_position                   Aerodynamics
                  printing_time                 Performance
  Propulsion      max_thrust                    Performance
                  battery_power_over_thrust     Performance
                  battery                       Performance
                  propulsion_weight             Structures
                  total_component_cost          Performance

  Performance computes the final results in its own files (not here):
      T_mission                <- Performance/mission_simulation.py
      take-off distance, f_TO, f_stall, score  <- Performance/score_calculation.py
"""

import math

import numpy as np

import initializations as init  # shared constants and RFP values


# ============================================================================
# EXAMPLE OF `design_variables`  (one aircraft configuration)
# ============================================================================
# Copy this, change the numbers, and pass it to any function in this file.
# Keys = name of the design variable, value = the number we choose.
DESIGN_VARIABLES_EXAMPLE = {
    # --- flight ---
    "cruise_speed": 14.0,       # speed of the 4 cruise laps and the climb [m/s]
                                # RFP: must be a whole number (14.0 ok, 14.5
                                # not allowed) and at least stall speed + 3 m/s
    "max_velocity": 25.0,       # highest level-flight speed [m/s], RFP: >= 25
    # --- wing (Aerodynamics) ---
    "wing_span": 1.8,           # tip to tip [m], RFP: <= 2.0
    "wing_area": 0.40,          # wing reference area [m^2]
    "wing_taper_ratio": 0.6,    # tip chord / root chord [-]
    # --- components (Propulsion) ---
    "battery": "3S_2200_20C",   # key of init.batteries (text, not a number)
}


# ============================================================================
# OVERALL INPUTS
# Chosen by the team lead / optimiser, not calculated by a sub-team.
# ============================================================================
def cruise_speed(design_variables):
    """Airspeed during the climb and the 4 cruise laps.

    Returns : float, [m/s]
    Source  : design_variables["cruise_speed"] (we choose it)
    RFP     : - must be a whole number, e.g. 14.0 is allowed, 14.5 is not
              - must be at least (stall speed + 3 m/s)
    """
    return float(design_variables.get("cruise_speed", 14.0))


def mission_velocity(design_variables):
    """Airspeed during the reconnaissance (mission) phase.

    Returns : float, [m/s]
    Source  : fixed by the RFP to 20 m/s. We can NOT choose it.
    Why it is still here: Aerodynamics needs it for the polar and the
    lift distribution in the recon phase.
    """
    return init.v_recon


def max_velocity(design_variables):
    """Highest airspeed the aircraft must reach in level flight.

    Returns : float, [m/s]
    Source  : design_variables["max_velocity"], default 25 m/s
    RFP     : must be at least 25 m/s
    Used for: lift distribution at max speed (Aero), wing torsion check at
              25 m/s (Structures).
    """
    return float(design_variables.get("max_velocity", init.v_max_min))


def air_density(design_variables):
    """Density of the air.

    Returns : float, [kg/m^3]
    Source  : 1.225 kg/m^3 (standard atmosphere, sea level) unless
              design_variables["air_density"] is given.
    """
    return float(design_variables.get("air_density", init.rho))


# ============================================================================
# AERODYNAMICS  ->  filled in by the Aerodynamics team
# (their files: wing_creation.py, aero_coefficients.py,
#  Static_margin_calculation.py)
# ============================================================================
def wing_area(design_variables):
    """Wing reference area S.

    Returns : float, [m^2]
    Used by : Performance (lift and drag), Structures (wing mass)
    Status  : PLACEHOLDER, reads design_variables["wing_area"]
    """
    return float(design_variables.get("wing_area", 0.40))


def CL_max(design_variables):
    """Highest lift coefficient of the whole aircraft in TRIMMED flight.

    "Trimmed" = pitching moment is zero (C_M = 0), i.e. the aircraft flies
    steadily without pitching up or down. The RFP calculates the stall speed
    in exactly this state with XFLR5, so we must use the same.

    Returns : float, [-] (no unit)
    Used by : Performance (stall speed, f_stall, take-off speed)
    Status  : PLACEHOLDER (1.2)
    """
    return 1.2


def CLCD_polar(design_variables):
    """Drag polar of the WHOLE aircraft: which drag coefficient CD belongs to
    which lift coefficient CL.

    Returns : tuple (CL_values, CD_values)
              CL_values : numpy array, [-], sorted from small to large
              CD_values : numpy array, [-], same length as CL_values
    Example : (array([0.0, 0.1, ..., 1.2]), array([0.030, 0.031, ..., 0.11]))

    Requirements for Aerodynamics:
      - CD must include ALL drag: wing, tail, fuselage, landing gear, boom.
        Performance uses it directly as  Drag = 0.5 * rho * v^2 * S * CD.
      - CL range from about 0 up to CL_max, because Performance needs it in
        the ground roll (CL ~ 0.3), cruise, recon and turns (higher CL).

    Used by : Performance (drag in every mission phase)
    Status  : PLACEHOLDER, simple formula CD = 0.030 + CL^2 / (pi * 0.8 * AR)
    """
    planform = wing_planform(design_variables)
    aspect_ratio = planform["wing_span"] ** 2 / wing_area(design_variables)
    CL_values = np.linspace(0.0, CL_max(design_variables), 61)
    CD_values = 0.030 + CL_values**2 / (math.pi * 0.80 * aspect_ratio)
    return CL_values, CD_values


def wing_planform(design_variables):
    """Shape of the wing, needed by Structures for mass, bending and print time.

    Returns : dict with these keys
              "wing_span"         float, [m]    tip to tip
              "wing_inner_chord"  float, [m]    chord at the wing root
              "wing_taper_ratio"  float, [-]    tip chord / root chord
              "wing_NACA"         int           4-digit airfoil, e.g. 2412
              "wing_washout"      float, [rad]  twist at the tip (negative)
              "wing_spar_pos"     float, [-]    spar position / chord, e.g. 0.25
    (names follow the wing_creation.py inputs on the Miro board)

    Used by : Structures
    Status  : PLACEHOLDER (trapezoidal wing from span, area and taper ratio)
    """
    span = float(design_variables.get("wing_span", 1.8))
    taper = float(design_variables.get("wing_taper_ratio", 0.6))
    # trapezoid: area = span * root_chord * (1 + taper) / 2
    inner_chord = 2.0 * wing_area(design_variables) / (span * (1.0 + taper))
    return {
        "wing_span": span,
        "wing_inner_chord": inner_chord,
        "wing_taper_ratio": taper,
        "wing_NACA": 2412,
        "wing_washout": init.washout_tip_max,
        "wing_spar_pos": 0.25,
    }


def lift_dist_stall_speed(design_variables):
    """Lift along the half span when flying at stall speed.

    Returns : tuple (y, lift_per_span)
              y             : numpy array, [m],   0 = wing root, last = tip
              lift_per_span : numpy array, [N/m], lift on each wing station
    Used by : Structures (bending load case)
    Status  : NotImplementedError, Aerodynamics has to fill it in
    """
    raise NotImplementedError("Aerodynamics has to fill in lift_dist_stall_speed")


def lift_dist_max_speed(design_variables):
    """Lift along the half span when flying at max_velocity.

    Returns : tuple (y, lift_per_span), same format as lift_dist_stall_speed
    Used by : Structures (bending and torsion load case)
    Status  : NotImplementedError, Aerodynamics has to fill it in
    """
    raise NotImplementedError("Aerodynamics has to fill in lift_dist_max_speed")


def NP_position(design_variables):
    """Neutral point position x_NP.

    Returns : float, [m], measured from the wing root leading edge,
              positive = towards the tail
    Status  : NotImplementedError, Aerodynamics has to fill it in
    """
    raise NotImplementedError("Aerodynamics has to fill in NP_position")


def static_margin(design_variables):
    """Static margin SM = (x_NP - x_CG) / c_mac.

    Positive = stable. RFP requires SM >= 0.18 (18 %).
    Aero computes it with CG_position() from Structures.

    Returns : float, [-] (0.18 means 18 %)
    Status  : NotImplementedError, Aerodynamics has to fill it in
    """
    raise NotImplementedError("Aerodynamics has to fill in static_margin")


# ============================================================================
# STRUCTURES  ->  filled in by the Structures team
# ============================================================================
def aircraft_mass(design_variables):
    """Total take-off mass of the aircraft (everything: structure, battery,
    motor, avionics, fixed RFP components).

    Returns : float, [kg]
    Used by : Performance (weight in every phase), Aerodynamics (needed CL)
    Note    : includes propulsion_weight() from Propulsion. This is the value
              the mass loop in Orchestrator.py iterates until it stops changing.
    Status  : PLACEHOLDER (2.2 kg, first hand estimate)
    """
    return 2.2


def CG_position(design_variables):
    """Centre of gravity position x_CG.

    Returns : float, [m], measured from the wing root leading edge,
              positive = towards the tail (same reference as NP_position)
    Used by : Aerodynamics (static margin)
    Status  : NotImplementedError, Structures has to fill it in
    """
    raise NotImplementedError("Structures has to fill in CG_position")


def printing_time(design_variables):
    """Total 3D printing time of all printed parts.

    Returns : float, [s]  (SECONDS: 25 h = 25 * 3600 = 90000 s)
    Used by : Performance (printing cost 10 EUR/h and penalty above 30 h)
    Status  : PLACEHOLDER (25 h)
    """
    return 25.0 * 3600.0


# ============================================================================
# PROPULSION  ->  filled in by the Propulsion team
# ============================================================================
def max_thrust(design_variables):
    """Highest thrust the propulsion system gives at full throttle (standing
    still, i.e. at airspeed 0).

    Returns : float, [N]
    Used by : Performance (take-off run at full thrust, climb check,
              25 m/s top speed check)
    Status  : PLACEHOLDER (12 N)
    """
    return 12.0


POWERTRAIN_EFFICIENCY_PLACEHOLDER = 0.55
# Constant efficiency of propeller * motor * ESC together (Miro note: "for now
# we consider the powertrain efficiency to be constant"). The Propulsion
# lecture gives 50-70 % for the whole chain; 0.55 is on the cautious side.


def battery_power_over_thrust(design_variables, T, v):
    """Electrical power the battery must deliver to produce thrust T at
    airspeed v.

    Arguments: T : float, [N]    thrust needed (between 0 and max_thrust)
               v : float, [m/s]  airspeed (between 0 and max_velocity)
    Returns  : float, [W]
    Used by  : Performance, in every mission phase, to calculate how fast the
               battery is emptied.
    Status   : PLACEHOLDER, power = T * v / 0.55 (constant efficiency).
               Propulsion replaces this with its real component model
               (propeller CT/CP, motor KV/R_i/I0, ESC 0.75 + 0.2 * throttle).
    """
    return T * v / POWERTRAIN_EFFICIENCY_PLACEHOLDER


def battery(design_variables):
    """Data of the selected battery.

    Returns : tuple (s, Q_batt, C_rate, mass, cost)
              s      : int,   [-]    number of cells in series (3 for 3S)
              Q_batt : float, [A s]  capacity (2200 mAh = 2.2 * 3600 A s)
              C_rate : float, [1/h]  max discharge rate (20C -> 20)
              mass   : float, [kg]
              cost   : float, [EUR]
              Same format as init.batteries.
    Source  : design_variables["battery"], e.g. "3S_2200_20C"
    Used by : Performance (mission ends when 70 % of Q_batt is used)
    Note    : not on the Miro board yet, added because the "70 % of battery
              capacity" end of the mission cannot be calculated without it.
    """
    return init.batteries[design_variables.get("battery", "3S_2200_20C")]


def propulsion_weight(design_variables):
    """Mass of motor + propeller + battery + ESC together.

    Returns : float, [kg]
    Used by : Structures (total mass and CG)
    Status  : NotImplementedError, Propulsion has to fill it in
    """
    raise NotImplementedError("Propulsion has to fill in propulsion_weight")


def total_component_cost(design_variables):
    """Price of all BOUGHT components (fixed RFP parts + motor, propeller,
    battery, landing gear, ...).

    Returns : float, [EUR]
    Used by : Performance (aircraft cost in the score)
    Note    : printing cost is NOT included here. score_calculation.py adds it
              from printing_time(), so it is not counted twice.
    Status  : NotImplementedError, Propulsion has to fill it in
    """
    raise NotImplementedError("Propulsion has to fill in total_component_cost")
