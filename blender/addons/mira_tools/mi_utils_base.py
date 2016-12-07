import bpy
import bmesh
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


def get_obj_dup_meshes(obj_snap_mode, convert_instances, context):
    """Get all meshes"""

    objects_array = None
    active_obj = context.scene.objects.active
    if obj_snap_mode == 'Selected':
        objects_array = [obj for obj in context.selected_objects if obj != active_obj]
    else:
        objects_array = [obj for obj in context.visible_objects if obj != active_obj]

    listObjMatrix = []
    for obj in objects_array:
        if obj.type == 'MESH':
            listObjMatrix.append((obj, obj.matrix_world.copy()))

        if obj.dupli_type != 'NONE' and convert_instances is True:
            obj.dupli_list_create(context.scene)
            for dob in obj.dupli_list:
                obj_dupli = dob.object
                if obj_dupli.type == 'MESH':
                    listObjMatrix.append((obj_dupli, dob.matrix.copy()))

        obj.dupli_list_clear()

    return listObjMatrix


# mesh picking from screen
def get_mouse_raycast(context, objects_list, coords_2d, ray_max=10000.0):
    region = context.region
    rv3d = context.region_data

    best_obj, hit_normal, hit_position = None, None, None
    best_length_squared = 20000.0 * 20000.0

    # get the ray from the viewport and mouse
    view_vector = view3d_utils.region_2d_to_vector_3d(
        region, rv3d, coords_2d)
    ray_origin = view3d_utils.region_2d_to_origin_3d(
        region, rv3d, coords_2d)

    for obj, matrix in objects_list:
        # Do RayCast! t1,t2,t3,t4 - temp values
        t1, t2, t3 = obj_raycast(
            obj, matrix, view_vector, ray_origin, ray_max)
        if t1 is not None and t3 < best_length_squared:
            best_obj, hit_normal, hit_position = obj, t1, t2
            best_length_squared = t3

    return best_obj, hit_normal, hit_position


# mesh picking from 3d space
def get_3dpoint_raycast(context, objects_list, vec_pos, vec_dir, ray_max=10000.0):
    best_obj, hit_normal, hit_position = None, None, None
    best_length_squared = 20000.0 * 20000.0

    for obj, matrix in objects_list:
        # Do RayCast! t1,t2,t3,t4 - temp values
        t1, t2, t3 = obj_raycast(
            obj, matrix, vec_dir, vec_pos, ray_max)
        if t1 is not None and t3 < best_length_squared:
            best_obj, hit_normal, hit_position = obj, t1, t2
            best_length_squared = t3

    return best_obj, hit_normal, hit_position


# mesh picking
def obj_raycast(obj, matrix, view_vector, ray_origin, ray_max=10000.0):
    """Wrapper for ray casting that moves the ray into object space"""

    # get the ray relative to the object
    matrix_inv = matrix.inverted()
    ray_target = ray_origin + (view_vector * ray_max)

    ray_origin_obj = matrix_inv * ray_origin
    ray_target_obj = matrix_inv * ray_target
    ray_direction_obj = ray_target_obj - ray_origin_obj
    #ray_target_obj = matrix_inv * ray_target

    # cast the ray
    hit_result, hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj, ray_max)

    if hit_result:
        hit_world = matrix * hit

        length_squared = (hit_world - ray_origin).length_squared

        if face_index != -1:
            #normal_world = (matrix.to_quaternion() * normal).normalized()
            normal_world = get_normal_world(normal, matrix, matrix_inv)

            return normal_world, hit_world, length_squared

    return None, None, None


# get normal world
def get_normal_world(normal, matrix, matrix_inv):
    normal_world = (matrix.to_quaternion() * normal).to_4d()
    normal_world.w = 0
    normal_world = (matrix.to_quaternion() * (matrix_inv * normal_world).to_3d()).normalized()

    return normal_world


# get mouse on a plane
def get_mouse_on_plane(context, plane_pos, plane_dir, mouse_coords):
    region = context.region
    rv3d = context.region_data

    final_dir = plane_dir
    if plane_dir is None:
        final_dir = rv3d.view_rotation * Vector((0.0, 0.0, -1.0))

    mouse_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_coords)
    mouse_dir = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_coords)
    new_pos = mathu.geometry.intersect_line_plane(
        mouse_pos, mouse_pos + (mouse_dir * 10000.0), plane_pos, final_dir, False)
    if new_pos:
        return new_pos

    return None


# get object local axys
def get_obj_axis(obj, axis):
    ax = 0
    if axis == 'Y' or axis == '-Y':
        ax = 1
    if axis == 'Z' or axis == '-Z':
        ax = 2

    obj_matrix = obj.matrix_world
    axis_tuple = (
        obj_matrix[0][ax], obj_matrix[1][ax], obj_matrix[2][ax])
    axisResult = Vector(axis_tuple).normalized()

    if axis == '-X' or axis == '-Y' or axis == '-Z':
        axisResult.negate()

    return axisResult


def generate_id(other_ids):
    # Generate unique id
    while True:
        uniq_numb = None
        uniq_id_temp = ''.join(random.choice(string.ascii_uppercase + string.digits)
                               for _ in range(10))

        if other_ids:
            if uniq_id_temp not in other_ids:
                uniq_numb = uniq_id_temp
                break
        else:
            uniq_numb = uniq_id_temp
            break

    return uniq_numb


