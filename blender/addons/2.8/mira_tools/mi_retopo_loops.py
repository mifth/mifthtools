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

class MI_OT_Wrap_Object(bpy.types.Operator):
    bl_idname = "mira.retopo_loops"
    bl_label = "Retopo Loops"
    bl_description = "Retopo Loops"
    bl_options = {'REGISTER', 'UNDO'}

    retpo_mode: EnumProperty(
        items=(('Normal', 'Normal', ''),
               ('Generic', 'Generic', '')
               ),
        default='Generic'
    )

    #reset_values: BoolProperty(default=False)
    cuts_number: bpy.props.IntProperty(name="Cuts Number", description="Cuts Number for Generic Mode", default=10, min=2)
    verts_number: bpy.props.IntProperty(name="Verts Number", description="Verts Number for Cuts", default=8, min=3)
    rotate_loops: bpy.props.IntProperty(name="Rotate Loops", description="Cuts Number for Generic Mode", default=0, min=-360, max=360)


    def execute(self, context):
        sel_objs = context.selected_objects.copy()
        #wrap_obj = context.active_object

        curve_settings = context.scene.mi_settings

        # get meshes for snapping
        if sel_objs:
            for obj in sel_objs:
                obj.hide_viewport = True

            meshes_array = ut_base.get_obj_dup_meshes(None, curve_settings.convert_instances, context)

            for obj in sel_objs:
                obj.hide_viewport = False

        if not sel_objs and meshes_array:
            self.report({'WARNING'}, "Please, Select Objects for Loops and Add Some Hipoly Objects!")
            return {'CANCELLED'}
        else:

            generic_sel_objs = []

            if self.retpo_mode == 'Generic':
                distances = []
                max_dist = 0

                # get distances
                for idx, obj in enumerate(sel_objs):
                    if idx == 0:
                        distances.append(0)
                    else:
                        dist = (obj.location - sel_objs[idx - 1].location).length 
                        max_dist += dist
                        distances.append(max_dist)

                # create new generic objects
                for obj_count in range(self.cuts_number):
                    count_length = (obj_count/(self.cuts_number - 1)) * max_dist

                    obj_count_pos = None
                    obj_count_rot = None
                    obj_count_scale = None

                    if obj_count == 0:
                        obj_count_pos = sel_objs[0].location.copy()
                        obj_count_rot = sel_objs[0].rotation_euler.copy()
                        obj_count_scale = sel_objs[0].scale.copy()

                    elif obj_count == self.cuts_number - 1:
                        obj_count_pos = sel_objs[-1].location.copy()
                        obj_count_rot = sel_objs[-1].rotation_euler.copy()
                        obj_count_scale = sel_objs[-1].scale.copy()

                    else:
                        for idx, dist in enumerate(distances):
                            if dist > count_length:
                                obj1 = sel_objs[idx]
                                obj2 = sel_objs[idx - 1]
                                count_length_2 = (count_length - distances[idx-1]) / (dist - distances[idx-1])

                                obj_count_pos = obj2.location.lerp(obj1.location, count_length_2)
                                obj_count_rot = Vector(obj2.rotation_euler).lerp(Vector(obj1.rotation_euler), count_length_2)
                                obj_count_scale = obj2.scale.lerp(obj1.scale, count_length_2)
                                break

                    bpy.ops.object.select_all(action='DESELECT')
                    sel_objs[0].select_set(True)

                    # create new prims
                    bpy.ops.mesh.primitive_circle_add(vertices=self.verts_number, radius=1.0, enter_editmode=False)
                    new_gen_obj = context.active_object
                    new_gen_obj.location = obj_count_pos
                    new_gen_obj.rotation_euler = obj_count_rot
                    new_gen_obj.scale = obj_count_scale
                    generic_sel_objs.append(new_gen_obj)
                    
            # create new prims
            else:
                for obj in sel_objs:
                    bpy.ops.object.select_all(action='DESELECT')
                    bpy.ops.mesh.primitive_circle_add(vertices=self.verts_number, radius=1.0, enter_editmode=False)
                    new_gen_obj = context.active_object
                    new_gen_obj.location = obj.location.copy()
                    new_gen_obj.rotation_euler = obj.rotation_euler.copy()
                    new_gen_obj.scale = obj.scale.copy()
                    generic_sel_objs.append(new_gen_obj)

            if self.rotate_loops != 0:
                for obj in generic_sel_objs:
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.ops.transform.rotate(value=math.radians(self.rotate_loops), orient_axis='Z', orient_type='LOCAL', orient_matrix_type='LOCAL', constraint_axis=(False, False, True), use_proportional_edit=False, release_confirm=False)

            bpy.ops.object.select_all(action='DESELECT')
            for obj in generic_sel_objs:
                obj.select_set(True)

            context.view_layer.objects.active = context.selected_objects[0]

            bpy.ops.object.make_single_user(type='SELECTED_OBJECTS', object=True, obdata=True, material=False, animation=False)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            bpy.ops.object.join()

            retop_obj = context.active_object
            retop_obj.show_in_front = True
            retop_obj.show_wire = True
            #dg = bpy.context.evaluated_depsgraph_get() 
            #dg.update()

            bpy.ops.object.editmode_toggle()
            bm = bmesh.from_edit_mesh(retop_obj.data)

            bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='EDGE')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.bridge_edge_loops()

            # snap verts
            new_positions = []
            for vert in bm.verts:
                vert_nor = vert.normal.copy()
                vert_nor.negate()
                best_obj, hit_normal, hit_position = ut_base.get_3dpoint_raycast(context, meshes_array, vert.co, vert_nor)

                if hit_position:
                    new_positions.append(hit_position)
                else:
                    new_positions.append(None)

            # set positions
            for idx, vert in enumerate(bm.verts):
                if new_positions[idx]:
                    vert.co = new_positions[idx]

            bpy.ops.object.editmode_toggle()

            #retop_obj.data.from_pydata(out_verts, [], out_faces)
            retop_obj.data.update()

        return {'FINISHED'}


