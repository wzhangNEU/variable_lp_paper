"""Reference TGV denoising of the affine example."""

import matplotlib.pyplot as plt
import numpy as np
import scipy
import odl


# --- Reconstruction space and phantom --- #

# Read image and transform from 'ij' storage to 'xy'
# NOTE: this requires the "pillow" package
image = np.rot90(scipy.misc.imread('affine_phantom.png'), k=-1)

reco_space = odl.uniform_discr([-10, -10], [10, 10], image.shape,
                               dtype='float32')
phantom = reco_space.element(image)


# --- Set up the forward operator --- #

# Make a fan beam geometry with flat detector
# Angles: uniformly spaced, n = 360, min = 0, max = 2 * pi
angle_partition = odl.uniform_partition(0, 2 * np.pi, 360)
# Detector: uniformly sampled, n = 558, min = -60, max = 60
detector_partition = odl.uniform_partition(-40, 40, 400)
# Geometry with large fan angle
geometry = odl.tomo.FanFlatGeometry(
    angle_partition, detector_partition, src_radius=40, det_radius=40)

# Ray transform (= forward projection).
ray_trafo = odl.tomo.RayTransform(reco_space, geometry)


# Read the data
bad_data = ray_trafo.range.element(np.load('affine_tomo_bad_data.npy'))


# --- Set up the inverse problem --- #


# Initialize gradient and 2nd order derivative operator
gradient = odl.Gradient(reco_space, pad_mode='order1')
eps = odl.DiagonalOperator(gradient, reco_space.ndim)
domain = odl.ProductSpace(gradient.domain, eps.domain)

# Assemble operators and functionals for the solver

# The linear operators are
# 1. ray transform on the first component for the data matching
# 2. gradient of component 1 - component 2 for the auxiliary functional
# 3. eps on the second component
# 4. projection onto the first component

lin_ops = [
    ray_trafo * odl.ComponentProjection(domain, 0),
    odl.ReductionOperator(gradient, odl.ScalingOperator(gradient.range, -1)),
    eps * odl.ComponentProjection(domain, 1),
    odl.ComponentProjection(domain, 0)
    ]

# The functionals are
# 1. L2 data matching
# 2. regularization parameter 1 times L1 norm on the range of the gradient
# 3. regularization parameter 2 times L1 norm on the range of eps
# 4. box indicator on the reconstruction space

data_matching = odl.solvers.L2NormSquared(ray_trafo.range).translated(bad_data)
reg_param1 = 1.5e2
regularizer1 = reg_param1 * odl.solvers.L1Norm(gradient.range)
reg_param2 = 4e1
regularizer2 = reg_param2 * odl.solvers.L1Norm(eps.range)
box_constr = odl.solvers.IndicatorBox(reco_space, 0, 255)

g = [data_matching, regularizer1, regularizer2, box_constr]

# Don't use f
f = odl.solvers.ZeroFunctional(domain)

# Create callback that prints the iteration number and shows partial results
callback_fig = None


def show_first(x):
    global callback_fig
    callback_fig = x[0].show('iterate', clim=[0, 255], fig=callback_fig)


# Uncomment the combined callback to also display iterates
callback = (odl.solvers.CallbackApply(show_first, step=10) &
            odl.solvers.CallbackPrintIteration())
# callback = odl.solvers.CallbackPrintIteration()

# Solve with initial guess x = 0.
# Step size parameters are selected to ensure convergence.
# See douglas_rachford_pd doc for more information.
x = domain.zero()
odl.solvers.douglas_rachford_pd(x, f, g, lin_ops,
                                tau=0.1, sigma=[0.1, 0.02, 0.001, 1], lam=1.5,
                                niter=600, callback=callback)


# --- Display images --- #


# phantom.show(title='Phantom', clim=[-5, 5])
# data.show(title='Data')
x[0].show(title='TGV Reconstruction', clim=[0, 255])
# Display horizontal profile
# fig = phantom.show(coords=[None, -4.25])
# x.show(coords=[None, -4.25], fig=fig, force_show=True)

# Create horizontal profile through the "tip"
phantom_slice = phantom[:, 35]
reco_slice = x[0][:, 35]
x_vals = reco_space.grid.coord_vectors[0]
plt.figure()
axes = plt.gca()
axes.set_ylim([80, 270])
plt.plot(x_vals, phantom_slice, label='Phantom')
plt.plot(x_vals, reco_slice, label='TGV reconstruction')
plt.legend()
plt.tight_layout()
plt.savefig('affine_bimodal_tomo_tgv_profile.png')


# Display full image
plt.figure()
plt.imshow(np.rot90(x[0]), cmap='bone', clim=[0, 255])
axes = plt.gca()
axes.axis('off')
plt.tight_layout()
plt.savefig('affine_bimodal_tomo_tgv_reco.png')
