import bpy

from bpy.props import *
from bpy.types import Operator, AddonPreferences, PropertyGroup


class MI_Addon_Settings(AddonPreferences):
    bl_idname = __package__

    key_inputs: EnumProperty(
        name = "Key Inputs Style",
        items = (('Blender', 'Blender', ''),
                ('Maya', 'Maya', '')
                ),
        default = 'Blender'
    )

    point_size: IntProperty( default = 6, min = 1)
    line_size: IntProperty( default = 1, min = 1)
    select_point_radius: FloatProperty( default = 9.0, min = 3.0)

    def draw(self, context):
        layout = self.layout
        #row = layout.row()
        #row.prop(self, "sg_icons_style")
        layout.prop(self, "key_inputs")
        layout.prop(self, "point_size")
        layout.prop(self, "line_size")
        layout.prop(self, "select_point_radius")


class MI_Settings(PropertyGroup):
    # For all tools
    surface_snap: BoolProperty(default=False)
    snap_objects: EnumProperty(
        name = "Objects To Snap",
        items = (('Selected', 'Selected', ''),
                ('Visible', 'Visible', '')
                ),
        default = 'Visible'
    )

    convert_instances: BoolProperty(default=False)  # This feat converts off duplis and group instances into meshes
    snap_points: BoolProperty(default=True)  # This feat snaps points for CurveSurfaces and CurveStretch

    # Curve Settings
    curve_resolution: IntProperty(default=13, min=1, max=128)
    draw_handlers: BoolProperty(default=False)

    spread_mode: EnumProperty(
        name = "Spread Mode",
        items = (('Original', 'Original', ''),
                ('Uniform', 'Uniform', '')
                ),
        default = 'Original'
    )
