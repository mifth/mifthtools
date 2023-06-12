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
# import bgl
# import blf
# import string

from bpy.props import *
from bpy.types import Operator, AddonPreferences

#from bpy_extras import view3d_utils

import math
import mathutils as mathu
#import random
#from mathutils import Vector, Matrix


class MI_OT_SM_Symmetry(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.sm_symmetry"
    bl_label = "MiraSymmetry"
    bl_description = "MiraSymmetry"
    bl_options = {'REGISTER', 'UNDO'}

    #taper_value: FloatProperty(default=0.0, min=-1000.0, max=1.0)

    sym_axis: EnumProperty(
        items=(('X', 'X', ''),
               ('Y', 'Y', ''),
               ('Z', 'Z', ''),
               ),
        default = 'X'
    )

    # deform_direction: EnumProperty(
        # items=(('Top', 'Top', ''),
               #('Bottom', 'Bottom', ''),
               #('Left', 'Left', ''),
               #('Right', 'Right', ''),
               #),
        # default = 'Top'
    #)


    def invoke(self, context, event):


        return self.execute(context)
        # else:
            # self.report({'WARNING'}, "View3D not found, cannot run operator")
            # return {'CANCELLED'}


    def execute(self, context):

        bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
        ref_obj = context.active_object
        verts_ref = [v for v in ref_obj.data.vertices if v.select]

        tmp_obj = bpy.data.objects.new("MIRA_TMP", ref_obj.data.copy())
        tmp_obj.matrix_world = ref_obj.matrix_world.copy()
        context.scene.collection.objects.link(tmp_obj)

        bpy.ops.object.select_all(action='DESELECT')

        context.view_layer.objects.active = tmp_obj
        tmp_obj.select_set(True)
        verts_tmp = [v for v in tmp_obj.data.vertices if v.select]

        if self.sym_axis == 'X':
            for v in verts_tmp:
                v.co[0] = -v.co[0]
        elif self.sym_axis == 'Y':
            for v in verts_tmp:
                v.co[1] = -v.co[1]
        elif self.sym_axis == 'Z':
            for v in verts_tmp:
                v.co[2] = -v.co[2]

        bpy.ops.object.modifier_add(type='SHRINKWRAP')
        tmp_obj.modifiers["Shrinkwrap"].wrap_method = 'NEAREST_VERTEX'
        bpy.context.object.modifiers["Shrinkwrap"].target = ref_obj
        bpy.ops.object.modifier_apply(modifier="Shrinkwrap")

        verts_tmp = [v for v in tmp_obj.data.vertices if v.select]  # get verts again with new positions

        for i,v in enumerate(verts_ref):
            v.co = verts_tmp[i].co

        if self.sym_axis == 'X':
            for v in verts_ref:
                v.co[0] = -v.co[0]
        elif self.sym_axis == 'Y':
            for v in verts_ref:
                v.co[1] = -v.co[1]
        elif self.sym_axis == 'Z':
            for v in verts_ref:
                v.co[2] = -v.co[2]

        bpy.ops.object.delete(use_global=False)

        context.view_layer.objects.active = ref_obj
        ref_obj.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT', toggle=False)

        return {'FINISHED'}




