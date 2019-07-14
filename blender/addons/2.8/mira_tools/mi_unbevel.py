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
from math import *
import mathutils as mathu

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from . import mi_utils_base as ut_base
from . import mi_looptools as loop_t
from mathutils import Vector, Matrix


class MI_OT_Unbevel(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "mira.unbevel"
    bl_label = "Unbevel"
    bl_description = "Unbevel"
    bl_options = {'REGISTER', 'UNDO'}

    #reset_values: BoolProperty(default=False)
    unbevel_value: bpy.props.FloatProperty(name="Unbevel Value", description="Unbevel Value", default=1.0, min=0.0)

    def execute(self, context):

        #if self.reset_values is True:
            #self.reset_all_values()

        active_obj = context.active_object

        bm = bmesh.from_edit_mesh(active_obj.data)
        bm.verts.ensure_lookup_table()
        #verts = [v for v in bm.verts if v.select]

        # get loops
        loops = loop_t.get_connected_input(bm)
        loops = loop_t.check_loops(loops, bm)

        if not loops:
            #self.report({'WARNING'}, "No Loops!")
            #return {'CANCELLED'}

            b_edges = [edge for edge in bm.edges if edge.select]

        #obj_matrix = active_obj.matrix_world
        #obj_matrix_inv = obj_matrix.inverted()

        if self.unbevel_value != 1:

            degree_90 = 1.5708

            if loops:
                for loop in loops:
                    if loop[1] is True:
                        continue

                    loop_verts = []

                    for ind in loop[0]:
                        loop_verts.append(bm.verts[ind])

                    v1 = (loop_verts[1].co - loop_verts[0].co).normalized()
                    v2 = (loop_verts[2].co - loop_verts[1].co).normalized()
                    angle_1 = v1.angle(v2) / 2

                    v3 = (loop_verts[-2].co - loop_verts[-1].co).normalized()
                    v4 = (loop_verts[-3].co - loop_verts[-2].co).normalized()
                    angle_2 = v1.angle(v2) / 2

                    rot_dir = v1.cross(v2).normalized()
                    rot_mat = Matrix.Rotation(-angle_1, 3, rot_dir)
                    rot_mat_2 = Matrix.Rotation((angle_2 - degree_90), 3, rot_dir)
                    v1_nor = ((rot_mat @ v1).normalized() * 10000) + loop_verts[0].co
                    v3_nor = (rot_mat_2 @ v3).normalized()

                    scale_pos = mathu.geometry.intersect_line_plane(loop_verts[0].co, v1_nor, loop_verts[-1].co, v3_nor)

                    for vert in loop_verts:
                        vert.co = scale_pos.lerp(vert.co, self.unbevel_value)

                if self.unbevel_value == 0:
                    bpy.ops.mesh.merge(type='COLLAPSE')

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

            elif b_edges:
                b_edges_pos = []
                b_edgess_ids = [edge.index for edge in b_edges]

                for edge in b_edges:
                    verts = edge.verts

                    # fix normals
                    if len(edge.link_faces) > 1:
                        linked_edges_0 = 0
                        linked_edges_1 = 0

                        for edge2 in edge.link_faces[0].edges:
                            if edge2.index in b_edgess_ids:
                                linked_edges_0 += 1

                        for edge2 in edge.link_faces[1].edges:
                            if edge2.index in b_edgess_ids:
                                linked_edges_1 += 1                            

                        if len(edge.link_faces[0].verts) > 4 or linked_edges_0 < 2:
                            ed_normal = edge.link_faces[1].normal
                        elif len(edge.link_faces[1].verts) > 4 or linked_edges_1 < 2:
                            ed_normal = edge.link_faces[0].normal
                        else:
                            ed_normal = edge.link_faces[0].normal.lerp(edge.link_faces[1].normal, 0.5)

                        fix_dir = ed_normal.cross( (verts[0].co - verts[1].co).normalized() )
                        v0_nor = mathu.geometry.intersect_line_plane(verts[0].normal + (fix_dir * 2), verts[0].normal - (fix_dir * 2), Vector((0,0,0)), fix_dir).normalized()
                        v1_nor = mathu.geometry.intersect_line_plane(verts[1].normal + (fix_dir * 2), verts[1].normal - (fix_dir * 2), Vector((0,0,0)), fix_dir).normalized()
                        #nor_dir = ed_normal

                    else:
                        v0_nor = verts[0].normal
                        v1_nor = verts[1].normal
                        #nor_dir = v0_nor.lerp(v1_nor, 0.5).normalized()

                    # base math
                    nor_dir = v0_nor.lerp(v1_nor, 0.5).normalized()
                    side_dir_2 = (verts[0].co - verts[1].co).normalized()
                    side_dir_2.negate()
                    side_dir_1 = nor_dir.cross(side_dir_2).normalized()
                    #side_dir_2 = (verts[0].co - verts[1].co).normalized()
                    #side_dir_2 = nor_dir.cross(side_dir_1).normalized()

                    pos_between = verts[0].co.lerp(verts[1].co, 0.5)
                    angle_between_1 = v0_nor.angle(nor_dir)
                    angle_between_2 = v1_nor.angle(nor_dir)

                    rot_mat = Matrix.Rotation((-angle_between_1 * 2) - degree_90, 3, side_dir_1)
                    rot_mat_2 = Matrix.Rotation((angle_between_1 * 2) + (degree_90 * 2), 3, side_dir_1)
                    dir_1 = ((rot_mat @ nor_dir).normalized() * 10000) + verts[0].co
                    dir_2 = (rot_mat_2 @ nor_dir).normalized()

                    scale_pos = mathu.geometry.intersect_line_plane(verts[0].co, dir_1, verts[1].co, dir_2)
                    b_edges_pos.append((verts[0], scale_pos))
                    b_edges_pos.append((verts[1], scale_pos))

                for v_data in b_edges_pos:
                    v_data[0].co = v_data[1].lerp(v_data[0].co, self.unbevel_value)

                if self.unbevel_value == 0:
                    bpy.ops.mesh.merge(type='COLLAPSE')

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

        return {'FINISHED'}
