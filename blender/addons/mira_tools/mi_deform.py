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
from mathutils import Vector, Matrix


class MI_Deform(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.deformer"
    bl_label = "Deformer"
    bl_description = "Deformer"
    bl_options = {'REGISTER', 'UNDO'}

    reset_values = BoolProperty(default=False)
    taper_value = FloatProperty(default=0.0, min=-1000.0, max=1.0)
    twist_angle = FloatProperty(default=0.0)
    bend_angle = FloatProperty(default=0.0)
    offset_rotation = FloatProperty(default=0.0)
    offset_axis = FloatProperty(default=0.0)
    bend_scale = FloatProperty(default=1.0)

    # selected_verts = BoolProperty(default=True)
    deform_axis = EnumProperty(
        items=(('X', 'X', ''),
               ('Y', 'Y', ''),
               ('Z', 'Z', ''),
               ),
        default = 'X'
    )
    # deform_direction = EnumProperty(
        # items=(('Top', 'Top', ''),
               #('Bottom', 'Bottom', ''),
               #('Left', 'Left', ''),
               #('Right', 'Right', ''),
               #),
        # default = 'Top'
    #)

    def execute(self, context):

        active_obj = context.scene.objects.active

        # reset properties
        if self.reset_values is True:
            reset_all_values(self)

        deform_obj(active_obj, context, self)

        return {'FINISHED'}

    def invoke(self, context, event):
        # if context.area.type == 'VIEW_3D':
            # change startup
            # self.select_mouse_mode = context.user_preferences.inputs.select_mouse
            # context.user_preferences.inputs.select_mouse = 'RIGHT'

        return self.execute(context)
        # else:
            # self.report({'WARNING'}, "View3D not found, cannot run operator")
            # return {'CANCELLED'}


def reset_all_values(self):
    self.taper_value = 0.0
    self.twist_angle = 0.0
    self.bend_angle = 0.0
    self.offset_rotation = 0.0
    self.offset_axis = 0.0
    self.bend_scale = 1.0
    self.deform_axis = 'X'
    self.reset_values = False


def deform_obj(active_obj, context, self):
    offset_rotation = 0.2
    offset_axis = 5.0
    bend_scale = 0.7

    # get vertices
    verts = None
    if active_obj.mode == 'EDIT':
        # this works only in edit mode,
        bm = bmesh.from_edit_mesh(active_obj.data)

        verts = [v for v in bm.verts if v.select]
        if len(verts) == 0:
            verts = [v for v in bm.verts if v.hide is False]

    else:
        # this works only in object mode,
        verts = [v for v in active_obj.data.vertices if v.select]
        if len(verts) == 0:
            verts = [v for v in active_obj.data.vertices if v.hide is False]

    # TODO Move it into utilities method. As Extrude class has the same
    # min/max.
    if verts:
        if active_obj.mode == 'EDIT':
            bm.verts.ensure_lookup_table()
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

        x_orig = ((x_max - x_min) / 2.0) + x_min
        y_orig = ((y_max - y_min) / 2.0) + y_min
        z_orig = z_min
        if self.deform_axis == 'Z':
            y_orig = y_min
            z_orig = ((z_max - z_min) / 2.0) + z_min

        rot_origin = Vector((x_orig, y_orig, z_orig))

        visual_max = z_max - z_min
        if self.deform_axis == 'Z':
            visual_max = y_max - y_min

        if visual_max != 0.0:
            for vert in verts:
                vec = vert.co.copy()
                visual_up_pos = None
                if self.deform_axis != 'Z':
                    visual_up_pos = vec.z - z_min
                else:
                    visual_up_pos = vec.y - y_min

                # TAPER CODE
                # scale the vert
                if self.taper_value != 0:
                    taper_value = (
                        (self.taper_value) * (visual_up_pos / visual_max))
                    if self.deform_axis != 'Z':
                        vert.co.xy -= (vert.co.xy - rot_origin.xy) * taper_value
                    else:
                        vert.co.xz -= (vert.co.xz - rot_origin.xz) * taper_value

                # TWIST CODE
                # rotate the vert
                if self.twist_angle != 0:
                    twist_angle = self.twist_angle * (visual_up_pos / visual_max)
                    # if self.deform_axis == 'X':
                        # rot_angle = -rot_angle
                    rot_mat = None
                    if self.deform_axis != 'Z':
                        rot_mat = Matrix.Rotation(twist_angle, 3, 'Z')
                    else:
                        rot_mat = Matrix.Rotation(twist_angle, 3, 'Y')
                    vert.co = rot_mat * (vert.co - rot_origin) + rot_origin

                # BEND CODE
                beta = math.radians(self.bend_angle * (visual_up_pos / visual_max))
                if beta != 0:
                    final_offset = visual_up_pos * self.offset_rotation
                    if beta < 0:
                        final_offset = -final_offset

                    move_to_rotate = (
                        (visual_up_pos / beta) + final_offset) * self.bend_scale
                    if self.deform_axis == 'X':
                        vert.co.y -= move_to_rotate
                    elif self.deform_axis == 'Y' or self.deform_axis == 'Z':
                        vert.co.x -= move_to_rotate

                    if self.deform_axis != 'Z':
                        vert.co.z = rot_origin.z
                    else:
                        vert.co.y = rot_origin.y

                    # rotate the vert
                    rot_angle = beta
                    if self.deform_axis == 'X' or self.deform_axis == 'Z':
                        rot_angle = -rot_angle
                    rot_mat = Matrix.Rotation(rot_angle, 3, self.deform_axis)
                    vert.co = rot_mat * (vert.co - rot_origin) + rot_origin

                    # back the rotation offset
                    back_offset = (visual_up_pos / (beta)) * self.bend_scale
                    if self.deform_axis == 'X':
                        vert.co.y += back_offset
                    elif self.deform_axis == 'Y' or self.deform_axis == 'Z':
                        vert.co.x += back_offset

                    # offset axys
                    move_offset = self.offset_axis * (visual_up_pos / visual_max)
                    if self.deform_axis == 'X':
                        vert.co.x += move_offset
                    elif self.deform_axis == 'Y':
                        vert.co.y += move_offset
                    elif self.deform_axis == 'Z':
                        vert.co.z += move_offset

    # active_obj.data.update()
    #bpy.ops.mesh.normals_make_consistent()  # recalculate normals
    #bpy.ops.object.editmode_toggle()
    #bpy.ops.object.editmode_toggle()
    bm.normal_update()
    bmesh.update_edit_mesh(active_obj.data)
