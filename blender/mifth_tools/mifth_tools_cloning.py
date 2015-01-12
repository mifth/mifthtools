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
from bpy_extras import view3d_utils

import math
import mathutils
import random
from bpy.props import *
from mathutils import *

# bpy.mifthCloneTools = dict()

global drawForClonesObj
drawForClonesObj = []  # Array of Objects Names


# groups
def getGroups(scene, context):

    lst = []
    obj = context.scene.objects.active
    for group in bpy.data.groups:
        if obj is not None and obj.name in group.objects:
            lst.append((group.name, group.name, ""))

    return lst


class MFTCloneProperties(bpy.types.PropertyGroup):
    # Draw Cloned Settings
    drawClonesDirectionRotate = BoolProperty(
        name="drawClonesDirectionRotate",
        description="drawClonesDirectionRotate...",
        default=False
    )

    drawClonesRadialRotate = BoolProperty(
        name="drawClonesRadialRotate",
        description="drawClonesRadialRotate...",
        default=True
    )

    drawClonesNormalRotate = BoolProperty(
        name="drawClonesNormalRotate",
        description="drawClonesNormalRotate...",
        default=True
    )

    drawClonesOptimize = BoolProperty(
        name="drawClonesOptimize",
        description="drawClonesOptimize...",
        default=True
    )

    drawStrokeLength = FloatProperty(
        default=0.5,
        min=0.001,
        max=500.0
    )

    drawRandomStrokeScatter = FloatProperty(
        default=0.0,
        min=0.0,
        max=500.0
    )

    randNormalRotateClone = FloatProperty(
        default=0.0,
        min=0.0,
        max=180.0
    )

    randDirectionRotateClone = FloatProperty(
        default=0.0,
        min=0.0,
        max=180.0
    )

    randScaleClone = FloatProperty(
        default=0.0,
        min=0.0,
        max=0.99
    )

    drawPressure = FloatProperty(
        default=0.7,
        min=0.0,
        max=0.95
    )

    drawPressureRelativeStroke = BoolProperty(
        name="drawPressureRelativeStroke",
        description="Relative Stroke To Scale and Pressure",
        default=True
    )

    drawPressureScale = BoolProperty(
        name="drawPressureScale",
        description="Pressure for Scale",
        default=True
    )

    drawPressureScatter = BoolProperty(
        name="drawPressureScatter",
        description="Pressure for Scatter",
        default=True
    )

    drawClonesAxis = EnumProperty(
        items=(('X', 'X', ''),
               ('-X', '-X', ''),
               ('Y', 'Y', ''),
               ('-Y', '-Y', ''),
               ('Z', 'Z', ''),
               ('-Z', '-Z', '')
               ),
        default = 'Z'
    )

    # Radial Clone Settings
    radialClonesAxis = EnumProperty(
        items=(('X', 'X', ''),
               ('Y', 'Y', ''),
               ('Z', 'Z', '')
               ),
        default = 'Z'
    )

    radialClonesAxisType = EnumProperty(
        items=(('Global', 'Global', ''),
               ('Local', 'Local', '')
               ),
        default = 'Global'
    )

    # GroupInstance to Cursor
    getGroupsLst = EnumProperty(name='Get Groups',
                                description='Get Groups.',
                                items=getGroups)


class MFTPanelCloning(bpy.types.Panel):
    bl_label = "Cloning"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
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


