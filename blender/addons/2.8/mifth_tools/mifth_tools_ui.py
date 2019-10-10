import bpy
from bpy.props import *
from bpy.types import Operator, AddonPreferences


class MFT_PT_PanelPose(bpy.types.Panel):
    bl_label = "Bones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "posemode"
    bl_category = 'Mifth'
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        mifthTools = context.scene.mifthTools

        op = layout.operator("mft.copy_bones_transform", text="CopyBonesTransform")
        op.mode = 'Copy'
        op = layout.operator("mft.copy_bones_transform", text="PasteBonesTransform")
        op.mode = 'Paste'


class MFT_PT_PanelAnimation(bpy.types.Panel):
    bl_label = "Animations"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Mifth'
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        mifthTools = context.scene.mifthTools

        layout.operator("mft.curveanimator", text="Curve Animator")
        layout.prop(mifthTools, "doUseSceneFrames", text='UseSceneFrames')
        row = layout.row()
        row.prop(mifthTools, "curveAniStartFrame", text='Start')
        row.prop(mifthTools, "curveAniEndFrame", text='End')
        row = layout.row()
        row.prop(mifthTools, "curveAniStepFrame", text='Steps')
        row.prop(mifthTools, "curveAniInterpolation", text='Interpolation')

        layout.separator()
        layout.separator()
        layout.operator("mft.morfcreator", text="Morfer")
        layout.prop(mifthTools, "morfCreatorNames")
        layout.prop(mifthTools, "morfUseWorldMatrix", text='useWorldMatrix')
        layout.prop(mifthTools, "morfApplyModifiers", text='applyModifiers')


class MFT_PT_PanelPlaykot(bpy.types.Panel):
    bl_label = "PlaykotTools"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Mifth'
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        mifthTools = context.scene.mifthTools

        layout.operator("mft.render_scene_2x", text="ScaleCrop")
        layout.operator("mft.cropnoderegion", text="CropNodeRegion")
        layout.operator("mft.crop_to_viewport", text="CropToViewport")

        layout.separator()
        layout.operator("mft.outputcreator", text="Create Output")
        layout.prop(mifthTools, "outputFolder")
        row = layout.row()
        row.prop(mifthTools, "outputSubFolder")
        row.prop(mifthTools, "doOutputSubFolder", text='')
        layout.prop(mifthTools, "outputSequence")
        layout.prop(mifthTools, "outputSequenceSize")


class MFT_PT_PanelCloning(bpy.types.Panel):
    bl_label = "Cloning"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Mifth'
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        mifthTools = bpy.context.scene.mifthTools
        mifthCloneTools = bpy.context.scene.mifthCloneTools

        layout.label(text="Draw Clones:")
        layout.operator("mft.draw_clones", text="DrawClones")
        layout.operator("mft.pick_obj_to_clone_draw", text="PickObjects")
        layout.prop(
            mifthCloneTools, "drawClonesDirectionRotate", text='DirectionRotate')
        layout.prop(
            mifthCloneTools, "drawClonesRadialRotate", text='RadialRotate')
        layout.prop(
            mifthCloneTools, "drawClonesNormalRotate", text='NormalRotate')
        layout.prop(mifthCloneTools, "drawClonesOptimize", text='Optimize')

        layout.prop(mifthCloneTools, "drawStrokeLength", text='Stroke')

        layout.prop(mifthCloneTools, "drawRandomStrokeScatter", text='Scatter')
        layout.prop(
            mifthCloneTools, "randNormalRotateClone", text='RandNormal')
        layout.prop(
            mifthCloneTools, "randDirectionRotateClone", text='RandDirection')
        layout.prop(mifthCloneTools, "randScaleClone", text='RandScale')

        layout.prop(mifthCloneTools, "drawPressure", text='DrawPressure')
        row = layout.row()
        row.prop(mifthCloneTools, "drawPressureRelativeStroke", text='S')
        row.prop(mifthCloneTools, "drawPressureScale", text='S')
        row.prop(mifthCloneTools, "drawPressureScatter", text='S')

        layout.prop(mifthCloneTools, "drawClonesAxis", text='Axis')
        layout.separator()

        layout.label(text="Clone Selected:")
        layout.operator("mft.clonetoselected", text="CloneToSelected")
        layout.separator()

        layout.label(text="Radial Clone:")
        layout.operator("mft.radialclone", text="Radial Clone")
        # layout.prop(mifthTools, "radialClonesNumber", text='')
        row = layout.row()
        row.prop(mifthCloneTools, "radialClonesAxis", text='')
        row.prop(mifthCloneTools, "radialClonesAxisType", text='')
        layout.separator()

        layout.label(text="Position Group:")
        layout.operator("mft.group_instance_to_cursor", text="Position Group")
        layout.prop(mifthCloneTools, "getGroupsLst", text='')
        layout.separator()

        layout.operator("mft.group_to_mesh", text="Groups To Mesh")
