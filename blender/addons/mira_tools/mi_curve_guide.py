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
from mathutils import Vector, Matrix

from . import mi_utils_base as ut_base
from . import mi_color_manager as col_man
from . import mi_curve_main as cur_main
from . import mi_color_manager as col_man
from . import mi_looptools as loop_t
from . import mi_inputs
from . import mi_widget_linear_deform as l_widget
from . import mi_widget_select as s_widget
from . import mi_widget_curve as c_widget

# Settings
class MI_CurGuide_Settings(bpy.types.PropertyGroup):
    points_number = IntProperty(default=5, min=2, max=128)
    deform_type = EnumProperty(
        items=(('Stretch', 'Stretch', ''),
               ('Scale', 'Scale', ''),
               ('Shear', 'Shear', ''),
               ('Twist', 'Twist', ''),
               ('Deform', 'Deform', '')
               ),
        default = 'Stretch'
    )


class MI_Curve_Guide(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.curve_guide"
    bl_label = "CurveGuide"
    bl_description = "Curve Guide"
    bl_options = {'REGISTER', 'UNDO'}

    # curve tool mode
    tool_modes = ('IDLE', 'MOVE_LW_POINT', 'MOVE_CUR_POINT', 'SELECT_CUR_POINT')
    tool_mode = 'IDLE'

    # linear widget
    lw_tool = None
    lw_tool_axis = None
    active_lw_point = None
    tool_side_vec = None
    tool_side_vec_len = None
    tool_up_vec = None

    curve_tool = None
    picked_meshes = None

    deform_mouse_pos = None
    deform_vec_pos = None

    manipulator = None

    work_verts = None
    apply_tool_verts = None
    invert_deform_upvec = None

    def invoke(self, context, event):
        reset_params(self)

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)

            region = context.region
            rv3d = context.region_data
            m_coords = event.mouse_region_x, event.mouse_region_y
            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)
            curve_settings = context.scene.mi_settings

            pre_verts = ut_base.get_selected_bmverts(bm)
            if not pre_verts:
                pre_verts = [v for v in bm.verts if v.hide is False]

            if pre_verts:
                # change manipulator
                self.manipulator = context.space_data.show_manipulator
                context.space_data.show_manipulator = False

                self.work_verts = [vert.index for vert in pre_verts]  # here we add temporaryly verts which can be applied for the tool

                # create linear deformer
                self.lw_tool = l_widget.MI_Linear_Widget()

                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'Auto', 1.0001)

                # get meshes for snapping
                if curve_settings.surface_snap is True:
                    meshes_array = ut_base.get_obj_dup_meshes(curve_settings.snap_objects, curve_settings.convert_instances, context)
                    if meshes_array:
                        self.picked_meshes = meshes_array

                # Add the region OpenGL drawing callback
                # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
                self.cur_guide_handle_3d = bpy.types.SpaceView3D.draw_handler_add(cur_guide_draw_3d, args, 'WINDOW', 'POST_VIEW')
                self.cur_guide_handle_2d = bpy.types.SpaceView3D.draw_handler_add(cur_guide_draw_2d, args, 'WINDOW', 'POST_PIXEL')
                context.window_manager.modal_handler_add(self)

                return {'RUNNING_MODAL'}

            else:
                self.report({'WARNING'}, "No verts!!")
                return {'CANCELLED'}

        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        context.area.tag_redraw()

        lin_def_settings = context.scene.mi_ldeformer_settings

        region = context.region
        rv3d = context.region_data
        m_coords = event.mouse_region_x, event.mouse_region_y
        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)

        region = context.region
        rv3d = context.region_data

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences
        curve_settings = context.scene.mi_settings
        curguide_settings = context.scene.mi_curguide_settings

        # tooltip
        tooltip_text = None
        if self.curve_tool:
            tooltip_text = "NewPoint: Ctrl+Click, SelectAdditive: Shift+Click, DeletePoint: Del, SurfaceSnap: Shift+Tab, SelectLinked: L"

            if curguide_settings.deform_type == 'Deform':
                tooltip_text = "InvertUpVec: I, " + tooltip_text
        else:
            tooltip_text = "X: X-Axis, Z: Z-Axis, Move Points, press Enter to continue"
        context.area.header_text_set(tooltip_text)

        keys_pass = mi_inputs.get_input_pass(mi_inputs.pass_keys, addon_prefs.key_inputs, event)

        # key pressed
        if self.tool_mode == 'IDLE' and event.value == 'PRESS' and keys_pass is False:
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:

                # curve tool pick
                curve_picked = False  # checker for curve picking
                if self.curve_tool:
                    picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point([self.curve_tool], context, m_coords)
                    if picked_point:
                        self.deform_mouse_pos = m_coords
                        self.curve_tool.active_point = picked_point.point_id
                        additive_sel = event.shift

                        cur_main.select_point(self.curve_tool, picked_point, additive_sel)

                        curve_picked = True
                        self.tool_mode = 'SELECT_CUR_POINT'
                    else:
                        # add point
                        if event.ctrl and self.curve_tool and self.curve_tool.active_point:
                            act_point = cur_main.get_point_by_id(self.curve_tool.curve_points, self.curve_tool.active_point)

                            new_point_pos = None
                            if curguide_settings.deform_type != 'Deform':
                                new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, self.tool_up_vec, m_coords)
                            else:
                                new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)

                            if new_point_pos:
                                new_point = cur_main.add_point(new_point_pos, self.curve_tool)

                                # fix position
                                if curguide_settings.deform_type != 'Deform':
                                    fix_curve_point_pos(self.lw_tool, self.curve_tool, [new_point])

                                self.curve_tool.active_point = new_point.point_id

                                # add to display
                                cur_main.curve_point_changed(self.curve_tool, self.curve_tool.curve_points.index(new_point), curve_settings.curve_resolution, self.curve_tool.display_bezier)

                                curve_picked = True
                                self.tool_mode = 'MOVE_CUR_POINT'

                # pick linear widget point but only before the curve is created
                if curve_picked is False:
                    if not self.curve_tool:
                        picked_point = l_widget.pick_lw_point(context, m_coords, self.lw_tool)
                        if picked_point:
                            self.deform_mouse_pos = Vector(m_coords)
                            self.active_lw_point = picked_point

                            self.tool_mode = 'MOVE_LW_POINT'

            elif event.type in {'RET', 'NUMPAD_ENTER'}:
                # create curve
                if not self.curve_tool:

                    points_number = curguide_settings.points_number
                    points_dir = self.lw_tool.end_point.position - self.lw_tool.start_point.position
                    lw_tool_dir = points_dir.copy().normalized()

                    # get side vec
                    cam_z = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()

                    # set tool vecs
                    self.tool_side_vec = cam_z.cross(lw_tool_dir).normalized()
                    self.tool_up_vec = lw_tool_dir.cross(self.tool_side_vec).normalized()  # here we set upvec

                    # get verts
                    pre_verts = ut_base.get_selected_bmverts(bm)
                    if not pre_verts:
                        pre_verts = [v for v in bm.verts if v.hide is False]

                    self.work_verts = {}
                    for vert in pre_verts:
                        vert_world = active_obj.matrix_world * vert.co
                        v_front_dist = mathu.geometry.distance_point_to_plane(vert_world, self.lw_tool.start_point.position, lw_tool_dir)
                        if v_front_dist >= 0.0 and v_front_dist <= points_dir.length:
                            v_side_dist = mathu.geometry.distance_point_to_plane(vert_world, self.lw_tool.start_point.position, self.tool_side_vec)
                            v_up_dist = mathu.geometry.distance_point_to_plane(vert_world, self.lw_tool.start_point.position, self.tool_up_vec)
                            self.work_verts[vert.index] = (vert_world, v_front_dist, v_side_dist, v_up_dist)

                    if self.work_verts:
                        # create curve
                        self.curve_tool = cur_main.MI_CurveObject(None)

                        verts = [bm.verts[vert_id] for vert_id in self.work_verts.keys()]
                        bounds = ut_base.get_verts_bounds(verts, active_obj, self.tool_side_vec, lw_tool_dir, None, False)

                        # set tool vecs
                        widget_offset = mathu.geometry.distance_point_to_plane(self.lw_tool.middle_point.position, bounds[3], self.tool_side_vec)
                        self.tool_side_vec_len = ((bounds[0] * 0.5) + abs(widget_offset) )  # here we set the length of the side vec

                        # create points
                        for i in range(points_number):
                            point = cur_main.MI_CurvePoint(self.curve_tool.curve_points)
                            self.curve_tool.curve_points.append(point)
                            if curguide_settings.deform_type == 'Deform':
                                point.position = Vector(self.lw_tool.start_point.position + ( points_dir * (float(i)/float(points_number-1)) ) )
                            else:
                                point.position = Vector(self.lw_tool.start_point.position + ( points_dir * (float(i)/float(points_number-1)) ) ) + (self.tool_side_vec * self.tool_side_vec_len)
                        cur_main.generate_bezier_points(self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)

            # set linear widet to axis constraint
            elif event.type in {'Z', 'X'}:
                if not self.curve_tool:
                    pre_verts = [bm.verts[v_id] for v_id in self.work_verts]
                    if event.type == 'X':
                        if self.lw_tool_axis:
                            if self.lw_tool_axis == 'X':
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'X_Left', 1.0001)
                                self.lw_tool_axis = 'X_Left'
                            elif self.lw_tool_axis == 'X_Left':
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'X_Right', 1.0001)

                                # revert direction
                                stp = self.lw_tool.start_point.position.copy()
                                self.lw_tool.start_point.position = self.lw_tool.end_point.position
                                self.lw_tool.end_point.position = stp

                                self.lw_tool_axis = 'X_Right'
                            elif self.lw_tool_axis == 'X_Right':
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'X', 1.0001)
                                self.lw_tool_axis = 'X'
                            else:
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'X', 1.0001)
                                self.lw_tool_axis = 'X'
                        else:
                            l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'X', 1.0001)
                            self.lw_tool_axis = 'X'
                    else:
                        if self.lw_tool_axis:
                            if self.lw_tool_axis == 'Z':
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'Z_Top', 1.0001)
                                self.lw_tool_axis = 'Z_Top'
                            elif self.lw_tool_axis == 'Z_Top':
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'Z_Bottom', 1.0001)

                                # revert direction
                                stp = self.lw_tool.start_point.position.copy()
                                self.lw_tool.start_point.position = self.lw_tool.end_point.position
                                self.lw_tool.end_point.position = stp

                                self.lw_tool_axis = 'Z_Bottom'
                            elif self.lw_tool_axis == 'Z_Bottom':
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'Z', 1.0001)
                                self.lw_tool_axis = 'Z'
                            else:
                                l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'Z', 1.0001)
                                self.lw_tool_axis = 'Z'
                        else:
                            l_widget.setup_lw_tool(rv3d, self.lw_tool, active_obj, pre_verts, 'Z', 1.0001)
                            self.lw_tool_axis = 'Z'

            # invert upvec
            elif event.type == 'I' and self.curve_tool and curguide_settings.deform_type == 'Deform':
                if self.invert_deform_upvec is True:
                    self.invert_deform_upvec = False
                else:
                    self.invert_deform_upvec = True

                # update mesh positions
                update_mesh_to_curve(self, bm, curguide_settings.deform_type, active_obj)
                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

            # delete curve point
            elif event.type == 'DEL' and self.curve_tool:
                sel_points = cur_main.get_selected_points(self.curve_tool.curve_points)
                if sel_points:
                    for point in sel_points:
                        #the_act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                        #the_act_point_index = self.active_curve.curve_points.index(point)

                        cur_main.delete_point(point, self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)

                    self.curve_tool.display_bezier.clear()
                    cur_main.generate_bezier_points(self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)
                    self.curve_tool.active_point = None

            # switch snapping
            elif event.type in {'TAB'} and event.shift and self.curve_tool:
                if curve_settings.surface_snap is True:
                    curve_settings.surface_snap = False
                else:
                    curve_settings.surface_snap = True
                    if not self.picked_meshes:
                        # get meshes for snapping
                        meshes_array = ut_base.get_obj_dup_meshes(curve_settings.snap_objects, curve_settings.convert_instances, context)
                        if meshes_array:
                            self.picked_meshes = meshes_array

            # Select Linked
            elif event.type == 'L' and self.curve_tool and curguide_settings.deform_type == 'Deform':
                picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point([self.curve_tool], context, m_coords)

                if picked_point:
                    cur_main.select_all_points(picked_curve.curve_points, True)
                    picked_curve.active_point = picked_point.point_id

        # TOOL WORK!
        if self.tool_mode == 'MOVE_LW_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                new_point_pos = ut_base.get_mouse_on_plane(context, self.active_lw_point.position, None, m_coords)
                if self.active_lw_point.position == self.lw_tool.start_point.position or self.active_lw_point.position == self.lw_tool.end_point.position:
                    self.active_lw_point.position = new_point_pos
                    l_widget.update_middle_point(self.lw_tool)
                elif self.active_lw_point.position == self.lw_tool.middle_point.position:
                    self.lw_tool.start_point.position += new_point_pos - self.active_lw_point.position
                    self.lw_tool.end_point.position += new_point_pos - self.active_lw_point.position
                    self.lw_tool.middle_point.position = new_point_pos

                return {'RUNNING_MODAL'}

        elif self.tool_mode == 'SELECT_CUR_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # set to move point
                m_coords = event.mouse_region_x, event.mouse_region_y
                if ( Vector((m_coords[0], m_coords[1])) - Vector((self.deform_mouse_pos[0], self.deform_mouse_pos[1])) ).length > 4.0:
                    self.tool_mode = 'MOVE_CUR_POINT'
                    return {'RUNNING_MODAL'}

        elif self.tool_mode == 'MOVE_CUR_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                # Snap to Surface
                if curve_settings.surface_snap is True and self.picked_meshes:
                    selected_points = cur_main.get_selected_points(self.curve_tool.curve_points)
                    if selected_points:
                        cur_main.snap_to_surface(context, selected_points, self.picked_meshes, region, rv3d, None)

                        if len(selected_points) == 1:
                            cur_main.curve_point_changed(self.curve_tool, self.curve_tool.curve_points.index(selected_points[0]), curve_settings.curve_resolution, self.curve_tool.display_bezier)
                        else:
                            cur_main.generate_bezier_points(self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)

                # update mesh positions
                update_mesh_to_curve(self, bm, curguide_settings.deform_type, active_obj)
                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                m_coords = event.mouse_region_x, event.mouse_region_y
                act_point = cur_main.get_point_by_id(self.curve_tool.curve_points, self.curve_tool.active_point)
                selected_points = cur_main.get_selected_points(self.curve_tool.curve_points)

                # get new point position
                new_point_pos = None
                if curguide_settings.deform_type != 'Deform':
                    new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, self.tool_up_vec, m_coords)
                else:
                    new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)

                if new_point_pos and selected_points:
                    move_offset = new_point_pos - act_point.position

                    # move point
                    for point in selected_points:
                        point.position += move_offset

                    # fix points pos
                    if curguide_settings.deform_type != 'Deform':
                        fix_curve_point_pos(self.lw_tool, self.curve_tool, selected_points)

                    # update bezier
                    if len(selected_points) == 1:
                        cur_main.curve_point_changed(self.curve_tool, self.curve_tool.curve_points.index(selected_points[0]), curve_settings.curve_resolution, self.curve_tool.display_bezier)
                    else:
                        cur_main.generate_bezier_points(self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)

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
            context.space_data.show_manipulator = self.manipulator

            bpy.types.SpaceView3D.draw_handler_remove(self.cur_guide_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.cur_guide_handle_2d, 'WINDOW')

            context.area.header_text_set()

            return {'FINISHED'}

        return {'RUNNING_MODAL'}


