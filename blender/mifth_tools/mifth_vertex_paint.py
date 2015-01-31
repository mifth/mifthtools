import bpy

from bpy.props import *
from bpy.types import Operator, AddonPreferences
from bpy.types import Menu, Panel, UIList, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, BoolVectorProperty, PointerProperty


class MFTVertexPaintMenu(bpy.types.Menu):
    bl_idname = "mftv.vertex_paint_menu"
    bl_label = "Mifth VertexPaint"
    bl_description = "Mifth Vertex Paint Menu"

    def draw(self, context):
        layout = self.layout

        layout.separator()
        op = layout.operator(MFTSetColorToSelected.bl_idname)
        if context.scene.tool_settings.unified_paint_settings.use_unified_color is True:
            op.strength = context.scene.tool_settings.unified_paint_settings.color
        else:
            op.strength = context.tool_settings.vertex_paint.brush.color

        layout.operator(MFTInvertColors.bl_idname)


class MFTSetColorToSelected(bpy.types.Operator):
    bl_idname = "mftv.set_colors_to_selected"
    bl_label = "Set Colors to Selected"
    bl_description = "Set Colors to Selected"
    bl_options = {'REGISTER', 'UNDO'}

    strength = FloatVectorProperty(
        name="Color",
        subtype='COLOR',
        default=(0.5, 0.5, 0.5),
        min=0.0, max=1.0,
        description="wire color of the group"
    )
    selected_faces_only = BoolProperty(
        name="Selected Faces Only", default=False)

    def execute(self, context):

        obj = context.scene.objects.active
        color_layer = obj.data.vertex_colors.active

        i = 0
        for poly in obj.data.polygons:
            for vert_idx in poly.vertices:
                if obj.data.vertices[vert_idx].select is True:
                    # rgb = [0 for i in range(3)]
                    if self.selected_faces_only is False:
                        color_layer.data[i].color = self.strength
                    else:
                        if poly.select is True:
                            color_layer.data[i].color = self.strength

                i += 1

            obj.data.update()

        return {'FINISHED'}


class MFTInvertColors(bpy.types.Operator):
    bl_idname = "mftv.invert_colors"
    bl_label = "Invert Colors"
    bl_description = "Invert Colors"
    bl_options = {'REGISTER', 'UNDO'}

    selected_faces_only = BoolProperty(
        name="Selected Faces Only", default=False)
    split_points = BoolProperty(name="Split Points", default=False)

    def execute(self, context):

        obj = context.scene.objects.active
        color_layer = obj.data.vertex_colors.active

        i = 0
        for poly in obj.data.polygons:
            for vert_idx in poly.vertices:
                if self.selected_faces_only is False:
                    color_layer.data[i].color[
                        0] = 1.0 - color_layer.data[i].color[0]
                    color_layer.data[i].color[
                        1] = 1.0 - color_layer.data[i].color[1]
                    color_layer.data[i].color[
                        2] = 1.0 - color_layer.data[i].color[2]
                else:
                    if obj.data.vertices[vert_idx].select is True:
                        if self.split_points is True:
                            if poly.select is True:
                                color_layer.data[i].color[
                                    0] = 1.0 - color_layer.data[i].color[0]
                                color_layer.data[i].color[
                                    1] = 1.0 - color_layer.data[i].color[1]
                                color_layer.data[i].color[
                                    2] = 1.0 - color_layer.data[i].color[2]
                        else:
                            color_layer.data[i].color[
                                0] = 1.0 - color_layer.data[i].color[0]
                            color_layer.data[i].color[
                                1] = 1.0 - color_layer.data[i].color[1]
                            color_layer.data[i].color[
                                2] = 1.0 - color_layer.data[i].color[2]
                i += 1

            obj.data.update()

        return {'FINISHED'}
