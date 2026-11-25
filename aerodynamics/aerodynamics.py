# aerodynamics.py
"""
=============================================================================
 AERODYNAMICS TEMPLATE  (TUM Design/Build/Fly WS 2026/27)
=============================================================================

HOW THIS FILE WORKS
-------------------
Part A  OUTPUTS       Functions the other teams call. Keep NAME, ARGUMENT,
                      RETURN TYPE and UNIT exactly as they are. Replace the
                      PLACEHOLDER body with a call to your calculation steps.
Part B  STEPS         The calculations you need to get the outputs, with the
                      equation from the lecture in each docstring.
                      Simple equations are already written; "TODO" steps are
                      yours (XFOIL / XFLR5 / textbook methods).

WHAT WE NEED FROM OTHER TEAMS (call these, never copy numbers)
--------------------------------------------------------------
  structures.aircraft_mass(design_variables)   [kg]   -> needed CL in flight
  structures.CG_position(design_variables)     [m]    -> static margin
  init.v_recon, init.rho                       fixed RFP / environment values
  design_variables["max_velocity"]             [m/s]  max-speed load case

WHAT WE GIVE TO OTHER TEAMS (Part A)
------------------------------------
  wing_area, CL_max, CLCD_polar              -> Performance
  wing_planform, lift_dist_stall_speed,
  lift_dist_max_speed                        -> Structures
  NP_position, static_margin                 -> stability check (RFP SM >= 18 %)

Units: SI (m, kg, s, N, rad). Status words: PLACEHOLDER = rough test value so
the program runs; NotImplementedError = not done yet, nobody can use it.
"""

import math

try:
    import numpy as np
except ImportError:
    np = None

import initializations as init
from structure import structures


# ============================================================================
# PART A - OUTPUTS (other teams call these)
# ============================================================================
def wing_area(design_variables):
    """Wing reference area S.  Returns float [m^2].  Used by: Performance, Structures.
    Status: PLACEHOLDER (reads design_variables["wing_area"])."""
    return float(design_variables.get("wing_area", 0.40))


def CL_max(design_variables):
    """Highest TRIMMED lift coefficient of the aircraft (C_M = 0, as the RFP
    recalculates v_stall with XFLR5).  Returns float [-].
    Used by: Performance (stall speed, f_stall, take-off).
    Status: PLACEHOLDER (1.2). Later: from wing_polar() at trim."""
    return 1.2


def CLCD_polar(design_variables):
    """Drag polar of the WHOLE aircraft: CD for each CL.
    Returns tuple (CL_values, CD_values): two numpy arrays, CL ascending,
    from ~0 up to CL_max. CD includes ALL drag (wing, tail, fuselage, gear, boom).
    Used by: Performance (drag in every mission phase).
    Status: PLACEHOLDER parabolic polar. Later: aircraft_polar()."""
    S = wing_area(design_variables)
    AR = aspect_ratio(wing_planform(design_variables)["wing_span"], S)
    cl_max = CL_max(design_variables)
    CL_values = [i * cl_max / 60.0 for i in range(61)]
    CD_values = [0.030 + induced_drag_coefficient(cl, AR, e=0.80) for cl in CL_values]
    if np is not None:
        CL_values = np.array(CL_values)
        CD_values = np.array(CD_values)
    return CL_values, CD_values


def wing_planform(design_variables):
    """Wing geometry for Structures.
    Returns dict: wing_span [m], wing_inner_chord [m], wing_taper_ratio [-],
    wing_NACA [int], wing_washout [rad], wing_spar_pos [-, fraction of chord].
    Status: PLACEHOLDER trapezoidal wing. Later: from wing_creation.py."""
    span = float(design_variables.get("wing_span", 1.8))
    taper = float(design_variables.get("wing_taper_ratio", 0.6))
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
    """Lift along the half span at stall speed.
    Returns tuple (y [m] root->tip, lift_per_span [N/m]).  Used by: Structures.
    Status: NotImplementedError. Use lift_distribution() at v_stall."""
    raise NotImplementedError("Aerodynamics: lift_dist_stall_speed")


