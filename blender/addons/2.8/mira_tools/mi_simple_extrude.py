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
# import bgl

from bpy.props import *
from bpy.types import Operator, AddonPreferences

import math
import mathutils as mathu
from mathutils import Vector, Matrix

from . import mi_utils_base as ut_base
from . import mi_color_manager as col_man
from . import mi_widget_curve as c_widget
from bpy_extras import view3d_utils


class MI_Simple_Extrude(bpy.types.Operator):
    """Extrude like in Modo"""
    bl_idname = "mira.simple_extrude"
    bl_label = "Simple Extrude"
    bl_description = "Simple Extrude"
    bl_options = {'REGISTER', 'UNDO'}


    first_mouse_x = None
    center = None
    depth = 0
    thickness = 0
    move_size = None
    extrude_dirs = None
    extrude_verts_ids = None

    zero_x_verts = None
    zero_y_verts = None
    zero_z_verts = None

    tool_mode = 'IDLE'  # IDLE, EXTRUDE, INSET

    old_auto_merge = None  # fix for crash


    def invoke(self, context, event):
        clean(self)

        if context.mode == 'EDIT_MESH':
            # the arguments we pass the the callbackection
            args = (self, context)

            active_obj = context.active_object
            self.old_auto_merge = bpy.context.scene.tool_settings.use_mesh_automerge
            context.scene.tool_settings.use_mesh_automerge = False

            # fix some essues. Just go to ObjectMode then o Edit Mode
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

            bm = bmesh.from_edit_mesh(active_obj.data)

            self.first_mouse_x = event.mouse_x

            # EXTRUDE TEST
            bpy.ops.ed.undo_push()
            #bpy.ops.mesh.inset(depth=1.0, thickness=0.0)
            bpy.ops.mesh.extrude_region_shrink_fatten(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_shrink_fatten={"value":0.001, "use_even_offset":True})
            #bm = bmesh.from_edit_mesh(active_obj.data)
            bm.verts.ensure_lookup_table()

            verts_temp_1 = []
            self.extrude_verts_ids = []

            tmp_ids = []
            tmp_bverts = list(bm.verts)
            for ff in bm.faces:
                if ff.select:
                    for v in ff.verts:
                        if v.index not in tmp_ids:
                            verts_temp_1.append(v.co.copy())
                            self.extrude_verts_ids.append(tmp_bverts.index(v))

            bpy.ops.ed.undo()

            # INSET TEST
            bpy.ops.ed.undo_push()
            bpy.ops.mesh.inset(depth=0.0, thickness=0.001)
            bm = bmesh.from_edit_mesh(active_obj.data)
            bm.verts.ensure_lookup_table()

            verts_temp_2 = []
            tmp_ids = []
            tmp_bverts = list(bm.verts)
            for ff in bm.faces:
                if ff.select:
                    for v in ff.verts:
                        if v.index not in tmp_ids:
                            verts_temp_2.append(v.co.copy())

            bpy.ops.ed.undo()

            # BASE
            #bpy.ops.mesh.inset(depth=0.0, thickness=0.0)
            bpy.ops.mesh.extrude_region_shrink_fatten(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_shrink_fatten={"value":0, "use_even_offset":True})

            bm = bmesh.from_edit_mesh(active_obj.data)
            #bm.verts.index_update()
            bm.verts.ensure_lookup_table()

            verts_temp_3 = []

            snap_mir_x = None
            snap_mir_y = None
            snap_mir_z = None

            for modifier in active_obj.modifiers:
                if modifier.type == 'MIRROR':
                    if modifier.use_axis[0] and modifier.use_clip:
                        snap_mir_x = modifier.merge_threshold
                    if modifier.use_axis[1] and modifier.use_clip:
                        snap_mir_y = modifier.merge_threshold
                    if modifier.use_axis[2] and modifier.use_clip:
                        snap_mir_z = modifier.merge_threshold

            for i in self.extrude_verts_ids:
                bv = bm.verts[i]
                verts_temp_3.append(bv.co.copy())

                # get zero faces
                if snap_mir_x or snap_mir_y or snap_mir_z:
                    if snap_mir_x:
                        if bv.co[0] <= snap_mir_x and bv.co[0] >= -snap_mir_x:
                            self.zero_x_verts.append(i)
                    if snap_mir_y:
                        if bv.co[1] <= snap_mir_y and bv.co[1] >= -snap_mir_y:
                            self.zero_y_verts.append(i)
                    if snap_mir_z:
                        if bv.co[2] <= snap_mir_z and bv.co[2] >= -snap_mir_z:
                            self.zero_z_verts.append(i)

            # Get Dirs
            self.extrude_dirs = []
            for i in range(len(verts_temp_1)):
                p1 = verts_temp_1[i]
                p2 = verts_temp_2[i]
                p3 = verts_temp_3[i]

                # set Extrude Dirs
                dir_ex = (p1 - p3) * 1000.0
                dir_ins = (p2 - p3) * 1000.0
                self.extrude_dirs.append((dir_ex, dir_ins, p3))

            # Center Calculation
            self.center = active_obj.matrix_world @ verts_temp_3[0].copy()

            self.mi_extrude_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_extrude_draw_2d, args, 'WINDOW', 'POST_PIXEL')

            # set default Extrude mode
            self.move_size = calc_move_size(self, context)
            #self.tool_mode = 'EXTRUDE'

            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}

        else:
            self.report({'WARNING'}, "Go to Edit Mode!")
            return {'CANCELLED'}


    def modal(self, context, event):
        # Tooltip
        context.area.tag_redraw()
        tooltip_text = "E: Extrude, W: Inset, R: Reset, Leftclick/Esc: Finish"
        context.area.header_text_set(tooltip_text)

        active_obj = context.active_object
        m_coords = event.mouse_region_x, event.mouse_region_y
        bm = bmesh.from_edit_mesh(active_obj.data)

        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}

        # DELTA CALCULATION
        if self.tool_mode != 'IDLE':
            delta = ((self.first_mouse_x - event.mouse_x) * self.move_size)

        # EXTRUDE
        if event.type == 'E' and event.value == 'PRESS':
            if self.tool_mode == 'IDLE':
                self.move_size = calc_move_size(self, context)

                self.first_mouse_x = event.mouse_x
                self.tool_mode = 'EXTRUDE'

            elif self.tool_mode == 'EXTRUDE':
                self.depth += delta

                #bm = bmesh.from_edit_mesh(active_obj.data)
                #sel_faces = [f for f in bm.faces if f.select]
                self.center = active_obj.matrix_world @ bm.verts[self.extrude_verts_ids[0]].co.copy()
                #context.scene.cursor_location = self.center

                self.tool_mode = 'IDLE'

            return {'RUNNING_MODAL'}

        # INSET
        elif event.type == 'W' and event.value == 'PRESS':
            if self.tool_mode == 'IDLE':
                self.move_size = calc_move_size(self, context)

                self.first_mouse_x = event.mouse_x
                self.tool_mode = 'INSET'

            elif self.tool_mode == 'INSET':
                #self.thickness = max(delta, 0)
                self.thickness += delta
                
                #bm = bmesh.from_edit_mesh(active_obj.data)
                #sel_faces = [f for f in bm.faces if f.select]
                self.center = active_obj.matrix_world @ bm.verts[self.extrude_verts_ids[0]].co.copy()
                #context.scene.cursor_location = self.center

                self.tool_mode = 'IDLE'

            return {'RUNNING_MODAL'}

        # RESET
        elif event.type == 'R' and event.value == 'PRESS':
            if self.tool_mode == 'IDLE':
                bm_verts = bm.verts

                for i in range(len(self.extrude_verts_ids)):
                    vert_idx = self.extrude_verts_ids[i]

                    bm_verts[vert_idx].co = self.extrude_dirs[i][2]
                    self.thickness = 0.0
                    self.depth = 0.0

                self.center = active_obj.matrix_world @ bm_verts[self.extrude_verts_ids[0]].co.copy()

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

            return {'RUNNING_MODAL'}

        # TOOL WORK
        if self.tool_mode != 'IDLE':
            if event.type == 'MOUSEMOVE':
                #bpy.ops.ed.undo()

                if self.tool_mode in {'EXTRUDE', 'INSET'}:
                    bm_verts = bm.verts
                    for i in range(len(self.extrude_verts_ids)):
                        vert_idx = self.extrude_verts_ids[i]
                        ex_dir = self.extrude_dirs[i][0].copy()
                        if self.tool_mode == 'EXTRUDE':
                            ex_dir *= (self.depth + delta)
                        else:
                            ex_dir *= (self.depth)

                        inset_dir = self.extrude_dirs[i][1].copy()
                        if self.tool_mode == 'INSET':
                            inset_dir *= (self.thickness + delta)
                        else:
                            inset_dir *= (self.thickness)

                        # change vertex position
                        bm_verts[vert_idx].co = self.extrude_dirs[i][2] - ex_dir + inset_dir

                        # fix zero positions
                        if self.zero_x_verts:
                            for v_id in self.zero_x_verts:
                                zero_verts = bm.verts[v_id].co[0] = 0.0

                        if self.zero_y_verts:
                            for v_id in self.zero_y_verts:
                                zero_verts = bm.verts[v_id].co[1] = 0.0

                        if self.zero_z_verts:
                            for v_id in self.zero_z_verts:
                                zero_verts = bm.verts[v_id].co[2] = 0.0


                    bm.normal_update()
                    bmesh.update_edit_mesh(active_obj.data)

        if event.type in {'LEFTMOUSE', 'RIGHTMOUSE', 'ESC'}:

            # fix some essues. Just go to ObjectMode then o Edit Mode
            bpy.ops.object.mode_set(mode='OBJECT', toggle=False)
            bpy.ops.object.mode_set(mode='EDIT', toggle=False)

            context.scene.tool_settings.use_mesh_automerge = self.old_auto_merge

            bpy.types.SpaceView3D.draw_handler_remove(self.mi_extrude_handle_2d, 'WINDOW')
            context.area.header_text_set(None)

            return {'FINISHED'}

        return {'RUNNING_MODAL'}