class MFTDrawClones(bpy.types.Operator):
    bl_idname = "mft.draw_clones"
    bl_label = "Draw Clones"
    bl_description = "Draw Clones with Mouse"
    bl_options = {'REGISTER', 'UNDO'}

    doPick = False
    tabletPressure = 1.0
    drawOnObjects = None  # List of objects on which will be drawn
    obj_Active_True = None  # Active object befor starting drawing
    dupliList = None  # duplilist of objects for picking stuff
    currentStrokeList = None  # this is a stroke
    allStrokesList = None  # this is all strokes

    def modal(self, context, event):
        mifthCloneTools = bpy.context.scene.mifthCloneTools
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            finish_drawing(self, context)
            return {'FINISHED'}
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.doPick = True
            self.currentStrokeList = []
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.doPick = False
            self.allStrokesList.append(self.currentStrokeList)

            # Do optimization
            if mifthCloneTools.drawClonesOptimize is True and self.currentStrokeList is not None:
                for point in self.currentStrokeList:
                    copy_settings_clones(point.objNew, point.objOriginal)
            self.currentStrokeList = None

        if self.doPick is True:
            self.tabletPressure = event.pressure
            mft_pick_and_clone(self, context, event)

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        mifthCloneTools = bpy.context.scene.mifthCloneTools
        # global drawForClonesObj
        if len(drawForClonesObj) == 0 or len(context.selected_objects) == 0:
            self.report({'WARNING'}, "Pick Objects to Clone")
            return {'CANCELLED'}

        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            prepare_drawing(self, context)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}


class MFTPickObjToDrawClone(bpy.types.Operator):
    bl_idname = "mft.pick_obj_to_clone_draw"
    bl_label = "Pick"
    bl_description = "Pick To Clone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        mifthCloneTools = context.scene.mifthCloneTools

        if len(context.selected_objects) > 0:
            # global drawForClonesObj
            drawForClonesObj.clear()
            for obj in context.selected_objects:
                drawForClonesObj.append(obj.name)

        return {'FINISHED'}


class MTFDCPoint:

    def __init__(self, objNew, objOriginal, hitPoint, hitNormal):
        self.objNew, self.objOriginal, self.hitPoint, self.hitNormal = objNew, objOriginal, hitPoint, hitNormal


# Just prepare some stuff
def prepare_drawing(self, context):
    self.drawOnObjects = context.selected_objects
    for obj in self.drawOnObjects:
        obj.select = False
    self.obj_Active_True = context.scene.objects.active

    self.dupliList = mft_selected_objects_and_duplis(self)
    self.allStrokesList = []


# Just clear some stuff at the end
def finish_drawing(self, context):
    for obj in self.drawOnObjects:
        obj.select = True
    context.scene.objects.active = self.obj_Active_True
    self.drawOnObjects = None
    self.dupliList = None

    if self.allStrokesList is not None:
        for stroke in self.allStrokesList:
            stroke.clear()
        self.allStrokesList.clear()
    self.allStrokesList = None

    if self.currentStrokeList is not None:
        self.currentStrokeList.clear()
    self.currentStrokeList = None


def mft_selected_objects_and_duplis(self):
    """Loop over (object, matrix) pairs (mesh only)"""

    listObjMatrix = []
    for obj in self.drawOnObjects:
        if obj.type == 'MESH':
            listObjMatrix.append((obj, obj.matrix_world.copy()))

        if obj.dupli_type != 'NONE':
            obj.dupli_list_create(scene)
            for dob in obj.dupli_list:
                obj_dupli = dob.object
                if obj_dupli.type == 'MESH':
                    listObjMatrix.append((obj_dupli, dob.matrix.copy()))

        obj.dupli_list_clear()

    return listObjMatrix


def copy_settings_clones(newObj, oldObj):
    # Copy Groups
    for thisGroup in bpy.data.groups:
        if oldObj.name in thisGroup.objects:
            thisGroup.objects.link(newObj)

    # Copy Modifiers
    for old_modifier in oldObj.modifiers.values():
            new_modifier = newObj.modifiers.new(name=old_modifier.name,
                                                type=old_modifier.type)

    # copy duplis
    if oldObj.dupli_group is not None:
        newObj.dupli_type = oldObj.dupli_type
        newObj.dupli_group = oldObj.dupli_group


