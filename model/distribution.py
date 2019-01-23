import numpy as NP

#__doc__ = """
#Function definitions for variogram models. In each function, m is a list of
#defining parameters and d is an array of the distance values at which to
#calculate the variogram model.
#
#References
#----------
#.. [1] P.K. Kitanidis, Introduction to Geostatistcs: Applications in
#    Hydrogeology, (Cambridge University Press, 1997) 272 p.
#"""

## distriubtions
def linear(m, d):
    """Linear model, m is [slope, nugget]"""
    slope = float(m[0])
    nugget = float(m[1])
    return slope * d + nugget


def power(m, d):
    """Power model, m is [scale, exponent, nugget]"""
    scale = float(m[0])
    exponent = float(m[1])
    nugget = float(m[2])
    return scale * d**exponent + nugget


def gaussian(m, d):
    """Gaussian model, m is [psill, range, nugget]"""
    psill = float(m[0])
    range_ = float(m[1])
    nugget = float(m[2])
    return psill * (1. - NP.exp(-d**2./(range_*4./7.)**2.)) + nugget


def exponential(m, d):
    """Exponential model, m is [psill, range, nugget]"""
    psill = float(m[0])
    range_ = float(m[1])
    nugget = float(m[2])
    return psill * (1. - NP.exp(-d/(range_))) + nugget


def spherical(m, d):
    """Spherical model, m is [psill, range, nugget]"""
    psill = float(m[0])
    range_ = float(m[1])
    nugget = float(m[2])
    return NP.piecewise(d, [d <= range_, d > range_],
                        [lambda x: psill * ((3.*x)/(2.*range_) - (x**3.)/(2.*range_**3.)) + nugget, psill + nugget])


def hole_effect(m, d):
    """Hole Effect model, m is [psill, range, nugget]"""
    psill = float(m[0])
    range_ = float(m[1])
    nugget = float(m[2])
    return psill * (1. - (1.-d/(range_/3.)) * NP.exp(-d/(range_/3.))) + nugget


def circular(m, d):
    """Circular model, m is [psill, range, nugget]"""
    psill = float(m[0])
    range_ = float(m[1])
    nugget = float(m[2])
    return NP.piecewise(d, [d <= range_, d > range_],
                        [lambda x: psill * (1 - 2/NP.pi/NP.cos(x/range_) + NP.sqrt(1-(x/range_)**2)) + nugget, psill + nugget])

distributions = { 'linear':linear, 
                  'power':power,
                  'gaussian':gaussian,
                  'exponential':exponential,
                  'spherical':spherical,
                  'hole_effect':hole_effect,
                  'circular':circular }

