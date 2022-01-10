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


class SimpleSceneCoat3D(bpy.types.PropertyGroup):

    exportModelType: EnumProperty(
        name="Export Type",
        items=(('OBJ', 'OBJ', ''),
               ('FBX', 'FBX', ''),
               # ('DAE', 'DAE', ''),
               ),
        default='FBX'
    )

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

    copyTexturesPath: StringProperty(
        name="Copy Textures Path",
        subtype="DIR_PATH",
        default="",
    )

    type: EnumProperty(name="Export Type",
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
                              ("autopo", "Mesh For Auto-retopology", ""),),
                       default="ppp")


class S3DC_PT_MainPanel(bpy.types.Panel):
    
    bl_label = '3DCoat Applink'
    bl_space_type = "VIEW_3D"
    
    bl_region_type = "UI"
    # bl_region_type = 'TOOLS'
    
    bl_category = "Ex"
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        simple3Dcoat = context.scene.simple3Dcoat

        # GUI
        row = layout.row()
        row.label(text="Import/Export Objects")
        row = layout.row()
        row.prop(simple3Dcoat, "type", text="")
        row = layout.row()

        colL = row.column()
        colR = row.column()

        colL.operator("export_applink.simple_3d_coat", text="Export")
        colR.operator("import_applink.simple_3d_coat", text="Import")

        row = layout.row()
        row.prop(simple3Dcoat, "doApplyModifiers", text="Apply Modifiers")
        row = layout.row()
        row.prop(simple3Dcoat, "exportMaterials", text="Export Materials")
        row = layout.row()
        row = layout.row()
        row.label(text="Textures Path")
        row = layout.row()
        row.prop(simple3Dcoat, "copyTexturesPath", text="")
        # row = layout.row()
        # row.operator("copytextures.simple_3d_coat", text="Copy Textures to a Path")
        row = layout.row()
        row = layout.row()
        row.operator("clearexchange.simple_3d_coat", text="Clear Exchange Folder")

        row = layout.row()
        row.label(text="Export Type")
        row = layout.row()
        row.prop(simple3Dcoat, "exportModelType", text='export Model Type', expand=True)


class S3DC_AddonPreferences(AddonPreferences):
    # this must match the addon name, use '__package__'
    # when defining this in a submodule of a python package.
    # bl_idname = __name__
    bl_idname = __package__

    exchangedir: StringProperty(name="ExchangeFolder",
                                subtype="DIR_PATH",
                                default="")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text="Please, set Exchanges Folder and save Preferences")
        row = layout.row()
        row.prop(self, "exchangedir")


class S3DC_OP_ExportScene(bpy.types.Operator):
    bl_idname = "export_applink.simple_3d_coat"
    bl_label = "Export your custom property"
    bl_description = "Export your custom property"
    # bl_options = {'UNDO'}

    def invoke(self, context, event):
        # Addon Preferences
        user_pref = context.preferences
        addon_prefs = user_pref.addons[__package__].preferences

        # checkname = ''
        simple3Dcoat = context.scene.simple3Dcoat
        # scene = context.scene

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
            # elif simple3Dcoat.exportModelType == 'DAE':
            #     exportModelExtension = ".dae"

            # create Simple3DCoat directory
            simple3DCoatDir = addon_prefs.exchangedir + "BlenderSimple3DCoat" + os.sep
            if not(os.path.isdir(simple3DCoatDir)):
                os.makedirs(simple3DCoatDir)

            # Model Path
            modelExportPath = simple3DCoatDir + blenderExportName + exportModelExtension
            
            tspace = False
            export_normals = False
            if simple3Dcoat.type in {'ppp', 'mv', 'ptex', 'uv'}:
                tspace = True
                export_normals = True

            # Export Model
            if simple3Dcoat.exportModelType == 'OBJ':
                bpy.ops.export_scene.obj(filepath=modelExportPath, use_selection=True,
                                         use_mesh_modifiers=simple3Dcoat.doApplyModifiers,
                                         use_blen_objects=True, use_normals=export_normals,
                                         use_materials=simple3Dcoat.exportMaterials,
                                         keep_vertex_order=True, axis_forward='-Z',
                                         axis_up='Y')

            elif simple3Dcoat.exportModelType == 'FBX':
                bpy.ops.export_scene.fbx(filepath=modelExportPath, check_existing=True,
                                         axis_forward='-Z', axis_up='Y', use_selection=True,
                                         global_scale=1.0, apply_unit_scale=True,
                                         use_tspace=tspace,
                                         bake_space_transform=True,
                                         use_mesh_modifiers=simple3Dcoat.doApplyModifiers,
                                         bake_anim=False)
                
            # elif simple3Dcoat.exportModelType == 'DAE':
            #     bpy.ops.wm.collada_export(filepath=modelExportPath, apply_modifiers=simple3Dcoat.doApplyModifiers,
            #                               selected=True, include_children=True,
            #                               include_armatures=False, include_shapekeys=False,
            #                               include_uv_textures=False, include_material_textures=False,
            #                               use_texture_copies=False, use_object_instantiation=True)

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
                file.write("\n[TexOutput:%s]" % (copyToFolder))

            file.close()

        else:
            self.report(
                {'INFO'}, "No Selected Objects or Bad Exchange Folder!!!")

        return {'FINISHED'}


