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
    "name": "Simple 3D-Coat Applink",
    "author": "Kalle-Samuli Riihikoski (haikalle), Paul Geraskin",
    "version": (0, 3, 2),
    "blender": (2, 69, 0),
    "location": "Scene > Simple 3D-Coat Applink",
    "description": "Transfer data between 3D-Coat/Blender",
    "warning": "",
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.6/Py/"
    "Scripts/Import-Export/3dcoat_applink",
    "tracker_url": "https://projects.blender.org/tracker/?"
    "func=detail&aid=24446",
    "category": "Import-Export"}


if "bpy" in locals():
    import imp
    imp.reload(simple_coat)
else:
    from . import simple_coat


import bpy
from bpy.props import *


def register():

    class SimpleSceneCoat3D(bpy.types.PropertyGroup):

        exportModelType = EnumProperty(
            name = "Export Type",
            items = (('OBJ', 'OBJ', ''),
                   ('FBX', 'FBX', ''),
                   ('DAE', 'DAE', ''),
                   ),
            default = 'OBJ'
        )

        doApplyModifiers = BoolProperty(
            name="Apply Modifiers",
            description="Apply Modifiers...",
            default=True
        )

        exportMaterials = BoolProperty(
            name="Export Materials",
            description="Export Materials...",
            default=True
        )

        copyTexturesPath = StringProperty(
            name="Copy Textures Path",
            subtype="DIR_PATH",
            default="",
        )

        type = EnumProperty(name="Export Type",
                            description="Different Export Types",
                            items=(("ppp", "Per-Pixel Painting", ""),
                           ("mv", "Microvertex Painting", ""),
                                ("ptex", "Ptex Painting", ""),
                                ("uv", "UV-Mapping", ""),
                                ("ref", "Reference Mesh", ""),
                                ("retopo", "Retopo mesh as new layer", ""),
                                ("vox", "Mesh As Voxel Object", ""),
                                ("voxcombine", "Mesh As single Voxel Object", ""),
                                ("alpha", "Mesh As New Pen Alpha", ""),
                                ("prim", "Mesh As Voxel Primitive", ""),
                                ("curv", "Mesh As a Curve Profile", ""),
                                ("autopo", "Mesh For Auto-retopology", ""),
                            ),
                            default= "ppp"
                            )

    bpy.utils.register_module(__name__)

    bpy.types.Scene.simple3Dcoat = PointerProperty(
        name="Applink Variables",
        type=SimpleSceneCoat3D,
        description="Applink variables"
    )


def unregister():
    import bpy

    del bpy.types.Scene.simple3Dcoat
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
