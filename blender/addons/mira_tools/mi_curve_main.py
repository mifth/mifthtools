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

#class MI_CurvePoint(bpy.types.PropertyGroup):
    #position = FloatVectorProperty()
    #direction = FloatVectorProperty()
    #up_direction = FloatVectorProperty()
    #handle1 = FloatVectorProperty()
    #handle2 = FloatVectorProperty()
    #point_id = StringProperty(default="")


#class MI_CurveObject(bpy.types.PropertyGroup):
    #curve_points = CollectionProperty(
        #type=MI_CurvePoint
    #)
    #active_point = StringProperty(default="")


class MI_CurvePoint():

    # class constructor
    def __init__(self):
        self.position = FloatVectorProperty()
        self.direction = FloatVectorProperty()
        self.up_direction = FloatVectorProperty()
        self.handle1 = None  # Vector
        self.handle2 = None  # Vector
        self.point_id = StringProperty(default="")
        self.selected = BoolProperty(default=False)


class MI_CurveObject():

    # class constructor
    def __init__(self):
        self.curve_points = []
        self.active_point = StringProperty(default="")


def curve_point_changed(curve, point_numb, curve_resolution, display_bezier):
    # here we update 4 bezier areas
    len_cur = len(curve.curve_points)
    for i in range(4):
        new_i = (i - 1) + point_numb
        if new_i < len_cur and new_i > 0:
            new_b_points = generate_bezier_area(curve, new_i, curve_resolution)
            if new_b_points:
                display_bezier[curve.curve_points[new_i].point_id] = new_b_points


def generate_bezier_points(curve, display_bezier, curve_resolution):
    p_len = len(curve.curve_points)
    for i in range(p_len):
        if i > 0:
            if p_len == 2 and i == 1:
                b_points = generate_line_area(curve, i)
                display_bezier[curve.curve_points[1].point_id] = b_points
            else:
                b_points = generate_bezier_area(curve, i, curve_resolution)
                if b_points:
                    display_bezier[curve.curve_points[i].point_id] = b_points


def generate_line_area(curve, point_numb):
    return [curve.curve_points[point_numb-1].position, curve.curve_points[point_numb].position]


def generate_bezier_area(curve, point_numb, curve_resolution):
    p_len = len(curve.curve_points)
    if point_numb > 0:
        if p_len > 2 and curve_resolution > 1:
            back_point = point_numb-1

            two_back_point = None
            if point_numb-2 < 0:
                two_back_point = point_numb-1
            else:
                two_back_point = point_numb-2

            forward_point = None
            if point_numb+1 > p_len-1:
                forward_point = point_numb
            else:
                forward_point = point_numb+1

            knot1 = Vector(curve.curve_points[back_point].position)
            knot2 = Vector(curve.curve_points[point_numb].position)

            handle1 = None
            handle2 = None

            # Make common interpolation for handles
            if point_numb > 1:
                dist1 = (Vector(curve.curve_points[point_numb].position) - Vector(curve.curve_points[two_back_point].position))
                dl1 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[point_numb].position))
                dl1_2 = (Vector(curve.curve_points[two_back_point].position) - Vector(curve.curve_points[point_numb].position))

                handle1_len = ( dl1.length  ) * (dl1.length/(dl1.length+dl1_2.length))  # 1.1042 is smooth coefficient

                if dl1.length > dl1_2.length/1.5 and dl1.length != 0:
                    handle1_len *= ((dl1_2.length/1.5)/dl1.length)
                elif dl1.length < dl1_2.length/3.0 and dl1.length != 0:
                    handle1_len *= (dl1_2.length/3.0)/dl1.length

                # handle1_len = min(( dl1.length  ) * (dl1.length/(dl1.length+dl1_2.length)) ,dist1.length* h1_final*0.5)  # 1.1042 is smooth coefficient
                handle1 = knot1 + (dist1.normalized() * handle1_len)

            if point_numb < p_len-1:
                dist2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[forward_point].position))
                dl2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[point_numb].position))
                dl2_2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[forward_point].position))

                handle2_len = (dl2.length  ) * (dl2.length/(dl2.length+dl2_2.length)) # 1.1042 is smooth coefficient

                if dl2.length > dl2_2.length/1.5 and dl2.length != 0:
                    handle2_len *= ((dl2_2.length/1.5)/dl2.length)
                elif dl2.length < dl2_2.length/3.0 and dl2.length != 0:
                    handle2_len *= (dl2_2.length/3.0)/dl2.length

                # handle2_len = min((dl2.length  ) * (dl2.length/(dl2.length+dl2_2.length)), dist2.length* h2_final*0.5) # 1.1042 is smooth coefficient
                handle2 = knot2 + (dist2.normalized() * handle2_len)

            # Make end points
            if handle1 is None:
                handle1 = (handle2 - knot1)
                handle1_len = handle1.length * 0.4
                handle1 = knot1 + (handle1.normalized() * handle1_len)
            if handle2 is None:
                handle2 = (handle1 - knot2)
                handle2_len = handle2.length * 0.4
                handle2 = knot2 + (handle2.normalized() * handle2_len)

            curve.curve_points[point_numb-1].handle1 = handle1  # save handle
            curve.curve_points[point_numb].handle2 = handle2  # save handle

            # Display Bezier points
            # Get all the points on the curve between these two items.  Uses the default of 12 for a "preview" resolution
            # on the curve.  Note the +1 because the "preview resolution" tells how many segments to use.  ie. 2 => 2 segments
            # or 3 points.  The "interpolate_bezier" functions takes the number of points it should generate.
            vecs = mathu.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, curve_resolution+1)
            return vecs
        else:
            vecs = generate_line_area(curve, point_numb)
            return vecs

    return None

