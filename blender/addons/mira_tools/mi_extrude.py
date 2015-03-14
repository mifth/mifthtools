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
import bgl
import blf
import string

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from bpy_extras import view3d_utils

import math
import mathutils as mathu
import random
from mathutils import Vector

#if "bpy" in locals():
    #import imp
    #imp.reload(mi_utils_base)
#else:
from . import mi_utils_base as ut_base


class MI_ExtrudeSettings(bpy.types.PropertyGroup):
    # Extrude Settings
    absolute_extrude_step = FloatProperty(default=1.0,min=0.0)
    relative_extrude_step = FloatProperty(default=1.5,min=0.0)
    extrude_step_type = EnumProperty(
        items=(('Asolute', 'Asolute', ''),
               ('Relative', 'Relative', '')
               ),
        default = 'Relative'
    )
    snap_geometry = BoolProperty(default=False)


class MI_ExtrudePanel(bpy.types.Panel):
    bl_label = "Mira"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'


    def draw(self, context):
        layout = self.layout
        extrude_settings = context.scene.mi_extrude_settings

        layout.operator("mira.draw_extrude", text="Draw Extrude")
        layout.prop(extrude_settings, "extrude_step_type", text='Step')

        if extrude_settings.extrude_step_type == 'Asolute':
            layout.prop(extrude_settings, "absolute_extrude_step", text='')
        else:
            layout.prop(extrude_settings, "relative_extrude_step", text='')

        layout.prop(extrude_settings, "snap_geometry", text='SnapToSelected')


