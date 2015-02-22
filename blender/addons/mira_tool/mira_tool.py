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

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from bpy_extras import view3d_utils

import math
import mathutils as mathu
import random
from mathutils import Vector


class MI_CurvePoint(bpy.types.PropertyGroup):
    position = FloatVectorProperty()
    direction = FloatVectorProperty()
    up_direction = FloatVectorProperty()


class MI_CurveObject(bpy.types.PropertyGroup):
    curve_points = CollectionProperty(
        name="x",
        description="x...",
        type=MI_CurvePoint
    )


class MI_BasePanel(bpy.types.Panel):
    bl_label = "Mira"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = 'Mira'


    def draw(self, context):
        layout = self.layout
        layout.operator("mira.start_draw", text="Test")


class MRStartDraw(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.start_draw"
    bl_label = "StartDraw"
    bl_description = "Draw Test"
    bl_options = {'REGISTER', 'UNDO'}

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_handle_2d, 'WINDOW')
            return {'CANCELLED'}

        return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self.mi_handle_3d = bpy.types.SpaceView3D.draw_handler_add(mi_draw_3d, args, 'WINDOW', 'POST_VIEW')
            self.mi_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_draw_2d, args, 'WINDOW', 'POST_PIXEL')

            # test test test
            if context.selected_objects:


                cur = context.scene.objects.active.mi_curves.add()
                # points
                point = cur.curve_points.add()
                point.position = (-1.0, 0.0, 0.0)
                point = cur.curve_points.add()
                point.position = (0.0, 1.0, 0.0)
                point = cur.curve_points.add()
                point.position = (1.0, 0.0, 0.0)
                point = cur.curve_points.add()
                point.position = (0.0, -1.0, 0.0)

                point = cur.curve_points.add()
                point.position = (-1.0, 0.0, 0.0)
                # print(cur.x[0].y)

            # self.mouse_path = []

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def mi_draw_2d_point(point_x, point_y, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
    # 50% alpha, 2 pixel width line
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


def mi_draw_curve(curves, context):
    region = context.region
    rv3d = context.region_data
    # coord = event.mouse_region_x, event.mouse_region_y
    for curve in curves:
        for cu_point in curve.curve_points:
            point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)
            # if point_pos_2d.x
            mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, (0.5,0.8,1.0,0.7))


def mi_draw_2d(self, context):
    active_obj = context.scene.objects.active
    if active_obj.mi_curves:
        mi_draw_curve(active_obj.mi_curves, context)

        # test1
        region = context.region
        rv3d = context.region_data
        for curve in active_obj.mi_curves:
            p_len = len(curve.curve_points)
            for i in range(p_len):
                if i > 0:

                    back_point = None
                    if i-1 < 0:
                        back_point = i
                    else:
                        back_point = i-1

                    two_back_point = None
                    if i-2 < 0:
                        two_back_point = i
                    else:
                        two_back_point = i-2

                    forward_point = None
                    if i+1 > p_len-1:
                        forward_point = i
                    else:
                        forward_point = i+1

                    knot1 = Vector(curve.curve_points[back_point].position)
                    knot2 = Vector(curve.curve_points[i].position)

                    handle1 = knot1
                    if i != 0:
                        handle1 = (Vector(curve.curve_points[i].position) - Vector(curve.curve_points[two_back_point].position)) / 3.6225
                        handle1_len = handle1.length
                        handle1 = knot1 + (handle1.normalized()*handle1_len)
                    
                    handle2 = knot2
                    if i != p_len-1:
                        handle2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[forward_point].position)) / 3.6225
                        handle2_len = handle2.length
                        handle2 = knot2 + (handle2.normalized()*handle2_len)

                    vecs = mathu.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, 30)

                    for vec in vecs:
                        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, vec)
                        mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 2, (0.7,0.9,1.0,0.7))

                    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, handle1)
                    mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 4, (0.0,0.5,1.0,0.7))
                    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, handle2)
                    mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 4, (0.0,0.5,1.0,0.7))


def mi_draw_3d(self, context):
    pass


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