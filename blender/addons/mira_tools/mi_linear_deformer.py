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
from mathutils import Vector

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
                 'NUMPAD_9', 'LEFTMOUSE', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'SELECTMOUSE', 'MOUSEMOVE']

    # curve tool mode
    tool_modes = ('IDLE', 'MOVE_POINT')
    tool_mode = 'IDLE'

    lw_tool = None
    active_lw_point = None
    deform_mouse_pos = None

    def invoke(self, context, event):
        reset_params(self)

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)

            self.lw_tool = l_widget.MI_Linear_Widget()

            # test test test
            self.lw_tool.start_point = Vector((0.0, 0.0, 0.0))
            self.lw_tool.middle_point = Vector((0.0, 0.0, 1.0))
            self.lw_tool.end_point = Vector((0.0, 0.0, 2.0))

            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            # self.lin_deform_handle_3d = bpy.types.SpaceView3D.draw_handler_add(lin_def_draw_3d, args, 'WINDOW', 'POST_VIEW')
            self.lin_deform_handle_2d = bpy.types.SpaceView3D.draw_handler_add(lin_def_draw_2d, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        region = context.region
        rv3d = context.region_data

        # make picking
        if self.tool_mode == 'IDLE':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'PRESS':
                # pick point test
                m_coords = event.mouse_region_x, event.mouse_region_y
                # picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point(self.all_curves, context, m_coords)
                # if picked_point:
                #     self.deform_mouse_pos = m_coords
                #
                #     self.tool_mode = 'SELECT_POINT'

                return {'RUNNING_MODAL'}

        elif self.tool_mode == 'MOVE_POINT':
            if event.value == 'RELEASE':
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                m_coords = event.mouse_region_x, event.mouse_region_y

                return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE':
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}


        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            # bpy.types.SpaceView3D.draw_handler_remove(self.lin_deform_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.lin_deform_handle_2d, 'WINDOW')

            # clear
            #display_bezier = None

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


def reset_params(self):
    self.tool_mode = 'IDLE'
    self.deform_mouse_pos = None
    self.lw_tool = None
    self.active_lw_point = None


def lin_def_draw_2d(self, context):
    # active_obj = context.scene.objects.active
    rv3d = context.region_data
    lw_dir = (self.lw_tool.start_point - self.lw_tool.end_point).normalized()
    cam_view = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()
    side_dir = lw_dir.cross(cam_view).normalized()
    l_widget.draw_lw(context, self.lw_tool, side_dir)

