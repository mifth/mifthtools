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
    bl_region_type = 'UI'
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
        #op.world_scale = 1.0
        col.operator("ex_import.exchanger", text="Import")
        #op.world_scale = 1.0

        layout.separator()

        row = layout.row()
        op = col.operator("ex_export.exchanger", text="ExportHoudini")
        op.world_scale = 0.01
        op = col.operator("ex_import.exchanger", text="ImportHoudini")
        op.world_scale = 100.0

        row = layout.row()
        row.prop(b_exchanger, "doApplyModifiers", text="Apply Modifiers")
        row = layout.row()
        row.prop(b_exchanger, "exportMaterials", text="Export Materials")
        row = layout.row()
        row.prop(b_exchanger, "importNormals", text="Import Normals")


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

    world_scale = FloatProperty( default=1.0 )

    def invoke(self, context, event):
        # Addon Preferences
        #user_preferences = context.user_preferences
        addon_prefs = context.preferences.addons[__package__].preferences

        b_exchanger = bpy.context.scene.b_exchanger
        scene = context.scene

        exchange_dir = addon_prefs.exchangedir.replace("\\", os.sep)
        if exchange_dir.endswith(os.sep) is False:
            exchange_dir += os.sep

        if len(bpy.context.selected_objects) > 0 and os.path.isdir(addon_prefs.exchangedir):

            # change render levl of susurf and multires for good export
            fix_modidiers = []
            for obj in bpy.context.selected_objects:
                for mod in obj.modifiers:
                    if mod.type in {'SUBSURF', 'MULTIRES'}:
                        fix_modidiers.append((mod, mod.render_levels))

                        if mod.show_viewport is False:
                            mod.render_levels = 0
                        else:
                            mod.render_levels = mod.levels
    
            # Export setings
            model_path = exchange_dir + "exchange.fbx"
            apply_modifiers = b_exchanger.doApplyModifiers

            # Export Model
            bpy.ops.export_scene.fbx(filepath=model_path, check_existing=True, axis_forward='-Z', axis_up='Y', use_selection=True, global_scale=self.world_scale, apply_unit_scale=True, bake_space_transform=True, use_mesh_modifiers=apply_modifiers, use_custom_props=True, primary_bone_axis='Y', secondary_bone_axis='X')

            # revert render level of modifiers back
            for mod_stuff in fix_modidiers:
                mod_stuff[0].render_levels = mod_stuff[1]
            fix_modidiers = None  # clear array

        else:
            self.report(
                {'INFO'}, "No Selected Objects or Bad Exchange Folder!!!")

        return {'FINISHED'}


class EX_ImportScene(bpy.types.Operator):
    bl_idname = "ex_import.exchanger"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    bl_options = {'UNDO'}

    world_scale = FloatProperty( default=1.0 )

    def invoke(self, context, event):
        # Addon Preferences
        #user_preferences = context.user_preferences
        addon_prefs = context.preferences.addons[__package__].preferences

        scene = context.scene
        b_exchanger = bpy.context.scene.b_exchanger

        exchange_dir = addon_prefs.exchangedir.replace("\\", os.sep)
        if exchange_dir.endswith(os.sep) is False:
            exchange_dir += os.sep

        if os.path.isdir(exchange_dir):

            ## fix for animation removement for Modo
            #scene_objects = []
            #for obj in bpy.context.scene.objects:
                #scene_objects.append(obj.name)

            # Import setings
            model_path = exchange_dir + "exchange.fbx"
            importNormals = b_exchanger.importNormals

            # IMPORT
            bpy.ops.import_scene.fbx(filepath=model_path, axis_forward='-Z', axis_up='Y', global_scale=self.world_scale, bake_space_transform=True, use_custom_normals=importNormals, force_connect_children=False, primary_bone_axis='Y', secondary_bone_axis='X', use_prepost_rot=True)

            ## remove animatrins. Fix for Modo
            #for obj in scene.objects:
                #if obj.name not in scene_objects:
                    #obj.animation_data.action.use_fake_user = False
                    #obj.animation_data.action = None

            #scene_objects = None  # clear

        else:
            self.report({'INFO'}, "Bad Exchange Folder!!!")

        return {'FINISHED'}
