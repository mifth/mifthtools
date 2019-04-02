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
import string
import bmesh

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from bpy_extras import view3d_utils

import math
import mathutils as mathu
import random
from mathutils import Vector

from . import mi_utils_base as ut_base
from . import mi_color_manager as col_man
from . import mi_looptools as loop_t
from . import mi_inputs
from . import mi_widget_curve as c_widget


class MI_PL_LoopObject():

    # class constructor
    def __init__(self, selected_verts):

        self.loop_ids = []
        self.selected_verts = selected_verts  # Boolean, if the loop is from selected or not
        self.revert_prev_loops = False  # revert previous loops for face creation in some cases

class MI_PolyLoop(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.poly_loop"
    bl_label = "PolyLoop"
    bl_description = "Poly Loop Tool"
    bl_options = {'REGISTER', 'UNDO'}

    # curve tool mode
    tool_modes = ('IDLE', 'MOVE_POINT')
    tool_mode = 'IDLE'

    #all_curves = None
    #active_curve = None
    deform_mouse_pos = None

    picked_meshes = None

    # loops code
    id_layer = None
    id_value = None  # int
    all_loops_ids = None
    previous_loop_id = None  # int

    id_to_index = None  # get either first or last vert

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)

            mi_settings = context.scene.mi_settings
            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)

            # get loops
            loops_temp = loop_t.get_connected_input(bm)
            loops_temp = loop_t.check_loops(loops_temp, bm)

            if (loops_temp and len(loops_temp) == 1 and loops_temp[0][1] is False) or not loops_temp:
                reset_params(self, bm)

                self.manipulator = context.space_data.show_manipulator
                context.space_data.show_manipulator = False

                # change loops verts ids to custom ids
                if loops_temp:
                    new_loop = MI_PL_LoopObject(True)

                    for vert_id in loops_temp[0][0]:
                        vert = bm.verts[vert_id]
                        vert[self.id_layer] = self.id_value
                        new_loop.loop_ids.append(self.id_value)
                        self.id_value += 1

                    self.all_loops_ids.append(new_loop)  # add loop from selected

                self.all_loops_ids.append(MI_PL_LoopObject(False))  # add another empty loop

                # get meshes for snapping
                if mi_settings.surface_snap is True:
                    meshes_array = ut_base.get_obj_dup_meshes(mi_settings.snap_objects, mi_settings.convert_instances, context)
                    if meshes_array:
                        self.picked_meshes = meshes_array

                # Add the region OpenGL drawing callback
                # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
                #self.mi_pl_3d = bpy.types.SpaceView3D.draw_handler_add(mi_pl_draw_3d, args, 'WINDOW', 'POST_VIEW')
                self.mi_pl_2d = bpy.types.SpaceView3D.draw_handler_add(mi_pl_draw_2d, args, 'WINDOW', 'POST_PIXEL')

                context.window_manager.modal_handler_add(self)
                return {'RUNNING_MODAL'}

            else:
                #finish_work(self, context)
                self.report({'WARNING'}, "Please, select one non-closed loop!")
                return {'CANCELLED'}

        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        context.area.header_text_set("Shift+A: NewLoops, A: NewLoop, LeftClick: CreatePoint, X: DeletePoint, C: CreateTriangle, Ctrl+LeftClick: CreateTriangle2, Shift+Tab: SurfaceSnap")

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences
        mi_settings = context.scene.mi_settings

        m_coords = event.mouse_region_x, event.mouse_region_y
        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)

        region = context.region
        rv3d = context.region_data

        # check nearest id to index
        # this is to get loop direction
        if not self.all_loops_ids[-1].loop_ids and len(self.all_loops_ids) > 1:
            m_coords_vec = Vector(m_coords)
            first_id = self.all_loops_ids[-2].loop_ids[0]
            last_id = self.all_loops_ids[-2].loop_ids[-1]
            test_verts = ut_base.get_verts_from_ids([first_id, last_id], self.id_layer, bm)

            pos_3d_1 = active_obj.matrix_world * test_verts[0].co
            pos_2d_1 = view3d_utils.location_3d_to_region_2d(region, rv3d, pos_3d_1)
            pos_3d_2 = active_obj.matrix_world * test_verts[1].co
            pos_2d_2 = view3d_utils.location_3d_to_region_2d(region, rv3d, pos_3d_2)

            if pos_2d_1 and pos_2d_2:
                dist_1 = (m_coords_vec - pos_2d_1).length
                dist_2 = (m_coords_vec - pos_2d_2).length

                if dist_1 < dist_2:
                    self.id_to_index = (first_id, pos_2d_1)
                    self.all_loops_ids[-1].revert_prev_loops = False
                else:
                    self.id_to_index = (last_id, pos_2d_2)
                    self.all_loops_ids[-1].revert_prev_loops = True
            elif not pos_2d_1:
                self.id_to_index = (last_id, pos_2d_2)
                self.all_loops_ids[-1].revert_prev_loops = True                
            elif not pos_2d_2:
                self.id_to_index = (first_id, pos_2d_1)
                self.all_loops_ids[-1].revert_prev_loops = False

        else:
            self.id_to_index = None

        keys_pass = mi_inputs.get_input_pass(mi_inputs.pass_keys, addon_prefs.key_inputs, event)

        # Make Picking
        if self.tool_mode == 'IDLE' and event.value == 'PRESS' and keys_pass is False:
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                # get position
                new_point_pos = None
                if mi_settings.surface_snap is True and self.picked_meshes:
                    best_obj, hit_normal, hit_position = ut_base.get_mouse_raycast(context, self.picked_meshes, m_coords)
                    if hit_position:
                        new_point_pos = active_obj.matrix_world.inverted() * hit_position
                else:
                    cursor_loc = context.space_data.cursor_location
                    new_point_pos = ut_base.get_mouse_on_plane(context, cursor_loc, None, m_coords)
                    new_point_pos = active_obj.matrix_world.inverted() * new_point_pos

                # create vert/edge/face
                if new_point_pos:
                    loop_obj = self.all_loops_ids[-1]
                    new_face_verts = []

                    # create a new vert
                    new_vert = bm.verts.new((new_point_pos[0], new_point_pos[1], new_point_pos[2]))
                    new_vert[self.id_layer] = self.id_value
                    loop_obj.loop_ids.append(self.id_value)
                    self.id_value += 1

                    bm.verts.index_update()
                    bm.verts.ensure_lookup_table()

                    # create a new face
                    new_face_verts.append(new_vert)
                    temp_ids = []
                    if len(self.all_loops_ids) > 1:
                        prev_loop_ids = self.all_loops_ids[-2].loop_ids

                        if len(loop_obj.loop_ids) > 1:
                            if self.all_loops_ids[-1].revert_prev_loops is True:
                                prev_loop_ids = prev_loop_ids.copy()
                                prev_loop_ids.reverse()

                            temp_ids.append(loop_obj.loop_ids[-2])

                            prev_len = len(prev_loop_ids) - 1

                            temp_ids.append(prev_loop_ids[self.previous_loop_id])
                            if self.previous_loop_id < prev_len and event.ctrl is False:
                                temp_ids.append(prev_loop_ids[self.previous_loop_id + 1])

                            other_verts = ut_base.get_verts_from_ids(temp_ids, self.id_layer, bm)
                            new_face_verts += other_verts
                            new_face = bm.faces.new( new_face_verts )

                            bmesh.ops.recalc_face_normals(bm, faces=[new_face])

                            if self.previous_loop_id < prev_len and event.ctrl is False:
                                self.previous_loop_id += 1

                            bm.faces.index_update()
                            bm.faces.ensure_lookup_table()

                        else:
                            if self.all_loops_ids[-1].revert_prev_loops is True:
                                prev_loop_ids = prev_loop_ids.copy()
                                prev_loop_ids.reverse()

                            temp_ids.append(prev_loop_ids[0])
                            other_verts = ut_base.get_verts_from_ids(temp_ids, self.id_layer, bm)
                            new_face_verts += other_verts
                            new_edge = bm.edges.new(new_face_verts)

                            self.previous_loop_id = 0

                            bm.edges.index_update()
                            bm.edges.ensure_lookup_table()

                    else:
                        if len(loop_obj.loop_ids) > 1:
                            temp_ids.append(loop_obj.loop_ids[-2])
                            other_verts = ut_base.get_verts_from_ids(temp_ids, self.id_layer, bm)
                            new_face_verts += other_verts
                            new_edge = bm.edges.new(new_face_verts)

                            bm.edges.index_update()
                            bm.edges.ensure_lookup_table()

                    self.tool_mode = 'MOVE_POINT'

                    bm.normal_update()
                    bmesh.update_edit_mesh(active_obj.data)

            # Create Curve
            elif event.type == 'C':
                loop_obj = self.all_loops_ids[-1]
                new_face_verts = []

                # create a new face
                temp_ids = []
                if len(self.all_loops_ids) > 1 and self.all_loops_ids[-1].loop_ids:
                    prev_loop_ids = self.all_loops_ids[-2].loop_ids

                    if self.all_loops_ids[-1].revert_prev_loops is True:
                        prev_loop_ids = prev_loop_ids.copy()
                        prev_loop_ids.reverse()

                    prev_len = len(prev_loop_ids) - 1

                    if self.previous_loop_id < prev_len:
                        temp_ids.append(loop_obj.loop_ids[-1])
                        temp_ids.append(prev_loop_ids[self.previous_loop_id])
                        temp_ids.append(prev_loop_ids[self.previous_loop_id + 1])

                        other_verts = ut_base.get_verts_from_ids(temp_ids, self.id_layer, bm)
                        new_face_verts += other_verts
                        new_face = bm.faces.new( new_face_verts )

                        bmesh.ops.recalc_face_normals(bm, faces=[new_face])

                        if self.previous_loop_id < prev_len and event.ctrl is False:
                            self.previous_loop_id += 1

                        bm.faces.index_update()
                        bm.faces.ensure_lookup_table()

                        bm.normal_update()
                        bmesh.update_edit_mesh(active_obj.data)

            # Create Curve
            elif event.type == 'A':
                # all new loops
                if event.shift:
                    self.all_loops_ids.clear()
                    self.all_loops_ids.append(MI_PL_LoopObject(False))  # add another empty loop
                    self.previous_loop_id = 0
                    id_to_index = None
                # new loop
                else:
                    last_ids = self.all_loops_ids[-1].loop_ids
                    if len(last_ids) > 1:
                        self.all_loops_ids.append(MI_PL_LoopObject(False))  # add another empty loop
                        self.previous_loop_id = 0
                        id_to_index = None

            elif event.type in {'X'}:
                if self.all_loops_ids and self.all_loops_ids[-1].loop_ids:
                    # remove last vert
                    last_vert = ut_base.get_verts_from_ids([self.all_loops_ids[-1].loop_ids[-1]], self.id_layer, bm)[0]
                    self.all_loops_ids[-1].loop_ids.remove(self.all_loops_ids[-1].loop_ids[-1])

                    bmesh.ops.delete(bm, geom=[last_vert], context=1)
                    bmesh.update_edit_mesh(active_obj.data)

                    # set new previous index
                    if len(self.all_loops_ids) > 1 and self.all_loops_ids[-1].loop_ids:
                        new_last_vert = ut_base.get_verts_from_ids([self.all_loops_ids[-1].loop_ids[-1]], self.id_layer, bm)[0]
                        linked_edges = new_last_vert.link_edges

                        new_prev_loop_id = 0

                        prev_loop_ids = self.all_loops_ids[-2].loop_ids
                        if self.all_loops_ids[-1].revert_prev_loops is True:
                            prev_loop_ids = prev_loop_ids.copy()
                            prev_loop_ids.reverse()

                        for edge in linked_edges:
                            for vert in edge.verts:
                                if vert[self.id_layer] in prev_loop_ids:
                                    if vert[self.id_layer] > new_prev_loop_id:
                                        new_prev_loop_id = prev_loop_ids.index(vert[self.id_layer])

                        self.previous_loop_id = new_prev_loop_id

                    else:
                        self.previous_loop_id = 0

            elif event.type in {'TAB'} and event.shift:
                if mi_settings.surface_snap is True:
                    mi_settings.surface_snap = False
                else:
                    mi_settings.surface_snap = True
                    if not self.picked_meshes:
                        # get meshes for snapping
                        meshes_array = ut_base.get_obj_dup_meshes(mi_settings.snap_objects, mi_settings.convert_instances, context)
                        if meshes_array:
                            self.picked_meshes = meshes_array

        # TOOL WORK
        if self.tool_mode == 'MOVE_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.tool_mode = 'IDLE'

                last_vert = ut_base.get_verts_from_ids([self.all_loops_ids[-1].loop_ids[-1]], self.id_layer, bm)[0]
                if mi_settings.surface_snap is True and self.picked_meshes:
                    best_obj, hit_normal, hit_position = ut_base.get_mouse_raycast(context, self.picked_meshes, m_coords)
                    if hit_position:
                        last_vert.co = active_obj.matrix_world.inverted() * hit_position

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

                return {'RUNNING_MODAL'}
            else:
                last_vert = ut_base.get_verts_from_ids([self.all_loops_ids[-1].loop_ids[-1]], self.id_layer, bm)[0]
                new_point_pos = ut_base.get_mouse_on_plane(context, active_obj.matrix_world * last_vert.co, None, m_coords)
                if new_point_pos:
                    last_vert.co = active_obj.matrix_world.inverted() * new_point_pos

                    bmesh.update_edit_mesh(active_obj.data)

                return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}

        # get keys
        if keys_pass is True:
            # allow navigation
            return {'PASS_THROUGH'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            #bpy.types.SpaceView3D.draw_handler_remove(self.mi_pl_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_pl_2d, 'WINDOW')
            finish_work(self, context, bm)
            context.area.header_text_set()

            return {'FINISHED'}

        return {'RUNNING_MODAL'}


def reset_params(self, bm):
    # reset base mi_settings
    self.tool_mode = 'IDLE'
    #self.all_curves = []
    #self.active_curve = None
    self.deform_mouse_pos = None
    self.picked_meshes = None

    # loops code
    self.all_loops_ids = []
    self.previous_loop_id = 0
    self.id_to_index = None

    # get ids layer
    self.id_value = 1
    self.id_layer = None
    if 'mi_cur_surf_ids' in bm.verts.layers.int.keys():
        self.id_layer = bm.verts.layers.int['mi_cur_surf_ids']
        bm.verts.layers.int.remove(self.id_layer)
    self.id_layer = bm.verts.layers.int.new('mi_cur_surf_ids')

    # reset ids
    for vert in bm.verts:
        vert[self.id_layer] = 0


def finish_work(self, context, bm):
    context.space_data.show_manipulator = self.manipulator
    bm.verts.layers.int.remove(self.id_layer)
    context.area.header_text_set()


def mi_pl_draw_2d(self, context):
    active_obj = context.scene.objects.active
    if self.id_to_index:
        c_widget.draw_2d_point(self.id_to_index[1][0], self.id_to_index[1][1], p_size=6, p_col=col_man.pl_point_col)

