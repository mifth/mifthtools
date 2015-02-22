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


bpy.simple3Dcoat = dict()
bpy.simple3Dcoat['active_coat'] = ''
bpy.simple3Dcoat['status'] = 0


class MainPanel3DCoat(bpy.types.Panel):
    bl_label = "Simple3DCoat Applink"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        me = context.scene.objects
        mat_list = []
        import_no = 0
        coat = bpy.simple3Dcoat
        simple3Dcoat = bpy.context.scene.simple3Dcoat

        # GUI
        row = layout.row()
        row.label(text="Import/Export Objects")
        row = layout.row()
        row.prop(simple3Dcoat, "type", text="")
        row = layout.row()

        colL = row.column()
        colR = row.column()

        colR.operator("export_applink.simple_3d_coat", text="ExportObjects")
        colL.operator("import_applink.simple_3d_coat", text="ImportObjects")

        row = layout.row()
        row.prop(simple3Dcoat, "doApplyModifiers", text="Apply Modifiers")
        row = layout.row()
        row.prop(simple3Dcoat, "exportMaterials", text="Export Materials")
        row = layout.row()
        row = layout.row()
        row.label(text="Textures Path")
        row = layout.row()
        row.prop(simple3Dcoat, "copyTexturesPath", text="")
        #row = layout.row()
        #row.operator("copytextures.simple_3d_coat", text="Copy Textures to a Path")
        row = layout.row()
        row = layout.row()
        row.operator("clearexchange.simple_3d_coat", text="Clear Exchange Folder")

        row = layout.row()
        row.label(text="Export Type")
        row = layout.row()
        row.prop(simple3Dcoat, "exportModelType", text='export Model Type', expand=True)


class Coat3DAddonPreferences(AddonPreferences):
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


class ExportScene3DCoat(bpy.types.Operator):
    bl_idname = "export_applink.simple_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        # Addon Preferences
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences

        #checkname = ''
        simple3Dcoat = bpy.context.scene.simple3Dcoat
        #scene = context.scene

        if len(bpy.context.selected_objects) > 0 and os.path.isdir(addon_prefs.exchangedir):
            importfile = addon_prefs.exchangedir
            importfile += ('%simport.txt' % (os.sep))

            # Paths for export/import
            blenderExportName = "export"
            blenderImportName = "import"

            # Model Extension
            exportModelExtension = ".obj"
            if simple3Dcoat.exportModelType == 'FBX':
                exportModelExtension = ".fbx"
            elif simple3Dcoat.exportModelType == 'DAE':
                exportModelExtension = ".dae"

            # create Simple3DCoat directory
            simple3DCoatDir = addon_prefs.exchangedir + "BlenderSimple3DCoat" + os.sep
            if not(os.path.isdir(simple3DCoatDir)):
                os.makedirs(simple3DCoatDir)

            # Model Path
            modelExportPath = simple3DCoatDir + blenderExportName + exportModelExtension

            # Export Model
            if simple3Dcoat.exportModelType == 'OBJ':
                bpy.ops.export_scene.obj(
                    filepath=modelExportPath, use_selection=True, use_mesh_modifiers=simple3Dcoat.doApplyModifiers,
                    use_blen_objects=True, use_normals=True, use_materials=simple3Dcoat.exportMaterials, keep_vertex_order=True, axis_forward='-Z', axis_up='Y')
            elif simple3Dcoat.exportModelType == 'FBX':
                bpy.ops.export_scene.fbx(check_existing=True, filepath=modelExportPath, filter_glob="*.fbx", version='BIN7400', use_selection=True, global_scale=1.0, axis_forward='-Z', axis_up='Y', bake_space_transform=False, object_types={'MESH'}, use_mesh_modifiers=simple3Dcoat.doApplyModifiers, mesh_smooth_type='FACE', use_mesh_edges=False, use_tspace=False, use_custom_properties=False, use_armature_deform_only=False, bake_anim=False, bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False, bake_anim_step=1.0, bake_anim_simplify_factor=1.0, use_anim=False, use_anim_action_all=False, use_default_take=True, use_anim_optimize=True, anim_optimize_precision=6.0, path_mode='AUTO', embed_textures=False, batch_mode='OFF', use_batch_own_dir=True, use_metadata=True)
            elif simple3Dcoat.exportModelType == 'DAE':
                bpy.ops.wm.collada_export(filepath=modelExportPath, apply_modifiers=simple3Dcoat.doApplyModifiers, selected=True, include_children=True, include_armatures=False, include_shapekeys=False, include_uv_textures=False, include_material_textures=False, use_texture_copies=False, use_object_instantiation=True)

            # Save import file
            file = open(importfile, "w")
            file.write("%s" %
                       (simple3DCoatDir + blenderExportName + exportModelExtension))
            file.write("\n%s" %
                       (simple3DCoatDir + blenderImportName + exportModelExtension))
            file.write("\n[%s]" % (simple3Dcoat.type))

            # Copy textures to a custom path
            copyToFolder = simple3Dcoat.copyTexturesPath
            if os.path.isdir(copyToFolder):
                file.write("\n[TexOutput:%s]"%(copyToFolder))

            file.close()

        else:
            self.report(
                {'INFO'}, "No Selected Objects or Bad Exchange Folder!!!")

        return {'FINISHED'}


class ImportScene3DCoat(bpy.types.Operator):
    bl_idname = "import_applink.simple_3d_coat"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        # Addon Preferences
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences

        #scene = context.scene
        simple3Dcoat = bpy.context.scene.simple3Dcoat
        #coat = bpy.simple3Dcoat

        exchangeFile = addon_prefs.exchangedir
        exchangeFile += ('%sexport.txt' % (os.sep))
        simple3DCoatDir = addon_prefs.exchangedir + "BlenderSimple3DCoat" + os.sep
        new_applink_name = None

        if(os.path.isfile(exchangeFile) and os.path.isdir(simple3DCoatDir)):
            obj_pathh = open(exchangeFile)

            for line in obj_pathh:
                new_applink_name = line
                if os.path.isfile(new_applink_name):
                    if new_applink_name.endswith(".obj"):
                        bpy.ops.import_scene.obj(filepath=new_applink_name, axis_forward='-Z', axis_up='Y', use_image_search=False)
                    elif new_applink_name.endswith(".fbx"):
                        bpy.ops.import_scene.fbx(filepath=new_applink_name, filter_glob="*.fbx", use_image_search=False, use_alpha_decals=False, decal_offset=0.0, axis_forward='-Z', axis_up='Y', global_scale=1.0)
                    elif new_applink_name.endswith(".dae"):
                        bpy.ops.wm.collada_import(filepath=new_applink_name)

                    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False) # Apply Rotation

                else:
                    self.report({'INFO'}, "No Imported Objects!!!")
                break
            obj_pathh.close()
        else:
            self.report({'INFO'}, "No Imported Objects or Bad Exchange Folder!!!")

        return {'FINISHED'}


class ClearExchangeFolder(bpy.types.Operator):
    bl_idname = "clearexchange.simple_3d_coat"
    bl_label = "Clear Exchange Folder"
    bl_description = "Clear Exchange Folder.."

    def invoke(self, context, event):
        # Addon Preferences
        user_preferences = context.user_preferences
        addon_prefs = user_preferences.addons[__package__].preferences
        simple3DCoatDir = addon_prefs.exchangedir + "BlenderSimple3DCoat" + os.sep

        # Remove BlenderSimple3DCoat Folder
        if os.path.isdir(simple3DCoatDir):
            shutil.rmtree(simple3DCoatDir)

        return {'FINISHED'}


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
