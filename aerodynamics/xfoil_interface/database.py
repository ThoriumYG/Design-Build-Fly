"""
PolarDatabase: the single entry point the rest of your program uses.

    db = PolarDatabase(XfoilRunner("xfoil"), XfoilSettings(), cache_dir="polar_cache")
    grid = db.get_polar(AirfoilSpec.from_naca("2412"), re_min=1.5e5, re_max=8e5)
    cl, cd, cm = grid.coefficients(alpha=4.0, re=3.2e5)

Caching strategy (built for optimisation loops)
  * Reynolds numbers are snapped to a fixed, global logarithmic ladder
    (default 8 values per decade). Two different wings needing Re 312 000 and
    318 000 both use the ladder value 316 000, so their results are shared.
  * Cache entries are stored per (airfoil, settings, Re). A new wing whose Re
    range overlaps an earlier one only runs XFOIL for the missing rungs.
  * Two levels: an in-memory dict (fast, per process) and optional .npz files
    on disk (persist between optimisation runs). Failed runs are cached too,
    so a non-converging case is not re-run every iteration.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from .airfoil import AirfoilSpec
from .polars import PolarGrid
from .runner import POLAR_COLUMNS, XfoilRunner, XfoilSettings


class PolarDatabase:
    def __init__(self, runner: XfoilRunner, settings: XfoilSettings | None = None,
                 cache_dir: str | Path | None = None, re_per_decade: int = 8,
                 max_gap_fill: int = 2, verbose: bool = False):
        self.runner = runner
        self.settings = settings or XfoilSettings()
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.re_per_decade = re_per_decade
        self.max_gap_fill = max_gap_fill
        self.verbose = verbose
        self._mem: dict[tuple[str, str, int], pd.DataFrame] = {}
        self.stats = {"memory_hits": 0, "disk_hits": 0, "xfoil_runs": 0}

    # ------------------------------------------------------------------ public
    def re_ladder(self, re_min: float, re_max: float) -> np.ndarray:
        """Ladder values that bracket [re_min, re_max] (one rung beyond each end)."""
        if re_min > re_max:
            re_min, re_max = re_max, re_min
        n = self.re_per_decade
        k_lo = int(np.floor(np.log10(re_min) * n + 1e-9))
        k_hi = int(np.ceil(np.log10(re_max) * n - 1e-9))
        ks = np.arange(k_lo, max(k_hi, k_lo + 1) + 1)
        return np.array([_round_sig(10 ** (k / n), 3) for k in ks])

    def get_polar(self, airfoil: AirfoilSpec, re_min: float, re_max: float,
                  settings: XfoilSettings | None = None) -> PolarGrid:
        """Polar grid covering at least [re_min, re_max]."""
        return self.get_polar_at(airfoil, self.re_ladder(re_min, re_max), settings)

    def get_polar_at(self, airfoil: AirfoilSpec, re_values, settings: XfoilSettings | None = None
                     ) -> PolarGrid:
        """Polar grid at exactly these Re values (bypasses the ladder)."""
        s = settings or self.settings
        re_values = sorted({float(r) for r in re_values})
        runs, missing = {}, []
        for r in re_values:
            df = self._lookup(airfoil, s, r)
            if df is None:
                missing.append(r)
            else:
                runs[r] = df
        if missing:
            if self.verbose:
                print(f"[xfoil] {airfoil.name}: running {len(missing)} Re "
                      f"({min(missing):.3g}..{max(missing):.3g})")
            new = self.runner.run(airfoil, missing, s)
            self.stats["xfoil_runs"] += len(missing)
            for r, df in new.items():
                self._store(airfoil, s, r, df)
                runs[r] = df
        return PolarGrid.from_runs(airfoil, s, runs, max_gap=self.max_gap_fill)

    def clear_memory(self):
        self._mem.clear()

    # ----------------------------------------------------------------- caching
    def _key(self, airfoil, s, re_num):
        return airfoil.key, s.key, int(round(re_num))

    def _path(self, key):
        a_key, s_key, re_int = key
        return self.cache_dir / f"{a_key}_{s_key}" / f"re_{re_int:010d}.npz"

    def _lookup(self, airfoil, s, re_num):
        key = self._key(airfoil, s, re_num)
        if key in self._mem:
            self.stats["memory_hits"] += 1
            return self._mem[key]
        if self.cache_dir is not None:
            p = self._path(key)
            if p.exists():
                try:
                    with np.load(p) as d:
                        df = pd.DataFrame(d["data"], columns=POLAR_COLUMNS)
                except Exception:          # corrupt or partial file -> recompute
                    return None
                self._mem[key] = df
                self.stats["disk_hits"] += 1
                return df
        return None

    def _store(self, airfoil, s, re_num, df):
        key = self._key(airfoil, s, re_num)
        self._mem[key] = df
        if self.cache_dir is None:
            return
        p = self._path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        # atomic write: safe if several optimiser processes share the cache
        fd, tmp = tempfile.mkstemp(dir=p.parent, suffix=".tmp")
        with os.fdopen(fd, "wb") as f:
            np.savez(f, data=df[POLAR_COLUMNS].to_numpy(float), airfoil=np.array(airfoil.name))
        os.replace(tmp, p)


def _round_sig(x: float, sig: int) -> float:
    return float(f"{x:.{sig}g}")
