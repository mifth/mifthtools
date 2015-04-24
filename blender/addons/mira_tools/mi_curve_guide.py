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
import bmesh

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from bpy_extras import view3d_utils

import math
import mathutils as mathu
import random
from mathutils import Vector, Matrix

from . import mi_utils_base as ut_base
from . import mi_color_manager as col_man
from . import mi_linear_widget as l_widget


class MI_Linear_Deformer(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.linear_deformer"
    bl_label = "LinearDeformer"
    bl_description = "Linear Deformer"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'MOUSEMOVE']

    # curve tool mode
    tool_modes = ('IDLE', 'MOVE_LW_POINT')
    tool_mode = 'IDLE'

    lw_tool = None
    active_lw_point = None
    deform_mouse_pos = None
    deform_vec_pos = None

    bend_scale_len = None

    start_work_center = None
    work_verts = None
    apply_tool_verts = None

    def invoke(self, context, event):
        reset_params(self)

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)
            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)

            if bm.verts:
                work_verts = ut_base.get_selected_bmverts(bm)
                if not work_verts:
                    work_verts = [v for v in bm.verts if v.hide is False]

                self.start_work_center = ut_base.get_vertices_center(work_verts, active_obj, False)
                self.work_verts = [vert.index for vert in work_verts]

                # Add the region OpenGL drawing callback
                # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
                # self.lin_deform_handle_3d = bpy.types.SpaceView3D.draw_handler_add(lin_def_draw_3d, args, 'WINDOW', 'POST_VIEW')
                self.lin_deform_handle_2d = bpy.types.SpaceView3D.draw_handler_add(lin_def_draw_2d, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)

                return {'RUNNING_MODAL'}
            else:
                self.report({'WARNING'}, "No verts!!")
                return {'CANCELLED'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        context.area.tag_redraw()

        lin_def_settings = context.scene.mi_ldeformer_settings

        region = context.region
        rv3d = context.region_data
        m_coords = event.mouse_region_x, event.mouse_region_y
        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)

        # tooltip
        # tooltip_text = None
        # context.area.header_text_set(tooltip_text)

        # key pressed
        if self.tool_mode == 'IDLE' and event.value == 'PRESS':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                # pick linear widget point
                picked_point = l_widget.pick_lw_point(context, m_coords, self.lw_tool)
                if picked_point:
                    self.deform_mouse_pos = Vector(m_coords)
                    self.active_lw_point = picked_point

                    self.tool_mode = 'MOVE_LW_POINT'

        # TOOL WORK!
        if self.tool_mode == 'MOVE_LW_POINT':
            if event.value == 'RELEASE':
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                new_point_pos = ut_base.get_mouse_on_plane(context, self.active_lw_point.position, None, m_coords)
                if self.active_lw_point.position == self.lw_tool.start_point.position or self.active_lw_point.position == self.lw_tool.end_point.position:
                    self.active_lw_point.position = new_point_pos
                    l_widget.update_middle_point(self.lw_tool)
                elif self.active_lw_point.position == self.lw_tool.middle_point.position:
                    self.lw_tool.start_point.position += new_point_pos - self.active_lw_point.position
                    self.lw_tool.end_point.position += new_point_pos - self.active_lw_point.position
                    self.lw_tool.middle_point.position = new_point_pos

                return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}

        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            # bpy.types.SpaceView3D.draw_handler_remove(self.lin_deform_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.lin_deform_handle_2d, 'WINDOW')

            context.area.header_text_set()

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


def reset_params(self):
    self.tool_mode = 'IDLE'
    self.deform_mouse_pos = None
    self.deform_vec_pos = None
    self.bend_scale_len = None

    self.lw_tool = None
    self.active_lw_point = None

    self.start_work_center = None
    self.work_verts = None
    self.apply_tool_verts = None


def lin_def_draw_2d(self, context):
    # active_obj = context.scene.objects.active
    rv3d = context.region_data
    if self.lw_tool:
        lw_dir = (self.lw_tool.start_point.position - self.lw_tool.end_point.position).normalized()
        cam_view = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()
        side_dir = lw_dir.cross(cam_view).normalized()
        l_widget.draw_lw(context, self.lw_tool, side_dir, True)