def reset_params(self):
    self.tool_mode = 'IDLE'
    self.deform_mouse_pos = None
    self.deform_vec_pos = None
    self.manipulator = None

    self.lw_tool = None
    self.lw_tool_axis = None
    self.active_lw_point = None
    self.tool_side_vec = None
    self.tool_side_vec_len = None
    self.tool_up_vec = None

    self.curve_tool = None
    self.picked_meshes = None

    self.work_verts = None
    self.apply_tool_verts = None
    self.invert_deform_upvec = False


def update_mesh_to_curve(self, bm, deform_type, obj):
    lw_tool_vec = self.lw_tool.end_point.position - self.lw_tool.start_point.position
    lw_tool_dir = (self.lw_tool.end_point.position - self.lw_tool.start_point.position).normalized()

    if deform_type == 'Deform':  # DEFORM TYPE ONLY
        deform_lines, points_indexes = get_bezier_area_data(self.curve_tool)
        line_len = deform_lines[-1][1]

        zero_vec = Vector( (0.0,0.0,0.0) )

        # get bezier dirs
        b_dirs = []
        for b_point_data in deform_lines:
            # bezier point direction
            b_point_dir = None
            index_point = deform_lines.index(b_point_data)
            if index_point < len(deform_lines) - 1:
                b_point_dir = deform_lines[index_point-1][3]
            else:
                b_point_dir = b_point_data[3]

            #check_angle = b_point_dir.angle(self.tool_up_vec)

            ### upVec approach by me
            ## calculate using cross vec
            #b_point_up = b_point_dir.cross(self.tool_up_vec).normalized()

            # upVec approach by mano-wii version 1
            pzv = self.tool_up_vec.project(b_point_dir)  # here we project the direction to get upVec
            b_point_up = (self.tool_up_vec - pzv).normalized()

            ## upVec approach by mano-wii version 2
            #dot = self.tool_up_vec.dot(b_point_dir)
            #pzv = dot * b_point_dir  # here we dot the direction to get upVec
            #b_point_up = (self.tool_up_vec - pzv).normalized()

            # invert direction feature
            if self.invert_deform_upvec is True:
                b_point_up.negate()

            # fix directions according to previous upvec
            if b_dirs:
                if b_point_up.length == 0.0:
                    b_point_up = b_dirs[-1][1].copy()
                elif b_dirs[-1][1].angle(b_point_up) > math.radians(90.0):
                    # here we invert upVec if it was incorrect according to previous one
                    b_point_up.negate()

            b_point_side = b_point_dir.cross(b_point_up).normalized()

            b_dirs.append([b_point_dir, b_point_up, b_point_side])

        # find the best point for every vert
        for vert_id in self.work_verts.keys():
            vert = bm.verts[vert_id]
            vert_data = self.work_verts[vert_id]

            for i, point in enumerate(self.curve_tool.curve_points):
                if i > 0:
                    point_len = deform_lines[points_indexes.get(point.point_id)][1] / line_len
                    vert_len = vert_data[1] / lw_tool_vec.length
                    if point_len >= vert_len:
                        # max is for the first point
                        first_index = 0
                        if i > 0:
                            first_index = points_indexes.get( self.curve_tool.curve_points[self.curve_tool.curve_points.index(point) - 1].point_id )

                        # get the best point
                        #b_point_up = None
                        #b_point_side = None
                        best_pos = None
                        for b_point_data in deform_lines[first_index:]:
                            j = deform_lines.index(b_point_data)
                            #print(j, jj)
                            if j > 0:
                                b_point_len = b_point_data[1] / line_len
                                if b_point_len >= vert_len:

                                    b_point_dirs = b_dirs[deform_lines.index(b_point_data)]

                                    # best position
                                    if b_point_len == vert_len:
                                        best_pos = b_point_data[0]
                                    else:
                                        previous_pos_len = deform_lines[j-1][1] / line_len

                                        interp_pos = (vert_len - previous_pos_len) * line_len

                                        # fix for interpolation between lines
                                        if j > 1 and j < len(deform_lines) - 1:
                                            prev_b_point_dirs = b_dirs[deform_lines.index(b_point_data)]
                                            b_point_dirs_temp = b_dirs[deform_lines.index(b_point_data)+1]
                                            b_point_dirs = b_point_dirs.copy()

                                            new_side_vec = prev_b_point_dirs[1].lerp(b_point_dirs_temp[1], interp_pos).normalized()
                                            b_point_dirs[1] = new_side_vec
                                            new_side_vec = prev_b_point_dirs[2].lerp(b_point_dirs_temp[2], interp_pos).normalized()
                                            b_point_dirs[2] = new_side_vec

                                        best_pos = deform_lines[j-1][0] + (( interp_pos) * b_point_dirs[0])

                                    break

                        vert.co = obj.matrix_world.inverted() * ( best_pos + (b_point_dirs[1] * vert_data[3]) - (b_point_dirs[2] * vert_data[2]) )
                        break

    else:  # ALL OTHER TYPES
        # get points dists
        points_dists = []
        for point in self.curve_tool.curve_points:
            bezier_dists = []
            p_dist = mathu.geometry.distance_point_to_plane(point.position, self.lw_tool.start_point.position, lw_tool_dir)

            # add bezer dists
            if self.curve_tool.curve_points.index(point) > 0:
                for b_point in self.curve_tool.display_bezier[point.point_id]:
                    b_p_dist = mathu.geometry.distance_point_to_plane(b_point, self.lw_tool.start_point.position, lw_tool_dir)
                    b_p_side_dist = mathu.geometry.distance_point_to_plane(b_point, self.lw_tool.start_point.position, self.tool_side_vec)
                    bezier_dists.append( (b_p_dist, b_p_side_dist, b_point) )

            points_dists.append( (p_dist, bezier_dists) )


        # find the best point for every vert
        for vert_id in self.work_verts.keys():
            vert = bm.verts[vert_id]
            vert_data = self.work_verts[vert_id]

            deform_dir = None
            if deform_type == 'Scale':
                deform_dir = (vert_data[0] - (self.lw_tool.start_point.position + (lw_tool_dir * vert_data[1]))).normalized()
            else:
                deform_dir = self.tool_side_vec

            for i, point_data in enumerate(points_dists):
                if point_data[0] >= vert_data[1]:
                    best_bezier_len = None
                    vert_front_pos = self.lw_tool.start_point.position + (lw_tool_dir * vert_data[1])

                    # loop bezier points according to vert
                    for j, b_point in enumerate(point_data[1]):
                        if not best_bezier_len:
                            best_bezier_len = b_point[1]
                        elif b_point[0] >= vert_data[1]:
                            bp_nor = (b_point[2] - point_data[1][j - 1][2]).normalized()
                            bp_nor = bp_nor.cross(self.tool_up_vec).normalized()
                            final_pos = mathu.geometry.intersect_line_plane(vert_front_pos - (self.tool_side_vec * 1000.0), vert_front_pos + (self.tool_side_vec * 1000.0), b_point[2], bp_nor)

                            best_bezier_len = (final_pos - vert_front_pos).length  # the length!

                            if deform_type in {'Shear', 'Twist'}:
                                if (final_pos - vert_front_pos).normalized().angle(self.tool_side_vec) > math.radians(90):
                                    best_bezier_len = -best_bezier_len
                            break

                    #final_dist = best_bezier_len

                    # multiplier for the vert
                    dir_multilpier = None
                    if deform_type == 'Stretch':
                        if self.tool_side_vec_len != 0.0:
                            dir_multilpier = (vert_data[2] * (best_bezier_len / self.tool_side_vec_len)) - vert_data[2]
                        else:
                            dir_multilpier = (vert_data[2] * 0.0) - vert_data[2]

                    elif deform_type in {'Shear', 'Twist'}:
                        dir_multilpier = best_bezier_len - self.tool_side_vec_len

                    else:
                        vert_dist_scale = (vert_data[0] - vert_front_pos).length

                        if self.tool_side_vec_len != 0.0:
                            dir_multilpier = abs(vert_dist_scale * (best_bezier_len / self.tool_side_vec_len)) - vert_dist_scale
                        else:
                            dir_multilpier = abs(vert_dist_scale * 0.0) - vert_dist_scale

                    # modify vert position
                    if deform_type == 'Twist':
                        twist_angle = dir_multilpier * math.radians(90)
                        rot_mat = Matrix.Rotation(twist_angle, 3, lw_tool_dir)
                        vert.co = obj.matrix_world.inverted() * (rot_mat * (vert_data[0] - self.lw_tool.start_point.position) + self.lw_tool.start_point.position)
                    else:
                        vert.co = obj.matrix_world.inverted() * (vert_data[0] + ( deform_dir *  dir_multilpier))
                    break


