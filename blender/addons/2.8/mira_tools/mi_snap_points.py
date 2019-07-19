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


class MI_OT_Unbevel(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.snap_points"
    bl_label = "Snap Points"
    bl_description = "Snap Points"
    bl_options = {'REGISTER', 'UNDO'}

    #reset_values: BoolProperty(default=False)
    #unbevel_value: bpy.props.FloatProperty(name="Snap Points", description="Snap Points", default=1000, min=0.0)

    def execute(self, context):

        #if self.reset_values is True:
            #self.reset_all_values()

        active_obj = context.active_object

        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.verts.ensure_lookup_table()
        sel_verts = [v for v in bm.verts if v.select]

        curve_settings = context.scene.mi_settings

        if curve_settings.snap_objects == 'Selected':
            objects_array = [obj for obj in context.selected_objects if obj != active_obj and obj.type == 'MESH']
        else:
            objects_array = [obj for obj in context.visible_objects if obj != active_obj and obj.type == 'MESH']

        # do snapping
        if sel_verts and objects_array:
            vert_pose_list = {}

            # get nearest positions
            for obj in objects_array:
                bvh = mathu.bvhtree.BVHTree.FromObject(obj, context.evaluated_depsgraph_get())

                for idx, vert in enumerate(sel_verts):
                    v_pos = obj.matrix_world.inverted() @ (active_obj.matrix_world @ vert.co)
                    nearest = bvh.find_nearest(v_pos)

                    if nearest and nearest[0]:
                        v_pos_near = active_obj.matrix_world.inverted() @ (obj.matrix_world @ nearest[0])

                        if vert in vert_pose_list.keys():
                            # if new near position is less
                            if (vert.co - vert_pose_list[vert]).length > (vert.co - v_pos_near).length:
                                vert_pose_list[vert] = v_pos_near
                        else:
                            vert_pose_list[vert] =  v_pos_near

            for vert in sel_verts:
                vert.co = vert_pose_list[vert]

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}
