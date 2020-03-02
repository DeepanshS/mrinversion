#!/usr/bin/env python
# coding: utf-8
"""
2D MAF of Rb2O 2.25SiO2 glass
=============================
"""
# sphinx_gallery_thumbnail_number = 5
#%%
# The following example is an application of the statistical learning method applied in
# determining the distribution of the nuclear shielding tensor parameters from a 2D
# magic-angle flipping (MAF) spectrum. In this example, we use the 2D MAF spectrum
# [#f1]_ of :math:`\text{Rb}_2\text{O}\cdot2.25\text{SiO}_2` glass.
#
# Setup for the matplotlib figure.
import matplotlib.pyplot as plt
from pylab import rcParams

rcParams["figure.figsize"] = 4, 3
rcParams["font.size"] = 9

#%%
# Import the dataset
# ^^^^^^^^^^^^^^^^^^
#
# Load the dataset. In this example, we import the dataset as the CSDM [#f2]_
# data-object.
import csdmpy as cp

from mrinversion import examples

# the 2D MAF dataset in csdm format
data_object = cp.load(examples.exp2)

#%%
# The variable ``data_object`` is a `CSDM <https://csdmpy.readthedocs.io/en/latest/api/CSDM.html>`_
# object that holds the 2D MAF dataset. The plot of the 2D MAF dataset is
cp.plot(data_object, cmap="gist_ncar_r", reverse_axis=[True, True])

#%%
# There are two dimensions in this dataset. The dimension at index 0, the horizontal
# dimension in the figure, is the pure anisotropic dimension, while the dimension at
# index 1, the vertical dimension, is the isotropic chemical shift dimension. The
# number of coordinates along the respective dimensions is
print(data_object.shape)

#%%
# When using csdm objects with mrinversion, the dimension at index 0 must always be
# the dimension undergoing the linear inversion, which in this example should be the
# pure anisotropic dimension. In the variable ``data_object``, the anisotropic dimension
# is already at index 0 and, therefore, no further action is required.
# Also notice, that the MAF data only occupies a small fraction of the two-dimensional
# frequency grid. It is, therefore, best to truncate the dataset to the desired region
# before proceeding. Use the appropriate array indexing/slicing to select the signal
# region.

data_object_truncated = data_object[:, 240:285]
cp.plot(data_object_truncated, cmap="gist_ncar_r", reverse_axis=[True, True])

#%%
# In the above code, we truncate the isotropic chemical shift dimension to isotropic
# chemical shift values between indexes 250 to 285, which corresponds to the following
# coordinates.
print(data_object_truncated.dimensions[1].coordinates)

#%%
# Linear Inversion
# ^^^^^^^^^^^^^^^^
#
# Set the anisotropic and inverse-dimension
# -----------------------------------------
#
# **The anisotropic-dimension**
#
# The anisotropic dimension of the 2D MAF dataset should always be the dimension at
# index 0.
anisotropic_dimension = data_object_truncated.dimensions[0]

#%%
# **Inverse-dimension**
#
# The two inverse dimensions correspond to the `x` and `y`-axis of the `x`-`y` grid.
inverse_dimensions = [
    # along the `x`-dimension.
    cp.LinearDimension(count=25, increment="400 Hz", label="x"),
    # along the `y`-dimension.
    cp.LinearDimension(count=25, increment="400 Hz", label="y"),
]

#%%
# Generate the line-shape kernel
# ------------------------------
# In this example, the line-shape kernel corresponds to the pure nuclear shielding
# anisotropy line-shapes, as observed by a MAF experiment.

from mrinversion.kernel import NuclearShieldingTensor

method = NuclearShieldingTensor(
    anisotropic_dimension=anisotropic_dimension,
    inverse_dimension=inverse_dimensions,
    isotope="29Si",
    magnetic_flux_density="9.4 T",
    rotor_angle="90 deg",
    rotor_frequency="13 kHz",
    number_of_sidebands=4,
)

