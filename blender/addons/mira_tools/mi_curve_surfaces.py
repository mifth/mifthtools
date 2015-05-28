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
from mathutils import Vector

from . import mi_curve_main as cur_main
from . import mi_utils_base as ut_base
from . import mi_color_manager as col_man
from . import mi_looptools as loop_t


#class MI_CurveSurfacesSettings(bpy.types.PropertyGroup):
    #points_number = IntProperty(default=5, min=2, max=128)
    #spread_mode = EnumProperty(
        #name = "Spread Mode",
        #items = (('Original', 'Original', ''),
                #('Uniform', 'Uniform', '')
                #),
        #default = 'Original'
    #)


class MI_SurfaceObject():

    # class constructor
    def __init__(self, other_surfaces, main_loop, surf_type, bm, obj):

        self.main_loop = main_loop
        self.main_loop_center = None
        # main_loop_center WILL BE STORED IN WORLD COORDINATES
        if main_loop:
            loop_verts_pos = [bm.verts[vert_id] for vert_id in main_loop[0]]
            self.main_loop_center = ut_base.get_vertices_center(loop_verts_pos, obj, False)

        self.all_curves = []
        self.active_curve = None
        self.curves_verts = {}  # verts ids per curve

        # surf_type is a type of loops to draw
        self.surf_type = surf_type
        self.surf_id = None  # string

        other_surfs_ids = None
        if other_surfaces:
            other_surfs_ids = get_surfs_ids(other_surfaces)
        self.surf_id = ut_base.generate_id(other_surfs_ids)


