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
import math
import mathutils as mathu

from bpy.props import *
from bpy.types import Operator, AddonPreferences


from . import mi_utils_base as ut_base
from . import mi_looptools as loop_t
from mathutils import Vector, Matrix


class MI_Make_Arc(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.make_arc"
    bl_label = "Make Arc"
    bl_description = "Make Arc"
    bl_options = {'REGISTER', 'UNDO'}

    reverse_direction = BoolProperty(default=False)
#    twist_angle = FloatProperty(default=0.0)


    #deform_axis = EnumProperty(
        #items=(('X', 'X', ''),
               #('Y', 'Y', ''),
               #('Z', 'Z', ''),
               #),
        #default = 'X'
    #)


    def invoke(self, context, event):
        # if context.area.type == 'VIEW_3D':
            # change startup
            # self.select_mouse_mode = context.user_preferences.inputs.select_mouse
            # context.user_preferences.inputs.select_mouse = 'RIGHT'

        return self.execute(context)
        # else:
            # self.report({'WARNING'}, "View3D not found, cannot run operator")
            # return {'CANCELLED'}


    def execute(self, context):

        active_obj = context.scene.objects.active

        if active_obj.mode == 'EDIT':
            # this works only in edit mode,
            bm = bmesh.from_edit_mesh(active_obj.data)
            bm.verts.ensure_lookup_table()
            #verts = [v for v in bm.verts if v.select]

            # get loops
            loops = loop_t.get_connected_input(bm)
            loops = loop_t.check_loops(loops, bm)

            if loops:
                first_indexes = []
                for element in bm.select_history:
                    first_indexes.append(element.index)

                for loop in loops:
                    loop_verts = []

                    for ind in loop[0]:
                        loop_verts.append(bm.verts[ind])

                    loop_centr = ut_base.get_vertices_center(loop_verts, active_obj, False)

                    #  for the case if we need to reverse it
                    if loop[0][-1] in first_indexes:
                        loop_verts = list(reversed(loop_verts))

                    # reverse again for the direction
                    if self.reverse_direction is True:
                        loop_verts = list(reversed(loop_verts))

                    for i, vert in enumerate(loop_verts):
                        if i != 0:
                            rot_angle = 180 * (i / (len(loop_verts) - 1))
                            rot_dir = Vector( (0.0, 0.0, 1.0) )
                            rot_mat = Matrix.Rotation(math.radians(rot_angle), 3, rot_dir)

                            vert.co = (rot_mat * (loop_verts[0].co - loop_centr)) + loop_centr

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}

