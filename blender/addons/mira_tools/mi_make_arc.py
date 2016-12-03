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
    upvec_offset = FloatProperty(default=0.0)

    rotate_axis = bpy.props.FloatVectorProperty(name="Rotate Axis", description="Rotate Axis", default=(0.0, 0.0, 1.0), size=3)

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
                if isinstance(bm.select_history[0], bmesh.types.BMVert):
                    for element in bm.select_history:
                        first_indexes.append(element.index)
                elif isinstance(bm.select_history[0], bmesh.types.BMEdge):
                    for element in bm.select_history:
                        el_verts = element.verts
                        first_indexes.append(el_verts[0].index)
                        first_indexes.append(el_verts[1].index)

                for loop in loops:
                    loop_verts = []

                    for ind in loop[0]:
                        loop_verts.append(bm.verts[ind])

                    #  for the case if we need to reverse it
                    if loop[0][-1] in first_indexes:
                        loop_verts = list(reversed(loop_verts))

                    # reverse again for the direction
                    if self.reverse_direction is True:
                        loop_verts = list(reversed(loop_verts))

                    # positions
                    first_vert_pos = active_obj.matrix_world * loop_verts[0].co
                    last_vert_pos = active_obj.matrix_world * loop_verts[-1].co
                    rot_dir = Vector((self.rotate_axis[0], self.rotate_axis[1], self.rotate_axis[2])).normalized()

                    sidevec = (first_vert_pos - last_vert_pos).normalized()
                    upvec = rot_dir.cross(sidevec).normalized()

                    loop_centr = first_vert_pos.lerp(last_vert_pos, 0.5)
                    loop_centr += ( self.upvec_offset * upvec * (first_vert_pos - loop_centr).length )

                    loop_angle = (first_vert_pos - loop_centr).normalized().angle((last_vert_pos - loop_centr).normalized())
                    if self.upvec_offset > 0:
                        loop_angle = math.radians( (360 - math.degrees(loop_angle)) )

                    for i, vert in enumerate(loop_verts):
                        if i != 0:
                            rot_angle = loop_angle * (i / (len(loop_verts) - 1))
                            #rot_angle = math.radians(rot_angle)
                            rot_mat = Matrix.Rotation(rot_angle, 3, rot_dir)

                            vert_pos = (rot_mat * (first_vert_pos - loop_centr)) + loop_centr
                            vert.co = active_obj.matrix_world.inverted() * vert_pos

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}

