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
    "author": "Pavel Geraskin, Marvin K. Breuer, Graham Held, JoseConseco",
    "version": (3, 0, 0),
    "blender": (2, 80, 0),
    "location": "3D Viewport",
    "description": "Mira Tools",
    "warning": "",
    "wiki_url": "https://github.com/mifth/mifthtools/wiki/Mira-Tools",
    "tracker_url": "https://github.com/mifth/mifthtools/issues",
    "category": "Tools"}


if "bpy" in locals():
    import imp
    imp.reload(mi_curve_test)
    imp.reload(mi_curve_stretch)
    imp.reload(mi_curve_surfaces)
    imp.reload(mi_settings)
    imp.reload(mi_gui)
    imp.reload(mi_noise)
    imp.reload(mi_deform)
    imp.reload(mi_linear_deformer)
    imp.reload(mi_linear_deformer_curve)
    imp.reload(mi_curve_guide)
    imp.reload(mi_draw_extrude)
    imp.reload(mi_poly_loop)
    imp.reload(mi_make_arc)
    imp.reload(mi_wrap_master)
    imp.reload(mi_primitives)
    imp.reload(mi_simple_extrude)
    imp.reload(mi_unbevel)
    imp.reload(mi_retopo_loops)
    imp.reload(mi_snap_points)

else:
    from . import mi_curve_test
    from . import mi_curve_stretch
    from . import mi_curve_surfaces
    from . import mi_settings
    from . import mi_linear_deformer
    from . import mi_linear_deformer_curve
    from . import mi_curve_guide
    from . import mi_deform
    from . import mi_gui
    from . import mi_noise
    from . import mi_draw_extrude
    from . import mi_poly_loop
    from . import mi_make_arc
    from . import mi_wrap_master
    from . import mi_primitives
    from . import mi_simple_extrude
    from . import mi_unbevel
    from . import mi_retopo_loops
    from . import mi_snap_points


import bpy
from bpy.props import *

from . import auto_load
auto_load.init()

import traceback

def register():
    try:
        auto_load.register()
    except:
        traceback.print_exc()

    # bpy.types.Scene.mira_curve_points: PointerProperty( name="Mira Tool Variables", type=mi_curve_test.MR_CurvePoint, description="Mira Curve" )
    # bpy.types.Object.mi_curves = CollectionProperty( name="Mira Tool Variables", type=mi_curve_test.MI_CurveObject, description="Mira Curve" )
    bpy.types.Scene.mi_settings = PointerProperty( name="Global Settings", type=mi_settings.MI_Settings, description="Global Settings." )
    bpy.types.Scene.mi_cur_stretch_settings = PointerProperty( name="Curve Stretch Settings", type=mi_curve_stretch.MI_CurveStretchSettings, description="Curve Stretch Settings." )
    bpy.types.Scene.mi_cur_surfs_settings = PointerProperty( name="Curve Surfaces Settings", type=mi_curve_surfaces.MI_CurveSurfacesSettings, description="Curve Surfaces Settings." )
    bpy.types.Scene.mi_extrude_settings = PointerProperty( name="Extrude Variables", type=mi_draw_extrude.MI_ExtrudeSettings, description="Extrude Settings" )
    bpy.types.Scene.mi_ldeformer_settings = PointerProperty( name="Linear Deformer Variables", type=mi_linear_deformer.MI_LDeformer_Settings, description="Linear Deformer Settings" )
    bpy.types.Scene.mi_curguide_settings = PointerProperty( name="Curve Guide Variables", type=mi_curve_guide.MI_CurGuide_Settings, description="Curve Guide Settings" )
    bpy.types.Scene.mi_makearc_settings = PointerProperty( name="Make Arc Variables", type=mi_make_arc.MI_MakeArc_Settings, description="Make Arc Settings" )
    #bpy.types.Scene.mi_unbevel_settings = PointerProperty( name="Unbevel Settings", type=mi_unbevel.MI_Unbevel_Settings, description="Unbevel Settings" )

    # alternative gui
    bpy.types.WindowManager.mirawindow = bpy.props.PointerProperty(type = mi_gui.DropdownMiraToolProps)
    bpy.types.VIEW3D_MT_mesh_add.prepend(mi_gui.mifth_prim_menu)


    # bpy.types.VIEW3D_PT_tools_curveedit.append(mi_linear_deformer_curve.linear_deform_button)

def unregister():

    #del bpy.types.Scene.miraTool
    #del bpy.types.Object.mi_curves  # need to investigate if i need to delete it
    del bpy.types.Scene.mi_settings
    del bpy.types.Scene.mi_cur_stretch_settings
    del bpy.types.Scene.mi_cur_surfs_settings
    del bpy.types.Scene.mi_extrude_settings
    del bpy.types.Scene.mi_ldeformer_settings
    del bpy.types.Scene.mi_curguide_settings
    del bpy.types.Scene.mi_makearc_settings

    del bpy.types.WindowManager.mirawindow
    bpy.types.VIEW3D_MT_mesh_add.remove(mi_gui.mifth_prim_menu)

    # bpy.types.VIEW3D_PT_tools_curveedit.remove(mi_linear_deformer_curve.linear_deform_button)
    try:
        auto_load.unregister()
    except:
        traceback.print_exc()

if __name__ == "__main__":
    register()
