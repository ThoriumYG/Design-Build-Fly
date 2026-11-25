import numpy as np
import pandas as pd
from copy import deepcopy as dc
import xml.etree.ElementTree as ET
from scipy.integrate import quad 

import sys
from pathlib import Path

# Get the parent directory of the current script
parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

import initializations


def superellipse_tapered(ellipticity, root_chord, half_span, taper_ratio, coordinate):
    split_ratio = (1 - taper_ratio ** ellipticity) ** (1. / ellipticity)
    l = (1 - (np.abs(coordinate) / half_span * split_ratio) ** ellipticity) ** (1. / ellipticity) * root_chord
    return l


def y_positions(n_panels,spacing_parameter=-1.5, ):
    pabs = abs(spacing_parameter)
    if pabs < 1:
        pequ = 1. - pabs
        pcos = pabs
        psin = 0.
    elif pabs < 2:
        pequ = 0.
        pcos = 2. - pabs
        psin = pabs - 1.
    else:
        pequ = pabs - 2.
        pcos = 0
        psin = 3. - pabs
    frac = np.linspace(0, 1., n_panels + 1)
    theta = np.pi * frac
    if spacing_parameter > 0:
        y = (pequ * frac + pcos * (1. - np.cos(theta)) / 2. + psin * (1. - np.cos(theta / 2.)))
    else:
        y = (pequ * frac + pcos * (1. - np.cos(theta)) / 2. + psin * (np.sin(theta / 2.)))
    return y


