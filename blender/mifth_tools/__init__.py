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
    "name": "Mifth Tools",
    "author": "Paul Geraskin",
    "version": (0, 1, 0),
    "blender": (2, 71, 0),
    "location": "3D Viewport",
    "description": "Mifth Tools",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Tools"}


if "bpy" in locals():
    import imp
    imp.reload(mifth_tools_cloning)
    imp.reload(mifth_tools)
else:
    from . import mifth_tools_cloning
    from . import mifth_tools


import bpy
from bpy.props import *


def register():
    bpy.mifthTools = dict()
    # bpy.mifthCloneTools = dict()

    class MFTProperties(bpy.types.PropertyGroup):

        # Output Settings
        outputFolder = StringProperty(
            name="outputFolder",
            subtype="NONE",
            default="seq"
        )

        outputSubFolder = StringProperty(
            name="outputSubFolder",
            subtype="NONE",
            default="ren"
        )

        outputSequence = StringProperty(
            name="outputSequence",
            subtype="NONE",
            default="render"
        )

        outputSequenceSize = IntProperty(
            default=8,
            min=1,
            max=60
        )

        doOutputSubFolder = BoolProperty(
            name="do Output SubFolder",
            description="do Output SubFolder...",
            default=False
        )

        # Curve Animator Settings
        doUseSceneFrames = BoolProperty(
            name="do use scene frames",
            description="do use scene frames...",
            default=False
        )

        curveAniStartFrame = IntProperty(
            default=1,
            min=1,
            max=10000
        )

        curveAniEndFrame = IntProperty(
            default=100,
            min=1,
            max=10000
        )

        curveAniStepFrame = IntProperty(
            default=10,
            min=1,
            max=10000
        )

        curveAniInterpolation = FloatProperty(
            default=0.3,
            min=0.0,
            max=1.0
        )

        # MorfCreator settings
        morfCreatorNames = StringProperty(
            name="MorfNames",
            subtype="NONE",
            default=""
        )

        morfUseWorldMatrix = BoolProperty(
            name="use world matrix",
            description="use world matrix...",
            default=False
        )

        morfApplyModifiers = BoolProperty(
            name="apply modifiers to morf",
            description="apply modifiers to morf...",
            default=False
        )

    bpy.utils.register_module(__name__)

    bpy.types.Scene.mifthTools = PointerProperty(
        name="Mifth Tools Variables",
        type=MFTProperties,
        description="Mifth Tools Properties"
    )

    bpy.types.Scene.mifthCloneTools = PointerProperty(
        name="Mifth Cloning Variables",
        type=mifth_tools_cloning.MFTCloneProperties,
        description="Mifth Cloning Properties"
    )


def unregister():
    import bpy

    del bpy.types.Scene.mifthTools
    del bpy.types.Scene.mifthCloneTools
    del bpy.mifthTools
    # del bpy.mifthCloneTools
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
