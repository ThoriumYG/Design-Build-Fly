"""XFOIL interface: airfoil specs, a cached polar database and a WingObject adapter."""
from .airfoil import AirfoilSpec
from .database import PolarDatabase
from .polars import PolarGrid
from .runner import XfoilRunner, XfoilSettings, read_polar_file
from .wing_adapter import (NU_SEA_LEVEL, station_coefficients, wing_airfoils, wing_polars,
                           wing_re_range, wing_stations)

__all__ = ["AirfoilSpec", "PolarDatabase", "PolarGrid", "XfoilRunner", "XfoilSettings",
           "read_polar_file", "NU_SEA_LEVEL", "station_coefficients", "wing_airfoils",
           "wing_polars", "wing_re_range", "wing_stations"]
