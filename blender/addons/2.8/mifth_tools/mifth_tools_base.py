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

import math
# import mifth_tools_cloning


# bpy.mifthTools = dict()

class MFTSceneRender2X(bpy.types.Operator):
    bl_idname = "mft.render_scene_2x"
    bl_label = "Render2X"
    bl_description = "Render2X..."
    bl_options = {'REGISTER', 'UNDO'}

    scale_value : FloatProperty(
        default=2.0,
        min=0.001,
        max=500.0
    )

    def execute(self, context):

        scene = context.scene
        nodes = scene.node_tree.nodes
        mifthTools = context.scene.mifthTools

        crop_nodes_2x(nodes, self.scale_value)

        return {'FINISHED'}


def crop_nodes_2x(nodes, scale_value):
    for node in nodes:
        if node.type == 'GROUP':
            crop_nodes_2x(node.node_tree.nodes, scale_value)
        elif node.type == 'CROP':
            node.min_x *= scale_value
            node.max_x *= scale_value
            node.min_y *= scale_value
            node.max_y *= scale_value


class MFTCropNodeRegion(bpy.types.Operator):
    bl_idname = "mft.cropnoderegion"
    bl_label = "Crop Node Region"
    bl_description = "Crop Node Region"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        nodes = scene.node_tree.nodes
        cropNode = nodes.active
        crop_percentage = context.scene.render.resolution_percentage / 100.0


        if cropNode != None:
            if cropNode.type == 'CROP':
                cropNode.min_x = scene.render.border_min_x * scene.render.resolution_x * crop_percentage
                cropNode.max_x = scene.render.border_max_x * scene.render.resolution_x * crop_percentage
                cropNode.min_y = scene.render.border_max_y * scene.render.resolution_y * crop_percentage
                cropNode.max_y = scene.render.border_min_y * scene.render.resolution_y * crop_percentage

            elif cropNode.type == 'GROUP':
                cropGroupNode = cropNode.node_tree.nodes.active

                if cropGroupNode != None and cropGroupNode.type == 'CROP':
                    cropGroupNode.min_x = scene.render.border_min_x * scene.render.resolution_x * crop_percentage
                    cropGroupNode.max_x = scene.render.border_max_x * scene.render.resolution_x * crop_percentage
                    cropGroupNode.min_y = scene.render.border_max_y * scene.render.resolution_y * crop_percentage
                    cropGroupNode.max_y = scene.render.border_min_y * scene.render.resolution_y * crop_percentage
        else:
            self.report({'INFO'}, "Select Crop Node!")

        return {'FINISHED'}

class MFTCropToViewport(bpy.types.Operator):
    bl_idname = "mft.crop_to_viewport"
    bl_label = "Crop To Viewport"
    bl_description = "Crop To Viewport..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        nodes = scene.node_tree.nodes
        cropNode = nodes.active

        if cropNode != None:
            if cropNode.type == 'CROP':
                scene.render.border_min_x = float(cropNode.min_x / scene.render.resolution_x) / (float(scene.render.resolution_percentage) / 100.0)
                scene.render.border_max_x = float(cropNode.max_x / scene.render.resolution_x) / (float(scene.render.resolution_percentage) / 100.0)
                scene.render.border_max_y = float(cropNode.min_y / scene.render.resolution_y) / (float(scene.render.resolution_percentage) / 100.0)
                scene.render.border_min_y = float(cropNode.max_y / scene.render.resolution_y) / (float(scene.render.resolution_percentage) / 100.0)

            elif cropNode.type == 'GROUP':
                cropGroupNode = cropNode.node_tree.nodes.active

                if cropGroupNode != None and cropGroupNode.type == 'CROP':
                    scene.render.border_min_x = float(cropGroupNode.min_x / scene.render.resolution_x) / (float(scene.render.resolution_percentage) / 100.0)
                    scene.render.border_max_x = float(cropGroupNode.max_x / scene.render.resolution_x) / (float(scene.render.resolution_percentage) / 100.0)
                    scene.render.border_max_y = float(cropGroupNode.min_y / scene.render.resolution_y) / (float(scene.render.resolution_percentage) / 100.0)
                    scene.render.border_min_y = float(cropGroupNode.max_y / scene.render.resolution_y) / (float(scene.render.resolution_percentage) / 100.0)
        else:
            self.report({'INFO'}, "Select Crop Node!")

        return {'FINISHED'}


class MFTOutputCreator(bpy.types.Operator):
    bl_idname = "mft.outputcreator"
    bl_label = "Create Output"
    bl_description = "Output Creator"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = context.scene
        nodes = scene.node_tree.nodes
        mifthTools = context.scene.mifthTools

        output_file = nodes.new("CompositorNodeOutputFile")
        output_file.base_path = "//" + mifthTools.outputFolder + "/"

        output_file.file_slots.remove(output_file.inputs[0])
        for i in range(mifthTools.outputSequenceSize):
            idx = str(i + 1)
            if i < 9:
                idx = "0" + idx

            outFile = ""
            if mifthTools.doOutputSubFolder is True:
                outFile = mifthTools.outputSubFolder + "_" + idx + "/"
            outFile += mifthTools.outputSequence + "_" + idx + "_"

            output_file.file_slots.new(outFile)

        return {'FINISHED'}


