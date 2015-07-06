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
from . import mi_inputs


class MI_CurveTest(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.curve_test"
    bl_label = "StartDraw"
    bl_description = "Draw Test"
    bl_options = {'REGISTER', 'UNDO'}

    # curve tool mode
    curve_tool_modes = ('IDLE', 'MOVE_POINT', 'SELECT_POINT')
    curve_tool_mode = 'IDLE'

    all_curves = None
    active_curve = None
    deform_mouse_pos = None

    picked_meshes = None

    def invoke(self, context, event):
        reset_params(self)

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)

            curve_settings = context.scene.mi_settings
            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)

            # get meshes for snapping
            if curve_settings.surface_snap is True:
                meshes_array = ut_base.get_obj_dup_meshes(curve_settings.snap_objects, curve_settings.convert_instances, context)
                if meshes_array:
                    self.picked_meshes = meshes_array

            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self.mi_curve_test_3d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_3d, args, 'WINDOW', 'POST_VIEW')
            self.mi_curve_test_2d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_2d, args, 'WINDOW', 'POST_PIXEL')

            # test test test
            if context.scene.objects.active:

                cur = cur_main.MI_CurveObject(self.all_curves)
                cur.closed = True
                self.all_curves.append(cur)
                #self.active_curve = cur  # set active curve

                for i in range(8):
                    point = cur_main.MI_CurvePoint(cur.curve_points)
                    vec = Vector((-10.0, 0.0, 0.0))

                    beta = math.radians((360.0 /8.0)*i )

                    eul = mathu.Euler((0.0, 0.0, beta), 'XYZ')
                    vec.rotate(eul)
                    point.position = Vector((vec.x, vec.y, vec.z))
                    #if i == 4:
                        #point.position = Vector((vec.x+15.0, vec.y, vec.z))
                    cur.curve_points.append(point)
                cur_main.generate_bezier_points(cur, cur.display_bezier, curve_settings.curve_resolution)

                # new curve
                cur = cur_main.MI_CurveObject(self.all_curves)
                self.all_curves.append(cur)
                self.active_curve = cur  # set active curve
                # points
                point = cur_main.MI_CurvePoint(cur.curve_points)
                cur.curve_points.append(point)
                point.position = Vector((-1.0, 0.0, 0.0))

                point = cur_main.MI_CurvePoint(cur.curve_points)
                cur.curve_points.append(point)
                point.position = Vector((0.0, 1.0, 0.0))

                # add to display
                cur_main.generate_bezier_points(cur, cur.display_bezier, curve_settings.curve_resolution)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        context.area.header_text_set("NewPoint: Ctrl+Click, SelectAdditive: Shift+Click, DeletePoint: Del, SurfaceSnap: Shift+Tab, SelectLinked: L/Shift+L")

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences
        curve_settings = context.scene.mi_settings
        m_coords = event.mouse_region_x, event.mouse_region_y

        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)

        region = context.region
        rv3d = context.region_data

        keys_pass = mi_inputs.get_input_pass(mi_inputs.pass_keys, addon_prefs.key_inputs, event)

        # make picking
        if self.curve_tool_mode == 'IDLE' and event.value == 'PRESS' and keys_pass is False:
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                # pick point test
                picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point(self.all_curves, context, m_coords)
                if picked_point:
                    self.deform_mouse_pos = m_coords
                    self.active_curve = picked_curve
                    self.active_curve.active_point = picked_point.point_id
                    additive_sel = event.shift

                    if additive_sel is False:
                        for curve in self.all_curves:
                            if curve is not self.active_curve and picked_point.select is False:
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

            elif event.type in {'DEL'} and event.value == 'PRESS':
                for curve in self.all_curves:
                    sel_points = cur_main.get_selected_points(curve.curve_points)
                    if sel_points:
                        for point in sel_points:
                            #the_act_point = cur_main.get_point_by_id(curve.curve_points, curve.active_point)
                            #the_act_point_index = curve.curve_points.index(point)

                            cur_main.delete_point(point, curve, curve.display_bezier, curve_settings.curve_resolution)

                        curve.display_bezier.clear()
                        cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)
                        curve.active_point = None

            elif event.type in {'TAB'} and event.shift:
                if curve_settings.surface_snap is True:
                    curve_settings.surface_snap = False
                else:
                    curve_settings.surface_snap = True
                    if not self.picked_meshes:
                        # get meshes for snapping
                        meshes_array = ut_base.get_obj_dup_meshes(curve_settings.snap_objects, curve_settings.convert_instances, context)
                        if meshes_array:
                            self.picked_meshes = meshes_array

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
                    self.active_curve = picked_curve

        # TOOL WORK
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
                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)
                if new_point_pos:
                    move_offset = new_point_pos - act_point.position
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


        # get keys
        if keys_pass is True:
            # allow navigation
            return {'PASS_THROUGH'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_curve_test_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_curve_test_2d, 'WINDOW')
            context.area.header_text_set()

            return {'FINISHED'}

        return {'RUNNING_MODAL'}


def reset_params(self):
    # reset base curve_settings
    self.curve_tool_mode = 'IDLE'
    self.all_curves = []
    self.active_curve = None
    self.deform_mouse_pos = None
    self.picked_meshes = None


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


def draw_curve_2d(curves, context):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_settings
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