# we could use cur_main.get_bezier_line() method but we need some modifications to get point's index
def get_bezier_area_data(curve):
    curve_vecs = []
    points_indexes = {}
    for point in curve.curve_points:
        b_points = curve.display_bezier.get(point.point_id)
        if b_points:
            for b_p in b_points:
                # get all points but not the last one
                if b_points.index(b_p) != len(b_points) - 1 or curve.curve_points.index(point) == len(curve.curve_points) - 1:
                    curve_vecs.append(b_p)

        # add index of the curve point according to last bezier point
        if point.point_id not in points_indexes:
            # we use max for first point
            points_indexes[point.point_id] = max(0, len(curve_vecs) - 1)

    besier_line = cur_main.pass_line(curve_vecs, False)
    return besier_line, points_indexes


# constraint curve point
def fix_curve_point_pos(lw_tool, curve_tool, points_to_fix):
    # fix point position point
    lw_tool_vec = lw_tool.end_point.position - lw_tool.start_point.position
    lw_tool_dir = (lw_tool.end_point.position - lw_tool.start_point.position).normalized()
    for point in points_to_fix:
        p_idx = curve_tool.curve_points.index(point)
        p_dist = mathu.geometry.distance_point_to_plane(point.position, lw_tool.start_point.position, lw_tool_dir)

        if p_idx == 0.0:
            if p_dist != 0.0:
                point.position -= lw_tool_dir * p_dist
        elif p_idx == len(curve_tool.curve_points) - 1:
            if p_dist != lw_tool_vec.length:
                point.position -= lw_tool_dir * (p_dist - lw_tool_vec.length)
        else:
            # constraint to previous point
            prev_p = curve_tool.curve_points[p_idx - 1]
            prev_p_dist = mathu.geometry.distance_point_to_plane(prev_p.position, lw_tool.start_point.position, lw_tool_dir)
            dist_fix = p_dist - prev_p_dist
            if dist_fix < 0.0:
                point.position -= lw_tool_dir * dist_fix

            # constraint to next point
            next_p = curve_tool.curve_points[p_idx + 1]
            next_p_dist = mathu.geometry.distance_point_to_plane(next_p.position, lw_tool.start_point.position, lw_tool_dir)
            dist_fix = p_dist - next_p_dist
            if dist_fix > 0.0:
                point.position -= lw_tool_dir * dist_fix


