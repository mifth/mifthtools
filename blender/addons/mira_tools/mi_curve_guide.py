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
import blf
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
from . import mi_linear_widget as l_widget
from . import mi_curve_main as cur_main
from . import mi_color_manager as col_man
from . import mi_looptools as loop_t


# Settings
class MI_CurGuide_Settings(bpy.types.PropertyGroup):
    points_number = IntProperty(default=9, min=3, max=128)
    deform_type = EnumProperty(
        items=(('Stretch', 'Stretch', ''),
               ('Scale', 'Scale', '')
               ),
        default = 'Stretch'
    )


class MI_Curve_Guide(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.curve_guide"
    bl_label = "CurveGuide"
    bl_description = "Curve Guide"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'MOUSEMOVE']

    # curve tool mode
    tool_modes = ('IDLE', 'MOVE_LW_POINT', 'MOVE_CUR_POINT', 'SELECT_CUR_POINT')
    tool_mode = 'IDLE'

    # linear widget
    lw_tool = None
    active_lw_point = None
    tool_side_vec = None
    tool_side_vec_len = None
    tool_up_vec = None

    curve_tool = None

    deform_mouse_pos = None
    deform_vec_pos = None

    manipulator = None

    start_work_center = None
    work_verts = None
    apply_tool_verts = None

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

            if bm.verts:
                pre_verts = ut_base.get_selected_bmverts(bm)
                if not pre_verts:
                    pre_verts = [v for v in bm.verts if v.hide is False]

                # get verts bounds
                cam_x = (rv3d.view_rotation * Vector((1.0, 0.0, 0.0))).normalized()
                cam_y = (rv3d.view_rotation * Vector((0.0, 1.0, 0.0))).normalized()
                #cam_z = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()
                bounds = ut_base.get_verts_bounds(pre_verts, active_obj, cam_x, cam_y, None, False)

                self.start_work_center = bounds[3]
                #self.work_verts = [vert.index for vert in pre_verts]

                # create linear deformer
                self.lw_tool = l_widget.MI_Linear_Widget()

                start_p = None
                end_p = None
                if bounds[0] > bounds[1]:
                    start_p = self.start_work_center - (cam_x * (bounds[0] / 2.0))
                    end_p = self.start_work_center + (cam_x * (bounds[0] / 2.0))
                else:
                    start_p = self.start_work_center - (cam_y * (bounds[1] / 2.0))
                    end_p = self.start_work_center + (cam_y * (bounds[1] / 2.0))

                self.lw_tool.start_point = l_widget.MI_LW_Point(start_p)
                self.lw_tool.middle_point = l_widget.MI_LW_Point(self.start_work_center.copy())
                self.lw_tool.end_point = l_widget.MI_LW_Point(end_p)

                # Add the region OpenGL drawing callback
                # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
                # self.lin_deform_handle_3d = bpy.types.SpaceView3D.draw_handler_add(lin_def_draw_3d, args, 'WINDOW', 'POST_VIEW')
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

        curve_settings = context.scene.mi_curve_settings
        curguide_settings = context.scene.mi_curguide_settings

        # tooltip
        # tooltip_text = None
        # context.area.header_text_set(tooltip_text)

        # key pressed
        if event.type in {'LEFTMOUSE', 'SELECTMOUSE', 'RET', 'DEL'}:
            if event.value == 'PRESS':
                if self.tool_mode == 'IDLE':
                    if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                        # pick linear widget point
                        picked_point = l_widget.pick_lw_point(context, m_coords, self.lw_tool)
                        if picked_point:
                            self.deform_mouse_pos = Vector(m_coords)
                            self.active_lw_point = picked_point

                            self.tool_mode = 'MOVE_LW_POINT'

                        # curve tool pick
                        elif self.curve_tool:
                            picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point([self.curve_tool], context, m_coords)
                            if picked_point:
                                self.deform_mouse_pos = m_coords
                                self.curve_tool.active_point = picked_point.point_id
                                additive_sel = event.shift

                                cur_main.select_point(self.curve_tool, picked_point, additive_sel)

                                self.tool_mode = 'SELECT_CUR_POINT'
                            else:
                                # add point
                                if event.ctrl and self.curve_tool and self.curve_tool.active_point:
                                    act_point = cur_main.get_point_by_id(self.curve_tool.curve_points, self.curve_tool.active_point)
                                    new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, self.tool_up_vec, m_coords)

                                    if new_point_pos:
                                        new_point = cur_main.add_point(new_point_pos, self.curve_tool)
                                        fix_curve_point_pos(self.lw_tool, self.curve_tool, [new_point])

                                        self.curve_tool.active_point = new_point.point_id
                                        self.tool_mode = 'MOVE_CUR_POINT'

                                        # add to display
                                        cur_main.curve_point_changed(self.curve_tool, self.curve_tool.curve_points.index(new_point), curve_settings.curve_resolution, self.curve_tool.display_bezier)

                    elif event.type == 'RET':
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
                                v_front_dist = mathu.geometry.distance_point_to_plane(vert.co, self.lw_tool.start_point.position, lw_tool_dir)
                                if v_front_dist >= 0.0 and v_front_dist <= points_dir.length:
                                    v_side_dist = mathu.geometry.distance_point_to_plane(vert.co, self.lw_tool.start_point.position, self.tool_side_vec)
                                    v_up_dist = mathu.geometry.distance_point_to_plane(vert.co, self.lw_tool.start_point.position, self.tool_up_vec)
                                    self.work_verts[vert.index] = (vert.co.copy(), v_front_dist, v_side_dist, v_up_dist)

                            if self.work_verts:
                                # create curve
                                self.curve_tool = cur_main.MI_CurveObject(None)

                                verts = [bm.verts[vert_id] for vert_id in self.work_verts.keys()]
                                bounds = ut_base.get_verts_bounds(verts, active_obj, self.tool_side_vec, lw_tool_dir, None, False)

                                # set tool vecs
                                widget_offset = mathu.geometry.distance_point_to_plane(self.lw_tool.middle_point.position, bounds[3], self.tool_side_vec)
                                self.tool_side_vec_len = ((bounds[0] * 0.75) + abs(widget_offset))  # here we set the length of the side vec

                                # create points
                                for i in range(points_number):
                                    point = cur_main.MI_CurvePoint(self.curve_tool.curve_points)
                                    self.curve_tool.curve_points.append(point)
                                    point.position = Vector(self.lw_tool.start_point.position + ( points_dir * (float(i)/float(points_number-1)) ) ) + (self.tool_side_vec * self.tool_side_vec_len)
                                cur_main.generate_bezier_points(self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)

                    elif event.type == 'DEL':
                        sel_points = cur_main.get_selected_points(self.curve_tool.curve_points)
                        if sel_points:
                            for point in sel_points:
                                #the_act_point = cur_main.get_point_by_id(self.active_curve.curve_points, self.active_curve.active_point)
                                #the_act_point_index = self.active_curve.curve_points.index(point)

                                cur_main.delete_point(point, self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)

                            self.curve_tool.display_bezier.clear()
                            cur_main.generate_bezier_points(self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)
                            self.curve_tool.active_point = None

        # TOOL WORK!
        if self.tool_mode == 'MOVE_LW_POINT':
            if event.value == 'RELEASE':
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
            if event.value == 'RELEASE':
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # set to move point
                m_coords = event.mouse_region_x, event.mouse_region_y
                if ( Vector((m_coords[0], m_coords[1])) - Vector((self.deform_mouse_pos[0], self.deform_mouse_pos[1])) ).length > 4.0:
                    self.tool_mode = 'MOVE_CUR_POINT'
                    return {'RUNNING_MODAL'}

        elif self.tool_mode == 'MOVE_CUR_POINT':
            if event.value == 'RELEASE':
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                m_coords = event.mouse_region_x, event.mouse_region_y
                act_point = cur_main.get_point_by_id(self.curve_tool.curve_points, self.curve_tool.active_point)
                selected_points = cur_main.get_selected_points(self.curve_tool.curve_points)
                new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, self.tool_up_vec, m_coords)
                if new_point_pos and selected_points:
                    move_offset = new_point_pos - act_point.position

                    # move point
                    for point in selected_points:
                        point.position += move_offset

                    # fix points pos
                    fix_curve_point_pos(self.lw_tool, self.curve_tool, selected_points)

                    # update bezier
                    if len(selected_points) == 1:
                        cur_main.curve_point_changed(self.curve_tool, self.curve_tool.curve_points.index(point), curve_settings.curve_resolution, self.curve_tool.display_bezier)
                    else:
                        cur_main.generate_bezier_points(self.curve_tool, self.curve_tool.display_bezier, curve_settings.curve_resolution)

                return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}

        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            # bpy.types.SpaceView3D.draw_handler_remove(self.lin_deform_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.cur_guide_handle_2d, 'WINDOW')

            context.area.header_text_set()

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