class MRStartDraw(bpy.types.Operator):
    """Draw a line with the mouse"""
    bl_idname = "mira.draw_extrude"
    bl_label = "DrawExtrude"
    bl_description = "Draw Extrude Test"
    bl_options = {'REGISTER', 'UNDO'}

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'LEFTMOUSE', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE',
                 'SELECTMOUSE', 'MOUSEMOVE']

    extrude_center = None
    extrude_dir = None

    # curve tool mode
    tool_modes = ('IDLE', 'DRAW', 'ADD_POINT')
    tool_mode = 'IDLE'

    # changed parameters
    manipulator = None
    relative_step_size = None
    extrude_steps = []
    mesh_automerge = None

    # draw on surface settings
    picked_meshes = None
    raycast_offset = None


    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            # the arguments we pass the the callbackection
            args = (self, context)
            # Add the region OpenGL drawing callback
            # draw in view space with 'POST_VIEW' and 'PRE_VIEW'

            reset_params(self)

            extrude_settings = context.scene.mi_extrude_settings
            active_obj = context.scene.objects.active
            bm = bmesh.from_edit_mesh(active_obj.data)
            sel_verts = [v for v in bm.verts if v.select]

            if len(sel_verts) == 0:
                self.report({'WARNING'}, "No Selection!!!")
                return {'CANCELLED'}

            else:
                # change parameters
                self.manipulator = context.space_data.show_manipulator
                context.space_data.show_manipulator = False
                self.mesh_automerge = bpy.context.scene.tool_settings.use_mesh_automerge
                bpy.context.scene.tool_settings.use_mesh_automerge = False

                self.extrude_center = get_vertices_center(sel_verts, active_obj)

                # prepare for snapping
                if extrude_settings.snap_geometry is True:
                    sel_objects = [obj for obj in context.selected_objects if obj != active_obj]
                    if sel_objects:
                        self.picked_meshes = ut_base.get_obj_dup_meshes(sel_objects, context)
                    else:
                        self.report({'WARNING'}, "Please, select objects to raycast!!!")
                        finish_extrude(self, context)
                        return {'CANCELLED'}

                # max_obj_scale
                self.max_obj_scale = active_obj.scale.x
                if active_obj.scale.y > self.max_obj_scale:
                    self.max_obj_scale = active_obj.scale.yget_vertices_size
                if active_obj.scale.z > self.max_obj_scale:
                    self.max_obj_scale = active_obj.scale.z

                # relative step
                self.relative_step_size = get_vertices_size(sel_verts, active_obj)
                if self.relative_step_size == 0.0 and extrude_settings.extrude_step_type == 'Relative':
                    self.report({'WARNING'}, "Please, use Absolute step for one point!!!")
                    finish_extrude(self, context)
                    return {'CANCELLED'}                    

            self.mi_extrude_handle_2d = bpy.types.SpaceView3D.draw_handler_add(mi_extrude_draw_2d, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)


            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


    def modal(self, context, event):
        #print(context.active_operator)
        context.area.tag_redraw()

        # make picking
        if event.type in {'LEFTMOUSE', 'SELECTMOUSE'}:
            if event.value == 'PRESS':
                if self.tool_mode == 'IDLE':
                    m_coords = event.mouse_region_x, event.mouse_region_y
                    do_pick = mi_pick_extrude_point(self.extrude_center, context, m_coords)

                    if do_pick:
                        self.tool_mode = 'DRAW'
                        return {'RUNNING_MODAL'}

            elif event.value == 'RELEASE':
                if self.tool_mode == 'DRAW':
                    #self.extrude_dir = None  # clear dir
                    self.tool_mode = 'IDLE'
                return {'RUNNING_MODAL'}

            return {'RUNNING_MODAL'}

        if self.tool_mode == 'DRAW':
            active_obj = context.scene.objects.active
            rv3d = context.region_data
            m_coords = event.mouse_region_x, event.mouse_region_y
            extrude_settings = context.scene.mi_extrude_settings

            # get new position according to a mouse
            new_pos = None
            f1, f2, f3 = None, None, None
            if extrude_settings.snap_geometry is True:
                f1, f2, f3 = ut_base.get_mouse_raycast(context, self.picked_meshes, m_coords, 10000.0)
                new_pos = f3

                # set offset for surface normal and extrude_center
                if new_pos is not None:
                    if self.raycast_offset is None:
                        self.raycast_offset = (f3 - self.extrude_center).length
                    else:
                        new_pos += f2*self.raycast_offset
                        #print(f2*self.raycast_offset)

            else:
                new_pos = get_mouse_on_plane(context, self.extrude_center, m_coords)

            extrude_step = None
            if extrude_settings.extrude_step_type == 'Relative':
                extrude_step = extrude_settings.relative_extrude_step * self.relative_step_size
            else:
                extrude_step = extrude_settings.absolute_extrude_step

            # EXTRUDE
            if new_pos is not None and (new_pos-self.extrude_center).length >= extrude_step:
                bpy.ops.mesh.extrude_region_move()

                bm = bmesh.from_edit_mesh(active_obj.data)

                # New Extrude center
                offset_dir = None
                offset_move = new_pos-self.extrude_center
                bpy.ops.transform.translate(value=(offset_move.x, offset_move.y, offset_move.z), proportional='DISABLED')
                offset_dir = offset_move.copy().normalized()

                up_vec = None
                cam_dir = rv3d.view_rotation * Vector((0.0, 0.0, -1.0))

                # rotate
                rotate_dir_vec = None
                if self.extrude_dir is not None:
                    # ratate direction
                    if extrude_settings.snap_geometry is True:
                        rotate_dir_vec = self.extrude_dir.cross( (f3-self.extrude_center).normalized() )
                    else:
                        rotate_dir_vec = cam_dir

                    rot_angle = self.extrude_dir.angle(offset_dir)
                    up_vec = rotate_dir_vec.cross(self.extrude_dir).normalized()

                    if up_vec.angle(offset_dir) > math.radians(90):
                        rot_angle = -rot_angle

                    bpy.ops.transform.rotate(value=rot_angle, axis=rotate_dir_vec, proportional='DISABLED')
                    self.extrude_dir = offset_dir
                else:
                    # fix first extrude
                    if extrude_settings.snap_geometry is True:
                        fix_first_extrude_dir = get_mouse_on_plane(context, self.extrude_center, m_coords)
                        self.extrude_dir = (fix_first_extrude_dir-self.extrude_center).normalized()
                    else:
                        self.extrude_dir = offset_dir

                # finalize things
                # empty array will be for extruded vertices
                self.extrude_steps.append( [new_pos, self.extrude_dir, [] ] )
                self.extrude_center = new_pos

                # fix direction of previous step
                if len(self.extrude_steps) > 2:
                    fix_dir = (self.extrude_steps[-1][0] - self.extrude_steps[-3][0]).normalized()
                    fix_up_vec = rotate_dir_vec.cross(fix_dir).normalized()
                    fix_step = self.extrude_steps[-2]
                    fix_rot_angle = fix_dir.angle(fix_step[1])
                    
                    selected_bmesh = get_selected_bmesh(bm)
                    previous_extrude_verts = get_previous_extrude_verts(bm, context)

                    # rotate previous extrude
                    if fix_rot_angle > 0.0:
                        sel_mode = context.tool_settings.mesh_select_mode
                        sel_mode = (sel_mode[0], sel_mode[1], sel_mode[2])

                        #bpy.ops.mesh.select_all(action='DESELECT')
                        for vert in selected_bmesh[0]:
                            vert.select = False
                        for edge in selected_bmesh[1]:
                            edge.select = False
                        for face in selected_bmesh[2]:
                            face.select = False

                        context.tool_settings.mesh_select_mode = (True, False, False)
                        #bmesh.update_edit_mesh(active_obj.data)
                        for vert in previous_extrude_verts:
                            vert.select = True

                        # rotate previous extrude to fix rotation
                        if fix_up_vec.angle( (fix_step[1] - fix_dir).normalized() ) < math.radians(90):
                            fix_rot_angle = -fix_rot_angle
                        bpy.ops.transform.rotate(value=fix_rot_angle, axis=rotate_dir_vec, proportional='DISABLED')

                        # revert selection
                        for vert in previous_extrude_verts:
                            vert.select = False

                        context.tool_settings.mesh_select_mode = (sel_mode[0], sel_mode[1], sel_mode[2])

                        for vert in selected_bmesh[0]:
                            vert.select = True
                        for edge in selected_bmesh[1]:
                            edge.select = True
                        for face in selected_bmesh[2]:
                            face.select = True

                    # chenge direction of previous extrude
                    fix_step[1] = fix_dir
                    # add verts of previos extrude
                    fix_step[2] = previous_extrude_verts

            #active_obj.data.update()
            bmesh.update_edit_mesh(active_obj.data)

            return {'RUNNING_MODAL'}

        # main stuff
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            finish_extrude(self, context)
            #bpy.types.SpaceView3D.draw_handler_remove(self.mi_handle_3d, 'WINDOW')
            bpy.types.SpaceView3D.draw_handler_remove(self.mi_extrude_handle_2d, 'WINDOW')

            return {'FINISHED'}

        elif event.type in self.pass_keys:
            # allow navigation
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}
        #return {'PASS_THROUGH'}