#%%
# The above code generates an instance of the NuclearShieldingTensor class, which we
# assign to the variable ``method``.
# The two required arguments of this class are the `anisotropic_dimension` and
# `inverse_dimension`, as previously defined.
# The value of the remaining optional attributes such as the isotope, magnetic flux
# density, rotor angle, and rotor frequency is set to match the conditions under which
# the MAF spectrum was acquired. Note for the MAF measurements the rotor angle is
# usually :math:`90^\circ` for the anisotropic dimension. Once the
# NuclearShieldingTensor instance is created, use the
# :meth:`~mrinversion.kernel.NuclearShieldingTensor.kernel` method to generate the MAF
# lineshape kernel.
K = method.kernel(supersampling=5)
print(K.shape)

#%%
# The kernel ``K`` is a NumPy array of shape (128, 625), where the axis with 128 points
# corresponds to the anisotropic dimension, and the axis with 625 points are the features
# corresponding to the :math:`25\times 25` `x`-`y` coordinates.

#%%
# Data Compression
# ----------------
# Data compression is optional but is recommended. It may reduce the size of the
# inverse problem and, thus, further computation time.
from mrinversion.linear_model import TSVDCompression

new_system = TSVDCompression(K, data_object_truncated)
compressed_K = new_system.compressed_K
compressed_s = new_system.compressed_s

print(f"truncation_index = {new_system.truncation_index}")

#%%
# Set up the inverse problem
# --------------------------
#
# Solve the smooth-lasso problem. Normally, one should use the statistical learning
# method to solve the problem over a range of α and λ values, and determine a nuclear
# shielding tensor distribution that best depicts the 2D MAF dataset.
# Given, the time constraints for building this documentation, we skip this step
# and evaluate the nuclear shielding tensor distribution at the pre-optimized α
# and λ values, where the optimum values are :math:`\alpha = 0.00248` and
# :math:`\lambda = 1.833\times 10^{-6}`.
# The following commented code was used in determining the optimum α and λ values.

#%%
import numpy as np

# from mrinversion.linear_model import SmoothLassoCV

# lambdas = 10 ** (-4 - 3 * (np.arange(20) / 19))
# alphas = 10 ** (-1 - 4 * (np.arange(20) / 19)

# s_lasso = SmoothLassoCV(
#     alphas=alphas,
#     lambdas=lambdas,
#     sigma=0.0043,
#     folds=10,
#     inverse_dimension=inverse_dimensions,
#     verbose=1,
# )
# s_lasso.fit(compressed_K, compressed_s)

# print(s_lasso.hyperparameter)
# # {'alpha': 0.003359818286283781, 'lambda': 1.8329807108324375e-06}

# # the solution
# f_sol = s_lasso.f

#%%
# If you use the ``SmoothLassoCV`` method shown above to evaluate the optimum α and
# λ values, skip the following section of the code.

from mrinversion.linear_model import SmoothLasso

s_lasso = SmoothLasso(
    alpha=0.0034, lambda1=1.833e-6, inverse_dimension=inverse_dimensions
)
s_lasso.fit(K=compressed_K, s=compressed_s)

# the solution
f_sol = s_lasso.f

#%%
# Here, ``f_sol`` is the solution corresponding to the optimized hyperparameters. To
# calculate the residuals between the data and predicted data(fit), use the
# :meth:`~mrinversion.linear_model.SmoothLasso.residuals` method, as follows,

residue = s_lasso.residuals(K, data_object_truncated.real)
cp.plot(
    residue,
    cmap="gist_ncar_r",
    vmax=data_object_truncated.real.max(),
    vmin=data_object_truncated.real.min(),
    reverse_axis=[True, True],
)

#%%
# The standard deviation of the residuals is
residue.std()

#%%
# **Serialize the solution**
#
# To serialize the solution data to a file, use the `save()` method of the CSDM object,
# for example,

f_sol.save("Rb2O.2.25SiO2_inverse.csdf")  # save the solution
residue.save("Rb2O.2.25SiO2_residue.csdf")  # save the residuals

#%%
# At this point, we have solved the inverse problem and obtained an optimum
# distribution of the nuclear shielding tensors from the 2D MAF dataset. You may use
# any data visualization and interpretation tool of choice for further analysis.
# In the following sections, we provide minimal visualization and analysis
# to complete the case study.
#
# Data Visualization
# ^^^^^^^^^^^^^^^^^^
#
from mpl_toolkits.mplot3d import Axes3D
from mrinversion.plot import plot_3d
from matplotlib import cm

