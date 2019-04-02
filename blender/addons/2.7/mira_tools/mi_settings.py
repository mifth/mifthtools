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

from bpy.props import *
from bpy.types import Operator, AddonPreferences, PropertyGroup


class MI_Addon_Settings(AddonPreferences):
    bl_idname = __package__

    key_inputs = EnumProperty(
        name = "Key Inputs Style",
        items = (('Blender', 'Blender', ''),
                ('Maya', 'Maya', '')
                ),
        default = 'Blender'
    )

    def draw(self, context):
        layout = self.layout
        #row = layout.row()
        #row.prop(self, "sg_icons_style")
        layout.prop(self, "key_inputs")


class MI_Settings(PropertyGroup):
    # For all tools
    surface_snap = BoolProperty(default=False)
    snap_objects = EnumProperty(
        name = "Objects To Snap",
        items = (('Selected', 'Selected', ''),
                ('Visible', 'Visible', '')
                ),
        default = 'Visible'
    )
    convert_instances = BoolProperty(default=False)  # This feat converts off duplis and group instances into meshes

    # Curve Settings
    curve_resolution = IntProperty(default=13, min=1, max=128)
    draw_handlers = BoolProperty(default=False)

    spread_mode = EnumProperty(
        name = "Spread Mode",
        items = (('Original', 'Original', ''),
                ('Uniform', 'Uniform', '')
                ),
        default = 'Original'
    )