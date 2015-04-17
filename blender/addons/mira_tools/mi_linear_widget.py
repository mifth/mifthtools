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


class MI_LW_Point():

    # class constructor
    def __init__(self, position):
        self.position = position


class MI_Linear_Widget():

    # class constructor
    def __init__(self):
        self.start_point = None
        self.middle_point = None
        self.end_point = None


def update_middle_point(lw_tool):
    lw_dir = (lw_tool.end_point.position - lw_tool.start_point.position)
    lw_len = (lw_dir).length
    lw_dir = lw_dir.normalized()

    lw_tool.middle_point.position = lw_tool.start_point.position + (lw_dir * (lw_len / 2.0))


def get_tool_verts(lw_tool, verts_ids, bm, obj):
    apply_tool_verts = []
    final_dir = ( lw_tool.end_point.position - lw_tool.start_point.position )
    max_dist = final_dir.length
    for vert_id in verts_ids:
        v_pos = obj.matrix_world * bm.verts[vert_id].co
        value = mathu.geometry.distance_point_to_plane(v_pos, lw_tool.start_point.position, final_dir)
        if value > 0:
            #if value > max_dist:
                #value = 1.0
            #else:
            value /= max_dist
            apply_tool_verts.append( (vert_id, value, bm.verts[vert_id].co.copy()) )

    return apply_tool_verts


def draw_lw(context, lw, cross_up_dir):
    region = context.region
    rv3d = context.region_data

    start_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.start_point.position)
    end_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.end_point.position)
    middle_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.middle_point.position)

    dist_ends = ((lw.start_point.position - lw.end_point.position).length * 0.1) * cross_up_dir
    end_p1 = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.end_point.position + dist_ends)
    end_p2 = view3d_utils.location_3d_to_region_2d(region, rv3d, lw.end_point.position - dist_ends)

    if start_2d and end_2d and end_p1 and end_p2:
        bgl.glEnable(bgl.GL_BLEND)
        bgl.glLineWidth(1)
        bgl.glPointSize(6)

        bgl.glBegin(bgl.GL_LINE_STRIP)
        bgl.glColor4f(0.95, 0.6, 0.25, 1.0)
        bgl.glVertex2f(start_2d[0], start_2d[1])
        bgl.glVertex2f(end_2d[0], end_2d[1])
        bgl.glEnd()

        bgl.glBegin(bgl.GL_LINE_LOOP)
        bgl.glColor4f(0.95, 0.6, 0.25, 1.0)
        bgl.glVertex2f(start_2d[0], start_2d[1])
        bgl.glVertex2f(end_p1[0], end_p1[1])
        bgl.glVertex2f(end_p2[0], end_p2[1])
        bgl.glEnd()

        bgl.glBegin(bgl.GL_POINTS)
     #   bgl.glBegin(bgl.GL_POLYGON)
        bgl.glColor4f(0.98, 0.8, 0.45, 1.0)
        bgl.glVertex2f(start_2d[0], start_2d[1])
        bgl.glVertex2f(middle_2d[0], middle_2d[1])
        bgl.glVertex2f(end_2d[0], end_2d[1])
        bgl.glEnd()

        # restore opengl defaults
        bgl.glLineWidth(1)
        bgl.glDisable(bgl.GL_BLEND)
        bgl.glColor4f(0.0, 0.0, 0.0, 1.0)