#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests backpropagation algorithm
"""
from __future__ import division, print_function

import numpy as np
import os
from os.path import abspath, basename, dirname, join, split, exists
import platform
import sys
import warnings
import zipfile

# Add parent directory to beginning of path variable
DIR = dirname(abspath(__file__))
sys.path = [split(DIR)[0]] + sys.path

import odtbrain
import odtbrain._Back_3D_tilted

from common_methods import create_test_sino_2d, get_test_parameter_set, write_results, get_results


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()


    import scipy
    import scipy.ndimage
    import spimagine
    import matplotlib.pylab as plt
    from mpl_toolkits.mplot3d import Axes3D
    from matplotlib.patches import FancyArrowPatch
    from mpl_toolkits.mplot3d import proj3d

    class Arrow3D(FancyArrowPatch):
        def __init__(self, xs, ys, zs, *args, **kwargs):
            FancyArrowPatch.__init__(self, (0,0), (0,0), *args, **kwargs)
            self._verts3d = xs, ys, zs
    
        def draw(self, renderer):
            xs3d, ys3d, zs3d = self._verts3d
            xs, ys, zs = proj3d.proj_transform(xs3d, ys3d, zs3d, renderer.M)
            self.set_positions((xs[0],ys[0]),(xs[1],ys[1]))
            FancyArrowPatch.draw(self, renderer)


    # Testarray
    N=50
    A=41
    proj = np.zeros((N,N,N))
    #proj[(N-1)/2,(N-1)/2,:(N-1)/2] = np.abs(np.linspace(-10,0,(N-1)/2))
    proj[(N)/2,(N)/2,:(N)/2] = np.abs(np.linspace(-10,1,(N)/2))
    
    # By default, the rotational axis in _Back_3D_tilted is the y-axis.
    # Define a rotational axis with a slight offset in x and in z.
    axis = np.array([.0,1,.3])
    axis /= np.sqrt(np.sum(axis**2))
    
    # Now, obtain the 3D angles that are equally distributed on the unit
    # sphere and correspond to the positions of projections that we would
    # measure.
    angles = np.linspace(0, 2*np.pi, A, endpoint=False)
    #angles = np.array([0, np.pi/2, np.pi])
    # The first point in that array will be in the x-z-plane.
    points = odtbrain._Back_3D_tilted.sphere_points_from_angles_and_tilt(angles, axis)
    
    # The following steps are exactly those that are used in 
    # odtbrain._Back_3D_tilted.backpropagate_3d_tilted
    # to perform 3D reconstruction with tilted angles.
    u, v, w = axis
    theta = np.arccos(v)
    
    # We need three rotations.
    
    # IMPROTANT:
    # We perform the reconstruction such that the rotational axis
    # is equal to the y-axis! This is easier than implementing a
    # rotation about the rotational axis and tilting with theta
    # before and afterwards.
    
    # This is the rotation that tilts the projection in the
    # direction of the rotation axis (new y-axis). 
    R2 = np.array([
                   [1,             0,              0],
                   [0, np.cos(theta),  np.sin(theta)],
                   [0, -np.sin(theta),  np.cos(theta)],
                   ])
    
    out = np.zeros((N,N,N))
    
    vectors = []
    
    for ang, pnt in zip(angles, points):
        R1 = np.array([
                       [np.cos(ang),             0,  -np.sin(ang)],
                       [0, 1, 0],
                       [np.sin(ang),0,  np.cos(ang)],
                       ])

        DR = np.dot(R2, R1)
        
        # pnt are already rotated by R1
        vectors.append(np.dot(R2, pnt))
        
        # We need to give this rotation the correct offset
        c = 0.5*np.array(proj.shape)
        offset=c-c.dot(DR.T)
        rotate = scipy.ndimage.interpolation.affine_transform(
                        proj, DR, offset=offset,
                        mode="constant", cval=0, order=2)
        proj *= 1.1
        out += rotate
    
   
    # show arrows pointing at projection directions (should form cone aligned with y)
    fig = plt.figure(figsize=(10,10))
    ax = fig.add_subplot(111, projection='3d')    
    for vec in vectors:
        u,v,w = vec
        a = Arrow3D([0,u],[0,v],[0,w], mutation_scale=20, lw=1, arrowstyle="-|>")
        ax.add_artist(a)
    
    radius=1
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_xlim(-radius*1.5, radius*1.5)
    ax.set_ylim(-radius*1.5, radius*1.5)
    ax.set_zlim(-radius*1.5, radius*1.5)
    plt.tight_layout()
    #plt.show()

    # show backprojection of test volume (should be cone aligned with y)
    spimagine.volshow(out)
    import IPython
    IPython.embed()    