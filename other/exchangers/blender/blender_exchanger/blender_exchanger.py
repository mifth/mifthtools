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
from bpy.types import Operator, AddonPreferences
import os
import shutil


class EX_MainPanel(bpy.types.Panel):
    bl_label = "Exchanger"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = 'Ex'
    #bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        b_exchanger = bpy.context.scene.b_exchanger

        # GUI
        row = layout.row()

        col = row.column()

        col.operator("ex_export.exchanger", text="Export")
        col.operator("ex_import.exchanger", text="Import")

        row = layout.row()
        row.prop(b_exchanger, "doApplyModifiers", text="Apply Modifiers")
        row = layout.row()
        row.prop(b_exchanger, "exportMaterials", text="Export Materials")
        row = layout.row()
        row = layout.row()


class EX_AddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    # bl_idname = __name__
    bl_idname = __package__

    exchangedir = StringProperty(
        name="ExchangeFolder",
        subtype="DIR_PATH",
        default="",
    )

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Please, set Exchanges Folder and save Preferences")
        row = layout.row()
        row.prop(self, "exchangedir")


class EX_ExportScene(bpy.types.Operator):
    bl_idname = "ex_export.exchanger"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        # Addon Preferences
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences

        #checkname = ''
        b_exchanger = bpy.context.scene.b_exchanger
        #scene = context.scene

        exchange_dir = addon_prefs.exchangedir.replace("\\", os.sep)
        if exchange_dir.endswith(os.sep) is False:
            exchange_dir += os.sep

        if len(bpy.context.selected_objects) > 0 and os.path.isdir(addon_prefs.exchangedir):
            # create Simple3DCoat directory
            if not(os.path.isdir(exchange_dir)):
                os.makedirs(exchange_dir)

            # Model Path
            model_path = exchange_dir + "exchange.fbx"

            # Export Model
            bpy.ops.export_scene.fbx(filepath=model_path, check_existing=True, axis_forward='-Z', axis_up='Y', use_selection=True, global_scale=1.0, apply_unit_scale=True, bake_space_transform=True, use_mesh_modifiers=b_exchanger.doApplyModifiers, use_custom_props=True, primary_bone_axis='Y', secondary_bone_axis='X', bake_anim=False, use_anim=False)

        else:
            self.report(
                {'INFO'}, "No Selected Objects or Bad Exchange Folder!!!")

        return {'FINISHED'}


class EX_ImportScene(bpy.types.Operator):
    bl_idname = "ex_import.exchanger"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        # Addon Preferences
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences

        #scene = context.scene
        b_exchanger = bpy.context.scene.b_exchanger

        exchange_dir = addon_prefs.exchangedir.replace("\\", os.sep)
        if exchange_dir.endswith(os.sep) is False:
            exchange_dir += os.sep

        model_path = exchange_dir + "exchange.fbx"

        if os.path.isdir(exchange_dir):
            bpy.ops.import_scene.fbx(filepath=model_path, axis_forward='-Z', axis_up='Y', global_scale=1.0, bake_space_transform=True, use_custom_normals=True, force_connect_children=False, primary_bone_axis='Y', secondary_bone_axis='X', use_prepost_rot=True)
        else:
            self.report({'INFO'}, "Bad Exchange Folder!!!")

        return {'FINISHED'}