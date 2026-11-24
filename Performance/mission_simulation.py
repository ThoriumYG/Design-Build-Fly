"""
    Inputs:
    - Aircraft Mass
    - Cruise Speed
    - Battery Power over Thrust
    Output:
    - T_mission
"""

import numpy as np
import sys
import os
from pathlib import Path

# Go up one level from the subfolder to the main folder
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

aero_path = Path(__file__).parent / "Aerodynamics"
prop_path = Path(__file__).parent / "Propulsion"
structure_path = Path(__file__).parent / "Structure"
sys.path.append(str(aero_path))

import initializations as init

def calc_t_mission():
    return

if __name__ == "__main__":
    print("Hello there!")