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

from . import mi_curve_main as cur_main
from . import mi_utils_base as ut_base
from . import mi_color_manager as col_man
from . import mi_looptools as loop_t
from . import mi_inputs
from . import mi_widget_select as s_widget
from . import mi_widget_curve as c_widget


class MI_CurveSurfacesSettings(bpy.types.PropertyGroup):
    spread_loops_type = EnumProperty(
        name = "Spread Loops",
        items = (('OnCurve', 'OnCurve', ''),
                ('Interpolate', 'Interpolate', '')
                ),
        default = 'OnCurve'
    )


# extended class of cur_main.MI_CurveObject
class MI_SurfaceCurveObject(cur_main.MI_CurveObject):
    def __init__(self, *args, **kwargs):
        super(MI_SurfaceCurveObject, self).__init__(*args, **kwargs)
        self.curve_verts_ids = None  # This is ids only
        #curve_faces_ids = None


class MI_SurfaceObject():

    # class constructor
    def __init__(self, other_surfaces, main_loop_ids, loop_verts, surf_type, bm, obj, spread_loops_type):

        self.main_loop_ids = main_loop_ids
        self.main_loop_center = None
        self.original_loop_data = None  # stored in local coordinates!

        self.loop_points = 5  # only for non loop_based surfs

        # There are types to spread 'OnCurve', 'Interpolate'
        self.spread_type = spread_loops_type
        self.cross_loop_points = 6  # only for 'Uniform' type
        self.uniform_loops = []  # only for 'Uniform' type

        # main_loop_center WILL BE STORED IN WORLD COORDINATES
        if main_loop_ids:
            self.main_loop_center = ut_base.get_vertices_center(loop_verts, obj, False)
            self.original_loop_data = cur_main.pass_line([vert.co.copy() for vert in loop_verts] , False)

        self.all_curves = []
        self.active_curve = None
        #self.curves_verts = {}  # verts ids per curve id

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

    # curve tool mode
    surf_tool_modes = ('IDLE', 'MOVE_POINT', 'SELECT_POINT', 'CREATE_CURVE', 'CREATE_SURFACE')
    surf_tool_mode = 'IDLE'

    all_surfs = None
    active_surf = None
    deform_mouse_pos = None

    picked_meshes = None

    id_layer = None
    id_value = None

    # loops code
    #loops = None
    #original_verts_data = None

    manipulator = None

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)

            curve_settings = context.scene.mi_settings
            cur_surfs_settings = context.scene.mi_cur_surfs_settings

            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)
            reset_params(self, bm)

            # get loops
            all_loops = loop_t.get_connected_input(bm)
            all_loops = loop_t.check_loops(all_loops, bm)
            for loop in all_loops:
                # check if loop is closed
                # cloased loops are not supported
                if loop[1] is False:

                    # change loops verts ids to custom ids
                    loop_ids = []
                    loop_verts = []
                    for vert_id in loop[0]:
                        vert = bm.verts[vert_id]
                        vert[self.id_layer] = self.id_value
                        loop_ids.append(self.id_value)
                        loop_verts.append(vert)
                        self.id_value += 1

                    # create surface object
                    surf = MI_SurfaceObject(self.all_surfs, loop_ids, loop_verts, None, bm, active_obj, cur_surfs_settings.spread_loops_type)
                    self.all_surfs.append(surf)

            # get meshes for snapping
            if curve_settings.surface_snap is True:
                meshes_array = ut_base.get_obj_dup_meshes(curve_settings.snap_objects, curve_settings.convert_instances, context)
                if meshes_array:
                    self.picked_meshes = meshes_array

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
        #print(event.type)
        context.area.tag_redraw()

        context.area.header_text_set("NewSurface: Shift+A, NewCurve: A, Add/Remove Loops: +/-, Add/Remove CrossLoops: Ctrl++/Ctrl+-, NewPoint: Ctrl+Click, SelectAdditive: Shift+Click, DeletePoint: Del, SurfaceSnap: Shift+Tab, SelectLinked: L/Shift+L, SpreadMode: M")

        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences
        curve_settings = context.scene.mi_settings
        cur_surfs_settings = context.scene.mi_cur_surfs_settings
        m_coords = event.mouse_region_x, event.mouse_region_y

        active_obj = context.scene.objects.active
        bm = bmesh.from_edit_mesh(active_obj.data)
        region = context.region
        rv3d = context.region_data

        keys_pass = mi_inputs.get_input_pass(mi_inputs.pass_keys, addon_prefs.key_inputs, event)

        # make picking
        if self.surf_tool_mode == 'IDLE' and event.value == 'PRESS' and keys_pass is False:
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

                        # here we create a loop of polygons
                        if len(self.active_surf.active_curve.curve_points) > 1:
                            do_create_loops = False
                            curve_index = self.active_surf.all_curves.index(self.active_surf.active_curve)

                            if self.active_surf.spread_type == 'OnCurve' and not self.active_surf.active_curve.curve_verts_ids:
                                # fix direction of loop
                                if len(self.active_surf.active_curve.curve_points) == 2:
                                    fix_curve_direction(self.active_surf, self.active_surf.active_curve, self.id_layer, bm, active_obj, curve_settings)

                                # logic for loop based curve
                                if self.active_surf.main_loop_ids:
                                    if curve_index > 0 and not self.active_surf.all_curves[curve_index - 1].curve_verts_ids:
                                        do_create_loops = False
                                    else:
                                        do_create_loops = True

                                # logic for non loop based curve
                                else:
                                    if curve_index > 1 and not self.active_surf.all_curves[curve_index - 1].curve_verts_ids:
                                        do_create_loops = False
                                    else:
                                        if curve_index > 0:
                                            do_create_loops = True

                                # create polygon loops
                                if do_create_loops:
                                    new_loop_verts = create_surface_loop(self.active_surf, self.active_surf.active_curve, bm, active_obj, curve_settings, self)
                                    self.active_surf.active_curve.curve_verts_ids = new_loop_verts

                                    bmesh.update_edit_mesh(active_obj.data)

                            elif self.active_surf.spread_type == 'Interpolate':
                                # fix direction of loop
                                if len(self.active_surf.active_curve.curve_points) == 2:
                                    fix_curve_direction(self.active_surf, self.active_surf.active_curve, self.id_layer, bm, active_obj, curve_settings)

                                if not self.active_surf.uniform_loops:
                                    # logic for loop based curve
                                    if self.active_surf.main_loop_ids:
                                        do_create_loops = True
                                    # logic for non loop based curve
                                    elif not self.active_surf.main_loop_ids and len(self.active_surf.all_curves) > 1:
                                        do_create_loops = True

                                    if do_create_loops:
                                        all_loops_verts = []

                                        loop_count = self.active_surf.cross_loop_points
                                        if self.active_surf.main_loop_ids:
                                            main_loop_verts = ut_base.get_verts_from_ids(self.active_surf.main_loop_ids, self.id_layer, bm)
                                            all_loops_verts.append(main_loop_verts)
                                            loop_count -= 1

                                        for i in range(loop_count):
                                            loop_verts = []
                                            loop_verts_ids = []

                                            verts_range = self.active_surf.loop_points
                                            if self.active_surf.main_loop_ids:
                                                verts_range = len(self.active_surf.main_loop_ids)

                                            for i in range(verts_range):
                                                vert = bm.verts.new((0.0, 0.0, 0.0))
                                                vert[self.id_layer] = self.id_value
                                                loop_verts.append(vert)
                                                loop_verts_ids.append(self.id_value)
                                                self.id_value += 1

                                            self.active_surf.uniform_loops.append(loop_verts_ids)
                                            all_loops_verts.append(loop_verts)

                                        # spread verts
                                        spread_verts_uniform(active_obj, self.active_surf, all_loops_verts, curve_settings)

                                        # create polygons
                                        for i, verts in enumerate(all_loops_verts):
                                            if i > 0:
                                                new_faces = create_polyloops(verts, all_loops_verts[i-1], bm)

                                        bmesh.update_edit_mesh(active_obj.data)

                        self.surf_tool_mode = 'MOVE_POINT'

                    # pick surf
                    else:
                        picked_surf = pick_surf(self.all_surfs, context, m_coords)
                        if picked_surf:
                            self.active_surf = picked_surf

            elif event.type in {'DEL'}:
                for surf in self.all_surfs:
                    for curve in surf.all_curves:
                        sel_points = cur_main.get_selected_points(curve.curve_points)
                        if sel_points and len(curve.curve_points) > 2:
                            # we revers to leave first points
                            for point in reversed(sel_points):
                                if len(curve.curve_points) > 2:
                                    cur_main.delete_point(point, curve, curve.display_bezier, curve_settings.curve_resolution)
                                else:
                                    point.select = False

                            curve.display_bezier.clear()
                            cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)

                            if self.active_surf.spread_type == 'OnCurve':
                                # move points to the curve
                                if curve.curve_verts_ids:
                                    verts_update = ut_base.get_verts_from_ids(curve.curve_verts_ids, self.id_layer, bm)
                                    update_curve_line(active_obj, curve, verts_update, curve_settings.spread_mode, surf.original_loop_data)
                            else:
                                if self.active_surf.uniform_loops:
                                    all_loops_verts = []

                                    # get all verts
                                    if surf.main_loop_ids:
                                        main_loop_verts = ut_base.get_verts_from_ids(surf.main_loop_ids, self.id_layer, bm)
                                        all_loops_verts.append(main_loop_verts)

                                    for verts_loop_ids in surf.uniform_loops:
                                        curve_verts = ut_base.get_verts_from_ids(verts_loop_ids, self.id_layer, bm)
                                        all_loops_verts.append(curve_verts)

                                    # spread verts
                                    spread_verts_uniform(active_obj, surf, all_loops_verts, curve_settings)

                        else:
                            for point in sel_points:
                                point.select = False

                        curve.active_point = None

                    surf.active_curve = None

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

            elif event.type in {'TAB'} and event.shift:
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
            elif event.type == 'L':
                picked_point, picked_curve, picked_surf = pick_all_surfs_point(self.all_surfs, context, m_coords)
                if picked_point:
                    if not event.shift:
                        for surf in self.all_surfs:
                            for curve in surf.all_curves:
                                if curve is not picked_curve:
                                    cur_main.select_all_points(curve.curve_points, False)
                                    curve.active_point = None

                    cur_main.select_all_points(picked_curve.curve_points, True)
                    self.active_surf = picked_surf
                    self.active_surf.active_curve = picked_curve
                    self.active_surf.active_curve.active_point = picked_point.point_id

            # Change Spread Type
            elif event.type == 'M':
                if curve_settings.spread_mode == 'Original':
                    curve_settings.spread_mode = 'Uniform'
                else:
                    curve_settings.spread_mode = 'Original'

                if self.active_surf.spread_type == 'OnCurve':
                    for surf in self.all_surfs:
                        for curve in surf.all_curves:
                            # move points to the curve
                            verts_update = ut_base.get_verts_from_ids(curve.curve_verts_ids, self.id_layer, bm)
                            update_curve_line(active_obj, curve, verts_update, curve_settings.spread_mode, surf.original_loop_data)

                elif self.active_surf.spread_type == 'Interpolate' and self.active_surf.uniform_loops:
                    all_loops_verts = []

                    if self.active_surf.main_loop_ids:
                        main_loop_verts = ut_base.get_verts_from_ids(self.active_surf.main_loop_ids, self.id_layer, bm)
                        all_loops_verts.append(main_loop_verts)

                    # get all verts
                    for verts_loop_ids in self.active_surf.uniform_loops:
                        curve_verts = ut_base.get_verts_from_ids(verts_loop_ids, self.id_layer, bm)
                        all_loops_verts.append(curve_verts)

                    spread_verts_uniform(active_obj, self.active_surf, all_loops_verts, curve_settings)

                # update mesh
                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

            # Create Curve
            elif event.type == 'A':
                if event.shift:
                    self.surf_tool_mode = 'CREATE_SURFACE'
                elif self.active_surf:
                    self.surf_tool_mode = 'CREATE_CURVE'

            elif event.type in {'NUMPAD_PLUS', 'NUMPAD_MINUS', 'MINUS', 'EQUAL'}:
                if event.type in {'NUMPAD_PLUS', 'EQUAL'}:
                    if not event.ctrl:
                        if self.active_surf and not self.active_surf.main_loop_ids:
                            new_verts = []
                            prev_verts = []

                            # OnCurve method
                            if self.active_surf.spread_type == 'OnCurve':
                                for curve in self.active_surf.all_curves:
                                    if curve.curve_verts_ids:
                                        vert = bm.verts.new((0.0, 0.0, 0.0))
                                        vert[self.id_layer] = self.id_value
                                        new_verts.append(vert)

                                        curve_verts = ut_base.get_verts_from_ids(curve.curve_verts_ids, self.id_layer, bm)
                                        prev_verts.append(curve_verts[-1])  # get previous point
                                        curve_verts.append(vert)
                                        curve.curve_verts_ids.append(self.id_value)
                                        update_curve_line(active_obj, curve, curve_verts, curve_settings.spread_mode, self.active_surf.original_loop_data)

                                        self.id_value += 1

                                self.active_surf.loop_points += 1
                                bm.verts.ensure_lookup_table()
                                if new_verts and prev_verts:
                                    create_polyloops(new_verts, prev_verts, bm)

                            # Interpolate method
                            else:
                                if self.active_surf.uniform_loops:
                                    all_loops_verts = []

                                    for verts_loop_ids in self.active_surf.uniform_loops:
                                        vert = bm.verts.new((0.0, 0.0, 0.0))
                                        vert[self.id_layer] = self.id_value
                                        new_verts.append(vert)

                                        curve_verts = ut_base.get_verts_from_ids(verts_loop_ids, self.id_layer, bm)
                                        prev_verts.append(curve_verts[-1])  # get previous point
                                        verts_loop_ids.append(self.id_value)

                                        curve_verts.append(vert)
                                        all_loops_verts.append(curve_verts)

                                        self.id_value += 1

                                    # spread verts
                                    self.active_surf.loop_points += 1
                                    spread_verts_uniform(active_obj, self.active_surf, all_loops_verts, curve_settings)

                                    bm.verts.ensure_lookup_table()
                                    if new_verts and prev_verts:
                                        create_polyloops(new_verts, prev_verts, bm)

                    # only for cross loops
                    else:
                        if self.active_surf.spread_type == 'Interpolate' and self.active_surf.uniform_loops:
                            all_loops_verts = []
                            new_verts = []
                            new_verts_ids = []
                            prev_verts = ut_base.get_verts_from_ids(self.active_surf.uniform_loops[-1], self.id_layer, bm)

                            if self.active_surf.main_loop_ids:
                                main_loop_verts = ut_base.get_verts_from_ids(self.active_surf.main_loop_ids, self.id_layer, bm)
                                all_loops_verts.append(main_loop_verts)

                            for verts_loop_ids in self.active_surf.uniform_loops:
                                curve_verts = ut_base.get_verts_from_ids(verts_loop_ids, self.id_layer, bm)
                                all_loops_verts.append(curve_verts)

                            verts_range = self.active_surf.loop_points
                            if self.active_surf.main_loop_ids:
                                verts_range = len(self.active_surf.main_loop_ids)

                            for verts_loop_ids in range(verts_range):
                                vert = bm.verts.new((0.0, 0.0, 0.0))
                                vert[self.id_layer] = self.id_value
                                new_verts.append(vert)
                                new_verts_ids.append(self.id_value)

                                self.id_value += 1

                            self.active_surf.uniform_loops.append(new_verts_ids)
                            self.active_surf.cross_loop_points += 1
                            all_loops_verts.append(new_verts)

                            # spread verts
                            spread_verts_uniform(active_obj, self.active_surf, all_loops_verts, curve_settings)

                            bm.verts.ensure_lookup_table()
                            if new_verts and prev_verts:
                                create_polyloops(new_verts, prev_verts, bm)

                elif event.type in {'NUMPAD_MINUS', 'MINUS'}:
                    verts_to_remove = []

                    if not event.ctrl:
                        if self.active_surf and not self.active_surf.main_loop_ids and self.active_surf.loop_points > 2:
                            # OnCurve method
                            if self.active_surf.spread_type == 'OnCurve':
                                for curve in self.active_surf.all_curves:
                                    if curve.curve_verts_ids and len(curve.curve_verts_ids) > 2:
                                        curve_verts = ut_base.get_verts_from_ids(curve.curve_verts_ids, self.id_layer, bm)
                                        last_vert = curve_verts[-1]

                                        curve.curve_verts_ids.remove(curve.curve_verts_ids[-1])
                                        curve_verts.remove(curve_verts[-1])
                                        verts_to_remove.append(last_vert)
                                        update_curve_line(active_obj, curve, curve_verts, curve_settings.spread_mode, self.active_surf.original_loop_data)

                                self.active_surf.loop_points -= 1
                                bmesh.ops.delete(bm, geom=verts_to_remove, context=1)
                                bm.verts.ensure_lookup_table()

                            # Interpolate method
                            else:
                                if self.active_surf.spread_type == 'Interpolate' and self.active_surf.uniform_loops:
                                    all_loops_verts = []

                                    # get all verts
                                    for verts_loop_ids in self.active_surf.uniform_loops:
                                        curve_verts = ut_base.get_verts_from_ids(verts_loop_ids, self.id_layer, bm)
                                        last_vert = curve_verts[-1]

                                        verts_loop_ids.remove(verts_loop_ids[-1])
                                        curve_verts.remove(curve_verts[-1])
                                        verts_to_remove.append(last_vert)

                                        all_loops_verts.append(curve_verts)

                                    self.active_surf.loop_points -= 1
                                    spread_verts_uniform(active_obj, self.active_surf, all_loops_verts, curve_settings)

                                    bmesh.ops.delete(bm, geom=verts_to_remove, context=1)
                                    bm.verts.ensure_lookup_table()

                    # only for cross loops
                    else:
                        if self.active_surf.spread_type == 'Interpolate' and self.active_surf.uniform_loops and len(self.active_surf.uniform_loops) > 2:
                            all_loops_verts = []
                            verts_to_remove = ut_base.get_verts_from_ids(self.active_surf.uniform_loops[-1], self.id_layer, bm)

                            # remove verts
                            bmesh.ops.delete(bm, geom=verts_to_remove, context=1)
                            bm.verts.ensure_lookup_table()
                            self.active_surf.cross_loop_points -= 1
                            self.active_surf.uniform_loops.remove(self.active_surf.uniform_loops[-1])

                            # get all verts
                            if self.active_surf.main_loop_ids:
                                main_loop_verts = ut_base.get_verts_from_ids(self.active_surf.main_loop_ids, self.id_layer, bm)
                                all_loops_verts.append(main_loop_verts)

                            for verts_loop_ids in self.active_surf.uniform_loops:
                                curve_verts = ut_base.get_verts_from_ids(verts_loop_ids, self.id_layer, bm)
                                all_loops_verts.append(curve_verts)

                            # spread verts
                            spread_verts_uniform(active_obj, self.active_surf, all_loops_verts, curve_settings)

                bmesh.update_edit_mesh(active_obj.data)

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

                # Snap to Surface
                if curve_settings.surface_snap is True and self.picked_meshes:
                    for surf in self.all_surfs:
                        for curve in surf.all_curves:
                            selected_points = cur_main.get_selected_points(curve.curve_points)
                            if selected_points:
                                cur_main.snap_to_surface(context, selected_points, self.picked_meshes, region, rv3d, None)

                                if len(selected_points) == 1:
                                    cur_main.curve_point_changed(curve, curve.curve_points.index(selected_points[0]), curve_settings.curve_resolution, curve.display_bezier)
                                else:
                                    cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)

                if self.active_surf.spread_type == 'OnCurve':
                    for surf in self.all_surfs:
                        for curve in surf.all_curves:
                            if curve.curve_verts_ids:
                                verts_update = ut_base.get_verts_from_ids(curve.curve_verts_ids, self.id_layer, bm)
                                update_curve_line(active_obj, curve, verts_update, curve_settings.spread_mode, surf.original_loop_data)
                else:
                    if self.active_surf.uniform_loops:
                        # spread verts
                        all_loops_verts = []
                        if self.active_surf.main_loop_ids:
                            main_loop_verts = ut_base.get_verts_from_ids(self.active_surf.main_loop_ids, self.id_layer, bm)
                            all_loops_verts.append(main_loop_verts)
                        for verts in self.active_surf.uniform_loops:
                            uni_verts = ut_base.get_verts_from_ids(verts, self.id_layer, bm)
                            all_loops_verts.append(uni_verts)
                        spread_verts_uniform(active_obj, self.active_surf, all_loops_verts, curve_settings)

                bm.normal_update()
                bmesh.update_edit_mesh(active_obj.data)

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
                                # Move Points without Snapping
                                for point in selected_points:
                                    point.position += move_offset

                                if len(selected_points) == 1:
                                    cur_main.curve_point_changed(curve, curve.curve_points.index(selected_points[0]), curve_settings.curve_resolution, curve.display_bezier)
                                else:
                                    cur_main.generate_bezier_points(curve, curve.display_bezier, curve_settings.curve_resolution)

                return {'RUNNING_MODAL'}

        elif self.surf_tool_mode in {'CREATE_CURVE', 'CREATE_SURFACE'}:
            if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'RELEASE':
                self.surf_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}
            else:
                #if event.ctrl:
                if event.type in {'LEFTMOUSE', 'SELECTMOUSE'} and event.value == 'PRESS':
                    # get center
                    center_plane = None
                    if self.surf_tool_mode == 'CREATE_SURFACE':
                        center_plane = context.space_data.cursor_location
                    else:
                        if self.active_surf and self.active_surf.active_curve and self.active_surf.active_curve.active_point:
                            act_point = cur_main.get_point_by_id(self.active_surf.active_curve.curve_points, self.active_surf.active_curve.active_point)
                            center_plane = act_point.position
                        elif self.active_surf.main_loop_center:
                            center_plane = self.active_surf.main_loop_center
                        else:
                            center_plane = context.space_data.cursor_location

                    new_point_pos = ut_base.get_mouse_on_plane(context, center_plane, None, m_coords)

                    if new_point_pos:
                        # deselect all points
                        for surf in self.all_surfs:
                            cur_main.deselect_all_curves(surf.all_curves, True)
                            surf.active_curve = None

                        # create new surface object
                        if self.surf_tool_mode == 'CREATE_SURFACE':
                            surf = MI_SurfaceObject(self.all_surfs, None, None, None, bm, active_obj, cur_surfs_settings.spread_loops_type)
                            self.all_surfs.append(surf)
                            self.active_surf = surf

                        # new curve
                        cur = MI_SurfaceCurveObject(self.active_surf.all_curves)
                        self.active_surf.all_curves.append(cur)
                        self.active_surf.active_curve = cur  # set active curve

                        # new point
                        new_point = cur_main.MI_CurvePoint(cur.curve_points)
                        cur.curve_points.append(new_point)
                        new_point.position = new_point_pos.copy()
                        new_point.select = True
                        cur.active_point = new_point.point_id

                        # Snap to Surface
                        if curve_settings.surface_snap is True:
                            if self.picked_meshes:
                                cur_main.snap_to_surface(context, [new_point], self.picked_meshes, region, rv3d, None)

                        self.surf_tool_mode = 'MOVE_POINT'
                        return {'RUNNING_MODAL'}

        else:
            if event.value == 'RELEASE' and event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
                self.surf_tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}


        # get keys
        if keys_pass is True:
            # allow navigation
            return {'PASS_THROUGH'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_curve_surf_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_curve_surf_2d, 'WINDOW')

            # clear
            finish_work(self, context, bm)

            return {'FINISHED'}

        return {'RUNNING_MODAL'}


