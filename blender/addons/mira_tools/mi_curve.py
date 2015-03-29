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


class MI_BasePanel(bpy.types.Panel):
    bl_label = "Curve"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'


    def draw(self, context):
        layout = self.layout
        curve_settings = context.scene.mi_curve_settings

        layout.operator("mira.start_draw", text="Draw Curve")
        layout.prop(curve_settings, "curve_resolution", text='Resolution')
        layout.prop(curve_settings, "draw_handlers", text='Handlers')


class MRStartDraw(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.start_draw"
    bl_label = "StartDraw"
    bl_description = "Draw Test"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'LEFTMOUSE', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'SELECTMOUSE', 'MOUSEMOVE']

    display_bezier = {}  # display bezier curves dictionary

    # curve tool mode
    curve_tool_modes = ('IDLE', 'MOVE_POINT', 'ADD_POINT', 'SELECT_POINT')
    curve_tool_mode = 'IDLE'

    curves = None
    active_curve = None


    def invoke(self, context, event):
        # reset base curve_settings
        self.curve_tool_mode = 'IDLE'
        self.curves = None
        self.active_curve = None

        if context.area.type == 'VIEW_3D':
            # initialize base variables
            self.curves = []
            active_curve = None

            # the arguments we pass the the callbackection
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self.mi_deform_handle_3d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_3d, args, 'WINDOW', 'POST_VIEW')
            self.mi_deform_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_curve_draw_2d, args, 'WINDOW', 'POST_PIXEL')

            ## test looptools
            #active_obj = context.scene.objects.active
            #bm = bmesh.from_edit_mesh(active_obj.data)
            #loops = loop_t.get_connected_input(bm)
            #loops = loop_t.check_loops(loops, bm)
            #print(loops)

            # test test test
            if context.scene.objects.active:
                curve_settings = context.scene.mi_curve_settings
                cur = None
                if self.curves:
                    cur = self.curves[0]
                else:
                    cur = cur_main.MI_CurveObject()
                self.curves.append(cur)
                self.active_curve = cur  # set active curve

                # for i in range(8):
                #     point = cur.curve_points.add()
                #     point.point_id = generate_point_id(cur.curve_points)
                #     vec = Vector((-1.0, 0.0, 0.0))
                #
                #     beta = math.radians((360.0 /8.0)*i )
                #curve_points
                #     eul = mathu.Euler((0.0, 0.0, beta), 'XYZ')
                #     vec.rotate(eul)
                #     point.position = (vec.x, vec.y, vec.z)
                    # if i == 4:
                    #     point.position = (vec.x+15.0, vec.y, vec.z)


                # points
                point = cur_main.MI_CurvePoint()
                cur.curve_points.append(point)
                point.point_id = generate_point_id(cur.curve_points)
                point.position = (-1.0, 0.0, 0.0)

                #point = cur_main.MI_CurvePoint()
                #cur.curve_points.append(point)
                #point.point_id = generate_point_id(cur.curve_points)
                #point.position = (0.0, 1.0, 0.0)

                #point = cur_main.MI_CurvePoint()
                #cur.curve_points.append(point)
                #point.point_id = generate_point_id(cur.curve_points)
                #point.position = (1.0, 0.0, 0.0)

                #point = cur_main.MI_CurvePoint()
                #cur.curve_points.append(point)
                #point.point_id = generate_point_id(cur.curve_points)
                #point.position = (0.0, -1.0, 0.0)

                #point = cur_main.MI_CurvePoint()
                #cur.curve_points.append(point)
                #point.point_id = generate_point_id(cur.curve_points)
                #point.position = (-1.0, 0.0, 0.0)

                cur.active_point = point.point_id

                # add to display
                cur_main.generate_bezier_points(cur, self.display_bezier, curve_settings.curve_resolution)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        curve_settings = context.scene.mi_curve_settings

        # make picking
        if self.curve_tool_mode == 'IDLE':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'PRESS':
                # pick point test
                m_coords = event.mouse_region_x, event.mouse_region_y
                picked_point = pick_curve_point(self.active_curve, context, m_coords)
                if picked_point:
                    self.active_curve.active_point = picked_point.point_id
                    self.curve_tool_mode = 'MOVE_POINT'
                    #print(picked_point)
                else:
                    # add point
                    act_point = get_point(self.active_curve.curve_points, self.active_curve.active_point)
                    new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)
                    if new_point_pos:
                        point = cur_main.MI_CurvePoint()
                        self.active_curve.curve_points.append(point)
                        point.point_id = generate_point_id(self.active_curve.curve_points)
                        point.position = new_point_pos
                        self.active_curve.active_point = point.point_id
                        self.curve_tool_mode = 'ADD_POINT'

                        # add to display
                        cur_main.curve_point_changed(self.active_curve, self.active_curve.curve_points.index(point), curve_settings.curve_resolution, self.display_bezier)

                return {'RUNNING_MODAL'}

        elif self.curve_tool_mode == 'MOVE_POINT':
            if event.value == 'RELEASE':
                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move point
                m_coords = event.mouse_region_x, event.mouse_region_y
                for point in self.active_curve.curve_points:
                    if point.point_id == self.active_curve.active_point:
                        new_point_pos = ut_base.get_mouse_on_plane(context, point.position, None, m_coords)
                        if new_point_pos:
                            point.position = new_point_pos
                            cur_main.curve_point_changed(self.active_curve, self.active_curve.curve_points.index(point), curve_settings.curve_resolution, self.display_bezier)
                            break

                return {'RUNNING_MODAL'}

        elif self.curve_tool_mode == 'ADD_POINT':
            self.curve_tool_mode = 'MOVE_POINT'

        else:
            if event.value == 'RELEASE':
                self.curve_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}


        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_deform_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_deform_handle_2d, 'WINDOW')

            # clear
            display_bezier = None

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}
        #return {'PASS_THROUGH'}


def mi_curve_draw_2d(self, context):
    active_obj = context.scene.objects.active
    if self.curves:
        draw_curve(self.curves, context)


def mi_curve_draw_3d(self, context):
    active_obj = context.scene.objects.active
    if self.curves:
        # test1
        region = context.region
        rv3d = context.region_data
        for curve in self.curves:
            for cur_point in curve.curve_points:
                if cur_point.point_id in self.display_bezier:
                    mi_curve_draw_3d_polyline(self.display_bezier[cur_point.point_id], 2, (0.5,0.8,0.9,1.0))


def generate_point_id(points):
    # Generate unique id
    other_ids = []
    for point in points:
        other_ids.append(point.point_id)

    while True:
        uniq_numb = None
        uniq_id_temp = ''.join(random.choice(string.ascii_uppercase + string.digits)
                               for _ in range(10))
        if uniq_id_temp not in other_ids:
            uniq_numb = uniq_id_temp
            break

    other_ids = None  # clean
    return uniq_numb

def get_point(points, p_id):
    for point in points:
        if point.point_id == p_id:
            return point
    return None


def pick_curve_point(curve, context, mouse_coords):
    region = context.region
    rv3d = context.region_data

    for cu_point in curve.curve_points:
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)
        length = (point_pos_2d - Vector(mouse_coords)).length
        if length <= 9.0:
            return cu_point

    return None


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


def draw_curve(curves, context):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_curve_settings
    # coord = event.mouse_region_x, event.mouse_region_y
    for curve in curves:
        for cu_point in curve.curve_points:
            point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)

            p_col = (0.5,0.8,1.0,1.0)
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


# ---------------------------------------


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