def mft_pick_and_clone(self, context, event, ray_max=5000.0):
    """Run this function on left mouse, execute the ray cast"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    def mft_obj_ray_cast(obj, matrix, view_vector, ray_origin):
        """Wrapper for ray casting that moves the ray into object space"""

        ray_target = ray_origin + (view_vector * ray_max)

        # get the ray relative to the object
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv * ray_origin
        ray_target_obj = matrix_inv * ray_target

        # cast the ray
        hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_target_obj)

        if hit is not None:
            hit_world = matrix * hit

            length_squared = (hit_world - ray_origin).length_squared

            if face_index != -1:
                return normal.normalized(), hit_world, length_squared

        return None, None, None

    # cast rays and find the closest object
    best_length_squared = ray_max * ray_max
    best_obj, best_obj_nor, best_obj_pos = None, None, None
    best_obj_rand, best_obj_nor_rand, best_obj_pos_rand = None, None, None
    best_obj_hit = None

    mifthCloneTools = bpy.context.scene.mifthCloneTools
    thePressure = max(1.0 - mifthCloneTools.drawPressure, self.tabletPressure)  # The pressure of a pen!

    for obj, matrix in self.dupliList:
        # get the ray from the viewport and mouse
        view_vector_mouse = view3d_utils.region_2d_to_vector_3d(
            region, rv3d, coord)
        ray_origin_mouse = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, coord)

        # if rv3d.view_perspective != 'PERSP':
        # move origin back for better work
        ray_origin_mouse = ray_origin_mouse - \
            (view_vector_mouse * (ray_max / 2.0))

        # Do RayCast! t1,t2,t3,t4 - temp values
        t1, t2, t3 = mft_obj_ray_cast(
            obj, matrix, view_vector_mouse, ray_origin_mouse)
        if t1 is not None and t3 < best_length_squared:
            best_obj = obj
            best_obj_nor, best_obj_pos, best_length_squared = t1, t2, t3
            best_obj_hit = t2

        # Check for stroke length
        if best_obj is not None:
            previousHit = None
            if len(self.currentStrokeList) > 0:
                previousHit = self.currentStrokeList[-1]  # get Last Element

            # Check for stroke
            strokeLength = mifthCloneTools.drawStrokeLength
            if mifthCloneTools.drawPressureScale is True and mifthCloneTools.drawPressureRelativeStroke is True and self.tabletPressure < 1.0 and mifthCloneTools.drawPressure > 0.0:
                strokeLength *= thePressure
            if previousHit is not None and (best_obj_pos - previousHit.hitPoint).length < strokeLength:
                best_obj = None  # Don't do cloning

    # random scatter things
    if mifthCloneTools.drawRandomStrokeScatter > 0.0 and best_obj is not None and t1 is not None:
        # Random Vec
        randX = random.uniform(
            -1.0, 1.0) * mifthCloneTools.drawRandomStrokeScatter  # 3.0 is random addition
        randY = random.uniform(
            -1.0, 1.0) * mifthCloneTools.drawRandomStrokeScatter  # 3.0 is random addition
        randZ = random.uniform(
            -1.0, 1.0) * mifthCloneTools.drawRandomStrokeScatter 

        if mifthCloneTools.drawPressureScatter is True and self.tabletPressure < 1.0 and mifthCloneTools.drawPressure > 0.0:
            randX *= thePressure
            randY *= thePressure
            randZ *= thePressure

        randVect = Vector((randX, randY, randZ))

        for obj, matrix in self.dupliList:
            ray_origin_rand = best_obj_pos + randVect
            ray_origin_rand_2d = view3d_utils.location_3d_to_region_2d(
                region, rv3d, ray_origin_rand)

            view_vector_rand = view3d_utils.region_2d_to_vector_3d(
                region, rv3d, (ray_origin_rand_2d.x, ray_origin_rand_2d.y))

            # if rv3d.view_perspective != 'PERSP':
            # move origin back for better work
            ray_origin_rand = ray_origin_rand - \
                (view_vector_rand * (ray_max / 2.0))

            t1, t2, t3 = mft_obj_ray_cast(
                obj, matrix, view_vector_rand, ray_origin_rand)
            # 3.0 is random addition
            if t1 is not None and (t2 - best_obj_hit).length <= mifthCloneTools.drawRandomStrokeScatter * 3.0:
                best_obj_nor, best_obj_pos = t1, t2

    # now we have the object under the mouse cursor,
    if best_obj is not None:
        objToClone = bpy.data.objects.get(random.choice(drawForClonesObj))

        # clone objects
        newDup = bpy.data.objects.new(objToClone.name, objToClone.data)
        context.scene.objects.link(newDup)
        newDup.select = True
        context.scene.objects.active = newDup
        newDup.location = best_obj_pos
        newDup.scale = objToClone.scale
        bpy.ops.object.rotation_clear()

        xyNor = best_obj_nor.copy()
        xyNor.z = 0.0

        if xyNor.length == 0:
            rotatePlaneAngle = math.radians(90.0)
            if best_obj_nor.z > 0:
                bpy.ops.transform.rotate(
                    value=-rotatePlaneAngle, axis=(1.0, 0.0, 0.0), proportional='DISABLED')
            else:
                bpy.ops.transform.rotate(
                    value=rotatePlaneAngle, axis=(1.0, 0.0, 0.0), proportional='DISABLED')
        else:
            xyNor = xyNor.normalized()

            if mifthCloneTools.drawClonesRadialRotate is True:
                # xyRot = ((best_obj_pos.copy() + xyNor) -
                # best_obj_pos.copy()).normalized()
                xyAngleRotate = Vector((0.0, -1.0, 0.0)).angle(xyNor)

                if xyNor.x < 0:
                    xyAngleRotate = -xyAngleRotate
                xyRotateAxis = Vector((0.0, 0.0, 1.0))
                bpy.ops.transform.rotate(
                    value=xyAngleRotate, axis=(0.0, 0.0, 1.0), proportional='DISABLED')

            if mifthCloneTools.drawClonesNormalRotate is True:
                # Other rotate

                xRotateAxis = xyNor.cross(best_obj_nor).normalized()
                angleRotate = xyNor.angle(best_obj_nor)

                if mifthCloneTools.drawClonesRadialRotate is False:
                    newDupMatrix = newDup.matrix_world

                    newDupYAxisTuple = (
                        newDupMatrix[0][1], newDupMatrix[1][1], newDupMatrix[2][1])
                    newDupYAxis = Vector(
                        newDupYAxisTuple).normalized()
                    newDupYAxis.negate()

                    xRotateAxis = newDupYAxis.cross(best_obj_nor).normalized()
                    angleRotate = newDupYAxis.angle(best_obj_nor)

                bpy.ops.transform.rotate(value=angleRotate, axis=(
                    (xRotateAxis.x, xRotateAxis.y, xRotateAxis.z)), proportional='DISABLED')

        # Ratate to Direction
        if mifthCloneTools.drawClonesDirectionRotate is True:
            previousHit = None
            if len(self.currentStrokeList) > 0:
                previousHit = self.currentStrokeList[-1]  # get Last Element
            else:
                if len(self.allStrokesList) > 0:
                    previousHit = self.allStrokesList[-1][
                        -1]  # get Last Element of previous Stroke

            if previousHit is not None:
                newDirRotLookAtt = (
                    self.prevClonePos - best_obj_pos).normalized()

                newDupMatrix2 = newDup.matrix_world
                newDupZAxisTuple2 = (
                    newDupMatrix2[0][2], newDupMatrix2[1][2], newDupMatrix2[2][2])
                newDupZAxis2 = (
                    Vector(newDupZAxisTuple2)).normalized()

                newDirRotVec2 = (newDirRotLookAtt.cross(best_obj_nor)).normalized().cross(
                    best_obj_nor).normalized()

                newDirRotAngle = newDirRotVec2.angle(newDupZAxis2)

                fixDirRotAngle = newDirRotLookAtt.cross(
                    best_obj_nor).angle(newDupZAxis2)

                if fixDirRotAngle < math.radians(90.0):
                    newDirRotAngle = - \
                        newDirRotAngle  # As we do it in negative axis

                # Main rotation
                bpy.ops.transform.rotate(value=newDirRotAngle, axis=(
                    (best_obj_nor.x, best_obj_nor.y, best_obj_nor.z)), proportional='DISABLED')

        # set PreviousClone position
        self.prevClonePos = best_obj_hit

        # Change Axis
        objMatrix = newDup.matrix_world
        #if mifthCloneTools.drawClonesDirectionRotate or mifthCloneTools.drawClonesRadialRotate:
        if mifthCloneTools.drawClonesAxis == 'Y':
            objFixAxisTuple = (
                objMatrix[0][2], objMatrix[1][2], objMatrix[2][2])
            bpy.ops.transform.rotate(value=math.radians(
                180), axis=(objFixAxisTuple), proportional='DISABLED')
        elif mifthCloneTools.drawClonesAxis == 'Z':
            objFixAxisTuple = (
                objMatrix[0][0], objMatrix[1][0], objMatrix[2][0])
            bpy.ops.transform.rotate(value=math.radians(
                90), axis=(objFixAxisTuple), proportional='DISABLED')
        elif mifthCloneTools.drawClonesAxis == '-Z':
            objFixAxisTuple = (
                objMatrix[0][0], objMatrix[1][0], objMatrix[2][0])
            bpy.ops.transform.rotate(
                value=math.radians(-90), axis=(objFixAxisTuple), proportional='DISABLED')
        elif mifthCloneTools.drawClonesAxis == 'X':
            objFixAxisTuple = (
                objMatrix[0][2], objMatrix[1][2], objMatrix[2][2])
            bpy.ops.transform.rotate(
                value=math.radians(-90), axis=(objFixAxisTuple), proportional='DISABLED')
        elif mifthCloneTools.drawClonesAxis == '-X':
            objFixAxisTuple = (
                objMatrix[0][2], objMatrix[1][2], objMatrix[2][2])
            bpy.ops.transform.rotate(value=math.radians(
                90), axis=(objFixAxisTuple), proportional='DISABLED')

        # Random rotation along Picked Normal
        if mifthCloneTools.randNormalRotateClone > 0.0:
            randNorAngle = random.uniform(
                math.radians(-mifthCloneTools.randNormalRotateClone), math.radians(mifthCloneTools.randNormalRotateClone))
            randNorAxis = (best_obj_nor.x, best_obj_nor.y, best_obj_nor.z)
            if mifthCloneTools.drawClonesRadialRotate is False and mifthCloneTools.drawClonesNormalRotate is False:
                randNorAxis = (0.0, 0.0, 1.0)
            bpy.ops.transform.rotate(
                value=randNorAngle, axis=(randNorAxis), proportional='DISABLED')

        # Random rotation along Picked Normal
        if mifthCloneTools.randDirectionRotateClone > 0.0:
            randDirX, randDirY, randDirZ = random.uniform(
                0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)
            randDirVec = (
                Vector((randDirX, randDirY, randDirZ))).normalized()
            randDirAngle = random.uniform(
                math.radians(-mifthCloneTools.randDirectionRotateClone), math.radians(mifthCloneTools.randDirectionRotateClone))
            bpy.ops.transform.rotate(
                value=randDirAngle, axis=(randDirVec), proportional='DISABLED')

        # change Size
        if mifthCloneTools.drawPressure > 0.0 or mifthCloneTools.randScaleClone > 0.0:
            newSize = newDup.scale
            if self.tabletPressure < 1.0 and mifthCloneTools.drawPressure > 0.0 and mifthCloneTools.drawPressureScale is True:
                newSize *= thePressure

            if mifthCloneTools.randScaleClone > 0.0:
                randScaleClone = 1.0 - \
                    (random.uniform(0.0, 0.99) *
                     mifthCloneTools.randScaleClone)
                newSize *= randScaleClone

        # Add this point with all its stuff
        self.currentStrokeList.append(
            MTFDCPoint(newDup, objToClone, best_obj_hit, best_obj_nor))

        # do optimization for a stroke or not
        if mifthCloneTools.drawClonesOptimize is False:
            copy_settings_clones(newDup, objToClone)

        newDup.select = False  # Clear Selection


class MFTCloneToSelected(bpy.types.Operator):
    bl_idname = "mft.clonetoselected"
    bl_label = "Clone To Selected"
    bl_description = "Clone To Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        if len(bpy.context.selected_objects) > 1:
            objToClone = bpy.context.scene.objects.active
            objectsToClone = []

            for obj in bpy.context.selected_objects:
                if obj != objToClone:
                    objectsToClone.append(obj)

            for obj in objectsToClone:
                bpy.ops.object.select_all(action='DESELECT')
                objToClone.select = True

                bpy.ops.object.duplicate(linked=True, mode='DUMMY')
                newDup = bpy.context.selected_objects[0]
                # print(newDup)
                newDup.location = obj.location
                newDup.rotation_euler = obj.rotation_euler
                newDup.scale = obj.scale

            bpy.ops.object.select_all(action='DESELECT')
            for obj3 in objectsToClone:
                obj3.select = True
            bpy.ops.object.delete(use_global=False)

            objectsToClone = None
        else:
            self.report({'INFO'}, "Need more Objects!")

        return {'FINISHED'}


class MFTRadialClone(bpy.types.Operator):
    bl_idname = "mft.radialclone"
    bl_label = "Radial Clone"
    bl_description = "Radial Clone"
    bl_options = {'REGISTER', 'UNDO'}

    radialClonesAngle = FloatProperty(
        default=360.0,
        min=-360.0,
        max=360.0
    )
    clonez = IntProperty(
        default=8,
        min=2,
        max=300
    )

    def execute(self, context):

        if len(bpy.context.selected_objects) > 0:
            activeObj = bpy.context.scene.objects.active
            selObjects = bpy.context.selected_objects
            mifthCloneTools = bpy.context.scene.mifthCloneTools
            # self.clonez = mifthCloneTools.radialClonesNumber

            activeObjMatrix = activeObj.matrix_world

            for i in range(self.clonez - 1):
                bpy.ops.object.duplicate(linked=True, mode='DUMMY')
                # newObj = bpy.context.selected_objects[0]
                # print(newObj)
                # for obj in bpy.context.selected_objects:
                theAxis = None

                if mifthCloneTools.radialClonesAxis == 'X':
                    if mifthCloneTools.radialClonesAxisType == 'Local':
                        theAxis = (
                            activeObjMatrix[0][0], activeObjMatrix[1][0], activeObjMatrix[2][0])
                    else:
                        theAxis = (1, 0, 0)

                elif mifthCloneTools.radialClonesAxis == 'Y':
                    if mifthCloneTools.radialClonesAxisType == 'Local':
                        theAxis = (
                            activeObjMatrix[0][1], activeObjMatrix[1][1], activeObjMatrix[2][1])
                    else:
                        theAxis = (0, 1, 0)

                elif mifthCloneTools.radialClonesAxis == 'Z':
                    if mifthCloneTools.radialClonesAxisType == 'Local':
                        theAxis = (
                            activeObjMatrix[0][2], activeObjMatrix[1][2], activeObjMatrix[2][2])
                    else:
                        theAxis = (0, 0, 1)

                rotateValue = (
                    math.radians(self.radialClonesAngle) / float(self.clonez))
                bpy.ops.transform.rotate(value=rotateValue, axis=theAxis)

            bpy.ops.object.select_all(action='DESELECT')

            for obj in selObjects:
                obj.select = True
            selObjects = None
            bpy.context.scene.objects.active = activeObj
        else:
            self.report({'INFO'}, "Select Objects!")

        return {'FINISHED'}


class MFTGroupInstance(bpy.types.Operator):
    bl_idname = "mft.group_instance_to_cursor"
    bl_label = "Set GroupInstance to Cursor"
    bl_description = "Set GroupInstance to Cursor..."
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        scene = bpy.context.scene
        mifthCloneTools = scene.mifthCloneTools

        obj_group = bpy.data.groups.get(mifthCloneTools.getGroupsLst)
        if obj_group is not None:
            obj_group.dupli_offset[
                0] = bpy.context.space_data.cursor_location[0]
            obj_group.dupli_offset[
                1] = bpy.context.space_data.cursor_location[1]
            obj_group.dupli_offset[
                2] = bpy.context.space_data.cursor_location[2]

        return {'FINISHED'}
