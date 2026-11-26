"""
Bridge between your WingObject (wing_creation.py) and the polar database.

The geometry is split in two, because XFOIL and the 3D wing model need
different things:

  * airfoils   -> AirfoilSpec, the only geometry XFOIL sees
  * stations   -> y, chord, twist, Re per spanwise station, used later by the
                  lifting-line / 3D step to look up section coefficients

Nothing here imports wing_creation.py; it only reads `wing.table` and
`wing.NACA`, so it works with Wing, HTP, VTP and VTail alike.

Per-section airfoils: if you later add an 'airfoil' column to `wing.table`
(holding an AirfoilSpec or a NACA code per row), it is used automatically
instead of `wing.NACA`.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .airfoil import AirfoilSpec
from .database import PolarDatabase
from .polars import PolarGrid

NU_SEA_LEVEL = 1.46e-5     # kinematic viscosity of air, ISA sea level [m^2/s]


def _as_spec(a) -> AirfoilSpec:
    return a if isinstance(a, AirfoilSpec) else AirfoilSpec.from_naca(a)


def wing_airfoils(wing) -> dict[str, AirfoilSpec]:
    """Unique airfoils used on the wing, keyed by AirfoilSpec.key."""
    if "airfoil" in wing.table.columns:
        specs = [_as_spec(a) for a in wing.table["airfoil"]]
    else:
        specs = [AirfoilSpec.from_naca(wing.NACA)]
    return {s.key: s for s in specs}


def wing_stations(wing, velocity: float, nu: float = NU_SEA_LEVEL) -> pd.DataFrame:
    """Spanwise station table with the local Reynolds number added."""
    t = wing.table
    if "airfoil" in t.columns:
        keys = [_as_spec(a).key for a in t["airfoil"]]
    else:
        keys = [AirfoilSpec.from_naca(wing.NACA).key] * len(t)
    return pd.DataFrame({
        "y": t["y_offset"].to_numpy(float),
        "chord": t["chord_length"].to_numpy(float),
        "twist_deg": t["twist"].to_numpy(float),
        "airfoil_key": keys,
        "Re": velocity * t["chord_length"].to_numpy(float) / nu,
    })


def wing_re_range(wing, v_min: float, v_max: float, nu: float = NU_SEA_LEVEL
                  ) -> tuple[float, float]:
    """Re range the wing sees between v_min (e.g. stall speed) and v_max.
    Uses the smallest chord at v_min and the largest chord at v_max."""
    c = wing.table["chord_length"].to_numpy(float)
    c = c[c > 0]
    return v_min * c.min() / nu, v_max * c.max() / nu


def wing_polars(wing, db: PolarDatabase, v_min: float, v_max: float,
                nu: float = NU_SEA_LEVEL) -> dict[str, PolarGrid]:
    """Polar grids for every airfoil on the wing, covering its full Re range.
    Returns {airfoil_key: PolarGrid}; join to stations via 'airfoil_key'."""
    re_lo, re_hi = wing_re_range(wing, v_min, v_max, nu)
    return {k: db.get_polar(spec, re_lo, re_hi) for k, spec in wing_airfoils(wing).items()}


def station_coefficients(stations: pd.DataFrame, polars: dict[str, PolarGrid],
                         alpha_local) -> pd.DataFrame:
    """Look up cl, cd, cm at each station for given local angles of attack
    [deg] (one value, or one per station). This is the call a lifting-line
    solver makes every iteration."""
    alpha_local = np.broadcast_to(np.asarray(alpha_local, float), (len(stations),))
    out = stations.copy()
    out["alpha_local"] = alpha_local
    for col in ("cl", "cd", "cm", "cl_max"):
        out[col] = np.nan
    for key, grid in polars.items():
        m = (stations["airfoil_key"] == key).to_numpy()
        cl, cd, cm = grid.coefficients(alpha_local[m], stations["Re"].to_numpy()[m])
        out.loc[m, "cl"], out.loc[m, "cd"], out.loc[m, "cm"] = cl, cd, cm
        out.loc[m, "cl_max"] = grid.scalar_at("cl_max", stations["Re"].to_numpy()[m])
    return out
