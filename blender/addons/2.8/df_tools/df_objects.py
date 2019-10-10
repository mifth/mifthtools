import bpy
import bmesh

from bpy.props import *
from bpy.types import Operator

import math
import mathutils as mathu
from mathutils import Vector, Matrix

class DFCopyOBJ(bpy.types.Operator):
    bl_idname = "df.copy_obj"
    bl_label = "Clone Objects to Verts"
    bl_description = "Clone Objects to Verts"
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):

        get_obj = context.active_object
        if context.selected_objects[0] is get_obj:
            copy_obj = context.selected_objects[1]
        else:
            copy_obj = context.selected_objects[0]

        bm = bmesh.from_edit_mesh(get_obj.data)
        bm.verts.ensure_lookup_table()

        v_indexes = []
        if isinstance(bm.select_history[0], bmesh.types.BMVert):
            for element in bm.select_history:
                v_indexes.append(element.index)

        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')

        for idx in range(int(len(v_indexes) / 3)):

            true_idx = idx * 3

            v1 = get_obj.matrix_world @ get_obj.data.vertices[v_indexes[true_idx]].co.copy()
            v2 = get_obj.matrix_world @ get_obj.data.vertices[v_indexes[true_idx + 1]].co.copy()
            v3 = get_obj.matrix_world @ get_obj.data.vertices[v_indexes[true_idx + 2]].co.copy()

            dir1 = (v1 - v2).normalized()
            dir2 = dir1.cross(((v3 - v2).normalized())).normalized()
            dir2.negate()
            dir3 = dir1.cross(dir2).normalized()

            # clone obj
            copy_obj.select_set(True)
            bpy.ops.object.duplicate(linked=True)
            new_obj =  context.selected_objects[0]

            new_mat = mathu.Matrix().to_3x3()
            new_mat[0][0], new_mat[1][0], new_mat[2][0] = dir1[0], dir1[1], dir1[2]
            new_mat[0][1], new_mat[1][1], new_mat[2][1] = dir2[0], dir2[1], dir2[2]
            new_mat[0][2], new_mat[1][2], new_mat[2][2] = dir3[0], dir3[1], dir3[2]
            #new_mat = new_mat.normalized()

            new_obj.matrix_world = new_mat.to_4x4()
            new_obj.location = v2.copy()
            new_obj.scale = copy_obj.scale.copy()

            bpy.ops.object.select_all(action='DESELECT')

        return {'FINISHED'}
