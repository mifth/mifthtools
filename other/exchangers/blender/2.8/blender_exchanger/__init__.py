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
    "name": "Blender Exchanger",
    "author": "Pavel Geraskin",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "3D View",
    "description": "Transfer data between Blender and other packages",
    "warning": "",
    "wiki_url": "",
    "support": '',
    "category": "Object",
}


if "bpy" in locals():
    import imp
    imp.reload(blender_exchanger)
else:
    from . import blender_exchanger


import bpy
from bpy.props import *


class EX_Settings(bpy.types.PropertyGroup):

    doApplyModifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply Modifiers...",
        default=True
    )

    exportMaterials: BoolProperty(
        name="Export Materials",
        description="Export Materials...",
        default=True
    )

    importNormals: BoolProperty(
        name="Import Normals",
        description="Import Normals...",
        default=False
    )


classes = (
    blender_exchanger.EX_ExportScene,
    blender_exchanger.EX_ImportScene,
    blender_exchanger.EX_MainPanel,
    blender_exchanger.EX_AddonPreferences,
    EX_Settings
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.b_exchanger = PointerProperty(name="Applink Variables", type=EX_Settings, description="Applink variables")


def unregister():
    import bpy

    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.b_exchanger
    #bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
