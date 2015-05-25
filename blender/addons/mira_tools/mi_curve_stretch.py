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
from . import mi_color_manager as col_man
from . import mi_looptools as loop_t


class MI_CurveStretchSettings(bpy.types.PropertyGroup):
    points_number = IntProperty(default=5, min=2, max=128)
    spread_mode = EnumProperty(
        name = "Spread Mode",
        items = (('ORIGINAL', 'ORIGINAL', ''),
                ('UNIFORM', 'UNIFORM', '')
                ),
        default = 'ORIGINAL'
    )


class MI_CurveStretch(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.curve_stretch"
    bl_label = "StartDraw"
    bl_description = "Draw Test"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'MOUSEMOVE']

    # curve tool mode
    curve_tool_modes = ('IDLE', 'MOVE_POINT', 'SELECT_POINT')
    curve_tool_mode = 'IDLE'

    all_curves = None
    active_curve = None
    deform_mouse_pos = None
    picked_meshes = None

    # loops code
    loops = None
    original_verts_data = None

    manipulator = None

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
                self.manipulator = context.space_data.show_manipulator
                context.space_data.show_manipulator = False


                for loop in self.loops:
                    loop_verts = [active_obj.matrix_world * bm.verts[i].co for i in loop[0]]
                    loop_line = cur_main.pass_line(loop_verts, loop[1])
                    new_curve = cur_main.create_curve_to_line(cur_stretch_settings.points_number, loop_line, self.all_curves, loop[1])

                    # set closed curve
                    if loop[1] is True:
                        new_curve.closed = True

                    self.all_curves.append(new_curve)
                    self.active_curve = new_curve

                    cur_main.generate_bezier_points(self.active_curve, self.active_curve.display_bezier, curve_settings.curve_resolution)

                    self.original_verts_data.append( cur_main.pass_line([bm.verts[i].co for i in loop[0]] , loop[1]) )

                    # move point to the curve
                    for curve in self.all_curves:
                        update_curve_line(active_obj, curve, self.loops, self.all_curves, bm, cur_stretch_settings.spread_mode, self.original_verts_data[self.all_curves.index(curve)])

                    # get meshes for snapping
                    if curve_settings.surface_snap is True:
                        sel_objects = [
                            obj for obj in context.selected_objects if obj != active_obj]
                        if sel_objects:
                            self.picked_meshes = ut_base.get_obj_dup_meshes(
                                sel_objects, context)

                self.mi_deform_handle_3d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_3d, args, 'WINDOW', 'POST_VIEW')
                self.mi_deform_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_2d, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

                return {'RUNNING_MODAL'}
            else:
                #finish_work(self, context)
                self.report({'WARNING'}, "No loops found!")
                return {'CANCELLED'}
        else:
            #finish_work(self, context)
            self.report({'WARNING'}, "View3D not found, cannot run operator!")
            return {'CANCELLED'}


    def modal(self, context, event):
        context.area.tag_redraw()

        context.area.header_text_set("NewPoint: Ctrl+Click, SelectAdditive: Shift+Click, DeletePoint: Del, SurfaceSnap: Shift+Tab, SelectLinked: L/Shift+L, SpreadMode: M")

        curve_settings = context.scene.mi_curve_settings
        cur_stretch_settings = context.scene.mi_cur_stretch_settings
        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)

        region = context.region
        rv3d = context.region_data
        m_coords = event.mouse_region_x, event.mouse_region_y

        # make picking
        if self.curve_tool_mode == 'IDLE' and event.value == 'PRESS':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                # pick point test
                picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point(self.all_curves, context, m_coords)
                if picked_point:
                    self.deform_mouse_pos = m_coords
                    self.active_curve = picked_curve
                    self.active_curve.active_point = picked_point.point_id
                    additive_sel = event.shift

                    if additive_sel is False and picked_point.select is False:
                        for curve in self.all_curves:
                            if curve is not self.active_curve:
                                cur_main.select_all_points(curve.curve_points, False)  # deselect points
                                curve.active_point = None

                    cur_main.select_point(self.active_curve, picked_point, additive_sel)

                    self.curve_tool_mode = 'SELECT_POINT'
                else:
                    # add point
                    if event.ctrl and self.active_curve and self.active_curve.active_point:
                        act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                        new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)

                        if new_point_pos:
                            for curve in self.all_curves:
                                if curve is not self.active_curve:
                                    cur_main.select_all_points(curve.curve_points, False)  # deselect points
                                    curve.active_point = None

                            new_point = cur_main.add_point(new_point_pos, self.active_curve)

                            self.active_curve.active_point = new_point.point_id
                            self.curve_tool_mode = 'MOVE_POINT'

                            # add to display
                            cur_main.curve_point_changed(self.active_curve, self.active_curve.curve_points.index(new_point), curve_settings.curve_resolution, self.active_curve.display_bezier)

                #return {'RUNNING_MODAL'}

            elif event.type in {'DEL'}:
                for curve in self.all_curves:
                    sel_points = cur_main.get_selected_points(curve.curve_points)
                    if sel_points:
                        for point in sel_points:
                            #the_act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                            #the_act_point_index = self.active_curve.curve_points.index(point)

                            if len(curve.curve_points) > 2:
                                cur_main.delete_point(point, curve, curve.display_bezier, curve_settings.curve_resolution)
                            else:
                                point.select = False

                        curve.display_bezier.clear()
                        cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)
                        curve.active_point = None

                        # move point to the curve
                        update_curve_line(active_obj, curve, self.loops, self.all_curves, bm, cur_stretch_settings.spread_mode, self.original_verts_data[self.all_curves.index(curve)])

                    bm.normal_update()
                    bmesh.update_edit_mesh(active_obj.data)

                #return {'RUNNING_MODAL'}

            elif event.type in {'TAB'} and event.shift:
                if curve_settings.surface_snap is True:
                    curve_settings.surface_snap = False
                else:
                    curve_settings.surface_snap = True
                    if not self.picked_meshes:
                        # get meshes for snapping
                        sel_objects = [
                            obj for obj in context.selected_objects if obj != active_obj]
                        if sel_objects:
                            self.picked_meshes = ut_base.get_obj_dup_meshes(
                                sel_objects, context)

            # Select Linked
            elif event.type == 'L':
                picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point(self.all_curves, context, m_coords)

                if picked_point:
                    if not event.shift:
                        for curve in self.all_curves:
                            if curve is not picked_curve:
                                cur_main.select_all_points(curve.curve_points, False)
                                curve.active_point = None

                    cur_main.select_all_points(picked_curve.curve_points, True)
                    picked_curve.active_point = picked_point.point_id

            # Change Spread Type
            elif event.type == 'M':
                if cur_stretch_settings.spread_mode == 'ORIGINAL':
                    cur_stretch_settings.spread_mode = 'UNIFORM'
                else:
                    cur_stretch_settings.spread_mode = 'ORIGINAL'

                for curve in self.all_curves:
                    update_curve_line(active_obj, curve, self.loops, self.all_curves, bm, cur_stretch_settings.spread_mode, self.original_verts_data[self.all_curves.index(curve)])

        # TOOLS WORK
        if self.curve_tool_mode == 'SELECT_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # set to move point
                if ( Vector((m_coords[0], m_coords[1])) - Vector((self.deform_mouse_pos[0], self.deform_mouse_pos[1])) ).length > 4.0:
                    self.curve_tool_mode = 'MOVE_POINT'
                    return {'RUNNING_MODAL'}

        elif self.curve_tool_mode == 'MOVE_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                # move point to the curve
                for curve in self.all_curves:
                    selected_points = cur_main.get_selected_points(curve.curve_points)
                    if selected_points:
                        update_curve_line(active_obj, curve, self.loops, self.all_curves, bm, cur_stretch_settings.spread_mode, self.original_verts_data[self.all_curves.index(curve)])

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)

                if new_point_pos:
                    move_offset = new_point_pos - act_point.position
                    camera_dir = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()

                    for curve in self.all_curves:
                        selected_points = cur_main.get_selected_points(curve.curve_points)
                        if selected_points:

                            # Snap to Surface
                            if curve_settings.surface_snap is True:
                                if self.picked_meshes:
                                    for point in selected_points:
                                        # get the ray from the viewport and mouse
                                        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, point.position + move_offset)
                                        if point_pos_2d:
                                            best_obj, hit_normal, hit_position = ut_base.get_mouse_raycast(context, self.picked_meshes, point_pos_2d, 10000.0)
                                            #best_obj, hit_normal, hit_position = ut_base.get_3dpoint_raycast(context, self.picked_meshes, point.position + move_offset, camera_dir, 10000.0)
                                        if hit_position:
                                            point.position = hit_position

                            # Move Points without Snapping
                            else:
                                for point in selected_points:
                                    point.position += move_offset

                            if len(selected_points) == 1:
                                cur_main.curve_point_changed(curve, curve.curve_points.index(selected_points[0]), curve_settings.curve_resolution, curve.display_bezier)
                            else:
                                cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)

                return {'RUNNING_MODAL'}

        #elif self.curve_tool_mode == 'ADD_POINT':
            #self.curve_tool_mode = 'MOVE_POINT'
            #return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                self.curve_tool_mode = 'IDLE'            
                return {'RUNNING_MODAL'}


        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_deform_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_deform_handle_2d, 'WINDOW')
            finish_work(self, context)

            context.area.header_text_set()

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

    self.picked_meshes = None

    # loops code
    self.loops = None
    self.original_verts_data = []


