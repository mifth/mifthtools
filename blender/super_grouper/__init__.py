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
    "name": "Super Grouper",
    "author": "Paul Geraskin, Aleksey Juravlev, BA Community",
    "version": (0, 1, 0),
    "blender": (2, 73, 0),
    "location": "Toolshelf > Relations Tab",
    "warning": "",
    "description": "Super Grouper",
    "wiki_url": "",
    "category": "3D View"}

if "bpy" in locals():
    import imp
    imp.reload(grouper_main)
else:
    from . import grouper_main


import bpy
from bpy.props import *


# registration
def menu_func(self, context):
    self.layout.separator()
    self.layout.menu(grouper_main.SG_Specials_Main_Menu.bl_idname)


def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.super_groups = CollectionProperty(
        type=grouper_main.SG_Group)
    bpy.types.Object.sg_belong_id = CollectionProperty(
        type=grouper_main.SG_Object_Id)
    bpy.types.Scene.sg_settings = PointerProperty(
        type=grouper_main.SG_Other_Settings)

    # Unused, but this is needed for the TemplateList to work...
    bpy.types.Scene.super_groups_index = IntProperty(default=-1)

    bpy.types.VIEW3D_MT_object_specials.append(menu_func)


def unregister():
    import bpy

    # del bpy.types.Scene.super_grouper
    # del bpy.miraTool
    del bpy.types.Scene.super_groups
    del bpy.types.Object.sg_belong_id
    del bpy.types.Scene.sg_settings

    del bpy.types.Scene.super_groups_index

    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