def reset_params(self, bm):
    # reset base curve_settings
    self.surf_tool_mode = 'IDLE'
    self.all_surfs = []
    self.active_surf = None
    self.deform_mouse_pos = None
    self.picked_meshes = None

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


def spread_verts_uniform(obj, surf, loop_verts, curve_settings):
    curves_verts_pos = []

    if surf.main_loop_ids:
        curves_verts_pos.append([ vert.co.copy() for vert in loop_verts[0] ])

    for curve in surf.all_curves:
        if len(curve.curve_points) > 1:
            update_curve_line(obj, curve, loop_verts[-1], curve_settings.spread_mode, surf.original_loop_data)
            curves_verts_pos.append([ vert.co.copy() for vert in loop_verts[-1] ])

    # new curve
    spread_cur = cur_main.MI_CurveObject(None)
    for i in range(len(curves_verts_pos)):
        new_point = cur_main.MI_CurvePoint(spread_cur.curve_points)
        spread_cur.curve_points.append(new_point)

    # spread verts
    verts_range = surf.loop_points
    if surf.main_loop_ids:
        verts_range = len(surf.main_loop_ids)

    for i in range(verts_range):
        spread_cur.display_bezier.clear()

        verts_to_spread = []

        for k, vec in enumerate(curves_verts_pos):
            # here we multiply to matrix_world to get world coords for the new curve
            spread_cur.curve_points[k].position = obj.matrix_world * vec[i]

        for j in range(surf.cross_loop_points):
            verts_to_spread.append(loop_verts[j][i])

        cur_main.generate_bezier_points(spread_cur, spread_cur.display_bezier, curve_settings.curve_resolution)
        update_curve_line(obj, spread_cur, verts_to_spread, 'Uniform', None)


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


