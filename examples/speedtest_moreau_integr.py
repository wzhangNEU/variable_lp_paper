import numpy as np
import pygpu

import odl
from variable_lp._numpy_impl import varlp_moreau_integrand_npy
from variable_lp._numba_impl import varlp_moreau_integrand_numba
from variable_lp._cython_impl import varlp_moreau_integrand_cython
from variable_lp._gpuarray_impl import varlp_moreau_integrand_gpuary

size = int(1e6)
sigma = 1.0
dtype = np.dtype('float64')

abs_f = np.random.uniform(low=0, high=5, size=size).astype(dtype)
p = np.random.uniform(low=1, high=2, size=size).astype(dtype)
out = np.empty_like(abs_f)

abs_f_gpu = pygpu.gpuarray.array(abs_f)
p_gpu = pygpu.gpuarray.array(p)
out_gpu = abs_f_gpu._empty_like_me()

with odl.util.Timer('Numpy'):
    varlp_moreau_integrand_npy(abs_f, p, sigma, 10)

with odl.util.Timer('Numpy in-place'):
    varlp_moreau_integrand_npy(abs_f, p, sigma, 10, out=out)

with odl.util.Timer('Numba CPU'):
    varlp_moreau_integrand_numba(abs_f, p, sigma, 10, 'cpu')

with odl.util.Timer('Numba parallel'):
    varlp_moreau_integrand_numba(abs_f, p, sigma, 10, 'parallel')

with odl.util.Timer('Numba CUDA'):
    varlp_moreau_integrand_numba(abs_f, p, sigma, 10, 'cuda')

with odl.util.Timer('Cython'):
    varlp_moreau_integrand_cython(abs_f, p, sigma, 10)

with odl.util.Timer('Cython in-place'):
    varlp_moreau_integrand_cython(abs_f, p, sigma, 10, out=out)

with odl.util.Timer('GpuArray 1st time'):
    varlp_moreau_integrand_gpuary(abs_f, p, sigma, 10)

with odl.util.Timer('GpuArray 2nd time'):
    varlp_moreau_integrand_gpuary(abs_f, p, sigma, 10)

with odl.util.Timer('GpuArray in-place'):
    varlp_moreau_integrand_gpuary(abs_f, p, sigma, 10, out=out_gpu)

with odl.util.Timer('GpuArray without copying'):
    varlp_moreau_integrand_gpuary(abs_f_gpu, p, sigma, 10)
