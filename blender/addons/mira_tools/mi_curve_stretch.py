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

from . import mi_curve_main as cur_main
from . import mi_utils_base as ut_base
from . import mi_looptools as loop_t


class MI_CurveStretchSettings(bpy.types.PropertyGroup):
    # Curve Stretch Settings
    #curve_resolution = IntProperty(default=13, min=1, max=128)

    point_number = IntProperty(default=5, min=2, max=128)


class MI_CurveStretch(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.curve_stretch"
    bl_label = "StartDraw"
    bl_description = "Draw Test"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'LEFTMOUSE', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'SELECTMOUSE', 'MOUSEMOVE']

    # curve tool mode
    curve_tool_modes = ('IDLE', 'MOVE_POINT', 'SELECT_POINT')
    curve_tool_mode = 'IDLE'

    all_curves = None
    active_curve = None
    deform_mouse_pos = None

    # loops code
    loops = None

    def invoke(self, context, event):
        reset_params(self)

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'

            cur_stretch_settings = context.scene.mi_cur_stretch_settings
            curve_settings = context.scene.mi_curve_settings

            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)

            # get loops
            self.loops = loop_t.get_connected_input(bm)
            self.loops = loop_t.check_loops(self.loops, bm)

            if self.loops:
                for loop in self.loops:
                    loop_verts = [active_obj.matrix_world * bm.verts[i].co for i in loop[0]]
                    loop_line = pass_line(loop_verts)
                    new_curve = crete_curve_to_line(cur_stretch_settings.point_number, loop_line, self.all_curves)
                    self.all_curves.append(new_curve)
                    self.active_curve = new_curve

                self.mi_deform_handle_3d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_3d, args, 'WINDOW', 'POST_VIEW')
                self.mi_deform_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_2d, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}
            else:
                self.report({'WARNING'}, "No loops found!")
                return {'CANCELLED'}                
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator!")
            return {'CANCELLED'}


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        curve_settings = context.scene.mi_curve_settings
        cur_stretch_settings = context.scene.mi_cur_stretch_settings
        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)

        # make picking
        if self.curve_tool_mode == 'IDLE':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'PRESS':
                # pick point test
                m_coords = event.mouse_region_x, event.mouse_region_y
                picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point(self.all_curves, context, m_coords)
                if picked_point:
                    self.deform_mouse_pos = m_coords
                    self.active_curve = picked_curve
                    self.active_curve.active_point = picked_point.point_id
                    additive_sel = event.shift

                    cur_main.select_point(self.active_curve, picked_point, additive_sel)

                    self.curve_tool_mode = 'SELECT_POINT'
                else:
                    # add point
                    if event.ctrl and self.active_curve and self.active_curve.active_point:
                        act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                        new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)

                        if new_point_pos:
                            new_point = cur_main.add_point(new_point_pos, self.active_curve)

                            self.active_curve.active_point = new_point.point_id
                            self.curve_tool_mode = 'MOVE_POINT'

                            # add to display
                            cur_main.curve_point_changed(self.active_curve, self.active_curve.curve_points.index(new_point), curve_settings.curve_resolution, self.active_curve.display_bezier)

                return {'RUNNING_MODAL'}

            elif event.type in {'DEL'} and event.value == 'PRESS':
                sel_points = cur_main.get_selected_points(self.active_curve.curve_points)
                if sel_points:
                    for point in sel_points:
                        #the_act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                        #the_act_point_index = self.active_curve.curve_points.index(point)

                        cur_main.delete_point(point, self.active_curve, self.active_curve.display_bezier, curve_settings.curve_resolution)

                    self.active_curve.display_bezier.clear()
                    cur_main.generate_bezier_points(self.active_curve, self.active_curve.display_bezier, curve_settings.curve_resolution)
                    self.active_curve.active_point = None

                return {'RUNNING_MODAL'}

        elif self.curve_tool_mode == 'SELECT_POINT':
            if event.value == 'RELEASE':
                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # set to move point
                m_coords = event.mouse_region_x, event.mouse_region_y
                if ( Vector((m_coords[0], m_coords[1])) - Vector((self.deform_mouse_pos[0], self.deform_mouse_pos[1])) ).length > 4.0:
                    self.curve_tool_mode = 'MOVE_POINT'
                    return {'RUNNING_MODAL'}

        elif self.curve_tool_mode == 'MOVE_POINT':
            if event.value == 'RELEASE':
                curve_vecs = [active_obj.matrix_world.inverted() * point.position for point in self.active_curve.curve_points]
                line = pass_line(curve_vecs)
                loop_verts = [bm.verts[i] for i in self.loops[self.all_curves.index(self.active_curve)][0]]
                verts_to_line(loop_verts, line)
                bmesh.update_edit_mesh(active_obj.data)

                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                m_coords = event.mouse_region_x, event.mouse_region_y
                act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                selected_points = cur_main.get_selected_points(self.active_curve.curve_points)
                new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)
                if new_point_pos and selected_points:
                    move_offset = new_point_pos - act_point.position
                    for point in selected_points:
                            point.position += move_offset

                    if len(selected_points) == 1:
                        cur_main.curve_point_changed(self.active_curve, self.active_curve.curve_points.index(point), curve_settings.curve_resolution, self.active_curve.display_bezier)
                    else:
                        cur_main.generate_bezier_points(self.active_curve, self.active_curve.display_bezier, curve_settings.curve_resolution)

                return {'RUNNING_MODAL'}

        #elif self.curve_tool_mode == 'ADD_POINT':
            #self.curve_tool_mode = 'MOVE_POINT'
            #return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE':
                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}


        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_deform_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_deform_handle_2d, 'WINDOW')

            # clear
            #display_bezier = None

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


