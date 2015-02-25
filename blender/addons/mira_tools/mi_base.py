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

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from bpy_extras import view3d_utils

import math
import mathutils as mathu
import random
from mathutils import Vector


#class MI_Bezier_Display():
    #bezier_points = []


#class MI_Curve_Display():
    #curve_points = []


class MI_CurvePoint(bpy.types.PropertyGroup):
    position = FloatVectorProperty()
    direction = FloatVectorProperty()
    up_direction = FloatVectorProperty()
    handle1 = FloatVectorProperty()
    handle2 = FloatVectorProperty()
    point_id = StringProperty(default="")


class MI_CurveObject(bpy.types.PropertyGroup):
    curve_points = CollectionProperty(
        type=MI_CurvePoint
    )


class MI_BasePanel(bpy.types.Panel):
    bl_label = "Mira"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'


    def draw(self, context):
        layout = self.layout
        layout.operator("mira.start_draw", text="Draw Curve")


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
    select_mouse_mode = None

    display_bezier = {}  # display bezier curves dictionary

    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_handle_2d, 'WINDOW')

            # clear
            display_bezier = None
            context.user_preferences.inputs.select_mouse = self.select_mouse_mode

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}
        #return {'PASS_THROUGH'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self.mi_handle_3d = bpy.types.SpaceView3D.draw_handler_add(mi_draw_3d, args, 'WINDOW', 'POST_VIEW')
            self.mi_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_draw_2d, args, 'WINDOW', 'POST_PIXEL')

            # change startup
            self.select_mouse_mode = context.user_preferences.inputs.select_mouse
            context.user_preferences.inputs.select_mouse = 'RIGHT'

            # test test test
            if context.selected_objects:
                cur = context.scene.objects.active.mi_curves.add()

                # for i in range(8):
                #     point = cur.curve_points.add()
                #     point.point_id = mi_generate_point_id(cur.curve_points)
                #     vec = Vector((-1.0, 0.0, 0.0))
                #
                #     beta = math.radians((360.0 /8.0)*i )
                #
                #     eul = mathu.Euler((0.0, 0.0, beta), 'XYZ')
                #     vec.rotate(eul)
                #     point.position = (vec.x, vec.y, vec.z)
                    # if i == 4:
                    #     point.position = (vec.x+15.0, vec.y, vec.z)


                # points
                point = cur.curve_points.add()
                point.point_id = mi_generate_point_id(cur.curve_points)
                point.position = (-1.0, 0.0, 0.0)
                point = cur.curve_points.add()
                point.point_id = mi_generate_point_id(cur.curve_points)
                point.position = (0.0, 1.0, 0.0)
                point = cur.curve_points.add()
                point.point_id = mi_generate_point_id(cur.curve_points)
                point.position = (1.0, 0.0, 0.0)
                point = cur.curve_points.add()
                point.point_id = mi_generate_point_id(cur.curve_points)
                point.position = (0.0, -1.0, 0.0)

                point = cur.curve_points.add()
                point.point_id = mi_generate_point_id(cur.curve_points)
                point.position = (-1.0, 0.0, 0.0)

                # add to display
                mi_generate_bezier(cur, self.display_bezier)

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def mi_generate_point_id(points):
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


def mi_draw_3d_polyline(points, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
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


def mi_draw_curve(curves, context):
    region = context.region
    rv3d = context.region_data
    # coord = event.mouse_region_x, event.mouse_region_y
    for curve in curves:
        for cu_point in curve.curve_points:
            point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)
            mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, (0.5,0.8,1.0,0.7))

            # Debug
            if curve.curve_points.values().index(cu_point) < len(curve.curve_points)-1:
                point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle1)
                mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 4, (0.0,0.5,1.0,0.7))
            if curve.curve_points.values().index(cu_point) > 0:
                point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle2)
                mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 4, (1.0,0.5,0.0,0.7))