def clean(self):
    self.tool_mode = 'IDLE'
    self.first_mouse_x = None
    self.center = None
    self.depth = 0
    self.thickness = 0
    self.move_size = None
    self.extrude_dirs = None
    self.extrude_verts_ids = None

    self.zero_x_verts = []
    self.zero_y_verts = []
    self.zero_z_verts = []

    self.old_auto_merge = None


# calculate Move Size
def calc_move_size(self, context):
    rv3d = context.region_data
    reg_w = bpy.context.region.width
    reg_h = bpy.context.region.height

    view_dir_neg = rv3d.view_rotation @ Vector((0.0, 0.0, 1.0))
    move_test_1 = ut_base.get_mouse_on_plane(context, self.center, view_dir_neg, (reg_w / 2, reg_h / 2))
    move_test_2 = ut_base.get_mouse_on_plane(context, self.center, view_dir_neg, ((reg_w / 2) + 4.0, reg_h / 2))  # Plus 4 pixels by X to change a horizontal distance

    return (move_test_1 - move_test_2).length / 4.0  # It's divided to 4 because of 4 pixels offset in the move_test_2


# Draw point in Viewport
def mi_extrude_draw_2d(self, context):
    if self.center:
        rv3d = context.region_data
        region = context.region
        addon_prefs = context.preferences.addons[__package__].preferences
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, self.center)

        p_col = col_man.dre_point_base
        c_widget.draw_2d_point(point_pos_2d.x, point_pos_2d.y, addon_prefs.point_size, p_col)
