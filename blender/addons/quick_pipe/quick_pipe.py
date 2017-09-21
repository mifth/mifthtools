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

    first_mouse_x = IntProperty()
    first_value = FloatProperty()

    def modal(self, context, event):
        if event.type in {'RIGHTMOUSE', 'ESC', 'LEFTMOUSE'}:
            return {'FINISHED'}

        if event.type == 'MOUSEMOVE':
            delta = (self.first_mouse_x - event.mouse_x)

            if event.ctrl:
                delta *= 0.1

                if event.shift:
                    delta *= 0.1

            context.object.data.bevel_depth = abs( (self.first_value + delta) * 0.01 )
        elif event.type == 'WHEELUPMOUSE':
            bpy.context.object.data.bevel_resolution += 1
        elif event.type == 'WHEELDOWNMOUSE':
            if bpy.context.object.data.bevel_resolution > 0:
                bpy.context.object.data.bevel_resolution -= 1

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.object:

            if( context.object.type == 'MESH' ):
                self.first_mouse_x = event.mouse_x

                bpy.ops.mesh.duplicate_move()
                bpy.ops.mesh.separate(type='SELECTED')
                bpy.ops.object.editmode_toggle()
                bpy.ops.object.select_all(action='DESELECT')

                pipe = bpy.context.scene.objects[0]
                pipe.select = True
                bpy.context.scene.objects.active = pipe
                bpy.ops.object.convert(target='CURVE')

                pipe.data.fill_mode = 'FULL'
                #pipe.data.splines[0].use_smooth = True
                pipe.data.bevel_resolution = 1
                pipe.data.bevel_depth = 0.1

            elif( context.object.type == 'CURVE' ):
                self.report({'WARNING'}, "Need Edit Mode!")
                return {'CANCELLED'}

            self.first_value = pipe.data.bevel_depth

            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
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
    