def mi_generate_bezier(curve, display_bezier):
        p_len = len(curve.curve_points)
        for i in range(p_len):
            if i > 0:

                back_point = i-1

                two_back_point = None
                if i-2 < 0:
                    two_back_point = i-1
                else:
                    two_back_point = i-2

                forward_point = None
                if i+1 > p_len-1:
                    forward_point = i
                else:
                    forward_point = i+1

                knot1 = Vector(curve.curve_points[back_point].position)
                knot2 = Vector(curve.curve_points[i].position)

                handle1 = None
                handle2 = None

                # Make common interpolation for handles
                if i > 1:
                    dist1 = (Vector(curve.curve_points[i].position) - Vector(curve.curve_points[two_back_point].position))
                    dl1 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[i].position))
                    dl1_2 = (Vector(curve.curve_points[two_back_point].position) - Vector(curve.curve_points[i].position))
                    # h1_len_back = (Vector(curve.curve_points[two_back_point].position) - Vector(curve.curve_points[back_point].position)).length
                    # h1_len_forward = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[i].position)).length
                    # h1_final = (h1_len_forward / (h1_len_back + h1_len_forward))
                    handle1_len = ( dl1.length  ) * (dl1.length/(dl1.length+dl1_2.length))  # 1.1042 is smooth coefficient

                    if dl1.length > dl1_2.length and dl1.length != 0:
                        handle1_len *= (dl1_2.length/dl1.length) * 0.5
                    elif dl1.length < dl1_2.length/2.0 and dl1.length != 0:
                        handle1_len *= (dl1_2.length/2.0)/dl1.length * 0.5

                    # handle1_len = min(( dl1.length  ) * (dl1.length/(dl1.length+dl1_2.length)) ,dist1.length* h1_final*0.5)  # 1.1042 is smooth coefficient
                    handle1 = knot1 + (dist1.normalized() * handle1_len)

                if i < p_len-1:
                    dist2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[forward_point].position))
                    dl2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[i].position))
                    dl2_2 = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[forward_point].position))
                    # h2_len_back = (Vector(curve.curve_points[back_point].position) - Vector(curve.curve_points[i].position)).length
                    # h2_len_forward = (Vector(curve.curve_points[forward_point].position) - Vector(curve.curve_points[i].position)).length
                    # h2_final = (h2_len_back / (h2_len_back + h2_len_forward))
                    handle2_len = (dl2.length  ) * (dl2.length/(dl2.length+dl2_2.length)) # 1.1042 is smooth coefficient

                    if dl2.length > dl2_2.length and dl2.length != 0:
                        handle2_len *= (dl2_2.length/dl2.length) * 0.5
                    elif dl2.length < dl2_2.length/2.0 and dl2.length != 0:
                        handle2_len *= (dl2_2.length/2.0)/dl2.length * 0.5

                    # handle2_len = min((dl2.length  ) * (dl2.length/(dl2.length+dl2_2.length)), dist2.length* h2_final*0.5) # 1.1042 is smooth coefficient
                    handle2 = knot2 + (dist2.normalized() * handle2_len)

                # Make end points
                if handle1 is None:
                    handle1 = (handle2 - knot1)
                    handle1_len = handle1.length * 0.4
                    handle1 = knot1 + (handle1.normalized() * handle1_len)
                if handle2 is None:
                    handle2 = (handle1 - knot2)
                    handle2_len = handle2.length * 0.4
                    handle2 = knot2 + (handle2.normalized() * handle2_len)

                curve.curve_points[i-1].handle1 = handle1  # save handle
                curve.curve_points[i].handle2 = handle2  # save handle

                # Display Bezier points
                # Get all the points on the curve between these two items.  Uses the default of 12 for a "preview" resolution
                # on the curve.  Note the +1 because the "preview resolution" tells how many segments to use.  ie. 2 => 2 segments
                # or 3 points.  The "interpolate_bezier" functions takes the number of points it should generate.
                vecs = mathu.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, 20+1)
                display_bezier[curve.curve_points[i].point_id] = vecs


def mi_draw_2d(self, context):
    active_obj = context.scene.objects.active
    if active_obj.mi_curves:
        mi_draw_curve(active_obj.mi_curves, context)


def mi_draw_3d(self, context):
    active_obj = context.scene.objects.active
    if active_obj.mi_curves:
        # test1
        region = context.region
        rv3d = context.region_data
        for curve in active_obj.mi_curves:
            for cur_point in curve.curve_points:
                if cur_point.point_id in self.display_bezier:
                    mi_draw_3d_polyline(self.display_bezier[cur_point.point_id], 2, (0.7,0.9,1.0,0.7))

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