def reset_params(self):
    self.extrude_center = None
    self.extrude_dir = None
    self.tool_mode = 'IDLE'
    self.relative_step_size = None
    self.extrude_steps = []
    self.picked_meshes = None
    self.raycast_offset = None


def finish_extrude(self, context):
    context.space_data.show_manipulator = self.manipulator
    bpy.context.scene.tool_settings.use_mesh_automerge = self.mesh_automerge
    self.extrude_steps = []


def mi_extrude_draw_2d(self, context):
    active_obj = context.scene.objects.active
    region = context.region
    rv3d = context.region_data
    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, self.extrude_center)

    p_col = (0.5,0.8,1.0,1.0)
    mi_draw_2d_point(point_pos_2d.x, point_pos_2d.y, 6, p_col)


# TODO move to utilities
def get_mouse_on_plane(context, plane_pos, mouse_coords):
    region = context.region
    rv3d = context.region_data
    cam_dir = rv3d.view_rotation * Vector((0.0, 0.0, -1.0))
    #cam_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, (region.width/2.0, region.height/2.0))
    mouse_pos = view3d_utils.region_2d_to_origin_3d(region, rv3d, mouse_coords)
    mouse_dir = view3d_utils.region_2d_to_vector_3d(region, rv3d, mouse_coords)
    new_pos = mathu.geometry.intersect_line_plane(mouse_pos, mouse_pos+(mouse_dir*10000.0), plane_pos, cam_dir, False)
    if new_pos:
        return new_pos

    return None


