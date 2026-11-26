"""
Example: from a WingObject to section polars and spanwise coefficients.

Place the `xfoil_interface` folder where your project can import it (e.g. next
to wing_creation.py) and set XFOIL_PATH to your executable.
"""
import numpy as np

from wing_creation import Wing
from xfoil_interface import (PolarDatabase, XfoilRunner, XfoilSettings,
                             station_coefficients, wing_polars, wing_stations)

XFOIL_PATH = "xfoil"             # e.g. r"C:\XFOIL6.99\xfoil.exe"

# Create these ONCE, outside the optimisation loop, and reuse them.
runner = XfoilRunner(XFOIL_PATH, max_workers=4)
settings = XfoilSettings(alpha_min=-6, alpha_max=18, alpha_step=0.5, ncrit=9)
db = PolarDatabase(runner, settings, cache_dir="polar_cache", verbose=True)


def evaluate(wing, v_min=10.0, v_max=30.0, v_eval=20.0):
    polars = wing_polars(wing, db, v_min, v_max)          # XFOIL only on cache miss
    stations = wing_stations(wing, velocity=v_eval)
    return polars, stations


if __name__ == "__main__":
    wing = Wing(root_chord=0.30, wing_span=2.0, taper_ratio=0.5, ellipticity=1.5,
                n_panels=20, tip_twist=-2, NACA="2412")

    polars, stations = evaluate(wing)
    for grid in polars.values():
        print(grid)
        print(grid.summary()[["Re", "cl_max", "alpha_cl_max", "cl_max_is_peak",
                              "cl_alpha_per_rad", "alpha_L0", "cd_min", "ld_max"]]
              .round(4).to_string(index=False))

    # Section coefficients at wing AoA 5 deg, twist included (no induced angle
    # yet; a lifting-line solver would subtract alpha_i here)
    coeffs = station_coefficients(stations, polars, 5.0 + stations["twist_deg"].to_numpy())
    print(coeffs[["y", "chord", "Re", "alpha_local", "cl", "cd", "cl_max"]]
          .round(4).to_string(index=False))

    # A second, slightly different wing reuses the cached polars
    wing2 = Wing(root_chord=0.31, wing_span=2.1, taper_ratio=0.45, ellipticity=1.5,
                 n_panels=20, tip_twist=-3, NACA="2412")
    evaluate(wing2)
    print("cache stats:", db.stats)