def fix_curve_direction(surf, curve_to_spread, id_layer, bm, obj, curve_settings):
    len_first = None
    len_last = None

    curve_index = surf.all_curves.index(surf.active_curve)

    if curve_index > 0:
        prev_curve = surf.all_curves[curve_index - 1]
        len_first = (curve_to_spread.curve_points[-1].position - prev_curve.curve_points[0].position).length
        len_last = (curve_to_spread.curve_points[-1].position - prev_curve.curve_points[-1].position).length
    else:
        if surf.main_loop_ids:
            main_loop_verts = ut_base.get_verts_from_ids(surf.main_loop_ids, id_layer, bm)

            first_v_pos = obj.matrix_world * main_loop_verts[0].co
            last_v_pos = obj.matrix_world * main_loop_verts[-1].co

            len_first = (curve_to_spread.curve_points[-1].position - first_v_pos).length
            len_last = (curve_to_spread.curve_points[-1].position - last_v_pos).length

    if len_first and len_last and len_last > len_first:
        # we reverse array if curve points
        curve_to_spread.curve_points.reverse()
        curve_to_spread.display_bezier.clear()
        cur_main.generate_bezier_points(curve_to_spread, curve_to_spread.display_bezier, curve_settings.curve_resolution)


def create_surface_loop(surf, curve_to_spread, bm, obj, curve_settings, self):
    next_loop_verts = []
    next_loop_verts_ids = []
    prev_loop_verts_ids = None

    orig_loop_data = surf.original_loop_data

    curve_index = surf.all_curves.index(surf.active_curve)
    prev_curve = surf.all_curves[curve_index - 1]

    # get previous verts ids
    if curve_index > 0:
        # fix for non loop based surfaces
        if not surf.main_loop_ids and curve_index == 1 and not prev_curve.curve_verts_ids:
            fix_main_loop_verts = []
            fix_main_loop_verts_ids = []
            for i in range(surf.loop_points):
                vert = bm.verts.new((0.0, 0.0, 0.0))
                vert[self.id_layer] = self.id_value
                fix_main_loop_verts.append(vert)
                fix_main_loop_verts_ids.append(self.id_value)
                self.id_value += 1

            bm.verts.index_update()
            bm.verts.ensure_lookup_table()

            update_curve_line(obj, surf.all_curves[0], fix_main_loop_verts, curve_settings.spread_mode, None)

            #for vert in fix_main_loop_verts:
                #prev_loop_verts_ids.append(vert.index)

            prev_curve.curve_verts_ids = fix_main_loop_verts_ids
            prev_loop_verts_ids = fix_main_loop_verts_ids

        else:
            prev_loop_verts_ids = surf.all_curves[curve_index - 1].curve_verts_ids
    else:
        prev_loop_verts_ids = surf.main_loop_ids

    # previous loop
    prev_loop_verts = ut_base.get_verts_from_ids(prev_loop_verts_ids, self.id_layer, bm)

    # next loop
    for i in range(len(prev_loop_verts_ids)):
        vert = bm.verts.new((0.0, 0.0, 0.0))
        vert[self.id_layer] = self.id_value
        next_loop_verts.append(vert)
        next_loop_verts_ids.append(self.id_value)
        self.id_value += 1

    bm.verts.index_update()
    bm.verts.ensure_lookup_table()
    #print(next_loop_verts_ids)

    ## another approach by extruding edges
    #get_edges = []
    #for edge in bm.edges:
        #if edge.verts[0] in prev_loop_verts and edge.verts[1] in prev_loop_verts:
            #get_edges.append(edge)
    #new_geo_data = bmesh.ops.extrude_edge_only(bm, edges=get_edges)

    #bm.verts.ensure_lookup_table()

    #for geo_obj in new_geo_data.get('geom'):
        #if type(geo_obj) is bmesh.types.BMVert:
            #next_loop_verts.append(geo_obj)
            #next_loop_verts_ids.append(geo_obj.index)

    update_curve_line(obj, curve_to_spread, next_loop_verts, curve_settings.spread_mode, orig_loop_data)

    new_faces = create_polyloops(next_loop_verts, prev_loop_verts, bm)

    return next_loop_verts_ids