def get_previous_extrude_verts(bm, context):
    verts_array = None
    selected_bmesh = get_selected_bmesh(bm)

    sel_mode = context.tool_settings.mesh_select_mode
    sel_mode = (sel_mode[0], sel_mode[1], sel_mode[2])
    context.tool_settings.mesh_select_mode = (True, False, False)
    bpy.ops.mesh.select_more()

    for vert in selected_bmesh[0]:
        vert.select = False
    for edge in selected_bmesh[1]:
        edge.select = False
    for face in selected_bmesh[2]:
        face.select = False

    verts_array = [v for v in bm.verts if v.select]

    bpy.ops.mesh.select_all(action='DESELECT')
    context.tool_settings.mesh_select_mode = (sel_mode[0], sel_mode[1], sel_mode[2])

    for vert in selected_bmesh[0]:
        vert.select = True
    for edge in selected_bmesh[1]:
        edge.select = True
    for face in selected_bmesh[2]:
        face.select = True

    return verts_array

# TODO move to utils
def get_selected_bmesh(bm):
    sel_verts = [v for v in bm.verts if v.select]
    sel_edges = [e for e in bm.edges if e.select]
    sel_faces = [f for f in bm.faces if f.select]

    return [sel_verts, sel_edges, sel_faces]


# TODO move to utils
def mi_pick_extrude_point(point, context, mouse_coords):
    region = context.region
    rv3d = context.region_data

    #for cu_point in curve.curve_points:
    point_pos_2d = view3d_utils.location_3d_to_region_2d(region, rv3d, point)
    length = (point_pos_2d - Vector(mouse_coords)).length
    if length <= 9.0:
        return True

    return False


# TODO Move it into utilities method. As Deform class has the same method.
def get_vertices_center(verts, obj):
    #if obj.mode == 'EDIT':
        #bm.verts.ensure_lookup_table()
    vert_world_first = obj.matrix_world * verts[0].co
    #multiply_scale(vert_world_first, obj.scale)

    x_min = vert_world_first.x
    x_max = vert_world_first.x
    y_min = vert_world_first.y
    y_max = vert_world_first.y
    z_min = vert_world_first.z
    z_max = vert_world_first.z

    for vert in verts:
        vert_world = obj.matrix_world * vert.co
        #multiply_scale(vert_world, obj.scale)

        if vert_world.x > x_max:
            x_max = vert_world.x
        if vert_world.x < x_min:
            x_min = vert_world.x
        if vert_world.y > y_max:
            y_max = vert_world.y
        if vert_world.y < y_min:
            y_min = vert_world.y
        if vert_world.z > z_max:
            z_max = vert_world.z
        if vert_world.z < z_min:
            z_min = vert_world.z

    x_orig = ((x_max-x_min) / 2.0) + x_min
    y_orig = ((y_max-y_min) / 2.0) + y_min
    z_orig = ((z_max-z_min) / 2.0) + z_min

    return Vector((x_orig, y_orig, z_orig))


# TODO Move it into utilities method. As Deform class has the same method.
def get_vertices_size(verts, obj):
    #if obj.mode == 'EDIT':
        #bm.verts.ensure_lookup_table()
    vert_world_first = obj.matrix_world * verts[0].co
    #multiply_scale(vert_world_first, obj.scale)

    x_min = vert_world_first.x
    x_max = vert_world_first.x
    y_min = vert_world_first.y
    y_max = vert_world_first.y
    z_min = vert_world_first.z
    z_max = vert_world_first.z

    for vert in verts:
        vert_world = obj.matrix_world * vert.co
        #multiply_scale(vert_world, obj.scale)

        if vert_world.x > x_max:
            x_max = vert_world.x
        if vert_world.x < x_min:
            x_min = vert_world.x
        if vert_world.y > y_max:
            y_max = vert_world.y
        if vert_world.y < y_min:
            y_min = vert_world.y
        if vert_world.z > z_max:
            z_max = vert_world.z
        if vert_world.z < z_min:
            z_min = vert_world.z

    x_size = (x_max-x_min)
    y_size = (y_max-y_min)
    z_size = (z_max-z_min)

    final_size = x_size
    if final_size < y_size:
        final_size = y_size
    if final_size < z_size:
        final_size = z_size

    return final_size


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
def multiply_scale(vec1, vec2):
    vec1[0] *= vec2[0]
    vec1[1] *= vec2[1]
    vec1[2] *= vec2[2]