class MI_CurveSurfaces(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.curve_surfaces"
    bl_label = "Curve Surfaces"
    bl_description = "Curve Surface"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'MOUSEMOVE']

    # curve tool mode
    surf_tool_modes = ('IDLE', 'MOVE_POINT', 'SELECT_POINT', 'CREATE_CURVE')
    surf_tool_mode = 'IDLE'

    all_surfs = None
    active_surf = None
    deform_mouse_pos = None

    picked_meshes = None

    # loops code
    #loops = None
    #original_verts_data = None

    manipulator = None

    def invoke(self, context, event):
        reset_params(self)

        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)

            curve_settings = context.scene.mi_curve_settings

            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)

            # get loops
            all_loops = loop_t.get_connected_input(bm)
            all_loops = loop_t.check_loops(all_loops, bm)
            for loop in all_loops:
                surf = MI_SurfaceObject(self.all_surfs, loop, None, bm, active_obj)
                self.all_surfs.append(surf)

            # get meshes for snapping
            if curve_settings.surface_snap is True:
                sel_objects = [
                    obj for obj in context.selected_objects if obj != active_obj]
                if sel_objects:
                    self.picked_meshes = ut_base.get_obj_dup_meshes(
                        sel_objects, context)

            self.manipulator = context.space_data.show_manipulator
            context.space_data.show_manipulator = False

            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'
            self.mi_curve_surf_3d = bpy.types.SpaceView3D.draw_handler_add(mi_surf_draw_3d, args, 'WINDOW', 'POST_VIEW')
            self.mi_curve_surf_2d = bpy.types.SpaceView3D.draw_handler_add(mi_surf_draw_2d, args, 'WINDOW', 'POST_PIXEL')

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        context.area.header_text_set("NewPoint: Ctrl+Click, SelectAdditive: Shift+Click, DeletePoint: Del, SurfaceSnap: Shift+Tab, SelectLinked: L/Shift+L")

        curve_settings = context.scene.mi_curve_settings
        m_coords = event.mouse_region_x, event.mouse_region_y

        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)
        region = context.region
        rv3d = context.region_data

        # make picking
        if self.surf_tool_mode == 'IDLE' and event.value == 'PRESS':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                # pick point test
                picked_point, picked_curve, picked_surf = pick_all_surfs_point(self.all_surfs, context, m_coords)
                if picked_point:
                    self.deform_mouse_pos = m_coords
                    self.active_surf = picked_surf
                    self.active_surf.active_curve = picked_curve
                    self.active_surf.active_curve.active_point = picked_point.point_id
                    additive_sel = event.shift

                    if additive_sel is False and picked_point.select is False:
                        for surf in self.all_surfs:
                            if surf is not self.active_surf:
                                for curve in surf.all_curves:
                                    cur_main.select_all_points(curve.curve_points, False)  # deselect points
                                    curve.active_point = None
                            else:
                                for curve in surf.all_curves:
                                    if curve is not self.active_surf.active_curve:
                                        cur_main.select_all_points(curve.curve_points, False)  # deselect points
                                        curve.active_point = None                                

                    cur_main.select_point(self.active_surf.active_curve, picked_point, additive_sel)

                    self.surf_tool_mode = 'SELECT_POINT'
                else:
                    # add point
                    if event.ctrl and self.active_surf and self.active_surf.active_curve and self.active_surf.active_curve.active_point:
                        act_point = cur_main.get_point_by_id(self.active_surf.active_curve.curve_points, self.active_surf.active_curve.active_point)
                        new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)
                        new_point = add_curve_point(self, m_coords, curve_settings, new_point_pos)
                        self.surf_tool_mode = 'MOVE_POINT'

                    # pick surf
                    else:
                        picked_surf = pick_surf(self.all_surfs, context, m_coords)
                        if picked_surf:
                            self.active_surf = picked_surf

                #return {'RUNNING_MODAL'}

            #elif event.type in {'DEL'} and event.value == 'PRESS':
                #for curve in self.all_curves:
                    #sel_points = cur_main.get_selected_points(curve.curve_points)
                    #if sel_points:
                        #for point in sel_points:
                            ##the_act_point = cur_main.get_point_by_id(curve.curve_points, curve.active_point)
                            ##the_act_point_index = curve.curve_points.index(point)

                            #cur_main.delete_point(point, curve, curve.display_bezier, curve_settings.curve_resolution)

                        #curve.display_bezier.clear()
                        #cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)
                        #curve.active_point = None

                ##return {'RUNNING_MODAL'}

            elif event.type in {'TAB'} and event.shift:
                if curve_settings.surface_snap is True:
                    curve_settings.surface_snap = False
                else:
                    curve_settings.surface_snap = True
                    if not self.picked_meshes:
                        # get meshes for snapping
                        sel_objects = [
                            obj for obj in context.selected_objects if obj != active_obj]
                        if sel_objects:
                            self.picked_meshes = ut_base.get_obj_dup_meshes(
                                sel_objects, context)

            ## Select Linked
            #elif event.type == 'L':
                #picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point(self.all_curves, context, m_coords)

                #if picked_point:
                    #if not event.shift:
                        #for curve in self.all_curves:
                            #if curve is not picked_curve:
                                #cur_main.select_all_points(curve.curve_points, False)
                                #curve.active_point = None

                    #cur_main.select_all_points(picked_curve.curve_points, True)
                    #picked_curve.active_point = picked_point.point_id
                    #self.active_curve = picked_curve

            # Create Curve
            elif event.type == 'N' and self.active_surf:
               self.surf_tool_mode = 'CREATE_CURVE'

        # TOOL WORK
        if self.surf_tool_mode == 'SELECT_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.surf_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # set to move point
                if ( Vector((m_coords[0], m_coords[1])) - Vector((self.deform_mouse_pos[0], self.deform_mouse_pos[1])) ).length > 4.0:
                    self.surf_tool_mode = 'MOVE_POINT'
                    return {'RUNNING_MODAL'}

        elif self.surf_tool_mode == 'MOVE_POINT':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.surf_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                # move points
                act_point = cur_main.get_point_by_id(self.active_surf.active_curve.curve_points, self.active_surf.active_curve.active_point)
                new_point_pos = ut_base.get_mouse_on_plane(context, act_point.position, None, m_coords)
                if new_point_pos:
                    move_offset = new_point_pos - act_point.position
                    for surf in self.all_surfs:
                        for curve in surf.all_curves:
                            selected_points = cur_main.get_selected_points(curve.curve_points)
                            if selected_points:
                                # Snap to Surface
                                if curve_settings.surface_snap is True:
                                    if self.picked_meshes:
                                        for point in selected_points:
                                            # get the ray from the viewport and mouse
                                            point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, point.position + move_offset)
                                            if point_pos_2d:
                                                best_obj, hit_normal, hit_position = ut_base.get_mouse_raycast(context, self.picked_meshes, point_pos_2d, 10000.0)
                                                #best_obj, hit_normal, hit_position = ut_base.get_3dpoint_raycast(context, self.picked_meshes, point.position + move_offset, camera_dir, 10000.0)
                                            if hit_position:
                                                point.position = hit_position

                                # Move Points without Snapping
                                else:
                                    for point in selected_points:
                                        point.position += move_offset

                                if len(selected_points) == 1:
                                    cur_main.curve_point_changed(curve, curve.curve_points.index(selected_points[0]), curve_settings.curve_resolution, curve.display_bezier)
                                else:
                                    cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)

                return {'RUNNING_MODAL'}

        elif self.surf_tool_mode == 'CREATE_CURVE':
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.surf_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                #if event.ctrl:
                if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'PRESS':
                    #act_point = cur_main.get_point_by_id(self.active_surf.active_curve.curve_points, self.active_surf.active_curve.active_point)
                    new_point_pos = ut_base.get_mouse_on_plane(context, self.active_surf.main_loop_center, None, m_coords)
                    #new_point = add_curve_point(self, m_coords, curve_settings, new_point_pos)

                    if new_point_pos:
                        # deselect all points
                        for surf in self.all_surfs:
                            cur_main.deselect_all_curves(surf.all_curves, True)

                        # new curve
                        cur = cur_main.MI_CurveObject(self.active_surf.all_curves)
                        self.active_surf.all_curves.append(cur)
                        self.active_surf.active_curve = cur  # set active curve

                        # new point
                        new_point = cur_main.MI_CurvePoint(cur.curve_points)
                        cur.curve_points.append(new_point)
                        new_point.position = new_point_pos.copy()
                        new_point.select = True
                        self.active_surf.active_curve.active_point = new_point.point_id

                        self.surf_tool_mode = 'MOVE_POINT'
                    return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                self.surf_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}


        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_curve_surf_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_curve_surf_2d, 'WINDOW')

            # clear
            finish_work(self, context)

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}