def reset_params(self):
    # reset base curve_settings
    self.curve_tool_mode = 'IDLE'
    self.all_curves = []
    self.active_curve = None
    self.deform_mouse_pos = None

    # loops code
    self.loops = None


def pass_line(vecs):
    line_length = 0.0
    line_data = []
    for i, vec in enumerate(vecs):
        if i == len(vecs) - 1:
            line_data.append((vec, line_length, 0.0, None))
        else:
            vec_area = vecs[i+1] - vec
            area_length = vec_area.length
            vec_dir = vec_area.normalized()
            line_data.append((vec, line_length, area_length, vec_dir))

            line_length += area_length

    return line_data


def crete_curve_to_line(points_number, line_data, all_curves):
    curve = cur_main.MI_CurveObject(all_curves)
    line_len = line_data[-1][1]
    point_passed = 0
    for i in range(points_number):
        if i == 0:
            curve_point = cur_main.MI_CurvePoint(curve.curve_points)
            curve_point.position = line_data[0][0]
            curve.curve_points.append(curve_point)
            continue
        elif i == points_number - 1:
            curve_point = cur_main.MI_CurvePoint(curve.curve_points)
            curve_point.position = line_data[-1][0]
            curve.curve_points.append(curve_point)
            break

        point_len = (line_len/ (points_number - 1)) * (i)
        for j, point_data in enumerate(line_data, start=point_passed):
            if line_data[j+1][1] >= point_len:
                curve_point = cur_main.MI_CurvePoint(curve.curve_points)
                curve_point.position = line_data[j][0] + (line_data[j][3] * (point_len - line_data[j][1]))
                curve.curve_points.append(curve_point)
                point_passed = j
                break

    return curve


def verts_to_line(verts, line_data):
    line_len = line_data[-1][1]
    verts_number = len(verts)
    point_passed = 0
    for i, vert in enumerate(verts):
        if i == 0:
            vert.co = line_data[0][0]
            continue
        elif i == verts_number - 1:
            vert.co = line_data[-1][0]
            break

        point_len = (line_len/ (verts_number - 1)) * (i)
        for j, point_data in enumerate(line_data, start=point_passed):
            if line_data[j+1][1] >= point_len:
                vert.co = line_data[j][0] + (line_data[j][3] * (point_len - line_data[j][1]))
                point_passed = j
                break


def mi_curve_draw_2d(self, context):
    active_obj = context.scene.objects.active
    if self.all_curves:
        draw_curve_2d(self.all_curves, context)


def mi_curve_draw_3d(self, context):
    active_obj = context.scene.objects.active
    if self.all_curves:
        # test1
        region = context.region
        rv3d = context.region_data
        for curve in self.all_curves:
            for cur_point in curve.curve_points:
                if cur_point.point_id in curve.display_bezier:
                    mi_curve_draw_3d_polyline(curve.display_bezier[cur_point.point_id], 2, (0.5,0.8,0.9,1.0))


