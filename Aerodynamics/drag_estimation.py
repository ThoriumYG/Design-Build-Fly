from math import pi, sqrt, log10, cos, radians


def basic_values(b, Sref, ctip, croot):
    b = None
    Sref = None
    AR = b**2 / Sref
    tip_root_ratio = ctip / croot
    return Sref, AR, tip_root_ratio


def induced_drag(rho, V, Sref, Cl, AR, e):
    k = 1 / (pi() * AR * e)
    induced_drag = 0.5 * rho * (V**2) * Sref * k * (Cl**2)

    return induced_drag


# With the weight defining the lift
def induced_drag_level_steady(rho, V, Sref, m, AR, e):
    k = 1 / (pi() * AR * e)
    induced_drag = 0.5 * rho * (V**2) * Sref * k * (2 * 9.81 * m / (rho * (V**2) * Sref)) ** 2

    return induced_drag


def lift_coefficient_slope(AR):
    Cl_alpha = (
        2
        * pi
        * AR
        / (2 + sqrt(((9.5**2 * 0.6258**2) / 1.184) * (1 + (0.4019**2) / (0.6258**2)) + 4))
    )
    return Cl_alpha


def re(rho, V, l, mu):
    return rho * V * l / mu


def reCO(l_fus, k_roughness):
    return 38 * (l_fus / k_roughness) ** 1.053


def cf_laminar(re):
    return 1.328 / sqrt(re)


def cf_turbulent(re, M_inf):
    return 0.455 / (log10(re) ** 2.58) * (1 + 0.144 * M_inf**2) ** -0.65


# Fuselage
def zero_lift_drag_coefficient_fuselage(
    l_fus, wfus, hfus, rho, V, mu, k_roughness, M_inf, laminar=False
):
    d = 0.5 * (wfus + hfus)
    f = l_fus / d
    Ffus = 0.9 + 5 / f**1.5 + f / 400
    re_min = min(re(rho, V, l_fus, mu), reCO(l_fus, k_roughness))
    S_fus_wet = pi * d**2 * ((l_fus / d) - 1.35)
    if laminar:
        cf = cf_laminar(re_min)
    else:
        cf = cf_turbulent(re_min, M_inf)

    return cf * Ffus * S_fus_wet


# A320 from exercise 2 ADB, 10000m
# print(zero_lift_drag_coefficient_fuselage(37.57, 3.95, 4.14, 0.4120, 299.4*0.78, 14.69*10**-6, 1.5*10**-6, 0.78))


# t/c: postion of maximum thickness
def zero_lift_drag_coefficient_wing(
    Sref, t_over_c, x_over_c, c_root, c_tip, sweep, rho, V, mu, k_roughness, M_inf, laminar=False
):
    tip_root_ratio = c_tip / c_root
    cmac = 2 / 3 * c_root * (1 + tip_root_ratio + tip_root_ratio**2) / (1 + tip_root_ratio)
    re_min = min(re(rho, V, cmac, mu), reCO(cmac, k_roughness))
    Swet = 2 * Sref
    re_min = min(re(rho, V, cmac, mu), reCO(cmac, k_roughness))
    if laminar:
        cf = cf_laminar(re_min)
    else:
        cf = cf_turbulent(re_min, M_inf)
    Fwing = (
        (1 + 0.6 / (x_over_c) * t_over_c + 100 * t_over_c**4)
        * 1.34
        * M_inf**0.18
        * (cos(sweep)) ** 0.28
    )
    return cf * Swet * Fwing


# print(zero_lift_drag_coefficient_wing(122.4, 0.1175, 0.399, 6.07, 1.5, radians(23.15), 0.4120, 299.4*0.78, 14.69*10**-6, 1.5*10**-6, 0.78))
# reference quantitites assumed kink


# not the wetted areas used here
def zero_lift_drag_coefficient_empennage(S_HT, S_VT, Cd_emp=0.007):
    # 0.006 <= Cd_emp <= 0.008 -> 0.007
    return Cd_emp * (S_HT + S_VT)


# print(zero_lift_drag_coefficient_empennage(31, 21.5))
# No nacelle
def zero_lift_drag_coefficient_total(rho, V, f_fus, f_w, f_emp, f_nac=0, f_interference=0):
    f = f_fus + f_w + f_emp + f_nac + f_interference
    return 0.5 * rho * V**2 * f


# interference drag, t/c_m: mean relative thickness of reference areas, c_m ** 2 = (S/AR)
def interference_drag_coefficient(t_w, c_w, t_emp, c_emp, c_m_w, c_m_e):
    Cd_w_f = 3.2 * (t_w / c_w) ** 3 - 0.0005
    Cd_e_f = 1.51 * (t_emp / c_emp) ** 3 - 0.0005
    Cd_e_e = 14 * (t_emp / c_emp) ** 4
    return Cd_w_f * c_m_w**2 + Cd_e_f * c_m_e**2 + Cd_e_e * c_m_e**2


"""
Questions:
- Which k_roughness does the 3D-printer filament have?
"""
