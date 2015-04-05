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


class MI_DeformPanel(bpy.types.Panel):
    bl_label = "Deform"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'

    def draw(self, context):
        cur_stretch_settings = context.scene.mi_cur_stretch_settings

        layout = self.layout
        layout.label(text="Deformer:")
        layout.operator("mira.deformer", text="Deformer")

        layout.separator()
        layout.label(text="CurveStretch:")
        layout.operator("mira.curve_stretch", text="CurveStretchTest")
        layout.prop(cur_stretch_settings, "point_number", text='PointsNumber')