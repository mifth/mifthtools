 
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


class MI_ExtrudePanel(bpy.types.Panel):
    bl_label = "Mira"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'


    def draw(self, context):
        layout = self.layout
        layout.operator("mira.draw_extrude", text="Draw Extrude")


class MRStartDraw(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.draw_extrude"
    bl_label = "DrawExtrude"
    bl_description = "Draw Extrude Test"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'LEFTMOUSE', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'SELECTMOUSE', 'MOUSEMOVE']

    extrude_center = None
    extrude_dir = None

    # curve tool mode
    tool_modes = ('IDLE', 'DRAW', 'ADD_POINT')
    tool_mode = 'IDLE'

    extrude_step = FloatProperty(default=1.0)
    manipulator = None


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        # make picking
        if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
            if event.value == 'PRESS':
                if self.tool_mode == 'IDLE':
                    m_coords = event.mouse_region_x, event.mouse_region_y
                    do_pick = mi_pick_extrude_point(self.extrude_center, context, m_coords)

                    if do_pick:
                        self.tool_mode = 'DRAW'
                        return {'RUNNING_MODAL'}

            elif event.value == 'RELEASE':
                if self.tool_mode == 'DRAW':
                    self.extrude_dir = None  # clear dir
                    self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}

            return {'RUNNING_MODAL'}

        if self.tool_mode == 'DRAW':
            m_coords = event.mouse_region_x, event.mouse_region_y
            new_pos = get_mouse_on_plane(context, self.extrude_center, m_coords)

            if (new_pos-self.extrude_center).length >= self.extrude_step:
                bpy.ops.mesh.extrude_region_move()
                offset_move = new_pos-self.extrude_center
                bpy.ops.transform.translate(value=(offset_move.x, offset_move.y, offset_move.z), proportional='DISABLED')
                self.extrude_center = new_pos

                if self.extrude_dir is not None:
                    rv3d = context.region_data
                    offset_dir = offset_move.copy().normalized()
                    move_angle = self.extrude_dir.angle(offset_dir)
                    cam_dir = rv3d.view_rotation * Vector((0.0, 0.0, -1.0))
                    up_vec = cam_dir.cross(self.extrude_dir).normalized()

                    if up_vec.angle(offset_dir) > math.radians(90):
                        move_angle = -move_angle

                    bpy.ops.transform.rotate(value=move_angle, axis=cam_dir, proportional='DISABLED')

                self.extrude_dir = offset_move.normalized()  # offset vector has been changed/normalized

            return {'RUNNING_MODAL'}

        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            finish_extrude(self, context)
            #bpy.types.SpaceView3D.draw_handler_remove(self.mi_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_extrude_handle_2d, 'WINDOW')

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

            reset_params(self)
            self.manipulator = context.space_data.show_manipulator
            context.space_data.show_manipulator = False

            obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(obj.data)
            sel_verts = [v for v in bm.verts if v.select]

            if len(sel_verts) == 0:
                self.report({'WARNING'}, "No Selection!!!")
                return {'CANCELLED'}
            else:
                self.extrude_center = get_vertices_center(sel_verts)

            self.mi_extrude_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_extrude_draw_2d, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)


            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


def reset_params(self):
    self.extrude_center = None
    self.extrude_dir = None
    self.tool_mode = 'IDLE'


def finish_extrude(self, context):
    context.space_data.show_manipulator = self.manipulator


def mi_extrude_draw_2d(self, context):
    active_obj = context.scene.objects.active
    region = context.region
    rv3d = context.region_data
    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, self.extrude_center)

    p_col = (0.5,0.8,1.0,1.0)
    mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, p_col)


def get_mouse_on_plane(context, plane_pos, mouse_coords):
    region = context.region
    rv3d = context.region_data
    cam_dir = rv3d.view_rotation * Vector((0.0, 0.0, -1.0))
    #cam_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, (region.width/2.0, region.height/2.0))
    mouse_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_coords)
    mouse_dir = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_coords)
    new_pos = mathu.geometry.intersect_line_plane(mouse_pos, mouse_pos+(mouse_dir*10000.0), plane_pos, cam_dir, False)
    if new_pos:
        return new_pos

    return None


def mi_pick_extrude_point(point, context, mouse_coords):
    region = context.region
    rv3d = context.region_data

    #for cu_point in curve.curve_points:
    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, point)
    length = (point_pos_2d - Vector(mouse_coords)).length
    if length <= 9.0:
        return True

    return False


# TODO Move it into utilities method. As Deform class has the same method.
def get_vertices_center(verts):
    #if obj.mode == 'EDIT':
        #bm.verts.ensure_lookup_table()
    x_min = verts[0].co.x
    x_max = verts[0].co.x
    y_min = verts[0].co.y
    y_max = verts[0].co.y
    z_min = verts[0].co.z
    z_max = verts[0].co.z

    for vert in verts:
        if vert.co.x > x_max:
            x_max = vert.co.x
        if vert.co.x < x_min:
            x_min = vert.co.x
        if vert.co.y > y_max:
            y_max = vert.co.y
        if vert.co.y < y_min:
            y_min = vert.co.y
        if vert.co.z > z_max:
            z_max = vert.co.z
        if vert.co.z < z_min:
            z_min = vert.co.z

    x_orig = ((x_max-x_min) / 2.0) + x_min
    y_orig = ((y_max-y_min) / 2.0) + y_min
    z_orig = ((z_max-z_min) / 2.0) + z_min

    return Vector((x_orig, y_orig, z_orig))


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