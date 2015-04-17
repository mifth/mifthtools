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
                 'NUMPAD_9', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'MOUSEMOVE']

    # curve tool mode
    tool_modes = ('IDLE', 'MOVE_POINT', 'DRAW_TOOL', 'SCALE_ALL', 'SCALE_FRONT', 'MOVE', 'TWIST', 'ROTATE', 'BEND')
    tool_mode = 'IDLE'

    lw_tool = None
    active_lw_point = None
    deform_mouse_pos = None

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
                    work_verts = bm.verts

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

        region = context.region
        rv3d = context.region_data
        m_coords = event.mouse_region_x, event.mouse_region_y
        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)

        # make picking
        if self.tool_mode == 'IDLE' and event.value == 'PRESS':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                if self.lw_tool:
                    # pick point test
                    picked_point = pick_lw_point(context, m_coords, self.lw_tool)
                    if picked_point:
                        self.deform_mouse_pos = m_coords
                        self.active_lw_point = picked_point
                        #print(picked_point)

                        self.tool_mode = 'MOVE_POINT'
                else:
                    picked_point = ut_base.get_mouse_on_plane(context, self.start_work_center, None, m_coords)
                    if picked_point:
                        self.lw_tool = l_widget.MI_Linear_Widget()

                        self.lw_tool.start_point = l_widget.MI_LW_Point(picked_point.copy())
                        self.lw_tool.middle_point = l_widget.MI_LW_Point(picked_point.copy())
                        self.lw_tool.end_point = l_widget.MI_LW_Point(picked_point)

                        self.active_lw_point = self.lw_tool.end_point

                        self.tool_mode = 'MOVE_POINT'

            elif event.type == 'S':
                self.apply_tool_verts = l_widget.get_tool_verts(self.lw_tool, self.work_verts, bm, active_obj)
                self.deform_mouse_pos = Vector(m_coords)

                if event.shift:
                    self.tool_mode = 'SCALE_FRONT'
                else:
                    self.tool_mode = 'SCALE_ALL'

                return {'RUNNING_MODAL'}

        elif self.tool_mode == 'MOVE_POINT':
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

        elif self.tool_mode in {'SCALE_ALL', 'SCALE_FRONT'}:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                self.tool_mode = 'IDLE'
            else:
                # move points
                start_point_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, self.lw_tool.start_point.position)
                if start_point_2d:
                    tool_dist = (start_point_2d - self.deform_mouse_pos).length
                    now_dist = (start_point_2d - Vector(m_coords)).length
                    apply_value = (now_dist - tool_dist) / tool_dist
                    if apply_value != 0.0:
                        tool_orig = active_obj.matrix_world.inverted() * self.lw_tool.start_point.position
                        for vert_data in self.apply_tool_verts:
                            scale_vec = None
                            if self.tool_mode == 'SCALE_ALL':
                                scale_vec = (vert_data[2] - tool_orig).normalized()
                            else:
                                # SCALE_FRONT
                                tool_end = active_obj.matrix_world.inverted() * self.lw_tool.end_point.position
                                scale_vec = (tool_end - tool_orig).normalized()

                            bm.verts[vert_data[0]].co = vert_data[2] + ( scale_vec * (vert_data[1]) * apply_value)
                        bmesh.update_edit_mesh(active_obj.data)

            return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
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

    self.start_work_center = None
    self.work_verts = None
    self.apply_tool_verts = None


def lin_def_draw_2d(self, context):
    # active_obj = context.scene.objects.active
    rv3d = context.region_data
    lw_dir = (self.lw_tool.start_point.position - self.lw_tool.end_point.position).normalized()
    cam_view = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()
    side_dir = lw_dir.cross(cam_view).normalized()
    l_widget.draw_lw(context, self.lw_tool, side_dir)


def pick_lw_point(context, m_coords, lw):
    region = context.region
    rv3d = context.region_data

    return_point = None
    good_distance = None

    mouse_coords = Vector(m_coords)

    lw_points = [lw.start_point, lw.middle_point, lw.end_point]
    for lw_point in lw_points:
        vec_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, lw_point.position)
        dist = (vec_2d - mouse_coords).length
        if dist <= 9.0:
            if not return_point:
                return_point = lw_point
                good_distance = dist
            elif good_distance > dist:
                return_point = lw_point

    return return_point

