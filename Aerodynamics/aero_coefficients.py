
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