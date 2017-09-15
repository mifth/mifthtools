import bpy
import bmesh
import math
import mathutils as mathu

from bpy.props import IntProperty, FloatProperty

bl_info = {
    "name": "Quick Pipe",
    "author": "floatvoid (Jeremy Mitchell), Pavel Geraskin",
    "version": (1, 0),
    "blender": (2, 79, 0),
    "location": "View3D > Edit Mode",
    "description": "Quickly converts an edge selection to an extruded curve.",
    "warning": "",
    "wiki_url": "",
    "category": "View3D"}


class jmPipeTool(bpy.types.Operator):
    bl_idname = "object.quickpipe"
    bl_label = "Quick Pipe"
    bl_options = {'REGISTER', 'UNDO'}

    #bevel_depth = FloatProperty(default=0.1)

    def execute(self, context):
        if context.object:

            if( context.object.type == 'MESH' ):
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')
                
                pipe = bpy.context.scene.objects[0]
                pipe.select = True
                bpy.context.scene.objects.active = pipe
                bpy.ops.object.convert(target='CURVE')

                pipe.data.fill_mode = 'FULL'
                #pipe.data.splines[0].use_smooth = True
                pipe.data.bevel_resolution = 2
                pipe.data.bevel_depth = 0.1

            #elif( context.object.type == 'CURVE' ):
                #pipe = context.object

            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "No active object, could not finish")
            return {'CANCELLED'}


class VIEW3D_PT_tools_jmPipeTool(bpy.types.Panel):

    bl_label = "Quick Pipe"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_category = 'Tools'
    bl_context = "mesh_edit"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        row = layout.row()        
        row.operator("object.quickpipe")


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
    