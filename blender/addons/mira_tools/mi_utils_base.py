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


def get_obj_dup_meshes(objects_array, context):
    """Get all meshes"""

    listObjMatrix = []
    for obj in objects_array:
        if obj.type == 'MESH':
            listObjMatrix.append((obj, obj.matrix_world.copy()))

        if obj.dupli_type != 'NONE':
            obj.dupli_list_create(context.scene)
            for dob in obj.dupli_list:
                obj_dupli = dob.object
                if obj_dupli.type == 'MESH':
                    listObjMatrix.append((obj_dupli, dob.matrix.copy()))

        obj.dupli_list_clear()

    return listObjMatrix 


def get_mouse_raycast(context, objects_list, coords_2d, ray_max):
    region = context.region
    rv3d = context.region_data

    best_obj, hit_normal, hit_position = None, None, None
    best_length_squared = ray_max * ray_max

    for obj, matrix in objects_list:
        # get the ray from the viewport and mouse
        view_vector = view3d_utils.region_2d_to_vector_3d(
            region, rv3d, coords_2d)
        ray_origin = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, coords_2d)

        # Do RayCast! t1,t2,t3,t4 - temp values
        t1, t2, t3 = obj_ray_cast(obj, matrix, view_vector, ray_origin, ray_max)
        if t1 is not None and t3 < best_length_squared:
            best_obj, hit_normal, hit_position = obj, t1, t2
            best_length_squared = t3

    return best_obj, hit_normal, hit_position


def obj_ray_cast(obj, matrix, view_vector, ray_origin, ray_max):
    """Wrapper for ray casting that moves the ray into object space"""

    ray_target = ray_origin + (view_vector * ray_max)

    # get the ray relative to the object
    matrix_inv = matrix.inverted()
    ray_origin_obj = matrix_inv * ray_origin
    ray_target_obj = matrix_inv * ray_target

    # cast the ray
    hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_target_obj)

    if hit is not None:
        hit_world = matrix * hit

        length_squared = (hit_world - ray_origin).length_squared

        if face_index != -1:
            normal_world = matrix.to_quaternion() * normal
            return normal_world.normalized(), hit_world, length_squared

    return None, None, None