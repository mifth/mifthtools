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
        active_obj = context.scene.objects.active
        #bm = bmesh.from_edit_mesh(active_obj.data)

        if active_obj and active_obj.select and active_obj.data.uv_layers:
            uvs = active_obj.data.uv_layers.active.data

            new_mesh = bpy.data.meshes.new(active_obj.data.name + 'wrap')
            new_obj = bpy.data.objects.new(active_obj.name + 'wrap', new_mesh)
            context.scene.objects.link(new_obj)
            #new_obj.select = True
            #context.scene.objects.active = new_obj
            #bpy.ops.object.mode_set(mode='EDIT')

            for face in active_obj.data.polygons:
                verts_list = []
                verts_idx_list = []

                for li in face.loop_indices:
                    uv = uvs[li].uv
                    new_mesh.vertices.add(1)
                    new_vert = new_mesh.vertices[-1]
                    new_vert.co = (uv[0], 0.0, uv[1])

                    verts_list.append(new_vert)
                    verts_idx_list.append(new_vert.index)

                new_obj.data.polygons.add(1)
                new_face = new_obj.data.polygons[-1]
                new_face.vertices = verts_idx_list
                #new_obj.data.update()

            new_obj.data.update()

        return {'FINISHED'}