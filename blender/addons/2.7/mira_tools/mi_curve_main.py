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


class MI_CurveObject(object):

    # class constructor
    def __init__(self, other_curves):
        self.curve_points = []
        self.active_point = None  # string
        self.display_bezier = {}  # display bezier curves dictionary

        self.curve_id = None  # string

        other_curve_ids = None
        if other_curves:
            other_curve_ids = get_curves_ids(other_curves)
        self.curve_id = ut_base.generate_id(other_curve_ids)

        self.closed = False


class MI_CurvePoint():

    # class constructor
    def __init__(self, other_points):
        self.position = FloatVectorProperty()
        self.direction = FloatVectorProperty()
        self.up_direction = FloatVectorProperty()
        self.handle1 = None  # Vector
        self.handle2 = None  # Vector

        self.point_id = None  # string

        other_points_ids = None
        if other_points:
            other_points_ids = get_points_ids(other_points)
        self.point_id = ut_base.generate_id(other_points_ids)

        self.select = False


def curve_point_changed(curve, point_numb, curve_resolution, display_bezier):
    # here we update 6 bezier areas
    len_cur = len(curve.curve_points)
    for i in range(6):
        new_i = (i - 2) + point_numb
        if new_i > len_cur-1 or new_i < 0:
            if curve.closed is False:
                continue
            else:
                new_i = new_i - len_cur
                if new_i > len_cur-1 or new_i < -(len_cur-1):
                    continue  # if out of the list

        new_b_points = generate_bezier_area(curve, new_i, curve_resolution)
        if new_b_points:
            display_bezier[curve.curve_points[new_i].point_id] = new_b_points


def generate_bezier_points(curve, display_bezier, curve_resolution):
    p_len = len(curve.curve_points)

    if p_len == 2:
        b_points = generate_line_area(curve, 1)
        display_bezier[curve.curve_points[1].point_id] = b_points

    elif p_len > 2:
        for i in range(p_len):
            # main generator
            b_points = generate_bezier_area(curve, i, curve_resolution)
            if b_points:
                display_bezier[curve.curve_points[i].point_id] = b_points


def generate_line_area(curve, point_numb):
    if point_numb == 0 and curve.closed is False:
        return None  # return None for closed curve at 0 index
    else:
        return [curve.curve_points[point_numb-1].position, curve.curve_points[point_numb].position]


def generate_bezier_area(curve, point_numb, curve_resolution):
    p_len = len(curve.curve_points)
    bezier_vecs = None

    if point_numb == 0 and curve.closed is False:
        return bezier_vecs  # return None for closed curve at 0 index

    elif p_len > 2 and curve_resolution > 1:
        back_point = point_numb-1

        two_back_point = None
        if point_numb-2 < 0 and curve.closed is False:
            two_back_point = point_numb-1
        else:
            two_back_point = point_numb-2

        forward_point = None
        if point_numb+1 > p_len-1:
            if curve.closed is False:
                forward_point = point_numb
            else:
                forward_point = point_numb+1 - p_len  # last index of points. For closed curves only
        else:
            forward_point = point_numb+1

        knot1 = Vector(curve.curve_points[back_point].position)
        knot2 = Vector(curve.curve_points[point_numb].position)

        handle1 = None
        handle2 = None

        # Make common interpolation for handles
        if point_numb > 1 or curve.closed is True:
            dist1 = (Vector(curve.curve_points[point_numb].position) - Vector(curve.curve_points[two_back_point].position))
            dl1 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[point_numb].position))
            dl1_2 = (Vector(curve.curve_points[two_back_point].position) - Vector(curve.curve_points[point_numb].position))

            handle1_len = ( dl1.length  ) * (dl1.length/(dl1.length+dl1_2.length))

            if dl1.length > dl1_2.length/1.5 and dl1.length != 0:
                handle1_len *= ((dl1_2.length/1.5)/dl1.length)
            elif dl1.length < dl1_2.length/3.0 and dl1.length != 0:
                handle1_len *= (dl1_2.length/3.0)/dl1.length

            # handle1_len = min(( dl1.length  ) * (dl1.length/(dl1.length+dl1_2.length)) ,dist1.length* h1_final*0.5) 
            handle1 = knot1 + (dist1.normalized() * handle1_len)

        if point_numb < p_len-1 or curve.closed is True:
            dist2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[forward_point].position))
            dl2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[point_numb].position))
            dl2_2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[forward_point].position))

            handle2_len = (dl2.length  ) * (dl2.length/(dl2.length+dl2_2.length)) 

            if dl2.length > dl2_2.length/1.5 and dl2.length != 0:
                handle2_len *= ((dl2_2.length/1.5)/dl2.length)
            elif dl2.length < dl2_2.length/3.0 and dl2.length != 0:
                handle2_len *= (dl2_2.length/3.0)/dl2.length

            # handle2_len = min((dl2.length  ) * (dl2.length/(dl2.length+dl2_2.length)), dist2.length* h2_final*0.5)
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

        curve.curve_points[back_point].handle1 = handle1  # save handle
        curve.curve_points[point_numb].handle2 = handle2  # save handle

        # Display Bezier points
        # Get all the points on the curve between these two items.  Uses the default of 12 for a "preview" resolution
        # on the curve.  Note the +1 because the "preview resolution" tells how many segments to use.  ie. 2 => 2 segments
        # or 3 points.  The "interpolate_bezier" functions takes the number of points it should generate.
        bezier_vecs = mathu.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, curve_resolution+1)
    else:
        bezier_vecs = generate_line_area(curve, point_numb)

    return bezier_vecs


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
    mouse_vec = Vector(mouse_coords)
    for cu_point in curve.curve_points:
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)
        the_length = (point_pos_2d - mouse_vec).length
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