class WingObject(object):
    def __init__(
            self,
            name: str, # wing name
            root_chord: float,  # root chord in [m]
            wing_span: float,  # wing span in [m]
            taper_ratio: float, # taper ratio
            ellipticity: float | int,  # ellipticity of wing (2 means perfect ellipse, 1 results in straight taper)
            n_panels: int,  # number of panels/positions. higher number means more accuracy, but also more calculation time in XFLR5
            dihedral: float | int = 0,  # dihedral in degree (must be 0 for the wing)
            tip_twist: float | int = 0, # tip twist / washout of wing, needed to adjust lift distribution in [°]
            spar_position: float | int = 25,  # relative spar position in [%]
            vtp: bool = False,  # flag if wing object is vertical tailplane
            NACA: int | str = '0008',  # NACA airfoil definition as string or as number
            x_panels: int | None = None, # number of panels in chord positions
    ):
        self.name = name
        self.root_chord = root_chord
        self.wing_span = wing_span
        self.projected_half_span = self.wing_span/2.
        self.taper_ratio = max(0.05, taper_ratio)
        self.ellipticity = ellipticity
        self.n_panels = n_panels
        if not x_panels:
            x_panels = np.ceil(n_panels / 4).astype(int)
        self.x_panels = max(5, x_panels)
        self.dihedral = float(dihedral)
        self.tip_twist = float(tip_twist)
        self.spar_position = float(spar_position)/100.
        self.vtp = vtp
        if self.vtp:
            self.projected_half_span *= 2.
        self.geometric_half_span = self.projected_half_span / np.cos(self.dihedral_rad())
        if isinstance(NACA, int):
            NACA = '%04i' % NACA
        if len(NACA) > 4:
            NACA = NACA[:4]
        elif len(NACA) < 4:
            NACA = (4-len(NACA))*'0' + NACA
        self.NACA = NACA

        self.cmac = 2/3 * self.root_chord *(1+self.taper_ratio+self.taper_ratio**2)/(1+self.taper_ratio)

        self.table = pd.DataFrame()
        self.create_table()


    def dihedral_rad(self):
        return np.deg2rad(self.dihedral)

    def chord(self, eta):
        """Chord at normalised half-span position eta = y/(b/2), 0 (root) .. 1 (tip)."""
        n, lam = self.ellipticity, self.taper_ratio
        return self.root_chord * (1.0 - eta**n * (1.0 - lam**n)) ** (1.0 / n)

    def area(self):
        """Wing reference area: S = 2 * integral of c(y) dy over the half-span."""
        integral, _ = quad(self.chord, 0.0, 1.0)   # integral of c over non dimensional eta
        return self.wing_span * integral                 # 2 * (b/2) * integral

    def aspect_ratio(self):
        return self.wing_span**2 / self.area()



    def create_table(self):
        y = y_positions(self.n_panels,) * self.projected_half_span
        l = superellipse_tapered(
            ellipticity=self.ellipticity,
            root_chord=self.root_chord,
            half_span=self.projected_half_span,
            taper_ratio=self.taper_ratio,
            coordinate=y
        )
        z = y * np.tan(self.dihedral_rad())
        twist = self.tip_twist * y / self.projected_half_span
        x = (self.root_chord - l) * self.spar_position
        dct = {
            'x_offset': x,
            'y_offset': y,
            'z_offset': z,
            'chord_length': l,
            'twist': twist,
        }
        self.table = pd.DataFrame.from_dict(dct)

        pass

    def to_XFLR5(self):

        explane = ET.Element("explane", attrib={"version": "1.0"})
        units = ET.SubElement(explane, "Units")
        for unit in ('length_unit_to_meter', 'mass_unit_to_kg'):
            ET.SubElement(units, unit).text = "1"

        wing = ET.SubElement(explane, "wing")
        ET.SubElement(wing, "Name").text=self.name
        if self.vtp:
            ET.SubElement(wing, "isFin").text="true"
        sections = ET.SubElement(wing, "Sections")
        prev_row = {
            'x_offset': 0,
            'y_offset': 0,
            'z_offset': 0,
        }
        y = 0
        for _, row in self.table.iterrows():

            y += np.linalg.norm((
                # row['x_offset']-prev_row['x_offset'],
                row['y_offset']-prev_row['y_offset'],
                row['z_offset']-prev_row['z_offset'],
            ))
            prev_row = dc(row)
            dct = {
                'y_position': y,
                'Chord': row['chord_length'],
                'xOffset': row['x_offset'],
                'Dihedral': self.dihedral,
                'Twist': row['twist'],
                'x_number_of_panels': self.x_panels,
                'x_panel_distribution': 'COSINE',
                'y_number_of_panels': 1,
                'y_panel_distribution': 'UNIFORM',
                'Left_Side_FoilName': f'NACA {self.NACA}',
                'Right_Side_FoilName': f'NACA {self.NACA}',
            }
            section = ET.SubElement(sections, "Section")
            for key, value in dct.items():
                if isinstance(value, (str, int)):
                    value = str(value)
                elif isinstance(value, float):
                    value = f'{np.round(value,6):.6f}'

                ET.SubElement(section, key).text =  str(value)

            pass

        ET.indent(explane, space=' ' * 3)
        ET.ElementTree(explane).write(f"{self.name}.xml", encoding="utf-8", xml_declaration=True)


class Wing(WingObject):
    def __init__(self,*args,**kwargs):
        kwargs.update({
            'name': 'wing',
            'dihedral': 0,
            'vtp': False,

        })
        super().__init__(*args, **kwargs)


class HTP(WingObject):
    def __init__(self,*args,**kwargs):
        kwargs.update({
            'name': 'htp',
            'dihedral': 0,
            'vtp': False,
            'tip_twist': 0,

        })
        super().__init__(*args, **kwargs)


class VTP(WingObject):
    def __init__(self,*args,**kwargs):
        kwargs.update({
            'name': 'vtp',
            'dihedral': 0,
            'vtp': True,
            'tip_twist': 0,

        })
        super().__init__(*args, **kwargs)


class VTail(WingObject):
    def __init__(self,*args,**kwargs):
        kwargs.update({
            'name': 'VTail',
            'vtp': False,
            'tip_twist': 0,

        })
        super().__init__(*args, **kwargs)


if __name__ == '__main__':
    pass