# Normalize the solution so that the maximum amplitude is 1.
f_sol /= f_sol.max()

# Convert the coordinates of the solution, `f_sol`, from frequency units to ppm.
[item.to("ppm", "nmr_frequency_ratio") for item in f_sol.dimensions]

# The 3d plot of the solution
plt.figure(figsize=(5, 4.4))
ax = plt.gca(projection="3d")
plot_3d(ax, f_sol, x_lim=[0, 140], y_lim=[0, 140], z_lim=[-50, -150])
plt.tight_layout()
plt.show()

#%%
# From the 3D plot, we observe two distinct volumes: one for the :math:`\text{Q}^4`
# sites and another for the :math:`\text{Q}^3` site.
# Select the respective volumes by using the appropriate array indexing,

Q4_region = f_sol[0:7, 0:7, 14:35]
Q4_region.description = "Q4 region"

Q3_region = f_sol[0:8, 10:24, 21:40]
Q3_region.description = "Q3 region"
#%%
# The plot of the respective volumes is shown below.

max_2d = [
    f_sol.sum(axis=0).max().value,
    f_sol.sum(axis=1).max().value,
    f_sol.sum(axis=2).max().value,
]
max_1d = [
    f_sol.sum(axis=(1, 2)).max().value,
    f_sol.sum(axis=(0, 2)).max().value,
    f_sol.sum(axis=(0, 1)).max().value,
]

plt.figure(figsize=(5, 4.4))
ax = plt.gca(projection="3d")

# plot for Q4 region
plot_3d(
    ax,
    Q4_region,
    x_lim=[0, 140],
    y_lim=[0, 140],
    z_lim=[-50, -150],
    max_2d=max_2d,
    max_1d=max_1d,
    cmap=cm.Reds_r,
    box=True,
)
# plot for Q3 region
plot_3d(
    ax,
    Q3_region,
    x_lim=[0, 140],
    y_lim=[0, 140],
    z_lim=[-50, -150],
    max_2d=max_2d,
    max_1d=max_1d,
    cmap=cm.Blues_r,
    box=True,
)
ax.legend()
plt.tight_layout()
plt.show()

#%%
# Because the :math:`\text{Q}^4` and :math:`\text{Q}^3` sites are fully resolved after
# inversion, we can observe the individual contributions from these sites without
# having to build any model. For examples, the distribution of the isotropic chemical
# shifts for these sites are

# Convert the coordinates of the 2D MAF dataset from frequency units to ppm.
[item.to("ppm", "nmr_frequency_ratio") for item in data_object_truncated.dimensions]
# Isotropic chemical shift projection from MAF dataset.
data_iso = data_object_truncated.sum(axis=0)
# Normalizing the isotropic projection.
data_iso /= data_iso.max()


# Isotropic chemical shift projection from the 3D tensor distribution dataset.
f_sol_iso = f_sol.sum(axis=(0, 1))
f_sol_iso_max = f_sol_iso.max()
# Normalizing the isotropic projection.
f_sol_iso /= f_sol_iso_max


# Isotropic chemical shift projection from the 3D tensor distribution of the Q4 sites.
Q4_region_iso = Q4_region.sum(axis=(0, 1))
# Normalizing the isotropic projection from the Q4 tensor distribution.
Q4_region_iso /= f_sol_iso_max


# Isotropic chemical shift projection from the 3D tensor distribution of the Q3 sites.
Q3_region_iso = Q3_region.sum(axis=(0, 1))
# Normalizing the isotropic projection from the Q3 tensor distribution.
Q3_region_iso /= f_sol_iso_max


def plot(csdm, style, label):
    plt.plot(
        csdm.dimensions[0].coordinates,
        csdm.dependent_variables[0].components[0].real,
        style,
        label=label,
    )


plt.figure(figsize=(5.5, 3.5))
plot(data_iso, "-k", label="MAF projection")
plot(f_sol_iso, "--k", label="tensor projection")
plot(Q4_region_iso, "r", label="Q4 isotropic shifts")
plot(Q3_region_iso, "b", label="Q3 isotropic shifts")
plt.xlabel("isotropic chemical shift / pmm")
plt.legend()
plt.show()