def lift_dist_max_speed(design_variables):
    """Lift along the half span at max_velocity. Same format as above.
    Used by: Structures (bending + torsion at 25 m/s)."""
    raise NotImplementedError("Aerodynamics: lift_dist_max_speed")


def NP_position(design_variables):
    """Neutral point x_NP from the wing root leading edge [m], + = towards tail.
    Status: NotImplementedError (XFLR5 stability analysis)."""
    raise NotImplementedError("Aerodynamics: NP_position")


def static_margin(design_variables):
    """Static margin [-] (0.18 = 18 %). RFP: must be >= 0.18.
    SM = (x_NP - x_CG) / c_mac, with x_CG from Structures."""
    planform = wing_planform(design_variables)
    c_mac = mean_aerodynamic_chord(planform["wing_inner_chord"], planform["wing_taper_ratio"])
    return (NP_position(design_variables) - structures.CG_position(design_variables)) / c_mac


# ============================================================================
# PART B - CALCULATION STEPS (equations from the lecture / textbook)
# ============================================================================
# --- step 1: preliminary estimations -----------------------------------------
def reynolds_number(v, chord, nu=init.nu):
    """Re = v * c / nu  [-]. Needed to pick the right airfoil polar."""
    return v * chord / nu


def required_lift_coefficient(m, S, v, rho=init.rho, load_factor=1.0):
    """CL needed to carry n * m * g:  CL = 2 n m g / (rho v^2 S)  [-]."""
    return 2.0 * load_factor * m * init.g / (rho * v**2 * S)


# --- step 2: geometry --------------------------------------------------------
def aspect_ratio(span, S):
    """AR = b^2 / S  [-]."""
    return span**2 / S


def mean_aerodynamic_chord(c_root, taper):
    """c_mac of a trapezoidal wing = 2/3 c_root (1 + l + l^2)/(1 + l)  [m]."""
    return 2.0 / 3.0 * c_root * (1 + taper + taper**2) / (1 + taper)


# --- step 3: airfoil (2D, XFOIL) ----------------------------------------------
def airfoil_polar(naca, reynolds):
    """2D airfoil polar (alpha, cl, cd, cm) from XFOIL.
    RFP: ncrit = 7 (init.ncrit). NACA 4-digit for the wing,
    symmetric NACA 4-digit for the tail.  TODO."""
    raise NotImplementedError("Aerodynamics: XFOIL airfoil polar")


# --- step 4: wing (3D, XFLR5 / AVL) ----------------------------------------
def wing_polar(design_variables):
    """3D wing (+ tail) polar: CL, CDi, CM vs alpha from XFLR5 (constant-lift
    analysis, as the RFP requires).  TODO."""
    raise NotImplementedError("Aerodynamics: XFLR5 wing polar")


def lift_distribution(design_variables, v):
    """Spanwise lift (y, lift per span) at airspeed v, from XFLR5.  TODO.
    Check: integral over the full span must equal the weight m * g."""
    raise NotImplementedError("Aerodynamics: lift distribution")


# --- step 5: drag -------------------------------------------------------------
def induced_drag_coefficient(CL, AR, e=0.80):
    """CD_i = CL^2 / (pi * e * AR)  [-]. e = Oswald factor (XFLR5 or ~0.8)."""
    return CL**2 / (math.pi * e * AR)


def zero_lift_drag_coefficient(design_variables):
    """CD0 = sum over components (Cf * FF * S_wet / S): wing, tail, fuselage,
    boom, landing gear (Hoerner / Raymer, component build-up).  TODO."""
    raise NotImplementedError("Aerodynamics: CD0 build-up")


def aircraft_polar(design_variables):
    """Whole-aircraft polar CD(CL) = CD0 + wing profile drag + CD_i.
    This is what CLCD_polar() should return in the end.  TODO."""
    raise NotImplementedError("Aerodynamics: aircraft polar")


# --- step 6: stability ---------------------------------------------------------
def stall_speed(m, S, CL_max_value, rho=init.rho):
    """v_stall = sqrt(2 m g / (rho S CL_max))  [m/s]. RFP formula for f_stall."""
    return math.sqrt(2.0 * m * init.g / (rho * S * CL_max_value))
