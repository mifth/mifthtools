# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

import bpy
import bgl
import blf
import string

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from bpy_extras import view3d_utils

import math
import mathutils as mathu
import random
from mathutils import Vector

from . import mi_utils_base as ut_base


class MI_Linear_Widget():

    # class constructor
    def __init__(self):
        self.start_point = None
        self.middle_point = None
        self.end_point = None


def draw_lw(context, lw, cross_up_dir):
    region = context.region
    rv3d = context.region_data

    start_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.start_point)
    end_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.end_point)
    middle_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.middle_point)

    dist_ends = ((lw.start_point - lw.end_point).length * 0.06) * cross_up_dir
    end_p1 = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.end_point + dist_ends)
    end_p2 = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.end_point - dist_ends)

    if start_2d and end_2d and end_p1 and end_p2:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(1)
        bgl.glColor4f(0.9, 0.6, 0.25, 1.0)
        bgl.glPointSize(5)

    #     bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glBegin(bgl.GL_LINE_LOOP)
        bgl.glVertex2f(start_2d[0], start_2d[1])
        bgl.glVertex2f(end_p1[0], end_p1[1])
        bgl.glVertex2f(end_p2[0], end_p2[1])
        bgl.glEnd()

        bgl.glBegin(bgl.GL_POINTS)
     #   bgl.glBegin(bgl.GL_POLYGON)
        bgl.glVertex2f(start_2d[0], start_2d[1])
        bgl.glVertex2f(middle_2d[0], middle_2d[1])
        bgl.glVertex2f(end_2d[0], end_2d[1])
        bgl.glEnd()

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)