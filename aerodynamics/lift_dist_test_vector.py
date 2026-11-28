'''
Concept: 
The wing is split up into spanwise parts. The y-span coordinate is the y-coordinate of the center of of such a wing part.
The Cl is the lift of that part of the wing divided by q*c*delta_y

Please copy the block of main wing data below the given header:

Main Wing
  y-span        Chord      Ai         Cl        PCd          ICd        CmGeom    CmAirf@chord/4    XTrtop    XTrBot      XCP       BM
'''
import numpy as np
import initializations
from aerodynamics import wing_creation

def get_lift_distribution_from_XFLR5():
  with open("data/XFLR5/main_wing_data_min.txt", "r", encoding="utf-8") as wing:
      wing_data = wing.read()
  wd1 = wing_data.replace("     ", ",")
  wd2 = wd1.replace("    ", ",")
  wd3 = wd2.replace("   ", ",")
  wd4 = wd3.replace("  ", ",")
  wd5 = wd4.replace(" ", ",")
  wd6 = wd5.replace("\n", ",")
  wd7 = np.fromstring(wd6, dtype=float, sep=",").reshape(-1, 12)


  #Cl-distribution:
  y = wd7[:, 0]
  cl = wd7[:, 3]
  wing_Cl_distr = np.column_stack((y, cl))
  #print(wing_Cl_distr)

  q = 0.5 * initializations.rho * initializations.v_recon**2
  #wing_span = 2 # [m]
  num_panels = 10
  y = wd7[:, 0]

  #print(wing_creation.y_positions(10))

  # This returns a wrong lift distribution because it neglects the y_positions function from the wing creation
  lift = []
  for x in range(len(wd7)):
    lift += [q * wd7[x, 3] * wd7[x, 1] * (wing_creation.y_positions(num_panels)[x+1]-wing_creation.y_positions(num_panels)[x])]
  L = np.array(lift)
  wing_L_distr = np.column_stack((y, L))
  #print(wing_L_distr)
  # Test the functions
  lift_sum = 0
  for x in range(len(wing_L_distr)):
      lift_sum += wing_L_distr[x, 1]
  lift_sum *= 2
  #print(lift_sum, q*0.34012902126915506*0.317281)
  return wing_L_distr
if __name__ == '__main__':
   print(get_lift_distribution_from_XFLR5())