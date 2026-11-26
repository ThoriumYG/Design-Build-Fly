"""
PolarGrid: one airfoil's 2D polars on a regular (Re, alpha) grid.

  * cl, cd, cm are (n_re, n_alpha) arrays; NaN where XFOIL did not converge.
  * Short interior gaps (isolated failed points) are filled linearly in alpha;
    `converged` keeps the raw mask so you can tell real from filled points.
  * Queries interpolate linearly in (log Re, alpha). Re outside the grid is
    clamped to the nearest end, alpha outside the converged range gives NaN
    (no post-stall model is applied here).
"""
from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.interpolate import RegularGridInterpolator


class PolarGrid:
    def __init__(self, airfoil_name: str, airfoil_key: str, settings_key: str,
                 re: np.ndarray, alpha: np.ndarray, cl: np.ndarray, cd: np.ndarray,
                 cm: np.ndarray, converged: np.ndarray):
        order = np.argsort(re)
        self.airfoil_name = airfoil_name
        self.airfoil_key = airfoil_key
        self.settings_key = settings_key
        self.re = np.asarray(re, float)[order]
        self.alpha = np.asarray(alpha, float)
        self.cl = np.asarray(cl, float)[order]
        self.cd = np.asarray(cd, float)[order]
        self.cm = np.asarray(cm, float)[order]
        self.converged = np.asarray(converged, bool)[order]
        self._summaries: dict[tuple, pd.DataFrame] = {}

    # ------------------------------------------------------------ construction
    @classmethod
    def from_runs(cls, airfoil, settings, runs: dict[float, pd.DataFrame],
                  max_gap: int = 2) -> "PolarGrid":
        """Assemble from {Re: DataFrame} as returned by XfoilRunner / the cache."""
        alpha = settings.alpha_grid()
        re = np.array(sorted(runs))
        shape = (len(re), len(alpha))
        cl, cd, cm = (np.full(shape, np.nan) for _ in range(3))
        for i, r in enumerate(re):
            df = runs[r]
            if df.empty:
                continue
            idx = np.rint((df["alpha"].values - alpha[0]) / settings.alpha_step).astype(int)
            ok = (idx >= 0) & (idx < len(alpha))
            ok &= np.abs(alpha[np.clip(idx, 0, len(alpha) - 1)] - df["alpha"].values) \
                < 0.25 * settings.alpha_step
            cl[i, idx[ok]] = df["CL"].values[ok]
            cd[i, idx[ok]] = df["CD"].values[ok]
            cm[i, idx[ok]] = df["CM"].values[ok]
        converged = np.isfinite(cl)
        for arr in (cl, cd, cm):
            _fill_interior_gaps(alpha, arr, max_gap)
        return cls(airfoil.name, airfoil.key, settings.key, re, alpha, cl, cd, cm, converged)

    # ------------------------------------------------------------ interpolation
    @cached_property
    def _interpolators(self):
        if len(self.re) == 1:
            return None
        pts = (np.log(self.re), self.alpha)
        return {k: RegularGridInterpolator(pts, getattr(self, k), bounds_error=False,
                                           fill_value=np.nan)
                for k in ("cl", "cd", "cm")}

    def coefficients(self, alpha, re):
        """Section (cl, cd, cm) at alpha [deg] and Re. Inputs broadcast together."""
        alpha, re = np.broadcast_arrays(np.asarray(alpha, float), np.asarray(re, float))
        if self._interpolators is None:
            out = [np.interp(alpha, self.alpha, getattr(self, k)[0], left=np.nan, right=np.nan)
                   for k in ("cl", "cd", "cm")]
        else:
            log_re = np.log(np.clip(re, self.re[0], self.re[-1]))
            pts = np.column_stack([log_re.ravel(), alpha.ravel()])
            out = [self._interpolators[k](pts).reshape(alpha.shape) for k in ("cl", "cd", "cm")]
        return tuple(o if o.ndim else float(o) for o in out)

    # ------------------------------------------------------------ derived data
    def summary(self, linear_window=(-2.0, 6.0)) -> pd.DataFrame:
        """One row per Re: cl_max, alpha_stall, lift slope, zero-lift angle,
        cd_min, (L/D)_max and moment data. Uses converged points only."""
        key = tuple(linear_window)
        if key not in self._summaries:
            rows = [self._row_summary(i, linear_window) for i in range(len(self.re))]
            self._summaries[key] = pd.DataFrame(rows)
        return self._summaries[key]

    def scalar_at(self, name: str, re, linear_window=(-2.0, 6.0)):
        """Interpolate a summary column (e.g. 'cl_max') to arbitrary Re, linear
        in log Re, clamped at the grid ends."""
        s = self.summary(linear_window)
        ok = np.isfinite(s[name].values)
        if not ok.any():
            return np.full(np.shape(re), np.nan)
        x = np.log(s["Re"].values[ok])
        return np.interp(np.log(np.asarray(re, float)), x, s[name].values[ok])

    def _row_summary(self, i, window):
        m = self.converged[i]
        a, cl, cd, cm = self.alpha[m], self.cl[i, m], self.cd[i, m], self.cm[i, m]
        row = {"Re": self.re[i], "n_converged": int(m.sum()),
               "converged_fraction": float(m.mean())}
        nan = np.nan
        if len(a) < 3:
            return {**row, **dict.fromkeys(
                ["cl_max", "alpha_cl_max", "cl_max_is_peak", "cl_alpha_per_deg",
                 "cl_alpha_per_rad", "alpha_L0", "cl0", "cm_alpha_per_deg", "cm0",
                 "cd_min", "cl_at_cd_min", "ld_max", "alpha_ld_max", "cl_at_ld_max"], nan)}

        j = int(np.argmax(cl))
        a_max, cl_max = _refined_extremum(a, cl, j)
        row.update(cl_max=cl_max, alpha_cl_max=a_max,
                   # False -> CL was still rising at the last converged point:
                   # XFOIL gave up before stall or alpha_max is too low.
                   cl_max_is_peak=bool(j < len(a) - 1))

        w = (a >= window[0]) & (a <= window[1])
        if w.sum() >= 3:
            slope, icpt = np.polyfit(a[w], cl[w], 1)
            alpha_l0 = -icpt / slope
            row.update(cl_alpha_per_deg=slope, cl_alpha_per_rad=np.degrees(slope),
                       alpha_L0=alpha_l0, cl0=icpt,
                       cm_alpha_per_deg=np.polyfit(a[w], cm[w], 1)[0],
                       cm0=float(np.interp(alpha_l0, a, cm)))
        else:
            row.update(cl_alpha_per_deg=nan, cl_alpha_per_rad=nan, alpha_L0=nan,
                       cl0=nan, cm_alpha_per_deg=nan, cm0=nan)

        k = int(np.argmin(cd))
        _, neg_cdmin = _refined_extremum(a, -cd, k)
        row.update(cd_min=-neg_cdmin, cl_at_cd_min=cl[k])

        pos = cl > 0
        if pos.any():
            ld = np.where(pos, cl / cd, -np.inf)
            k = int(np.argmax(ld))
            a_ld, ld_max = _refined_extremum(a, ld, k)
            row.update(ld_max=ld_max, alpha_ld_max=a_ld, cl_at_ld_max=float(np.interp(a_ld, a, cl)))
        else:
            row.update(ld_max=nan, alpha_ld_max=nan, cl_at_ld_max=nan)
        return row

    # ------------------------------------------------------------ export / io
    def to_dataframe(self) -> pd.DataFrame:
        """Long format (one row per Re/alpha) for CSV export or plotting."""
        R, A = np.meshgrid(self.re, self.alpha, indexing="ij")
        return pd.DataFrame({"airfoil": self.airfoil_name, "Re": R.ravel(), "alpha": A.ravel(),
                             "CL": self.cl.ravel(), "CD": self.cd.ravel(), "CM": self.cm.ravel(),
                             "converged": self.converged.ravel()})

    def save(self, path: str | Path):
        meta = json.dumps({"airfoil_name": self.airfoil_name, "airfoil_key": self.airfoil_key,
                           "settings_key": self.settings_key})
        np.savez_compressed(path, re=self.re, alpha=self.alpha, cl=self.cl, cd=self.cd,
                            cm=self.cm, converged=self.converged, meta=np.array(meta))

    @classmethod
    def load(cls, path: str | Path) -> "PolarGrid":
        with np.load(path) as d:
            meta = json.loads(str(d["meta"]))
            return cls(re=d["re"], alpha=d["alpha"], cl=d["cl"], cd=d["cd"], cm=d["cm"],
                       converged=d["converged"], **meta)

    def __repr__(self):
        return (f"PolarGrid({self.airfoil_name!r}, Re {self.re.min():.3g}..{self.re.max():.3g} "
                f"[{len(self.re)}], alpha {self.alpha[0]}..{self.alpha[-1]} "
                f"[{len(self.alpha)}], converged {self.converged.mean():.0%})")


# ---------------------------------------------------------------- helpers
def _fill_interior_gaps(x, arr, max_gap):
    """In-place: linearly fill NaN runs of length <= max_gap that have valid
    data on both sides. Leading/trailing NaNs (e.g. beyond stall) stay NaN."""
    for row in arr:
        ok = np.isfinite(row)
        if ok.sum() < 2:
            continue
        idx = np.flatnonzero(ok)
        for lo, hi in zip(idx[:-1], idx[1:]):
            if 1 < hi - lo <= max_gap + 1:
                row[lo + 1:hi] = np.interp(x[lo + 1:hi], [x[lo], x[hi]], [row[lo], row[hi]])


def _refined_extremum(x, y, i):
    """Refine the discrete maximum at index i with a parabola through its
    neighbours. Falls back to the raw point at the array ends."""
    if 0 < i < len(x) - 1:
        c2, c1, c0 = np.polyfit(x[i - 1:i + 2], y[i - 1:i + 2], 2)
        if c2 < 0:
            xv = -c1 / (2 * c2)
            if x[i - 1] <= xv <= x[i + 1]:
                return float(xv), float(c0 + c1 * xv + c2 * xv ** 2)
    return float(x[i]), float(y[i])
