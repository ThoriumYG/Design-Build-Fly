import numpy as np
import matplotlib.pyplot as plt

## Function of this program is to visualise the relationship between chosen stall speed,
#  CLmax, mass and wing reference area. The program plots a four dimensional visualisation
#  (with the fourth dimension being colour) showing how different parameter configurations
#  affect the required wing reference area. 

# Reasonable parameters chosen as estimates
density = 1.225
g = 9.81

# Reasonable ranges of variables created
stall_speed = np.linspace(7, 17, 15)   # fewer points keeps the plot readable
Cl_max = np.linspace(0.8, 1.4, 15)
mass = np.linspace(1.3, 2.0, 15)

""" # PLotting
V, CL, M = np.meshgrid(stall_speed, Cl_max, mass, indexing="ij")
Sref = (M * g) / (0.5 * density * V**2 * CL)

fig = plt.figure(figsize=(9, 7))
ax = fig.add_subplot(projection="3d")

sc = ax.scatter(V.ravel(), CL.ravel(), M.ravel(),
                c=Sref.ravel(), cmap="viridis", alpha=0.6)

ax.set_xlabel("Stall speed (m/s)")
ax.set_ylabel("Cl_max")
ax.set_zlabel("Mass (kg)")
fig.colorbar(sc, label="Sref (m²)", shrink=0.7)
plt.show() """


## In person calculation

inner_chord_length = 0.25 #m

CLmax_range = np.linspace(1.07, 1.42, 10)
stall_speed = 8 #m/s
Re_vel_range = np.linspace(8, 25, 20)
dynamic_visc = 17.96 * 10**(-6) #Pa*S

density = 1.16 #kg/m^3
mass = 2.2 #kg
ReNum = (density*stall_speed*inner_chord_length)/dynamic_visc
ReNum_range = (density*Re_vel_range*inner_chord_length)/dynamic_visc

area_range = (mass * g) / (0.5 * density * stall_speed**2 * CLmax_range)

# Assuming no taper
wingspan = area_range/inner_chord_length # m

plt.figure()
plt.plot(CLmax_range, area_range)
plt.xlabel("CL_max")
plt.ylabel("Required wing reference area (m²)")
plt.title("Required wing area vs. CL_max")
plt.grid(True)
plt.show()

""" plt.figure()
plt.plot(area_range, wingspan)
plt.xlabel("area of wing (m^2)")
plt.ylabel("wingspan (m)")
plt.title("Required wing span vs. wing area ")
plt.grid(True)
plt.show() """


max_re = np.max(ReNum_range)
min_re = np.min(ReNum_range)
print("range of reynolds numbers. Min:", min_re, "and Max:", max_re)




