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

bl_info = {
    "name": "Mira Tools",
    "author": "Paul Geraskin",
    "version": (0, 1, 0),
    "blender": (2, 74, 0),
    "location": "3D Viewport",
    "description": "Mira Tool",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Tools"}


if "bpy" in locals():
    import imp
    imp.reload(mi_curve_test)
    imp.reload(mi_curve_stretch)
    imp.reload(mi_curve_surfaces)
    imp.reload(mi_curve_settings)
    imp.reload(mi_gui)
    imp.reload(mi_noise)
    imp.reload(mi_deform)
    imp.reload(mi_linear_deformer)
    imp.reload(mi_curve_guide)
    imp.reload(mi_extrude)
else:
    from . import mi_curve_test
    from . import mi_curve_stretch
    from . import mi_curve_surfaces
    from . import mi_curve_settings
    from . import mi_linear_deformer
    from . import mi_curve_guide
    from . import mi_deform
    from . import mi_gui
    from . import mi_noise
    from . import mi_extrude


import bpy
from bpy.props import *


def register():

    bpy.utils.register_module(__name__)

    # bpy.types.Scene.mira_curve_points = PointerProperty(
    #     name="Mira Tool Variables",
    #     type=mi_curve_test.MR_CurvePoint,
    #     description="Mira Curve"
    # )

    #bpy.types.Object.mi_curves = CollectionProperty(
        #name="Mira Tool Variables",
        #type=mi_curve_test.MI_CurveObject,
        #description="Mira Curve"
    #)

    bpy.types.Scene.mi_curve_settings = PointerProperty(
        name="Global Curve Settings",
        type=mi_curve_settings.MI_CurveSettings,
        description="Global Curve Settings."
    )

    bpy.types.Scene.mi_cur_stretch_settings = PointerProperty(
        name="Curve Stretch Settings",
        type=mi_curve_stretch.MI_CurveStretchSettings,
        description="Curve Stretch Settings."
    )

    bpy.types.Scene.mi_cur_surfs_settings = PointerProperty(
        name="Curve Surfaces Settings",
        type=mi_curve_surfaces.MI_CurveSurfacesSettings,
        description="Curve Surfaces Settings."
    )

    bpy.types.Scene.mi_extrude_settings = PointerProperty(
        name="Extrude Variables",
        type=mi_extrude.MI_ExtrudeSettings,
        description="Extrude Settings"
    )

    bpy.types.Scene.mi_ldeformer_settings = PointerProperty(
        name="Linear Deformer Variables",
        type=mi_linear_deformer.MI_LDeformer_Settings,
        description="Linear Deformer Settings"
    )

    bpy.types.Scene.mi_curguide_settings = PointerProperty(
        name="Curve Guide Variables",
        type=mi_curve_guide.MI_CurGuide_Settings,
        description="Curve Guide Settings"
    )

def unregister():
    import bpy

    #del bpy.types.Scene.miraTool
    #del bpy.types.Object.mi_curves  # need to investigate if i need to delete it
    del bpy.types.Scene.mi_curve_settings
    del bpy.types.Scene.mi_cur_stretch_settings
    del bpy.types.Scene.mi_cur_surfs_settings
    del bpy.types.Scene.mi_extrude_settings
    del bpy.types.Scene.mi_ldeformer_settings
    del bpy.types.Scene.mi_curguide_settings
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
