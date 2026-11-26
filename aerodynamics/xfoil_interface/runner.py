"""
Low-level XFOIL driver (subprocess + stdin command script).

Design choices
  * One XFOIL session handles several Reynolds numbers (`RE` + `INIT` between
    them) so the airfoil is loaded and paneled once.
  * Each Re is swept twice from `alpha_start`: upward to `alpha_max` (stall
    side) and, after re-initialising the boundary layer, downward to
    `alpha_min`. Starting near zero lift converges far more reliably than
    starting at a large negative angle.
  * Sessions run in isolated temp dirs (RAM disk /dev/shm when available) and
    in parallel threads; each is a separate OS process, so a crash or hang only
    loses that chunk.
  * A Re that comes back nearly empty is retried once in a fresh session.
  * `INIT` is never sent before the first solution exists: doing so leaves
    XFOIL in a NaN state for the rest of the session.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .airfoil import AirfoilSpec

POLAR_COLUMNS = ["alpha", "CL", "CD", "CDp", "CM", "Top_Xtr", "Bot_Xtr"]
CACHE_FORMAT_VERSION = 1


@dataclass(frozen=True)
class XfoilSettings:
    """Everything that changes XFOIL's answer. Hashed into the cache key."""
    alpha_min: float = -6.0
    alpha_max: float = 18.0
    alpha_step: float = 0.5
    alpha_start: float = 0.0
    mach: float = 0.0
    ncrit: float = 9.0
    xtr_top: float = 1.0      # forced transition x/c, 1.0 = free transition
    xtr_bot: float = 1.0
    n_panels: int = 160
    max_iter: int = 100

    def alpha_grid(self) -> np.ndarray:
        n = int(round((self.alpha_max - self.alpha_min) / self.alpha_step))
        return np.round(self.alpha_min + self.alpha_step * np.arange(n + 1), 6)

    @property
    def key(self) -> str:
        payload = json.dumps({**asdict(self), "_v": CACHE_FORMAT_VERSION}, sort_keys=True)
        return hashlib.sha1(payload.encode()).hexdigest()[:12]