def finish_work(self, context):
    context.space_data.show_manipulator = self.manipulator


def update_curve_line(active_obj, curve_to_update, loops, all_curves, bm, spread_mode, original_verts_data):
    line = cur_main.get_bezier_line(curve_to_update, active_obj, True)
    loop_verts = [bm.verts[i] for i in loops[all_curves.index(curve_to_update)][0]]

    if spread_mode == 'ORIGINAL':
        cur_main.verts_to_line(loop_verts, line, original_verts_data, curve_to_update.closed)
    else:
        cur_main.verts_to_line(loop_verts, line, None, curve_to_update.closed)


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
                    mi_curve_draw_3d_polyline(curve.display_bezier[cur_point.point_id], 2, col_man.cur_line_base, True)


def draw_curve_2d(curves, context):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_curve_settings
    # coord = event.mouse_region_x, event.mouse_region_y
    for curve in curves:
        for cu_point in curve.curve_points:
            point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)

            if point_pos_2d:
                p_col = col_man.cur_point_base
                if curve.closed is True:
                    if curve.curve_points.index(cu_point) == 0:
                        p_col = col_man.cur_point_closed_start
                    elif curve.curve_points.index(cu_point) == len(curve.curve_points) - 1:
                        p_col = col_man.cur_point_closed_end

                if cu_point.select:
                    p_col = col_man.cur_point_selected
                if cu_point.point_id == curve.active_point:
                    p_col = col_man.cur_point_active
                mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, p_col)

                # Handlers
                if curve_settings.draw_handlers:
                #if curve.curve_points.index(cu_point) < len(curve.curve_points)-1:
                    if cu_point.handle1:
                        handle_1_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle1)
                        if handle_1_pos_2d:
                            mi_draw_2d_point(handle_1_pos_2d.x, handle_1_pos_2d.y, 3, col_man.cur_handle_1_base)
                #if curve.curve_points.index(cu_point) > 0:
                    if cu_point.handle2:
                        handle_2_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle2)
                        if handle_2_pos_2d:
                            mi_draw_2d_point(handle_2_pos_2d.x, handle_2_pos_2d.y, 3, col_man.cur_handle_2_base)


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
def mi_curve_draw_3d_polyline(points, p_size, p_col, x_ray):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(1)

    if x_ray is True:
        bgl.glDisable(bgl.GL_DEPTH_TEST)

    bgl.glPointSize(p_size)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glColor4f(p_col[0], p_col[1], p_col[2], p_col[3])
 #   bgl.glBegin(bgl.GL_POLYGON)

    for point in points:
        bgl.glVertex3f(point[0], point[1], point[2])

    if x_ray is True:
        bgl.glEnable(bgl.GL_DEPTH_TEST)

    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

