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
import bmesh

from bpy.props import *
from bpy.types import Operator, AddonPreferences

import math
import mathutils as mathu
import random
from mathutils import Vector, Matrix


from . import mi_utils_base as ut_base

class MI_Wrap_Object(bpy.types.Operator):
    bl_idname = "mira.wrap_object"
    bl_label = "Wrap Object"
    bl_description = "Wrap Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wrap_obj = context.scene.objects.active
        #bm = bmesh.from_edit_mesh(wrap_obj.data)

        if wrap_obj and wrap_obj.select and wrap_obj.data.uv_layers:
            uvs = wrap_obj.data.uv_layers.active.data

            new_mesh = bpy.data.meshes.new(wrap_obj.data.name + '_Wrap')
            new_obj = bpy.data.objects.new(wrap_obj.name + '_Wrap', new_mesh)
            context.scene.objects.link(new_obj)

            new_obj.select = True
            context.scene.objects.active = new_obj
            bpy.ops.object.mode_set(mode='EDIT')

            bm = bmesh.from_edit_mesh(new_obj.data)

            for face in wrap_obj.data.polygons:
                verts_list = []
                #verts_idx_list = []

                for li in face.loop_indices:
                    uv = uvs[li].uv
                    new_vert = bm.verts.new((uv[0], 0.0, uv[1]))

                    verts_list.append(new_vert)
                    #verts_idx_list.append(new_vert.index)

                bm.faces.new(verts_list)
                #new_obj.data.update()

            #bmesh.update_edit_mesh(new_obj.data)
            bpy.ops.object.mode_set(mode='OBJECT')
            new_obj.data.update()

        return {'FINISHED'}


class MI_Wrap_Master(bpy.types.Operator):
    bl_idname = "mira.wrap_master"
    bl_label = "Wrap Master"
    bl_description = "Wrap Master"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_objects = context.selected_objects
        if len(selected_objects) >= 2:
            #wrap_obj = selected_objects[-1]
            uv_obj = context.scene.objects.active
            bvh = mathu.bvhtree.BVHTree.FromObject(uv_obj, context.scene, deform=True, render=False, cage=False, epsilon=0.0)

            for the_obj in selected_objects:
                if the_obj != uv_obj:
                    for vert in the_obj.data.vertices:
                        vert_pos = the_obj.matrix_world * vert.co.copy()
                        vert_pos[1] = 0  # set position of uv_obj!!!
                        nearest = bvh.find_nearest(vert_pos)
                        print(nearest)

        return {'FINISHED'}