class S3DC_OP_ImportScene(bpy.types.Operator):
    bl_idname = "import_applink.simple_3d_coat"
    bl_label = "import your custom property"
    bl_description = "import your custom property"
    bl_options = {'UNDO'}

    def invoke(self, context, event):
        # Addon Preferences
        user_pref = context.preferences
        addon_prefs = user_pref.addons[__package__].preferences

        # scene = context.scene
        simple3Dcoat = context.scene.simple3Dcoat
        # coat = bpy.simple3Dcoat

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
                        bpy.ops.import_scene.obj(filepath=new_applink_name, axis_forward='-Z',
                                                 axis_up='Y', use_image_search=False)
                        
                    elif new_applink_name.endswith(".fbx"):
                        bpy.ops.import_scene.fbx(filepath=new_applink_name, axis_forward='-Z',
                                                 axis_up='Y', global_scale=1.0,
                                                 bake_space_transform=True, use_custom_normals=True,
                                                 force_connect_children=False,
                                                 primary_bone_axis='Y', secondary_bone_axis='X',
                                                 use_prepost_rot=True)
                        
                    # elif new_applink_name.endswith(".dae"):
                    #     bpy.ops.wm.collada_import(filepath=new_applink_name)

                    bpy.ops.object.transform_apply(location=False, rotation=True,
                                                   scale=False)  # Apply Rotation

                else:
                    self.report({'INFO'}, "No Imported Objects!!!")
                break
            obj_pathh.close()
        else:
            self.report({'INFO'}, "No Imported Objects or Bad Exchange Folder!!!")

        return {'FINISHED'}


class S3DC_OP_ClearExchangeFolder(bpy.types.Operator):
    bl_idname = "clearexchange.simple_3d_coat"
    bl_label = "Clear Exchange Folder"
    bl_description = "Clear Exchange Folder.."

    def invoke(self, context, event):
        # Addon Preferences
        user_pref = context.preferences
        addon_prefs = user_pref.addons[__package__].preferences
        simple3DCoatDir = addon_prefs.exchangedir + "BlenderSimple3DCoat" + os.sep

        # Remove BlenderSimple3DCoat Folder
        if os.path.isdir(simple3DCoatDir):
            shutil.rmtree(simple3DCoatDir)

        return {'FINISHED'}


classes = (
    SimpleSceneCoat3D,
    S3DC_AddonPreferences,
    S3DC_OP_ExportScene,
    S3DC_OP_ImportScene,
    S3DC_OP_ClearExchangeFolder,
    S3DC_PT_MainPanel
)


def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    bpy.types.Scene.simple3Dcoat = PointerProperty(name="Applink Variables",
                                                   type=SimpleSceneCoat3D,
                                                   description="Applink variables")
    

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    del bpy.types.Scene.simple3Dcoat