class MFTCurveAnimator(bpy.types.Operator):
    bl_idname = "mft.curveanimator"
    bl_label = "Curve Animator"
    bl_description = "Curve Animator"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        mifthTools = context.scene.mifthTools

        startFrame = context.scene.frame_start
        if mifthTools.doUseSceneFrames is False:
            startFrame = mifthTools.curveAniStartFrame

        endFrame = context.scene.frame_end
        if mifthTools.doUseSceneFrames is False:
            endFrame = mifthTools.curveAniEndFrame

        totalFrames = endFrame - startFrame
        frameSteps = mifthTools.curveAniStepFrame - 1

        for curve in context.selected_objects:
            if curve.type == 'CURVE':

                for frStep in range(frameSteps + 1):
                    aniPos = 1.0 - (float(frStep) / float(frameSteps))
                    goToFrame = int(aniPos * float(totalFrames))
                    goToFrame += startFrame
                    context.scene.frame_current = goToFrame
                    print(goToFrame)

                    for spline in curve.data.splines:
                        # print(spline.points)
                        # if len(spline.bezier_points) >= 2:
                        spline.use_bezier_u = False
                        spline.use_endpoint_u = True
                        # spline.use_cyclic_u = False

                        aniInterpolation = mifthTools.curveAniInterpolation

                        allPoints = None
                        if spline.type == 'BEZIER':
                            allPoints = spline.bezier_points
                        else:
                            allPoints = spline.points

                        splineSize = len(allPoints)
                        iInterpolation = aniPos - aniInterpolation

                        for i in range(splineSize):
                            point = allPoints[i]
                            iPlace = float(i + 1) / float(splineSize)

                            if iPlace >= aniPos and goToFrame != endFrame:
                                point.radius = 0.0

                            elif iPlace < aniPos and iPlace > iInterpolation and goToFrame != endFrame and goToFrame != startFrame:
                                additionalInterpolation = 1.0 - \
                                    ((iPlace - iInterpolation)
                                     / aniInterpolation)
                                point.radius *= additionalInterpolation
                                # print(additionalInterpolation)

                            point.keyframe_insert(
                                data_path="radius", frame=goToFrame)

        return {'FINISHED'}


class MFTMorfCreator(bpy.types.Operator):
    bl_idname = "mft.morfcreator"
    bl_label = "Morfing Creator"
    bl_description = "Morfing Creator from different objects"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        scene = bpy.context.scene
        mifthTools = scene.mifthTools

        if len(context.selected_objects):
            objAct = scene.objects.active
            morfIndex = 1

            # print(objAct.data.shape_keys)
            if objAct.data.shape_keys is None:
                basisKey = objAct.shape_key_add(from_mix=False)
                basisKey.name = 'Basis'

            for obj in context.selected_objects:
                if len(context.selected_objects) > 1 and obj == objAct:
                    pass
                else:
                    if len(obj.data.vertices) == len(objAct.data.vertices):
                        shapeKey = objAct.shape_key_add(from_mix=False)

                        if mifthTools.morfCreatorNames != '':
                            shapeKey.name = mifthTools.morfCreatorNames

                            if len(context.selected_objects) > 2:
                                shapeKey.name += "_" + str(morfIndex)

                            morfIndex += 1
                        else:
                            shapeKey.name = obj.name

                        modifiedMesh = obj.data
                        if mifthTools.morfApplyModifiers is True:
                            modifiedMesh = obj.to_mesh(
                                scene=context.scene, apply_modifiers=True, settings='PREVIEW')

                        for vert in modifiedMesh.vertices:
                            if mifthTools.morfUseWorldMatrix:
                                shapeKey.data[vert.index].co = obj.matrix_world * vert.co
                            else:
                                shapeKey.data[vert.index].co = vert.co
                            # print(vert.co)  # this is a vertex coord of the
                            # mesh
                    else:
                        self.report(
                            {'INFO'}, "Model " + obj.name + " has different points count")

        return {'FINISHED'}


class MFTCopyBonesTransform(bpy.types.Operator):
    bl_idname = "mft.copy_bones_transform"
    bl_label = "Copy Bones Transform"
    bl_description = "Copy Bones Transform"
    bl_options = {'REGISTER', 'UNDO'}

    bones_transform = []
    mode : EnumProperty(
        items=(('Copy', 'Copy', ''),
               ('Paste', 'Paste', '')
               ),
        default = 'Copy'
    )

    def execute(self, context):

        scene = context.scene
        mifthTools = scene.mifthTools
        obj_act = context.active_object
        all_bones = obj_act.data.bones

        sel_bones = context.selected_pose_bones

        if sel_bones:
            if self.mode == 'Copy':
                del self.bones_transform[:]
                for bone in sel_bones:
                    self.bones_transform.append(bone.matrix.copy())
                    #print(bone.matrix)
            elif self.mode == 'Paste':
                for i in range(len(sel_bones)):
                    sel_bones[i].matrix = self.bones_transform[i].copy()
                    #print(self.bones_transform[i])

        return {'FINISHED'}
