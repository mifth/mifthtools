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


# Settings
class MI_MakeArc_Settings(bpy.types.PropertyGroup):
    arc_axis = bpy.props.FloatVectorProperty(name="Arc Axis", description="Arc Axis", default=(0.0, 0.0, 1.0), size=3)


class MI_Make_Arc_Axis(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.make_arc_get_axis"
    bl_label = "Arc Axis From Selected Face"
    bl_description = "Arc Axis From Selected Face"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.verts.ensure_lookup_table()

        sel_polys = [f for f in bm.faces if f.select]
        if sel_polys:
            nor = sel_polys[0].normal.copy()
            world_nor = ut_base.get_normal_world(nor, active_obj.matrix_world, active_obj.matrix_world.inverted())
            context.scene.mi_makearc_settings.arc_axis = world_nor

        return {'FINISHED'}


class MI_Make_Arc(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.make_arc"
    bl_label = "Make Arc"
    bl_description = "Make Arc"
    bl_options = {'REGISTER', 'UNDO'}

    reset_values = BoolProperty(default=False)
    reverse_direction = BoolProperty(default=False)

    spread_mode = EnumProperty(
        items=(('Normal', 'Normal', ''),
               ('Even', 'Even', '')
               ),
        default = 'Normal'
    )

    direction_vector = EnumProperty(
        items=(('Custom', 'Custom', ''),
               ('Middle', 'Middle', ''),
               ('MiddleCrossed', 'MiddleCrossed', '')
               ),
        default = 'Custom'
    )

    upvec_offset = FloatProperty(name="Offset", description="Offset Arc", default=0.0)
    scale_arc = FloatProperty(name="Scale", description="Scale Arc", default=0.0)
    rotate_arc_axis = bpy.props.FloatProperty(name="Rotate", description="Rotate Arc Axis", default=0)
    rotate_axis = bpy.props.FloatVectorProperty(name="Rotate Axis", description="Rotate Axis", default=(0.0, 0.0, 1.0), size=3)


    def reset_all_values(self):
        self.reverse_direction = False
        self.spread_mode = 'Normal'
        self.direction_vector = 'Custom'
        self.upvec_offset = 0.0
        self.scale_arc = 0.0
        self.rotate_arc_axis = 0.0
        self.reset_values = False


    def invoke(self, context, event):

        self.rotate_axis = context.scene.mi_makearc_settings.arc_axis
        return self.execute(context)


    def execute(self, context):

        if self.reset_values is True:
            self.reset_all_values()

        active_obj = context.scene.objects.active

        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.verts.ensure_lookup_table()
        #verts = [v for v in bm.verts if v.select]

        # get loops
        loops = loop_t.get_connected_input(bm)
        loops = loop_t.check_loops(loops, bm)

        if not loops:
            self.report({'WARNING'}, "No Loops!")
            return {'CANCELLED'}

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
            if loop[1] is True:
                continue

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

            loop_centr_orig = first_vert_pos.lerp(last_vert_pos, 0.5)
            relative_dist = (first_vert_pos - loop_centr_orig).length
            sidevec = (first_vert_pos - last_vert_pos).normalized()

            obj_matrix = active_obj.matrix_world
            obj_matrix_inv = obj_matrix.inverted()

            if self.direction_vector == 'Custom':
                rot_dir = Vector((self.rotate_axis[0], self.rotate_axis[1], self.rotate_axis[2])).normalized()
            elif self.direction_vector == 'MiddleCrossed':
                middle_nor = loop_verts[int(len(loop_verts) / 2)].normal.copy().normalized()
                middle_nor = ut_base.get_normal_world(middle_nor, obj_matrix, obj_matrix_inv)
                rot_dir = middle_nor.cross(sidevec).normalized()

                # fix only for MiddleCrossed
                if not self.reverse_direction:
                    rot_dir.negate()

            else:
                middle_nor = loop_verts[int(len(loop_verts) / 2)].normal.copy().normalized()
                middle_nor = ut_base.get_normal_world(middle_nor, obj_matrix, obj_matrix_inv)
                middle_nor = middle_nor.cross(sidevec).normalized()
                rot_dir = middle_nor.cross(sidevec).normalized()
                rot_dir.negate()

            upvec = rot_dir.cross(sidevec).normalized()
            loop_centr = ( self.upvec_offset * upvec * relative_dist ) + loop_centr_orig

            loop_angle = (first_vert_pos - loop_centr).normalized().angle((last_vert_pos - loop_centr).normalized())
            if self.upvec_offset > 0:
                loop_angle = math.radians( (360 - math.degrees(loop_angle)) )

            # even spread
            line_data = None
            if self.spread_mode == 'Even':
                world_verts = [active_obj.matrix_world * vert.co for vert in loop_verts]

                line_data = []
                line_length = 0.0
                for i, vec in enumerate(world_verts):
                    if i == 0:
                        line_data.append(0)
                    else:
                        line_length += (vec - world_verts[i-1]).length
                        line_data.append(line_length)

            # make arc!
            for i, vert in enumerate(loop_verts):
                if i != 0 and i != len(loop_verts)-1:
                    if self.spread_mode == 'Normal':
                        rot_angle = loop_angle * (i / (len(loop_verts) - 1))
                    else:
                        rot_angle = loop_angle * (line_data[i] / line_data[len(loop_verts)-1])

                    rot_mat = Matrix.Rotation(rot_angle, 3, rot_dir)
                    vert_pos = (rot_mat * (first_vert_pos - loop_centr)) + loop_centr

                    if self.scale_arc != 0:
                        vert_rel_dist = mathu.geometry.distance_point_to_plane(vert_pos, loop_centr_orig, upvec)
                        vert_rel_dist_max = self.upvec_offset + relative_dist

                        if vert_rel_dist != 0 and vert_rel_dist_max != 0:
                            vert_pos_offset = vert_rel_dist / vert_rel_dist_max
                            vert_pos += (self.scale_arc * upvec * vert_pos_offset * vert_rel_dist_max) 

                    # rotate arc
                    if self.rotate_arc_axis != 0:
                        rot_mat_2 = Matrix.Rotation(math.radians(self.rotate_arc_axis), 3, sidevec)
                        vert_pos = (rot_mat_2 * (vert_pos - loop_centr_orig)) + loop_centr_orig                            

                    vert.co = active_obj.matrix_world.inverted() * vert_pos

        bm.normal_update()
        bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}

