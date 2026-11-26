"""
Airfoil definition passed to XFOIL.

An AirfoilSpec is the *only* geometry XFOIL needs. Planform data (chord, twist,
span position) never goes to XFOIL; chord only enters through the Reynolds
number, which the database handles.

Two kinds of airfoil are supported:
  * NACA 4/5-digit  -> XFOIL generates it internally (no file is written)
  * coordinates     -> written to a short-lived temp file in a RAM disk
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np


class AirfoilSpec:
    """Immutable airfoil description with a stable hash `key` for caching."""

    def __init__(self, name: str, naca: str | None = None,
                 coordinates: np.ndarray | None = None):
        if (naca is None) == (coordinates is None):
            raise ValueError("Give exactly one of `naca` or `coordinates`.")
        self.name = name
        self.naca = naca
        self.coordinates = None
        if coordinates is not None:
            xy = np.asarray(coordinates, dtype=float)
            if xy.ndim != 2 or xy.shape[1] != 2 or len(xy) < 10:
                raise ValueError("coordinates must be an (N, 2) array with N >= 10")
            self.coordinates = _to_selig_order(_normalise_chord(xy))
            self.coordinates.setflags(write=False)
        self.key = self._make_key()

    # ---- constructors -------------------------------------------------------
    @classmethod
    def from_naca(cls, code: str | int) -> "AirfoilSpec":
        """Accepts 2412, '2412', 'NACA 2412', 'naca23012'."""
        digits = "".join(ch for ch in str(code) if ch.isdigit())
        if isinstance(code, int):
            digits = f"{code:04d}"
        if len(digits) not in (4, 5):
            raise ValueError(f"NACA code must have 4 or 5 digits, got {code!r}")
        return cls(name=f"NACA {digits}", naca=digits)

    @classmethod
    def from_coordinates(cls, xy, name: str) -> "AirfoilSpec":
        return cls(name=name, coordinates=xy)

    @classmethod
    def from_dat(cls, path: str | Path) -> "AirfoilSpec":
        """Read a Selig or Lednicer .dat file (name line optional)."""
        path = Path(path)
        lines = path.read_text().splitlines()
        rows, name = [], path.stem
        for i, line in enumerate(lines):
            parts = line.replace(",", " ").split()
            try:
                vals = [float(p) for p in parts[:2]]
            except ValueError:
                if i == 0 and line.strip():
                    name = line.strip()
                continue
            if len(vals) == 2:
                rows.append(vals)
        xy = np.array(rows)
        # Lednicer format: first data row holds point counts (both > 1)
        if len(xy) and xy[0, 0] > 1.5 and xy[0, 1] > 1.5:
            n_up, n_lo = int(xy[0, 0]), int(xy[0, 1])
            up, lo = xy[1:1 + n_up], xy[1 + n_up:1 + n_up + n_lo]
            xy = np.vstack([up[::-1], lo[1:]])
        return cls(name=name, coordinates=xy)

    # ---- XFOIL interface ----------------------------------------------------
    def xfoil_load_commands(self, workdir: Path) -> list[str]:
        """Commands that put this airfoil into XFOIL's buffer, writing a file
        into `workdir` only for coordinate airfoils."""
        if self.naca is not None:
            return [f"NACA {self.naca}"]
        fname = "foil.dat"
        with open(workdir / fname, "w") as f:
            f.write(f"{self.name[:30] or 'foil'}\n")
            np.savetxt(f, self.coordinates, fmt="%.7f")
        return [f"LOAD {fname}"]

    # ---- helpers ------------------------------------------------------------
    def _make_key(self) -> str:
        h = hashlib.sha1()
        if self.naca is not None:
            h.update(f"naca:{self.naca}".encode())
        else:
            # rounding makes the key insensitive to float noise from generators
            h.update(np.round(self.coordinates, 6).tobytes())
        return h.hexdigest()[:16]

    def __repr__(self):
        kind = f"naca={self.naca}" if self.naca else f"{len(self.coordinates)} pts"
        return f"AirfoilSpec({self.name!r}, {kind}, key={self.key})"

    def __eq__(self, other):
        return isinstance(other, AirfoilSpec) and other.key == self.key

    def __hash__(self):
        return hash(self.key)


def _normalise_chord(xy: np.ndarray) -> np.ndarray:
    """Scale/translate so the leading edge is at x=0 and the chord is 1."""
    x0, x1 = xy[:, 0].min(), xy[:, 0].max()
    out = xy.copy()
    out[:, 0] = (xy[:, 0] - x0) / (x1 - x0)
    out[:, 1] = xy[:, 1] / (x1 - x0)
    return out


def _to_selig_order(xy: np.ndarray) -> np.ndarray:
    """XFOIL expects TE -> upper -> LE -> lower -> TE (counter-clockwise).
    Reverse the point order if the contour runs the other way."""
    x, y = xy[:, 0], xy[:, 1]
    signed_area = 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)
    return xy if signed_area > 0 else xy[::-1].copy()