def reset_params(self):
    self.tool_mode = 'IDLE'
    self.deform_mouse_pos = None
    self.deform_vec_pos = None
    self.manipulator = None

    self.lw_tool = None
    self.active_lw_point = None
    self.tool_side_vec = None
    self.tool_side_vec_len = None
    self.tool_up_vec = None

    self.curve_tool = None

    self.start_work_center = None
    self.work_verts = None
    self.apply_tool_verts = None


def update_mesh_to_curve(lw_tool, curve_tool, work_verts, bm):
    for vert_id in work_verts.keys():
        vert = bm.verts[vert_id]
        vert_data = work_verts[vert_id]


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
    rv3d = context.region_data
    curve_settings = context.scene.mi_curve_settings
    if self.lw_tool:
        lw_dir = (self.lw_tool.start_point.position - self.lw_tool.end_point.position).normalized()
        cam_view = (rv3d.view_rotation * Vector((0.0, 0.0, -1.0))).normalized()
        side_dir = lw_dir.cross(cam_view).normalized()
        l_widget.draw_lw(context, self.lw_tool, side_dir, False)

    if self.curve_tool:
        draw_curve_lines_2d(self.curve_tool, context)
        draw_curve_points_2d(self.curve_tool, context, curve_settings)


def draw_curve_points_2d(curve, context, curve_settings):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_curve_settings

    for cu_point in curve.curve_points:
        point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.position)

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
        draw_point_2d(point_pos_2d, 6, p_col)

        # Handlers
        if curve_settings.draw_handlers:
        #if curve.curve_points.index(cu_point) < len(curve.curve_points)-1:
            if cu_point.handle1:
                point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle1)
                draw_point_2d(point_pos_2d, 3, col_man.cur_handle_1_base)
        #if curve.curve_points.index(cu_point) > 0:
            if cu_point.handle2:
                point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle2)
                draw_point_2d(point_pos_2d, 3, col_man.cur_handle_2_base)