def reset_params(self):
    # reset base curve_settings
    self.surf_tool_mode = 'IDLE'
    self.all_surfs = []
    self.active_surf = None
    self.deform_mouse_pos = None
    self.picked_meshes = None

    #self.loops = None


def finish_work(self, context):
    context.space_data.show_manipulator = self.manipulator


def add_curve_point(self, m_coords, curve_settings, point_pos):
    new_point_pos = point_pos

    for surf in self.all_surfs:
        if surf is not self.active_surf:
            cur_main.deselect_all_curves(surf.all_curves, True)

    new_point = cur_main.add_point(new_point_pos, self.active_surf.active_curve)

    self.active_surf.active_curve.active_point = new_point.point_id

    # add to display
    cur_main.curve_point_changed(self.active_surf.active_curve, self.active_surf.active_curve.curve_points.index(new_point), curve_settings.curve_resolution, self.active_surf.active_curve.display_bezier)

    return new_point


def create_surface_loop(curve_to_spread, prev_loop_verts, bm, obj):
    next_loop_verts = []
    next_loop_verts_ids = []

    for i in range(len(prev_loop_verts)):
        vert = bm.verts.new((0.0, 0.0, 0.0))
        next_loop_verts.append(vert)
        next_loop_verts_ids.append(vert.index)

    update_curve_line(obj, curve_to_spread, next_loop_verts)


def update_curve_line(obj, curve_to_spread, loop_verts):
    line = cur_main.get_bezier_line(curve_to_spread, obj, True)
    cur_main.verts_to_line(loop_verts, line, None, curve_to_spread.closed)  # Uniform Spread


def get_surfs_ids(surfaces):
    other_ids = []
    for surf in surfaces:
        other_ids.append(surf.surf_id)

    return other_ids


def pick_all_surfs_point(all_surfs, context, mouse_coords):
    best_point = None
    best_length = None
    choosen_curve = None
    choosen_surf = None

    for surf in all_surfs:
        picked_point, picked_length, picked_curve = cur_main.pick_all_curves_point(surf.all_curves, context, mouse_coords)

        if picked_point is not None:
            if best_point is None:
                choosen_surf = surf
                choosen_curve = picked_curve
                best_point = picked_point
                best_length = picked_length
            elif picked_length < best_length:
                choosen_surf = surf
                choosen_curve = picked_curve
                best_point = picked_point
                best_length = picked_length

    return best_point, choosen_curve, choosen_surf