def cur_guide_draw_2d(self, context):
    # active_obj = context.scene.objects.active
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_settings
    curguide_settings = context.scene.mi_curguide_settings

    #lw_tool_dir = (self.lw_tool.end_point.position - self.lw_tool.start_point.position).normalized()

    if self.lw_tool:
        lw_dir = (self.lw_tool.start_point.position - self.lw_tool.end_point.position).normalized()
        cam_view = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()
        side_dir = lw_dir.cross(cam_view).normalized()
        l_widget.draw_lw(context, self.lw_tool, side_dir, False)

    if self.curve_tool:
        draw_curve_points_2d(self.curve_tool, context, curve_settings)


def cur_guide_draw_3d(self, context):
    # active_obj = context.scene.objects.active
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_settings
    curguide_settings = context.scene.mi_curguide_settings

    if self.curve_tool:
        if curguide_settings.deform_type != 'Deform':
            # draw start line
            start_pos = self.lw_tool.start_point.position + (self.tool_side_vec * self.tool_side_vec_len)
            #start_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, start_pos)
            end_pos = self.lw_tool.end_point.position + (self.tool_side_vec * self.tool_side_vec_len)
            #end_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, end_pos)
            #draw_polyline_2d([start_pos_2d, end_pos_2d], 1, (0.3, 0.6, 0.99, 1.0))
            c_widget.draw_3d_polyline([start_pos, end_pos], 1, col_man.cur_line_base, True)

            # draw points
            for point in self.curve_tool.curve_points:
                start_pos = point.position
                #start_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, start_pos)
                p_dist = mathu.geometry.distance_point_to_plane(start_pos, self.lw_tool.start_point.position, self.tool_side_vec)
                end_pos = start_pos - (self.tool_side_vec * p_dist)
                #end_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, end_pos)
                #draw_polyline_2d([start_pos_2d, end_pos_2d], 1, (0.7, 0.5, 0.95, 1.0))
                c_widget.draw_3d_polyline([start_pos, end_pos], 1, col_man.cur_line_base, True)

        for cur_point in self.curve_tool.curve_points:
            if cur_point.point_id in self.curve_tool.display_bezier:
                c_widget.draw_3d_polyline(self.curve_tool.display_bezier[cur_point.point_id], 2, col_man.cur_line_base, True)
        #draw_curve_lines_2d(self.curve_tool, context)