def create_polyloops(next_loop_verts, prev_loop_verts, bm):
    new_faces = []
    for i, vert in enumerate(next_loop_verts):
        if i > 0:
            new_face = bm.faces.new( (next_loop_verts[i-1], vert, prev_loop_verts[i], prev_loop_verts[i-1]) )
            #new_face.normal_update
            new_faces.append(new_face)

    bm.faces.index_update()
    bm.edges.index_update()
    bmesh.ops.recalc_face_normals(bm, faces=new_faces)
    #bmesh.ops.reverse_faces(bm, faces=new_faces)
    return new_faces


def update_curve_line(obj, curve_to_spread, loop_verts, spread_mode, original_loop_data):
    line = cur_main.get_bezier_line(curve_to_spread, obj, True)

    if spread_mode == 'Original':
        cur_main.verts_to_line(loop_verts, line, original_loop_data, curve_to_spread.closed)
    else:
        cur_main.verts_to_line(loop_verts, line, None, curve_to_spread.closed)


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
                        c_widget.draw_3d_polyline(curve.display_bezier[cur_point.point_id], 2, col_man.cur_line_base, True)


def draw_surf_2d(surfs, active_surf, context):
    region = context.region
    rv3d = context.region_data
    curve_settings = context.scene.mi_settings
    # coord = event.mouse_region_x, event.mouse_region_y
    for surf in surfs:
        # draw loops center
        if surf.main_loop_center:
            surf_center_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, surf.main_loop_center)
            if surf_center_2d:
                if surf is active_surf:
                    c_widget.draw_2d_point(surf_center_2d.x, surf_center_2d.y, 6, (0.7,0.75,0.95,1.0))
                else:
                    c_widget.draw_2d_point(surf_center_2d.x, surf_center_2d.y, 6, (0.5,0.5,0.8,1.0))

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
                    c_widget.draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, p_col)

                    # Handlers
                    if curve_settings.draw_handlers:
                    #if curve.curve_points.index(cu_point) < len(curve.curve_points)-1:
                        if cu_point.handle1:
                            handle_1_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle1)
                            if handle_1_pos_2d:
                                c_widget.draw_2d_point(handle_1_pos_2d.x, handle_1_pos_2d.y, 3, col_man.cur_handle_1_base)
                    #if curve.curve_points.index(cu_point) > 0:
                        if cu_point.handle2:
                            handle_2_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, cu_point.handle2)
                            if handle_2_pos_2d:
                                c_widget.draw_2d_point(handle_2_pos_2d.x, handle_2_pos_2d.y, 3, col_man.cur_handle_2_base)