#%%
#
# Analysis
# ^^^^^^^^
#
# For analysis, we use the `statistics <https://csdmpy.readthedocs.io/en/latest/api/statistics.html>`_
# module of the csdmpy package. In the following code, we perform the moment analysis
# of the 3d volumes for both the :math:`\text{Q}^4` and :math:`\text{Q}^3` sites
# up to the second moment.

import csdmpy.statistics as stat

int_Q4 = stat.integral(Q4_region)  # volume of the Q4 distribution
mean_Q4 = stat.mean(Q4_region)  # mean of the Q4 distribution
std_Q4 = stat.std(Q4_region)  # standard deviation of the Q4 distribution

int_Q3 = stat.integral(Q3_region)  # volume of the Q3 distribution
mean_Q3 = stat.mean(Q3_region)  # mean of the Q3 distribution
std_Q3 = stat.std(Q3_region)  # standard deviation of the Q3 distribution

print("Q4 statistics")
print(f"\tpopulation = {100 * int_Q4 / (int_Q4 + int_Q3)}%")
print("\tmean\n\t\tx:\t{0}\n\t\ty:\t{1}\n\t\tiso:\t{2}".format(*mean_Q4))
print("\tstandard deviation\n\t\tx:\t{0}\n\t\ty:\t{1}\n\t\tiso:\t{2}".format(*std_Q4))

print("Q3 statistics")
print(f"\tpopulation = {100 * int_Q3 / (int_Q4 + int_Q3)}%")
print("\tmean\n\t\tx:\t{0}\n\t\ty:\t{1}\n\t\tiso:\t{2}".format(*mean_Q3))
print("\tstandard deviation\n\t\tx:\t{0}\n\t\ty:\t{1}\n\t\tiso:\t{2}".format(*std_Q3))

#%%
# The statistics shown above are according to the respective dimensions, that is, the
# `x`, `y`, and the isotropic chemical shifts. To convert the `x` and `y` statistics
# to commonly used :math:`\zeta` and :math:`\eta` statistics, use the
# :func:`~mrinversion.kernel.x_y_to_zeta_eta` function.
from mrinversion.kernel import x_y_to_zeta_eta

mean_ζη_Q3 = x_y_to_zeta_eta(*mean_Q3[0:2])

# error propagation for calculating the standard deviation
std_ζ = (std_Q3[0] * mean_Q3[0]) ** 2 + (std_Q3[1] * mean_Q3[1]) ** 2
std_ζ /= mean_Q3[0] ** 2 + mean_Q3[1] ** 2
std_ζ = np.sqrt(std_ζ)

std_η = (std_Q3[1] * mean_Q3[0]) ** 2 + (std_Q3[0] * mean_Q3[1]) ** 2
std_η /= (mean_Q3[0] ** 2 + mean_Q3[1] ** 2) ** 2
std_η = (4 / np.pi) * np.sqrt(std_η)

print("Q3 statistics")
print(f"\tpopulation = {100 * int_Q3 / (int_Q4 + int_Q3)}%")
print("\tmean\n\t\tζ:\t{0}\n\t\tη:\t{1}\n\t\tiso:\t{2}".format(*mean_ζη_Q3, mean_Q3[2]))
print(
    "\tstandard deviation\n\t\tζ:\t{0}\n\t\tη:\t{1}\n\t\tiso:\t{2}".format(
        std_ζ, std_η, std_Q3[2]
    )
)


#%%
# References
# ^^^^^^^^^^
#
# .. [#f1] Baltisberger, J. H., Florian, P., Keeler, E. G., Phyo, P. A., Sanders, K. J.,
#       Grandinetti, P. J.. Modifier cation effects on 29Si nuclear shielding
#       anisotropies in silicate glasses, J. Magn. Reson. 268 (2016) 95 – 106.
#       `doi:10.1016/j.jmr.2016.05.003 <https://doi.org/10.1016/j.jmr.2016.05.003>`_.
#
# .. [#f2] Srivastava, D.J., Vosegaard, T., Massiot, D., Grandinetti, P.J. (2020) Core
#       Scientific Dataset Model: A lightweight and portable model and file format
#       for multi-dimensional scientific data.
#       `PLOS ONE 15(1): e0225953. <https://doi.org/10.1371/journal.pone.0225953>`_