# TODO MOVE TO UTILITIES
def mi_draw_2d_point(point_x, point_y, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
    bgl.glEnable(bgl.GL_BLEND)
    #bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
    #bgl.glLineWidth(2)

    bgl.glPointSize(p_size)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_POINTS)
 #   bgl.glBegin(bgl.GL_POLYGON)
    bgl.glColor4f(p_col[0], p_col[1], p_col[2], p_col[3])
    bgl.glVertex2f(point_x, point_y)
    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# TODO MOVE TO UTILITIES
def mi_curve_draw_3d_polyline(points, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(1)

    bgl.glPointSize(p_size)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glColor4f(p_col[0], p_col[1], p_col[2], p_col[3])
 #   bgl.glBegin(bgl.GL_POLYGON)

    for point in points:
        bgl.glVertex3f(point[0], point[1], point[2])

    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


def draw_curve_2d(curves, context):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_curve_settings
    # coord = event.mouse_region_x, event.mouse_region_y
    for curve in curves:
        for cu_point in curve.curve_points:
            point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)

            p_col = (0.5,0.8,1.0,1.0)
            if cu_point.select:
                p_col = (0.9,0.5,0.1,1.0)
            if cu_point.point_id == curve.active_point:
                p_col = (0.9,0.7,0.3,1.0)
            mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, p_col)

            # Handlers
            if curve_settings.draw_handlers:
            #if curve.curve_points.index(cu_point) < len(curve.curve_points)-1:
                if cu_point.handle1:
                    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle1)
                    mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 3, (0.0,0.5,1.0,0.7))
            #if curve.curve_points.index(cu_point) > 0:
                if cu_point.handle2:
                    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle2)
                    mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 3, (1.0,0.5,0.0,0.7))


# --------------------------------------- OLD STUFF


def draw_callback_px_3d(self, context):

    # 50% alpha, 2 pixel width line
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
    bgl.glLineWidth(2)

   # bgl.glBegin(bgl.GL_LINE_STRIP)
   # bgl.glVertex3f(*ob.matrix_world.translation)
   # bgl.glVertex3f(*context.scene.cursor_location)
   # bgl.glEnd()

    bgl.glBegin(bgl.GL_POLYGON)
    #bgl.glColor4f(0.0, 0.0, 0.0, 0.5)
    bgl.glVertex3f(0.0, 0.0, 0.0)
    bgl.glVertex3f(0.0, 1.0, 0.0)
    bgl.glVertex3f(1.0, 1.0, 0.0)
    bgl.glVertex3f(1.0, 0.0, 0.0)
    bgl.glEnd()

    ##bgl.glEnable(bgl.GL_BLEND)
    ##bgl.glLineWidth(1.5)
    #bgl.glPointSize(4)
##    bgl.glBegin(bgl.GL_LINE_LOOP)
    #bgl.glBegin(bgl.GL_POINTS)
 ##   bgl.glBegin(bgl.GL_POLYGON)
    #bgl.glColor4f(0.5,1.1,1.0,0.5)
    #bgl.glVertex2f(10, 20)
    #bgl.glVertex2f(50,60)
    #bgl.glVertex2f(700,80)
    #bgl.glVertex2f(2,180)
    #bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


def draw_callback_px_2d(self, context):

    # 50% alpha, 2 pixel width line
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
    bgl.glLineWidth(2)

   # bgl.glBegin(bgl.GL_LINE_STRIP)
   # bgl.glVertex3f(*ob.matrix_world.translation)
   # bgl.glVertex3f(*context.scene.cursor_location)
   # bgl.glEnd()

    #bgl.glBegin(bgl.GL_POLYGON)
    ##bgl.glColor4f(0.0, 0.0, 0.0, 0.5)
    #bgl.glVertex3f(0.0, 0.0, 0.0)
    #bgl.glVertex3f(0.0, 1.0, 0.0)
    #bgl.glVertex3f(1.0, 1.0, 0.0)
    #bgl.glVertex3f(1.0, 0.0, 0.0)
    #bgl.glEnd()

    #bgl.glEnable(bgl.GL_BLEND)
    #bgl.glLineWidth(1.5)
    bgl.glPointSize(4)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_POINTS)
 #   bgl.glBegin(bgl.GL_POLYGON)
    bgl.glColor4f(0.5,1.1,1.0,0.5)
    bgl.glVertex2f(10, 20)
    bgl.glVertex2f(50,60)
    bgl.glVertex2f(700,80)
    bgl.glVertex2f(2,180)
    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)