class XfoilRunner:
    """Runs XFOIL for one airfoil over a list of Reynolds numbers."""

    def __init__(self, xfoil_path: str = "xfoil", max_workers: int | None = None,
                 timeout_per_re: float = 60.0, min_points_fraction: float = 0.3,
                 workdir_root: str | Path | None = None, keep_files: bool = False):
        exe = shutil.which(xfoil_path) or (xfoil_path if Path(xfoil_path).is_file() else None)
        if exe is None:
            raise FileNotFoundError(f"XFOIL executable not found: {xfoil_path!r}")
        self.xfoil_path = exe
        self.max_workers = max_workers or max(1, (os.cpu_count() or 2) - 1)
        self.timeout_per_re = timeout_per_re
        self.min_points_fraction = min_points_fraction
        if workdir_root is None and os.access("/dev/shm", os.W_OK):
            workdir_root = "/dev/shm"          # RAM disk on Linux
        self.workdir_root = workdir_root
        self.keep_files = keep_files

    # ------------------------------------------------------------------ public
    def run(self, airfoil: AirfoilSpec, re_list, settings: XfoilSettings
            ) -> dict[float, pd.DataFrame]:
        """Return {Re: DataFrame(POLAR_COLUMNS)} of converged points only.
        A Re with no converged points maps to an empty DataFrame."""
        re_list = [float(r) for r in re_list]
        if not re_list:
            return {}
        n_chunks = min(self.max_workers, len(re_list))
        chunks = [[float(x) for x in c] for c in np.array_split(np.array(re_list), n_chunks)]

        results: dict[float, pd.DataFrame] = {}
        with ThreadPoolExecutor(max_workers=n_chunks) as pool:
            for part in pool.map(lambda c: self._session(airfoil, c, settings), chunks):
                results.update(part)

        # retry sparse results individually (a NaN or hang mid-session can
        # wipe out the remaining Re of that chunk)
        n_grid = len(settings.alpha_grid())
        sparse = [r for r in re_list
                  if len(results.get(r, ())) < self.min_points_fraction * n_grid]
        if sparse and len(re_list) > 1:
            with ThreadPoolExecutor(max_workers=min(self.max_workers, len(sparse))) as pool:
                for part in pool.map(lambda r: self._session(airfoil, [r], settings), sparse):
                    for r, df in part.items():
                        if len(df) > len(results.get(r, ())):
                            results[r] = df
        return {r: results.get(r, _empty()) for r in re_list}

    # ----------------------------------------------------------------- private
    def _session(self, airfoil, re_list, s: XfoilSettings) -> dict[float, pd.DataFrame]:
        tmp = Path(tempfile.mkdtemp(prefix="xf_", dir=self.workdir_root))
        try:
            files = [(f"u{i:02d}.pol", f"d{i:02d}.pol") for i in range(len(re_list))]
            script = self._script(airfoil.xfoil_load_commands(tmp), re_list, s, files)
            log = open(tmp / "xfoil.log", "w") if self.keep_files else subprocess.DEVNULL
            try:
                subprocess.run([self.xfoil_path], input="\n".join(script) + "\n",
                               text=True, cwd=tmp, stdout=log, stderr=subprocess.STDOUT,
                               timeout=30 + self.timeout_per_re * len(re_list))
            except subprocess.TimeoutExpired:
                pass  # keep whatever was written before the hang
            finally:
                if log is not subprocess.DEVNULL:
                    log.close()

            out = {}
            for re_num, (up, dn) in zip(re_list, files):
                frames = [f for f in (read_polar_file(tmp / up), read_polar_file(tmp / dn))
                          if not f.empty]
                if frames:
                    df = (pd.concat(frames, ignore_index=True)
                            .drop_duplicates("alpha", keep="first")
                            .sort_values("alpha", ignore_index=True))
                else:
                    df = _empty()
                out[re_num] = df
            return out
        finally:
            if not self.keep_files:
                shutil.rmtree(tmp, ignore_errors=True)

    @staticmethod
    def _script(load_cmds, re_list, s: XfoilSettings, files) -> list[str]:
        a0, step = s.alpha_start, abs(s.alpha_step)
        cmd = ["PLOP", "G F", "",                     # graphics off
               *load_cmds,
               "PPAR", f"N {s.n_panels}", "", "",     # re-panel
               "OPER",
               f"ITER {s.max_iter}",
               "VPAR", f"N {s.ncrit}", f"XTR {s.xtr_top} {s.xtr_bot}", "",
               f"MACH {s.mach}",
               f"VISC {re_list[0]:.0f}"]
        solved = False
        for i, re_num in enumerate(re_list):
            up, dn = files[i]
            if i > 0:
                cmd.append(f"RE {re_num:.0f}")
                if solved:
                    cmd.append("INIT")
            if s.alpha_max > a0:
                cmd += [f"ALFA {a0}",                          # warm-up point
                        "PACC", up, "",
                        f"ASEQ {a0} {s.alpha_max} {step}",
                        "PACC"]
                solved = True
            if s.alpha_min < a0:
                if solved:
                    cmd.append("INIT")
                cmd += [f"ALFA {a0}",
                        "PACC", dn, "",
                        f"ASEQ {a0} {s.alpha_min} {-step}",
                        "PACC"]
                solved = True
        cmd += ["", "QUIT"]
        return cmd


def read_polar_file(path: Path) -> pd.DataFrame:
    """Parse an XFOIL PACC polar file into a DataFrame."""
    if not path.exists():
        return _empty()
    lines = path.read_text(errors="replace").splitlines()
    try:
        dash = next(i for i, l in enumerate(lines) if l.strip().startswith("------"))
    except StopIteration:
        return _empty()
    rows = []
    for line in lines[dash + 1:]:
        parts = line.split()
        if len(parts) < len(POLAR_COLUMNS):
            continue
        try:
            rows.append([float(p) for p in parts[:len(POLAR_COLUMNS)]])
        except ValueError:          # '******' overflow fields etc.
            continue
    df = pd.DataFrame(rows, columns=POLAR_COLUMNS) if rows else _empty()
    return df[np.isfinite(df[["CL", "CD", "CM"]]).all(axis=1)].reset_index(drop=True)


def _empty() -> pd.DataFrame:
    return pd.DataFrame({c: pd.Series(dtype=float) for c in POLAR_COLUMNS})