def draw_curve_lines_2d(curve, context):
    region = context.region
    rv3d = context.region_data
    active_obj = context.scene.objects.active

    for cur_point in curve.curve_points:
        if cur_point.point_id in curve.display_bezier:
            points_2d = []
            for b_point in curve.display_bezier[cur_point.point_id]:
                point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, b_point)
                points_2d.append(point_pos_2d)
            draw_polyline_2d(points_2d, 1, col_man.cur_line_base)


# TODO MOVE TO UTILITIES
def draw_point_2d(point, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
    bgl.glEnable(bgl.GL_BLEND)
    #bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
    #bgl.glLineWidth(2)

    bgl.glPointSize(p_size)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_POINTS)
 #   bgl.glBegin(bgl.GL_POLYGON)
    bgl.glColor4f(p_col[0], p_col[1], p_col[2], p_col[3])
    bgl.glVertex2f(point[0], point[1])
    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# TODO MOVE TO UTILITIES
def draw_polyline_2d(points, pl_size=1, p_col=(1.0,1.0,1.0,1.0)):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(pl_size)

    #bgl.glPointSize(p_size)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glColor4f(p_col[0], p_col[1], p_col[2], p_col[3])
 #   bgl.glBegin(bgl.GL_POLYGON)

    for point in points:
        bgl.glVertex2f(point[0], point[1])
        #bgl.glVertex3f(point[0], point[1], point[2])

    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
