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
import math
from math import *
import mathutils as mathu

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from . import mi_utils_base as ut_base
from . import mi_looptools as loop_t
from mathutils import Vector, Matrix


## Settings
#class MI_Unbevel_Settings(bpy.types.PropertyGroup):
    #unbevel_value: bpy.props.FloatProperty(name="Unbevel Value", description="Unbevel Value", default=(1.0), hard_min=0)


class MI_OT_Unbevel(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.unbevel"
    bl_label = "Unbevel"
    bl_description = "Unbevel"
    bl_options = {'REGISTER', 'UNDO'}

    reset_values: BoolProperty(default=False)
    unbevel_value: bpy.props.FloatProperty(name="Unbevel Value", description="Unbevel Value", default=1.0, min=0.0)
    #rotate_arc_axis: bpy.props.FloatProperty(name="Rotate", description="Rotate Arc Axis", default=0)


    def reset_all_values(self):
        self.unbevel_value = 1
        self.reset_values = False

    def execute(self, context):

        if self.reset_values is True:
            self.reset_all_values()

        active_obj = context.active_object

        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.verts.ensure_lookup_table()
        #verts = [v for v in bm.verts if v.select]

        # get loops
        loops = loop_t.get_connected_input(bm)
        loops = loop_t.check_loops(loops, bm)

        if not loops:
            self.report({'WARNING'}, "No Loops!")
            return {'CANCELLED'}

        #obj_matrix = active_obj.matrix_world
        #obj_matrix_inv = obj_matrix.inverted()

        if self.unbevel_value != 1:

            for loop in loops:
                if loop[1] is True:
                    continue

                loop_verts = []

                for ind in loop[0]:
                    loop_verts.append(bm.verts[ind])

                v1 = (loop_verts[1].co - loop_verts[0].co).normalized()
                v2 = (loop_verts[2].co - loop_verts[1].co).normalized()
                angle_1 = v1.angle(v2) / 2

                v3 = (loop_verts[-2].co - loop_verts[-1].co).normalized()
                v4 = (loop_verts[-3].co - loop_verts[-2].co).normalized()
                angle_2 = v1.angle(v2) / 2
                degree_90 = 1.5708

                rot_dir = v1.cross(v2).normalized()
                rot_mat = Matrix.Rotation(-angle_1, 3, rot_dir)
                rot_mat_2 = Matrix.Rotation((angle_2 - degree_90), 3, rot_dir)
                v1_nor = ((rot_mat @ v1).normalized() * 10000) + loop_verts[0].co
                v3_nor = (rot_mat_2 @ v3).normalized()

                scale_pos = mathu.geometry.intersect_line_plane(loop_verts[0].co, v1_nor, loop_verts[-1].co, v3_nor)

                for vert in loop_verts:
                    vert.co = scale_pos.lerp(vert.co, self.unbevel_value)

            if self.unbevel_value == 0:
                bpy.ops.mesh.merge(type='COLLAPSE')

            bm.normal_update()
            bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}