## CODE FOR SELECTED BMESH ---
#def get_selected_bmesh(bm):
    #sel_verts = get_selected_bmverts(bm)
    #sel_edges = [e for e in bm.edges if e.select]
    #sel_faces = [f for f in bm.faces if f.select]

    #return [sel_verts, sel_edges, sel_faces]


def get_selected_bmverts(bm):
    sel_verts = [v for v in bm.verts if v.select]
    return sel_verts


def get_selected_bmverts_ids(bm):
    sel_verts = [v.index for v in bm.verts if v.select]
    return sel_verts


def get_bmverts_from_ids(bm, ids):
    verts = []
    bm.verts.ensure_lookup_table()
    for v_id in ids:
        verts.append(bm.verts[v_id])

    return verts


def get_vertices_center(verts, obj, local_space):

    vert_world_first = verts[0].co
    if not local_space:
        vert_world_first = obj.matrix_world * verts[0].co

    x_min = vert_world_first.x
    x_max = vert_world_first.x
    y_min = vert_world_first.y
    y_max = vert_world_first.y
    z_min = vert_world_first.z
    z_max = vert_world_first.z

    for vert in verts:
        vert_world = vert.co
        if not local_space:
            vert_world = obj.matrix_world * vert.co

        if vert_world.x > x_max:
            x_max = vert_world.x
        if vert_world.x < x_min:
            x_min = vert_world.x
        if vert_world.y > y_max:
            y_max = vert_world.y
        if vert_world.y < y_min:
            y_min = vert_world.y
        if vert_world.z > z_max:
            z_max = vert_world.z
        if vert_world.z < z_min:
            z_min = vert_world.z

    x_orig = ((x_max - x_min) / 2.0) + x_min
    y_orig = ((y_max - y_min) / 2.0) + y_min
    z_orig = ((z_max - z_min) / 2.0) + z_min

    return Vector((x_orig, y_orig, z_orig))


def get_verts_bounds(verts, obj, x_axis, y_axis, z_axis, local_space):

    center = get_vertices_center(verts, obj, local_space)

    x_min = 0.0
    x_max = 0.0
    y_min = 0.0
    y_max = 0.0
    z_min = 0.0
    z_max = 0.0

    for vert in verts:
        vert_world = vert.co
        if not local_space:
            vert_world = obj.matrix_world * vert.co

        if x_axis:
            x_check = mathu.geometry.distance_point_to_plane(vert_world, center, x_axis)
            if x_check > x_max:
                x_max = x_check
            elif x_check < x_min:
                x_min = x_check

        if y_axis:
            y_check = mathu.geometry.distance_point_to_plane(vert_world, center, y_axis)
            if y_check > y_max:
                y_max = y_check
            elif y_check < y_min:
                y_min = y_check

        if z_axis:
            z_check = mathu.geometry.distance_point_to_plane(vert_world, center, z_axis)
            if z_check > z_max:
                z_max = z_check
            elif z_check < z_min:
                z_min = z_check

    return ( x_max + abs(x_min), y_max + abs(y_min), z_max + abs(z_min), center )


def get_vertices_size(verts, obj):
    # if obj.mode == 'EDIT':
        # bm.verts.ensure_lookup_table()
    vert_world_first = obj.matrix_world * verts[0].co
    # multiply_scale(vert_world_first, obj.scale)

    x_min = vert_world_first.x
    x_max = vert_world_first.x
    y_min = vert_world_first.y
    y_max = vert_world_first.y
    z_min = vert_world_first.z
    z_max = vert_world_first.z

    for vert in verts:
        vert_world = obj.matrix_world * vert.co
        # multiply_scale(vert_world, obj.scale)

        if vert_world.x > x_max:
            x_max = vert_world.x
        if vert_world.x < x_min:
            x_min = vert_world.x
        if vert_world.y > y_max:
            y_max = vert_world.y
        if vert_world.y < y_min:
            y_min = vert_world.y
        if vert_world.z > z_max:
            z_max = vert_world.z
        if vert_world.z < z_min:
            z_min = vert_world.z

    x_size = (x_max - x_min)
    y_size = (y_max - y_min)
    z_size = (z_max - z_min)

    final_size = x_size
    if final_size < y_size:
        final_size = y_size
    if final_size < z_size:
        final_size = z_size

    return final_size


# VECTOR OPERATIONS
def multiply_local_vecs(vec1, vec2):
    vec1[0] *= vec2[0]
    vec1[1] *= vec2[1]
    vec1[2] *= vec2[2]

def multiply_vecs(vec1, vec2):
    vec3 = Vector( (0.0, 0.0, 0.0) )
    vec3[0] = vec1[0] * vec2[0]
    vec3[1] = vec1[1] * vec2[1]
    vec3[2] = vec1[2] * vec2[2]
    return vec3


# get verts by custom bmesh layer(integer)
def get_verts_from_ids(ids, id_layer, bm):
    verts_dict = {}
    verts_sorted = []

    for vert in bm.verts:
        if vert[id_layer] in ids:
            #print(vert[id_layer])
            verts_dict[vert[id_layer]] = vert

    for id_this in ids:
        if id_this in verts_dict.keys():
            verts_sorted.append(verts_dict.get(id_this))

    if len(verts_sorted) == len(ids):
        return verts_sorted

    return None
