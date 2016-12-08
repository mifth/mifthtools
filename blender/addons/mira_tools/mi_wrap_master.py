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

from bpy.props import *
from bpy.types import Operator, AddonPreferences

import math
import mathutils as mathu
import random
from mathutils import Vector, Matrix


from . import mi_utils_base as ut_base

class MI_Wrap_Object(bpy.types.Operator):
    bl_idname = "mira.wrap_object"
    bl_label = "Wrap Object"
    bl_description = "Wrap Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        wrap_obj = context.scene.objects.active

        if wrap_obj and wrap_obj.select and wrap_obj.data.uv_layers:
            uvs = wrap_obj.data.uv_layers.active.data

            new_mesh = bpy.data.meshes.new(wrap_obj.data.name + '_WRAP')
            new_obj = bpy.data.objects.new(wrap_obj.name + '_WRAP', new_mesh)
            new_obj.show_wire = True
            context.scene.objects.link(new_obj)

            new_obj.select = True
            context.scene.objects.active = new_obj
                        
            # get verts and faces
            out_verts=[]
            out_faces=[]
            for face in wrap_obj.data.polygons:
                oface=[]   

                for vert, loop in zip(face.vertices, face.loop_indices):
                    coord = wrap_obj.data.vertices[vert].normal
                    normal = wrap_obj.data.vertices[vert].co
                    uv = wrap_obj.data.uv_layers.active.data[loop].uv 
                    out_verts.append((uv.x, 0, uv.y))
                    oface.append(loop)

                out_faces.append(oface)

            # create mesh
            new_obj.data.from_pydata(out_verts, [], out_faces)
            new_obj.data.update()

        return {'FINISHED'}


class MI_Wrap_Master(bpy.types.Operator):
    bl_idname = "mira.wrap_master"
    bl_label = "Wrap Master"
    bl_description = "Wrap Master"
    bl_options = {'REGISTER', 'UNDO'}

    deform_normal = EnumProperty(
        items=(('Face', 'Face', ''),
               ('FaceAndVert', 'FaceAndVert', '')
               ),
        default = 'FaceAndVert'
    )

    def execute(self, context):
        selected_objects = context.selected_objects
        uv_obj = context.scene.objects.active
        wrap_name = uv_obj.name.replace('_WRAP', '')

        if len(selected_objects) >= 2 and wrap_name in context.scene.objects:
            wrap_obj = context.scene.objects[wrap_name]

            bvh = mathu.bvhtree.BVHTree.FromObject(uv_obj, context.scene)

            uv_matrix = uv_obj.matrix_world
            uv_matrix_inv = uv_matrix.inverted()
            wrap_matrix = wrap_obj.matrix_world
            wrap_matrix_inv = wrap_matrix.inverted()

            for the_obj in selected_objects:
                if the_obj != uv_obj:
                    for vert in the_obj.data.vertices:
                        vert_pos = the_obj.matrix_world * vert.co.copy()

                        # near
                        vert_pos_zero = vert_pos.copy()
                        vert_pos_zero[1] = 0  # set position of uv_obj!!!
                        vert_pos_zero = uv_obj.matrix_world.inverted() * vert_pos_zero
                        nearest = bvh.find_nearest(vert_pos_zero)

                        if nearest and nearest[2] is not None:
                            near_face = uv_obj.data.polygons[nearest[2]]
                            near_center = uv_obj.matrix_world * near_face.center

                            near_axis1 = ut_base.get_normal_world(near_face.normal, uv_matrix, uv_matrix_inv)


                            near_v1 = uv_obj.matrix_world * uv_obj.data.vertices[near_face.vertices[0]].co
                            near_v2 = uv_obj.matrix_world * uv_obj.data.vertices[near_face.vertices[1]].co
                            near_axis2 = (near_v1 - near_v2).normalized()

                            near_axis3 = near_axis1.cross(near_axis2).normalized()

                            dist_1 = mathu.geometry.distance_point_to_plane(vert_pos, near_center, near_axis1)
                            dist_2 = mathu.geometry.distance_point_to_plane(vert_pos, near_center, near_axis2)
                            dist_3 = mathu.geometry.distance_point_to_plane(vert_pos, near_center, near_axis3)

                            # wrap
                            wrap_face = wrap_obj.data.polygons[nearest[2]]
                            wrap_center = wrap_obj.matrix_world * wrap_face.center

                            wrap_axis1 = ut_base.get_normal_world(wrap_face.normal, wrap_matrix, wrap_matrix_inv)

                            wrap_v1 = wrap_obj.matrix_world * wrap_obj.data.vertices[wrap_face.vertices[0]].co
                            wrap_v2 = wrap_obj.matrix_world * wrap_obj.data.vertices[wrap_face.vertices[1]].co
                            wrap_axis2 = (wrap_v1 - wrap_v2).normalized()

                            wrap_axis3 = wrap_axis1.cross(wrap_axis2).normalized()

                            # move to face
                            relative_scale = (wrap_v1 - wrap_center).length / (near_v1 - near_center).length
                            new_vert_pos = wrap_center + (wrap_axis2 * dist_2 * relative_scale) + (wrap_axis3 * dist_3 * relative_scale)
                            new_vert_pos_loc = wrap_obj.matrix_world.inverted() * new_vert_pos

                            if self.deform_normal == 'FaceAndVert':
                                vert2_min = None
                                vert2_min_dist = None
                                for vert2_id in wrap_face.vertices:
                                    vert2 = wrap_obj.data.vertices[vert2_id]
                                    v2_dist = (vert2.co - new_vert_pos_loc).length

                                    if not vert2_min:
                                        vert2_min = vert2
                                        vert2_min_dist = v2_dist
                                    elif vert2_min_dist > v2_dist:
                                        vert2_min = vert2
                                        vert2_min_dist = v2_dist

                                vert2_min_nor = ut_base.get_normal_world(vert2_min.normal, wrap_matrix, wrap_matrix_inv)
                                vert2_pos_world = wrap_obj.matrix_world * vert2_min.co

                                mix_val = 0.0
                                mix_v1 = (new_vert_pos - wrap_center).length
                                mix_v2 = (vert2_pos_world - wrap_center).length
                                if mix_v2 != 0:
                                    mix_val = mix_v1 / mix_v2

                                wrap_normal = wrap_axis1.lerp(vert2_min_nor, mix_val).normalized()

                            else:
                                wrap_normal = wrap_axis1

                            # move from normal
                            new_vert_pos += (wrap_normal * dist_1 * relative_scale)

                            vert.co = the_obj.matrix_world.inverted() * new_vert_pos

                    the_obj.data.update()

        return {'FINISHED'}