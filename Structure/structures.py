# structures.py
"""
=============================================================================
 STRUCTURES TEMPLATE  (TUM Design/Build/Fly WS 2026/27)
=============================================================================

HOW THIS FILE WORKS
-------------------
Part A  OUTPUTS       Functions the other teams call. Keep NAME, ARGUMENT,
                      RETURN TYPE and UNIT exactly as they are. Replace the
                      PLACEHOLDER body with a call to your calculation steps.
Part B  STEPS         The calculations you need, with the lecture equation in
                      each docstring (Structure input presentation + RFP).
                      Simple equations are already written; "TODO" is yours.

WHAT WE NEED FROM OTHER TEAMS (call these, never copy numbers)
--------------------------------------------------------------
  aerodynamics.wing_planform(design_variables)          geometry
  aerodynamics.lift_dist_stall_speed / _max_speed       load cases
  propulsion.propulsion_weight(design_variables)  [kg]  mass, CG

WHAT WE GIVE TO OTHER TEAMS (Part A)
------------------------------------
  aircraft_mass   -> Performance, Aerodynamics
  CG_position     -> Aerodynamics (static margin)
  printing_time   -> Performance (cost + penalty)

Load case rules (RFP): n_z = 6, safety factor 1.5 (2.0 for printed parts in
bending without CFRP), torsion at tip <= 4 deg at 25 m/s.
Units: SI (m, kg, s, N, Pa, rad).
"""

import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")  # repo root
sys.path.extend([ROOT] + [os.path.join(ROOT, folder) for folder in
                          ("Aerodynamics", "Structure", "Propulsion", "Performance")])
import initializations as init
import aerodynamics
import propulsion


# ============================================================================
# PART A - OUTPUTS (other teams call these)
# ============================================================================
def aircraft_mass(design_variables):
    """Total take-off mass: structure + propulsion + fixed RFP parts + gear.
    Returns float [kg].  Used by: Performance (every phase), Aerodynamics.
    Status: PLACEHOLDER (2.2 kg, first hand estimate).
    Later: sum of the masses in mass_table()."""
    return 2.2


def CG_position(design_variables):
    """Centre of gravity x_CG from the wing root leading edge [m],
    + = towards the tail (same reference as aerodynamics.NP_position).
    Later: center_of_gravity(mass_table(...))."""
    raise NotImplementedError("Structures: CG_position")


def printing_time(design_variables):
    """Total printing time of all printed parts [s] (25 h = 90000 s).
    Used by: Performance (10 EUR/h + penalty above 30 h).
    Status: PLACEHOLDER (25 h). Later: print_time_from_volume(total volume)."""
    return 25.0 * 3600.0


# ============================================================================
# PART B - CALCULATION STEPS
# ============================================================================
# --- step 1: geometry of the printed parts ------------------------------------
def wetted_area_and_volume(planform):
    """Wetted surface S_wet [m^2] and volume V [m^3] of a wing or tail.
    Lecture: wetted surface = sum of individual trapezes,
             volume = sum of individual frustums (airfoil thickness).  TODO."""
    raise NotImplementedError("Structures: S_wet and volume")


# --- step 2: masses -----------------------------------------------------------
def printed_part_mass(S_wet, V):
    """m = rho_PETG * (2 * 0.4 mm * S_wet + 8 % * V)  [kg]
    (shell of 2 x 0.4 mm walls + 8 % infill). Same formula for wing and tail."""
    return init.rho_PETG * (2 * init.t_shell * S_wet + init.infill * V)


def mass_table(design_variables):
    """List of all parts as (name, mass [kg], x_CG [m]): fixed RFP components
    (init.fixed_components), wing, tail, spar caps, gear, and
    propulsion.propulsion_weight(). "Don't forget any components!"  TODO."""
    raise NotImplementedError("Structures: mass table")


def center_of_gravity(parts):
    """x_CG = sum(m_i * x_i) / sum(m_i)  [m], parts = [(name, m, x), ...]."""
    m_total = sum(m for _, m, _ in parts)
    return sum(m * x for _, m, x in parts) / m_total


# --- step 3: loads (massless wing, point masses at the fuselage) --------------
def shear_and_bending(y, lift_per_span, load_factor=init.n_z):
    """Shear force Q(y) [N] and bending moment M(y) [N m] along the half span,
    integrated from the tip to the root (numerical, grid points):
        Q(y) = integral_y^tip  n * l(eta) d eta
        M(y) = integral_y^tip  Q(eta) d eta
    lift_per_span from aerodynamics.lift_dist_*  [N/m]."""
    load = load_factor * np.asarray(lift_per_span)
    y = np.asarray(y)
    dy = np.diff(y)
    Q = np.zeros_like(y)
    M = np.zeros_like(y)
    for i in range(len(y) - 2, -1, -1):       # tip -> root, trapezoid rule
        Q[i] = Q[i + 1] + 0.5 * (load[i] + load[i + 1]) * dy[i]
        M[i] = M[i + 1] + 0.5 * (Q[i] + Q[i + 1]) * dy[i]
    return Q, M


# --- step 4: spar sizing (strength) ---------------------------------------------
def spar_cap_stress(M, section_modulus):
    """Normal stress in the spar caps: sigma = M / S_section  [Pa].
    Must be <= sigma_max / safety factor 1.5. Caps = 1 mm CFRP rods."""
    return M / section_modulus


def spar_web_stress(Q, web_area):
    """Shear stress in the web: tau = 1.5 * Q / A  [Pa]
    (1.5 is the shape factor, NOT the safety factor)."""
    return 1.5 * Q / web_area


# --- step 5: torsion (stiffness) -------------------------------------------------
def torsional_moment_section(cm, v, S_section, chord, rho=init.rho):
    """Pitching moment of one wing section: M = cm * 1/2 rho v^2 * S * l  [N m].
    Sum from tip to root gives the torsional moment M_T(y).
    Only valid for unswept wings with the spar at 25 % chord."""
    return cm * 0.5 * rho * v**2 * S_section * chord


def twist_rate(M_T, G, A_m, perimeter_over_thickness):
    """phi' = M_T / (G * I_T)  with  I_T = (2 A_m)^2 / (closed integral ds/t)
    [rad/m]. Integrate over the span -> tip twist, RFP: <= 4 deg at 25 m/s."""
    I_T = (2 * A_m) ** 2 / perimeter_over_thickness
    return M_T / (G * I_T)


# --- step 6: printing time -----------------------------------------------------
def print_time_from_volume(V_printed):
    """T_print = V_printed / (20 cm^3/h)  [s]. V_printed = printed material
    volume (shell + infill) [m^3]."""
    return V_printed / init.print_rate
