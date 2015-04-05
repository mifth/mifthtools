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
    def __init__(self, other_points):
        self.position = FloatVectorProperty()
        self.direction = FloatVectorProperty()
        self.up_direction = FloatVectorProperty()
        self.handle1 = None  # Vector
        self.handle2 = None  # Vector

        self.point_id = StringProperty(default="")

        other_points_ids = None
        if other_points:
            other_points_ids = get_points_ids(other_points)
        self.point_id = ut_base.generate_id(other_points_ids)

        self.select = False


class MI_CurveObject():

    # class constructor
    def __init__(self, other_curves):
        self.curve_points = []
        self.active_point = StringProperty(default="")
        self.display_bezier = {}  # display bezier curves dictionary

        self.curve_id = StringProperty(default="")

        other_curve_ids = None
        if other_curves:
            other_curve_ids = get_curves_ids(other_curves)
        self.curve_id = ut_base.generate_id(other_curve_ids)


def curve_point_changed(curve, point_numb, curve_resolution, display_bezier):
    # here we update 4 bezier areas
    len_cur = len(curve.curve_points)
    for i in range(6):
        new_i = (i - 2) + point_numb
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


def get_point_by_id(points, p_id):
    for point in points:
        if point.point_id == p_id:
            return point
    return None


def get_points_ids(points):
    other_ids = []
    for point in points:
        other_ids.append(point.point_id)

    return other_ids


def get_curves_ids(curves):
    other_ids = []
    for curve in curves:
        other_ids.append(curve.curve_id)

    return other_ids


def pick_curve_point(curve, context, mouse_coords):
    region = context.region
    rv3d = context.region_data

    picked_point = None
    picked_point_length = None
    for cu_point in curve.curve_points:
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)
        the_length = (point_pos_2d - Vector(mouse_coords)).length
        if the_length <= 9.0:
            if picked_point is None:
                picked_point = cu_point
                picked_point_length = the_length
            else:
                if the_length < picked_point_length:
                    picked_point = cu_point
                    picked_point_length = the_length                    

    return picked_point, the_length


def pick_all_curves_point(all_curves, context, mouse_coords):
    best_point = None
    best_length = None
    choosen_curve = None

    for curve in all_curves:
        pick_point, pick_length = pick_curve_point(curve, context, mouse_coords)

        if pick_point is not None:
            if best_point is None:
                choosen_curve = curve
                best_point = pick_point
                best_length = pick_length
            elif pick_length < best_length:
                choosen_curve = curve
                best_point = pick_point
                best_length = pick_length

    return best_point, best_length, choosen_curve


def select_point(curve, picked_point, additive_selection):
    if additive_selection is False:
        if picked_point.select is False:
            select_all_points(curve.curve_points, False)
        picked_point.select = True
    else:
        if picked_point.select:
            sel_points = get_selected_points(curve.curve_points)
            if len(sel_points) > 1:
                for point in sel_points:
                    if point.point_id != picked_point.point_id:
                        curve.active_point = point.point_id
                        break
                picked_point.select = False
        else:
            picked_point.select = True


def add_point(new_point_pos, curve):
    active_point = get_point_by_id(curve.curve_points, curve.active_point)
    point_index = curve.curve_points.index(active_point)

    # deselect points
    select_all_points(curve.curve_points, False)

    new_point = MI_CurvePoint(curve.curve_points)
    # add to 0 index
    if point_index == 0:
        curve.curve_points.insert(0, new_point)

    # add to last index
    elif point_index == len(curve.curve_points) - 1:
        curve.curve_points.append(new_point)

    # add to other indexes
    else:
        check_vec = (new_point_pos - active_point.position).normalized()
        point_1 = ((curve.curve_points[point_index + 1].position ) - active_point.position).normalized()
        p1_angle = point_1.angle(check_vec)
        point_2 = ((curve.curve_points[point_index - 1].position ) - active_point.position).normalized()
        p2_angle = point_2.angle(check_vec)

        if p1_angle < p2_angle:
            curve.curve_points.insert(point_index + 1, new_point)
        else:
            curve.curve_points.insert(point_index, new_point)

    new_point.position = new_point_pos
    new_point.select = True

    return new_point


def delete_point(point_to_delete, curve, display_bezier, curve_resolution):
    if point_to_delete.point_id in display_bezier:
        del display_bezier[point_to_delete.point_id]  # remove from dictionary

    curve.curve_points.remove(point_to_delete)  # remove from curve


def select_all_points(points, select_mode):
    for point in points:
        point.select = select_mode


def get_selected_points(points):
    sel_points = []
    for point in points:
        if point.select:
            sel_points.append(point)

    return sel_points