def pick_surf(all_surfs, context, mouse_coords):
    region = context.region
    rv3d = context.region_data

    picked_surf = None
    picked_point_length = None
    mouse_vec = Vector(mouse_coords)
    for surf in all_surfs:
        if surf.main_loop_center:
            point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, surf.main_loop_center)
            the_length = (point_pos_2d - mouse_vec).length
            if the_length <= 9.0:
                if picked_surf is None:
                    picked_surf = surf
                    picked_point_length = the_length
                else:
                    if the_length < picked_point_length:
                        picked_surf = surf
                        picked_point_length = the_length                    

    return picked_surf


def mi_surf_draw_2d(self, context):
    active_obj = context.scene.objects.active
    if self.all_surfs:
        draw_surf_2d(self.all_surfs, self.active_surf, context)


def mi_surf_draw_3d(self, context):
    active_obj = context.scene.objects.active
    for surf in self.all_surfs:
        if surf.all_curves:
            # test1
            region = context.region
            rv3d = context.region_data
            for curve in surf.all_curves:
                for cur_point in curve.curve_points:
                    if cur_point.point_id in curve.display_bezier:
                        mi_draw_3d_polyline(curve.display_bezier[cur_point.point_id], 2, col_man.cur_line_base, True)


def draw_surf_2d(surfs, active_surf, context):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_curve_settings
    # coord = event.mouse_region_x, event.mouse_region_y
    for surf in surfs:
        # draw loops center
        if surf.main_loop_center:
            surf_center_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, surf.main_loop_center)
            if surf_center_2d:
                if surf is active_surf:
                    mi_draw_2d_point(surf_center_2d.x, surf_center_2d.y, 6, (0.7,0.75,0.95,1.0))
                else:
                    mi_draw_2d_point(surf_center_2d.x, surf_center_2d.y, 6, (0.5,0.5,0.8,1.0))

        # draw curves points
        for curve in surf.all_curves:
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
                    if active_surf and cu_point.point_id == curve.active_point and curve is active_surf.active_curve:
                        p_col = col_man.cur_point_active
                    mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, p_col)

                    # Handlers
                    if curve_settings.draw_handlers:
                    #if curve.curve_points.index(cu_point) < len(curve.curve_points)-1:
                        if cu_point.handle1:
                            handle_1_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle1)
                            if handle_1_pos_2d:
                                mi_draw_2d_point(handle_1_pos_2d.x, handle_1_pos_2d.y, 3, col_man.cur_handle_1_base)
                    #if curve.curve_points.index(cu_point) > 0:
                        if cu_point.handle2:
                            handle_2_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle2)
                            if handle_2_pos_2d:
                                mi_draw_2d_point(handle_2_pos_2d.x, handle_2_pos_2d.y, 3, col_man.cur_handle_2_base)


# TODO MOVE TO UTILITIES
def mi_draw_2d_point(point_x, point_y, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
    bgl.glEnable(bgl.GL_BLEND)
    #bgl.glColor4f(1.0, 1.0, 1.0, 0.5)
    #bgl.glLineWidth(2)

    bgl.glPointSize(p_size)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_POINTS)
 #   bgl.glBegin(bgl.GL_POLYGON)
    bgl.glColor4f(p_col[0], p_col[1], p_col[2], p_col[3])
    bgl.glVertex2f(point_x, point_y)
    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)


# TODO MOVE TO UTILITIES
def mi_draw_3d_polyline(points, p_size, p_col, x_ray):
    bgl.glEnable(bgl.GL_BLEND)
    bgl.glLineWidth(1)

    if x_ray is True:
        bgl.glDisable(bgl.GL_DEPTH_TEST)

    bgl.glPointSize(p_size)
#    bgl.glBegin(bgl.GL_LINE_LOOP)
    bgl.glBegin(bgl.GL_LINE_STRIP)
    bgl.glColor4f(p_col[0], p_col[1], p_col[2], p_col[3])
 #   bgl.glBegin(bgl.GL_POLYGON)

    for point in points:
        bgl.glVertex3f(point[0], point[1], point[2])

    if x_ray is True:
        bgl.glEnable(bgl.GL_DEPTH_TEST)

    bgl.glEnd()

    # restore opengl defaults
    bgl.glLineWidth(1)
    bgl.glDisable(bgl.GL_BLEND)
    bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