def draw_curve_points_2d(curve, context, curve_settings):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_settings

    for cu_point in curve.curve_points:
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)

        if point_pos_2d:
            p_col = col_man.cur_point_base
            if curve.closed is True:
                if curve.curve_points.index(cu_point) == 0:
                    p_col = col_man.cur_point_closed_start
                elif curve.curve_points.index(cu_point) == len(curve.curve_points) - 1:
                    p_col = col_man.cur_point_closed_end

            if cu_point.select:
                p_col = col_man.cur_point_selected
            if cu_point.point_id == curve.active_point:
                p_col = col_man.cur_point_active
            c_widget.draw_2d_point(point_pos_2d[0], point_pos_2d[1], 6, p_col)

            # Handlers
            if curve_settings.draw_handlers:
            #if curve.curve_points.index(cu_point) < len(curve.curve_points)-1:
                if cu_point.handle1:
                    handle_1_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle1)
                    if handle_1_pos_2d:
                        c_widget.draw_2d_point(handle_1_pos_2d[0], handle_1_pos_2d[1], 3, col_man.cur_handle_1_base)
            #if curve.curve_points.index(cu_point) > 0:
                if cu_point.handle2:
                    handle_2_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle2)
                    if handle_2_pos_2d:
                        c_widget.draw_2d_point(handle_2_pos_2d[0], handle_2_pos_2d[1], 3, col_man.cur_handle_2_base)


def draw_curve_lines_2d(curve, context):
    region = context.region
    rv3d = context.region_data
    active_obj = context.scene.objects.active

    for cur_point in curve.curve_points:
        if cur_point.point_id in curve.display_bezier:
            #points_2d = []
            #for b_point in curve.display_bezier[cur_point.point_id]:
                #point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, b_point)
                #points_2d.append(point_pos_2d)
            #draw_polyline_2d(points_2d, 1, col_man.cur_line_base)
            c_widget.draw_3d_polyline(curve.display_bezier[cur_point.point_id], 2, col_man.cur_line_base, True)