def pick_curve_point_radius(curve, context, mouse_coords, radius):
    region = context.region
    rv3d = context.region_data

    picked_point = None
    picked_point_length = None
    mouse_vec = Vector(mouse_coords)
    for cu_point in curve.curve_points:
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)
        the_length = (point_pos_2d - mouse_vec).length
        if the_length <= radius:
            if picked_point is None:
                picked_point = cu_point
                picked_point_length = the_length
            else:
                if the_length < picked_point_length:
                    picked_point = cu_point
                    picked_point_length = the_length

    return picked_point, the_length

def pick_all_curves_points_radius(all_curves, context, mouse_coords, radius):
    best_points = []
    best_lengths = []
    choosen_curves = []

    for curve in all_curves:
        pick_point, pick_length = pick_curve_point_radius(curve, context, mouse_coords, radius)

        if pick_point is not None:
            choosen_curves.append(curve)
            best_points.append(pick_point)
            best_lengths.append(pick_length)

    return best_points, best_lengths, choosen_curves

def pick_curve_points_box(curve, context, mouse_coords, anchor):
    region = context.region
    rv3d = context.region_data

    picked_points = []
    picked_point_length = None
    mouse_vec = Vector(mouse_coords)
    for cu_point in curve.curve_points:
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)
        minx = min(anchor[0],mouse_coords[0])
        miny = min(anchor[1],mouse_coords[1])
        maxx = max(anchor[0], mouse_coords[0])
        maxy = max(anchor[1], mouse_coords[1])

        if point_pos_2d[0] > minx and point_pos_2d[0] < maxx and point_pos_2d[1] < maxy and point_pos_2d[1] > miny:
           picked_points.append(cu_point)
           picked_point_length = 0
        elif cu_point in picked_points:
            picked_points.remove(cu_point)

    return picked_points

def pick_all_curves_points_box(all_curves, context, mouse_coords, anchor):
    best_points = []
    best_lengths = []
    choosen_curves = []

    for curve in all_curves:
        pick_points = pick_curve_points_box(curve, context, mouse_coords, anchor)

        if pick_points is not None:
            choosen_curves.append(curve)
            best_points.extend(pick_points)
            best_lengths.append(0)

    return best_points, choosen_curves

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

def select_point_multi(all_curves, points, add = True):
    if len(points)>0:
        for point in points:
            point.select = add

        for curve in all_curves:
            sel_points = get_selected_points(curve.curve_points)
            if add:
                if len(sel_points) > 0:
                    curve.active_point = sel_points[-1].point_id

            else:
                if len(sel_points) > 0:
                    curve.active_point = sel_points[-1].point_id
                else:
                    curve.active_point = None


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


def deselect_all_curves(all_curves, reset_acive_point):
    for curve in all_curves:
        select_all_points(curve.curve_points, False)  # deselect points
        if reset_acive_point is True:
            curve.active_point = None


# CODE FOR LOOPS
def pass_line(vecs, is_closed_line):
    line_length = 0.0
    line_data = []
    vecs_len = len(vecs)

    for i, vec in enumerate(vecs):
        #if i == vecs_len - 1 and is_closed_line is False:
            #line_data.append((vec, line_length, 0.0, None))
        #else:
        vec_area = None
        if i == vecs_len - 1:
            if is_closed_line:
                vec_area = vecs[0] - vec
            else:
                vec_area = Vector( (0.0, 0.0, 0.0) )
        else:
            vec_area = vecs[i+1] - vec

        area_length = vec_area.length

        vec_dir = None
        if i == vecs_len - 1:
            vec_dir = (vec - vecs[i-1]).normalized()
        else:
            vec_dir = vec_area.normalized()

        line_data.append((vec.copy(), line_length, area_length, vec_dir))

        line_length += area_length

    # last point line of closed curve
    if is_closed_line:
        vec_area = vecs[0] - vecs[-1]
        area_length = vec_area.length
        vec_dir = vec_area.normalized()
        line_data.append((vecs[0], line_length, 0.0, None))

    return line_data


