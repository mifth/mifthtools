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


def draw_circle_select(m_coords, radius = 16, p_col = (0.7,0.8,1.0,0.6), enabled = False, sub = False):
    if(enabled):
        f_col = p_col
        if sub:
            f_col = (1.0, 0.5, 0.4, 0.6)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glBegin(bgl.GL_POLYGON)
        bgl.glColor4f(f_col[0], f_col[1], f_col[2], f_col[3]/3)

        point_x = m_coords[0]
        point_y = m_coords[1]

        radius = int(radius)

        for x in range(0, radius*2):
            bgl.glVertex2f(point_x + radius * math.cos(x * (360/(radius*2)) / 180 * 3.14159), point_y + radius * math.sin(x * (360/(radius*2)) / 180 * 3.14159))
        bgl.glEnd()

        bgl.glBegin(bgl.GL_LINES)
        bgl.glColor4f(f_col[0], f_col[1], f_col[2], f_col[3])
        for x in range(0, radius*2):
            bgl.glVertex2f(point_x + radius * math.cos(x * (360 / (radius * 2)) / 180 * 3.14159),
                           point_y + radius * math.sin(x * (360 / (radius * 2)) / 180 * 3.14159))

        bgl.glEnd()
        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


def draw_box_select(anchor, m_coords, region,  p_col = (0.7,0.8,1.0,0.6), enabled = False, dragging = False, sub = False):

    if enabled:
        f_col = p_col
        if sub:
            f_col = (1.0, 0.5, 0.4, 0.6)
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineStipple(1, 0xCCCC)
        bgl.glEnable(bgl.GL_LINE_STIPPLE)

        bgl.glBegin(bgl.GL_LINES)
        bgl.glColor4f(f_col[0], f_col[1], f_col[2], f_col[3])

        point_x = m_coords[0]
        point_y = m_coords[1]

        bgl.glVertex2f(point_x,0)
        bgl.glVertex2f(point_x, region.height)

        bgl.glVertex2f(0, point_y)
        bgl.glVertex2f(region.width, point_y)

        bgl.glEnd()
        bgl.glDisable(bgl.GL_LINE_STIPPLE)
        bgl.glDisable(bgl.GL_BLEND)

        if dragging:
            bgl.glEnable(bgl.GL_BLEND)
            bgl.glBegin(bgl.GL_QUADS)
            bgl.glColor4f(f_col[0], f_col[1], f_col[2], f_col[3] / 3)
            point_x = m_coords[0]
            point_y = m_coords[1]

            anc_x = anchor[0]
            anc_y = anchor[1]

            bgl.glVertex2f(anc_x, anc_y)
            bgl.glVertex2f(point_x, anc_y)
            bgl.glVertex2f(point_x,point_y)
            bgl.glVertex2f(anc_x,point_y)
            bgl.glEnd()

            bgl.glLineStipple(1, 0xCCCC)
            bgl.glEnable(bgl.GL_LINE_STIPPLE)
            bgl.glBegin(bgl.GL_LINE_LOOP)

            bgl.glColor4f(f_col[0], f_col[1], f_col[2], f_col[3])
            bgl.glVertex2f(anc_x, anc_y)
            bgl.glVertex2f(point_x, anc_y)
            bgl.glVertex2f(point_x, point_y)
            bgl.glVertex2f(anc_x, point_y)

            bgl.glEnd()
            # restore opengl defaults
            bgl.glLineWidth(1)
            bgl.glDisable(bgl.GL_LINE_STIPPLE)
            bgl.glDisable(bgl.GL_BLEND)
            bgl.glColor4f(0.0, 0.0, 0.0, 1.0)