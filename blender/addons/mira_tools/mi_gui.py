# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

import bpy


class MI_ModifyPanel(bpy.types.Panel):
    bl_label = "Modify"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'

    def draw(self, context):
        layout = self.layout

        mi_settings = context.scene.mi_settings
        extrude_settings = context.scene.mi_extrude_settings
        cur_surfs_settings = context.scene.mi_cur_surfs_settings

        layout.operator("mira.draw_extrude", text="Draw Extrude")
        #layout.prop(extrude_settings, "extrude_mode", text='Mode')
        layout.prop(extrude_settings, "extrude_step_type", text='Step')

        if extrude_settings.extrude_step_type == 'Asolute':
            layout.prop(extrude_settings, "absolute_extrude_step", text='')
        else:
            layout.prop(extrude_settings, "relative_extrude_step", text='')

        if mi_settings.surface_snap is False:
            layout.prop(extrude_settings, "do_symmetry", text='Symmetry')
            if extrude_settings.do_symmetry:
                layout.prop(extrude_settings, "symmetry_axys", text='Axys')

        layout.separator()
        layout.operator("mira.poly_loop", text="Poly Loop")

        layout.separator()
        layout.operator("mira.curve_surfaces", text="Curve Surfaces")
        layout.prop(cur_surfs_settings, "spread_loops_type", text='Points')


class MI_DeformPanel(bpy.types.Panel):
    bl_label = "Deform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'

    def draw(self, context):
        cur_stretch_settings = context.scene.mi_cur_stretch_settings
        lin_def_settings = context.scene.mi_ldeformer_settings
        curguide_settings = context.scene.mi_curguide_settings

        layout = self.layout
        layout.operator("mira.noise", text="Noise")
        # layout.label(text="Deformer:")
        layout.operator("mira.deformer", text="Deformer")

        layout.separator()
        layout.operator("mira.linear_deformer", text="Linear Deformer")
        layout.prop(lin_def_settings, "manual_update", text='ManualUpdate')

        layout.separator()
        #layout.label(text="CurveStretch:")
        layout.operator("mira.curve_stretch", text="Curve Stretch")
        #row = layout.row()
        layout.prop(cur_stretch_settings, "points_number", text='Points')

        layout.separator()
        #layout.label(text="CurveGuide:")
        layout.operator("mira.curve_guide", text="Curve Guide")
        row = layout.row()
        row.prop(curguide_settings, "points_number", text='LoopSpread')
        row.prop(curguide_settings, "deform_type", text='')


class MI_SettingsPanel(bpy.types.Panel):
    bl_label = "Settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'


    def draw(self, context):
        layout = self.layout
        mi_settings = context.scene.mi_settings

        layout.prop(mi_settings, "surface_snap", text='SurfaceSnapping')
        layout.prop(mi_settings, "convert_instances", text='ConvertInstances')
        layout.prop(mi_settings, "snap_objects", text='SnapObjects')
        layout.separator()

        layout.label(text="Curve Settings:")
        layout.prop(mi_settings, "spread_mode", text='Spread')
        layout.prop(mi_settings, "curve_resolution", text='Resolution')
        layout.prop(mi_settings, "draw_handlers", text='Handlers')
        layout.operator("mira.curve_test", text="Curve Test")