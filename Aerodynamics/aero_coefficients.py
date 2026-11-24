
import numpy as np
from wing_creation import Wing, HTP, VTP, VTail

import sys
from pathlib import Path

# Get the parent directory of the current script
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

import initializations
import drag_estimation


def wing_CL_alpha(wing_obj):

    #find CLalpha

    AR = wing_obj.aspect_ratio()
    M = initializations.v_recon/initializations.a0
    beta = np.sqrt(1-M**2) # For subsonic conditions
    t_c = int(wing_obj.NACA[-2:])/100

    if 0.03 <= t_c <= 0.08:
        Ksq = 1 + 1.5 * t_c
    elif 0.08 < t_c <= 0.12:
        Ksq = (1 + 0.75*t_c)**2
    else:
        raise ValueError(f"Input error: t/c value {t_c} is outside the supported range (3 to 12).")

    ## Polhamus defined without wing sweep angle
    CL_alpha = (2*np.pi*AR)/(2+np.sqrt((AR**2 * beta**2)/Ksq + 4))

    return CL_alpha

def induced_drag_co(wing_obj):
    e = 0.65
    k = 1/(np.pi*wing_obj.aspect_ratio()*e)
    return k
    
def zero_lift_drag(wing_obj):
    Re = initializations.v_recon*wing_obj.root_chord/initializations.nu
    rho = initializations.rho
    v_recon = initializations.v_recon
    mu = initializations.mu
    k_roughness = 1.5 * 10**(-6)
    M = initializations.v_recon/initializations.a0

    l_fus = 0.410 # m
    w_fus = 0.053 # m
    h_fus = 0.090 # m 

    t_c = int(wing_obj.NACA[-2:])/100
    x_c = 0.3 # For all NACA 4 digit airfoils
    c_tip = wing_obj.root_chord*wing_obj.aspect_ratio()

    cd0_fus = drag_estimation.zero_lift_drag_coefficient_fuselage(l_fus, w_fus, h_fus, rho, v_recon, mu, k_roughness, M)
    cd0_wing = drag_estimation.zero_lift_drag_coefficient_wing(wing_obj.area(), t_c, x_c, wing_obj.root_chord, c_tip, 0, rho,
                                                                v_recon, mu, k_roughness, M )
    return (cd0_fus + cd0_wing)


def c_one(x):
    return -0.0000264 * x**3 - 0.000564 * x**2 + 0.0556219 * x - 0.0054559
def c_two(x):
    return 0.000003 * x**5 - 0.000094 * x**4 + 0.0010118 * x**3 - 0.0015527 * x**2 - 0.1042267 * x + 1.001183
def c_three(x):
    return -0.0000506 * x**3 - 0.0007669 * x**2 + 0.0490423 * x - 0.002549
def c_four(x):
    return 0.0000034 * x**4 - 0.0000064 * x**3 - 0.0037242 * x**2 + 0.0913507 * x + 0.0008776

def cl_a(wing_obj):
    '''
    # Airfoil trailing edge angle here is assumed to be zero and thus now set to 0. If more complicated geometries are evaluated, please change the parameter accfordingly.
    phi_TE_dash = 0
    M = initializations.v_recon/initializations.a0
    beta = np.sqrt(1-M**2) # For subsonic conditions
    t_c = int(wing_obj.NACA[-2:])/100
    cl_a_theory = 2 * np.pi + 4.7 * t_c * (1 + 0.00375 * 0)
    cl_a_i = 0 # cl_a_i: experimental lift curve slope
    cla_a = 1.05/beta * (cl_a_i/cl_a_theory) * cl_a_theory
    '''
    return 6.1 # in 1/rad; exact data from airfoil not available; 0.1 < t_c < 0.2

# lift distribution at a given normalized spanwise wing coordinate
def gamma_tot(eta, wing_obj, cl=1):
    M = initializations.v_recon/initializations.a0
    beta = np.sqrt(1-M**2) # For subsonic conditions
    # l_a implemented for the condition of an unswept wing 
    # Assuming that for x in the coefficient formulas, the plan view parameter F is to be inserted
    F = 2 * np.pi * wing_obj.aspect_ratio() / (cl_a(wing_obj) * 1) # cos(phi25) = 1 for sweep of 25%-line = 0
    l_a = c_one(F) * wing_obj.chord(eta)/wing_obj.cmac + (c_two(F) + c_three(F)) * 4/np.pi * np.sqrt(1 - eta**2)
    gamma_a = l_a * cl
    # Again, phi_beta (effective sweep angle) assumed zero
    E = 1 + (2 * wing_obj.taper_ratio) / (wing_obj.aspect_ratio() * (1 + wing_obj.taper_ratio))
    alpha_01 = -(c_one(F) * (1 + 2 * wing_obj.taper_ratio)/(3 * (1 + wing_obj.taper_ratio)) + (c_two(F) + c_three(F)) * 4 / 3 * np.pi)# unswept wing
    l_b = l_a * c_four(F) * 1 * (wing_obj.tip_twist + alpha_01) * beta * E # assuming alpha_01 = 0
    gamma_b = l_b * wing_obj.tip_twist * cl_a(wing_obj) / E

    return gamma_a + gamma_b

if __name__ == '__main__':

    # Create Wing and Tail
    wing = Wing(root_chord=0.2, wing_span=1.9, taper_ratio=0.2, ellipticity=2.5, n_panels=52,
        spar_position=25, tip_twist=-3, NACA=2410, )

    vtail = VTail(root_chord=0.1, wing_span=0.3, taper_ratio=0.1, ellipticity=1.5, n_panels=20,
        spar_position=50, dihedral=35, NACA='0008', )

    clalpha = wing_CL_alpha(wing)
    cd0tot = zero_lift_drag(wing)
    k = induced_drag_co(wing)

    print("cd0 = ", cd0tot, "and CL_alpha = ", clalpha, "and induced drag coefficient k = ", k)
    import matplotlib.pyplot as plt
    # Try to check the lift distribution function
    eta = np.linspace(0, 1, 100)
    #etaw = eta*wing.wing_span
    #etav = eta*vtail.wing_span
    plt.plot(eta, gamma_tot(eta, wing))
    plt.plot(eta, gamma_tot(eta, wing, 0.5))
    plt.plot(eta, gamma_tot(eta, wing, 1.5))
    plt.plot(eta, gamma_tot(eta, vtail))
    plt.show()
