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
from mathutils import Vector, Matrix

from . import mi_utils_base as ut_base


class MI_Simple_Extrude(bpy.types.Operator):
    """Extrude like in Modo"""
    bl_idname = "mira.simple_exrude"
    bl_label = "Simple Extrude"
    bl_description = "Simple Extrude"
    bl_options = {'REGISTER', 'UNDO'}


    first_mouse_x = None
    center = None
    depth = 0
    thickness = 0
    move_size = None

    tool_mode = 'IDLE'  # IDLE, EXTRUDE, INSET


    def invoke(self, context, event):
        clean(self)

        if context.mode == 'EDIT_MESH':
            bpy.ops.ed.undo_push()

            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)

            self.first_mouse_x = event.mouse_x

            #bpy.ops.view3d.snap_cursor_to_selected()
            sel_faces = [f for f in bm.faces if f.select]
            self.center = sel_faces[0].calc_center_median()
            context.scene.cursor_location = self.center

            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}

        else:
            self.report({'WARNING'}, "Go to Edit Mode!")
            return {'CANCELLED'}


    def modal(self, context, event):
        active_obj = context.scene.objects.active
        m_coords = event.mouse_region_x, event.mouse_region_y

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}

        # DELTA CALCULATION
        if self.tool_mode == 'EXTRUDE':
            delta = ((self.first_mouse_x - event.mouse_x) * self.move_size) + self.depth
        elif self.tool_mode == 'INSET':
            delta = ((self.first_mouse_x - event.mouse_x) * self.move_size) + self.thickness

        # EXTRUDE
        if event.type == 'E' and event.value == 'PRESS':
            if self.tool_mode == 'IDLE':
                self.move_size = calc_move_size(self, context)

                self.first_mouse_x = event.mouse_x
                self.tool_mode = 'EXTRUDE'

            elif self.tool_mode == 'EXTRUDE':
                self.depth = delta

                bm = bmesh.from_edit_mesh(active_obj.data)
                sel_faces = [f for f in bm.faces if f.select]
                self.center = sel_faces[0].calc_center_median()
                context.scene.cursor_location = self.center

                self.tool_mode = 'IDLE'

            return {'RUNNING_MODAL'}

        # INSET
        elif event.type == 'W' and event.value == 'PRESS':
            if self.tool_mode == 'IDLE':
                self.move_size = calc_move_size(self, context)

                self.first_mouse_x = event.mouse_x
                self.tool_mode = 'INSET'

            elif self.tool_mode == 'INSET':
                self.thickness = max(delta, 0)
                
                bm = bmesh.from_edit_mesh(active_obj.data)
                sel_faces = [f for f in bm.faces if f.select]
                self.center = sel_faces[0].calc_center_median()
                context.scene.cursor_location = self.center

                self.tool_mode = 'IDLE'

            return {'RUNNING_MODAL'}

        # TOOL WORK
        if self.tool_mode != 'IDLE':
            if event.type == 'MOUSEMOVE':
                bpy.ops.ed.undo()

                if self.tool_mode == 'EXTRUDE':
                    bpy.ops.mesh.inset(depth=delta, thickness=self.thickness)
                else:
                    bpy.ops.mesh.inset(depth=self.depth, thickness=delta)

                bpy.ops.ed.undo_push()

        if event.type in {'LEFTMOUSE', 'ESC'}:
            return {'FINISHED'}

        return {'RUNNING_MODAL'}


def clean(self):
    self.tool_mode = 'IDLE'
    self.first_mouse_x = None
    self.center = None
    self.depth = 0
    self.thickness = 0
    self.move_size = None


# calculate Move Size
def calc_move_size(self, context):
    rv3d = context.region_data
    reg_w = bpy.context.region.width
    reg_h = bpy.context.region.height

    view_dir_neg = rv3d.view_rotation * Vector((0.0, 0.0, 1.0))
    move_test_1 = ut_base.get_mouse_on_plane(context, self.center, view_dir_neg, (reg_w / 2, reg_h / 2))
    move_test_2 = ut_base.get_mouse_on_plane(context, self.center, view_dir_neg, ((reg_w / 2) + 1.0, reg_h / 2))

    return (move_test_1 - move_test_2).length