# CODE FOR LOOPS
def get_bezier_line(curve, active_obj, local_coords):
    curve_vecs = []
    for point in curve.curve_points:
        # 0 point has b_points in only closed curve
        if curve.curve_points.index(point) == 0 and curve.closed is True:
            continue  # only for closed curve

        b_points = curve.display_bezier.get(point.point_id)
        if b_points:
            # get lengths
            b_point_len =  len(b_points)
            curve_points_len = len(curve.curve_points)
            #b_points = b_points.copy()

            for b_p in b_points:
                # if b_p is not the last in the point. But if b_p is the last in the end of the curve.
                if b_points.index(b_p) != b_point_len - 1 or curve.curve_points.index(point) == curve_points_len - 1:
                    if local_coords is True:
                        curve_vecs.append(active_obj.matrix_world.inverted() * b_p)
                    else:
                        curve_vecs.append(b_p)

    # only for closed curve to apply last bezier points
    if curve.closed is True:
        b_points = curve.display_bezier.get(curve.curve_points[0].point_id)
        if b_points:
            #b_points = b_points.copy()

            for b_p in b_points:
                if b_points.index(b_p) != 0:
                    if local_coords is True:
                        curve_vecs.append(active_obj.matrix_world.inverted() * b_p)
                    else:
                        curve_vecs.append(b_p)

    line = pass_line(curve_vecs, curve.closed)
    return line


# CODE FOR LOOPS
def create_curve_to_line(points_number, line_data, all_curves, is_closed_line):
    curve = MI_CurveObject(all_curves)
    line_len = line_data[-1][1]

    point_passed = 0
    for i in range(points_number):
        if i == 0:
            curve_point = MI_CurvePoint(curve.curve_points)
            curve_point.position = line_data[0][0].copy()
            curve.curve_points.append(curve_point)
            continue
        elif i == points_number - 1 and is_closed_line is False:
            curve_point = MI_CurvePoint(curve.curve_points)
            curve_point.position = line_data[-1][0].copy()
            curve.curve_points.append(curve_point)
            continue
            break

        if is_closed_line:
            point_len = ((line_len/ (points_number)) * (i))
        else:
            point_len = (line_len/ (points_number - 1)) * (i)

        for point_data in line_data[point_passed:]:
            j = line_data.index(point_data)
            if line_data[j+1][1] >= point_len:
                curve_point = MI_CurvePoint(curve.curve_points)
                curve_point.position = line_data[j][0] + (line_data[j][3] * (point_len - line_data[j][1]))
                curve.curve_points.append(curve_point)
                point_passed = j
                break

    return curve


# CODE FOR LOOPS
def verts_to_line(verts, line_data, verts_data, is_closed_line):
    line_len = line_data[-1][1]

    verts_number = len(verts)
    if is_closed_line:
        verts_number += 1  # only for uniform interpolation

    point_passed = 0
    for i, vert in enumerate(verts):
        if i == 0:
            vert.co = line_data[0][0].copy()
            continue
        elif i == verts_number - 1 and is_closed_line is False:
            vert.co = line_data[-1][0].copy()
            break

        point_len = None
        if verts_data:
            #if is_closed_line is False:
            point_len = (verts_data[i][1]/ verts_data[-1][1] ) * line_len
            #else:
                #point_len = ((verts_data[i][1]/ (verts_data[-1][1] + verts_data[-2][2]) ) * (line_len) )
        else:
            point_len = (line_len/ (verts_number - 1)) * (i)
        for point_data in line_data[point_passed:]:
            j = line_data.index(point_data)
            if line_data[j+1][1] >= point_len:
                vert.co = line_data[j][0] + (line_data[j][3] * (point_len - line_data[j][1]))
                point_passed = j
                break


# SURFACE SNAP FOR CURVE POINTS
def snap_to_surface(context, selected_points, picked_meshes, region, rv3d, move_offset):
    for point in selected_points:
        # get the ray from the viewport and mouse
        final_pos = point.position
        if move_offset:
            final_pos = point.position + move_offset
        
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, final_pos)

        if point_pos_2d:
            best_obj, hit_normal, hit_position = ut_base.get_mouse_raycast(context, picked_meshes, point_pos_2d)
            #best_obj, hit_normal, hit_position = ut_base.get_3dpoint_raycast(context, self.picked_meshes, final_pos, camera_dir, 10000.0)
        if hit_position:
            point.position = hit_position