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

from math import isclose
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

# bpy.mifthCloneTools = dict()

global drawForClonesObj
drawForClonesObj = []  # Array of Objects Names


# Math to convert vector into Rotation Matrix 3x3. Taken from Animation Nodes project.
def create_z_orient(rot_vec):
    x_dir_p = Vector(( 1.0,  0.0,  0.0))
    y_dir_p = Vector(( 0.0,  1.0,  0.0))
    z_dir_p = Vector(( 0.0,  0.0,  1.0))
    tol = 0.001
    rx, ry, rz = rot_vec
    if isclose(rx, 0.0, abs_tol=tol) and isclose(ry, 0.0, abs_tol=tol):
        if isclose(rz, 0.0, abs_tol=tol) or isclose(rz, 1.0, abs_tol=tol):
            return Matrix((x_dir_p, y_dir_p, z_dir_p))  # 3x3 identity
    new_z = rot_vec.copy()  # rot_vec already normalized
    new_y = new_z.cross(z_dir_p)
    new_y_eq_0_0_0 = True
    for v in new_y:
        if not isclose(v, 0.0, abs_tol=tol):
            new_y_eq_0_0_0 = False
            break
    if new_y_eq_0_0_0:
        new_y = y_dir_p
    new_x = new_y.cross(new_z)
    new_x.normalize()
    new_y.normalize()
    return Matrix(((new_x.x, new_y.x, new_z.x),
                   (new_x.y, new_y.y, new_z.y),
                   (new_x.z, new_y.z, new_z.z)))


# groups
def getGroups(scene, context):

    lst = []
    obj = context.active_object
    for group in bpy.data.collections:
        if obj is not None and obj.name in group.objects:
            lst.append((group.name, group.name, ""))

    return lst


class MFTCloneProperties(bpy.types.PropertyGroup):
    # Draw Cloned Settings
    drawClonesDirectionRotate : BoolProperty(
        name="drawClonesDirectionRotate",
        description="drawClonesDirectionRotate...",
        default=False
    )

    drawClonesRadialRotate : BoolProperty(
        name="drawClonesRadialRotate",
        description="drawClonesRadialRotate...",
        default=True
    )

    drawClonesNormalRotate : BoolProperty(
        name="drawClonesNormalRotate",
        description="drawClonesNormalRotate...",
        default=True
    )

    drawClonesOffsetNomalBefore: FloatProperty(
        default=0.0
    )

    drawClonesRotateNomalAfter: FloatProperty(
        default=0.0,
        min=-360,
        max=360
    )

    drawStrokeLength : FloatProperty(
        default=0.5,
        min=0.001,
        max=500.0
    )

    drawRandomStrokeScatter : FloatProperty(
        default=0.0,
        min=0.0,
        max=500.0
    )

    randNormalRotateClone : FloatProperty(
        default=0.0,
        min=0.0,
        max=180.0
    )

    randDirectionRotateClone : FloatProperty(
        default=0.0,
        min=0.0,
        max=180.0
    )

    randScaleClone : FloatProperty(
        default=0.0,
        min=0.0,
        max=0.99
    )

    drawPressure : FloatProperty(
        default=0.7,
        min=0.0,
        max=0.95
    )

    drawPressureRelativeStroke : BoolProperty(
        name="drawPressureRelativeStroke",
        description="Relative Stroke To Scale and Pressure",
        default=True
    )

    drawPressureScale : BoolProperty(
        name="drawPressureScale",
        description="Pressure for Scale",
        default=True
    )

    drawPressureScatter : BoolProperty(
        name="drawPressureScatter",
        description="Pressure for Scatter",
        default=True
    )

    drawClonesAxis : EnumProperty(
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
    radialClonesAxis : EnumProperty(
        items=(('X', 'X', ''),
               ('Y', 'Y', ''),
               ('Z', 'Z', '')
               ),
        default = 'Z'
    )

    radialClonesAxisType : EnumProperty(
        items=(('Global', 'Global', ''),
               ('Local', 'Local', '')
               ),
        default = 'Global'
    )

    # GroupInstance to Cursor
    getGroupsLst : EnumProperty(name='Get Groups',
                                description='Get Groups.',
                                items=getGroups)


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

    pass_keys = ['NUMPAD_0', 'NUMPAD_1', 'NUMPAD_3', 'NUMPAD_4',
                 'NUMPAD_5', 'NUMPAD_6', 'NUMPAD_7', 'NUMPAD_8',
                 'NUMPAD_9', 'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE']

    def modal(self, context, event):
        mifthCloneTools = bpy.context.scene.mifthCloneTools
        if event.type in self.pass_keys:
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

            ## Do optimization
            #if mifthCloneTools.drawClonesOptimize is True and self.currentStrokeList is not None:
                #for point in self.currentStrokeList:
                    #copy_settings_clones(point.objNew, point.objOriginal)
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

        for obj_name in drawForClonesObj:
            if obj_name not in context.scene.objects:
                self.report({'WARNING'}, "Picked Object was Deleted!")
                return {'CANCELLED'}
                break

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
        obj.select_set(False)
    self.obj_Active_True = context.active_object

    self.dupliList = mft_selected_objects_and_duplis(self, context)
    self.allStrokesList = []


# Just clear some stuff at the end
def finish_drawing(self, context):
    for obj in self.drawOnObjects:
        obj.select_set(True)
    context.view_layer.objects.active = self.obj_Active_True
    self.drawOnObjects = None
    self.dupliList = None

    if self.allStrokesList is not None:
        for stroke in self.allStrokesList:
            if stroke is not None:
                stroke.clear()
        self.allStrokesList.clear()
    self.allStrokesList = None

    if self.currentStrokeList is not None:
        self.currentStrokeList.clear()
    self.currentStrokeList = None


def mft_selected_objects_and_duplis(self, context):
    """Loop over (object, matrix) pairs (mesh only)"""

    listObjMatrix = []
    depsgraph = context.evaluated_depsgraph_get()

    for obj in self.drawOnObjects:
        if obj.type == 'MESH':
            #BVHTree.FromObject(obj, depsgraph)  # Update BVHTree (FIX)
            listObjMatrix.append((obj, obj.matrix_world.copy()))

        # convert particles and dupligroups
        for dup in depsgraph.object_instances:
            if dup.is_instance:  # Real dupli instance
                obj_dupli = dup.instance_object
                listObjMatrix.append( (obj_dupli, dup.matrix_world.copy()) )

    return listObjMatrix


#def copy_settings_clones(newObj, oldObj):
    ## Copy Groups
    #for thisGroup in bpy.data.groups:
        #if oldObj.name in thisGroup.objects:
            #thisGroup.objects.link(newObj)

    ## Copy Modifiers
    #for old_modifier in oldObj.modifiers.values():
            #new_modifier = newObj.modifiers.new(name=old_modifier.name,
                                                #type=old_modifier.type)

    ## copy duplis
    #if oldObj.dupli_group is not None:
        #newObj.dupli_type = oldObj.dupli_type
        #newObj.dupli_group = oldObj.dupli_group

    ## copy custom settings of the old object
    #for prop in oldObj.keys():
        #newObj[prop] = oldObj[prop]


def get_obj_axis(obj, axis):
    ax = 0
    if axis == 'Y' or axis == '-Y':
        ax = 1
    if axis == 'Z' or axis == '-Z':
        ax = 2

    obj_matrix = obj.matrix_world
    axis_tuple = (
        obj_matrix[0][ax], obj_matrix[1][ax], obj_matrix[2][ax])
    axisResult = Vector(axis_tuple).normalized()

    if axis == '-X' or axis == '-Y' or axis == '-Z':
        axisResult.negate()

    return axisResult


def mft_pick_and_clone(self, context, event, ray_max=10000.0):
    """Run this function on left mouse, execute the ray cast"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    def mft_obj_ray_cast(obj, matrix, view_vector, ray_origin):
        """Wrapper for ray casting that moves the ray into object space"""

        # get the ray relative to the object
        matrix_inv = matrix.inverted()
        ray_target = ray_origin + (view_vector * ray_max)

        ray_origin_obj = matrix_inv @ ray_origin
        ray_target_obj = matrix_inv @ ray_target
        ray_direction_obj = ray_target_obj - ray_origin_obj

        # cast the ray
        hit_result, hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_direction_obj, distance=ray_max)

        if hit_result:
            hit_world = matrix @ hit

            length_squared = (hit_world - ray_origin).length_squared

            if face_index != -1:
                #normal_world = (matrix.to_quaternion() * normal).normalized()

                normal_world = (matrix.to_quaternion() @ normal).to_4d()
                normal_world.w = 0
                normal_world = (matrix.to_quaternion() @ (matrix_inv @ normal_world).to_3d()).normalized()

                return normal_world, hit_world, length_squared

        return None, None, None

    # cast rays and find the closest object
    best_length_squared = ray_max * ray_max
    best_obj, best_obj_nor, best_obj_pos = None, None, None
    best_obj_rand, best_obj_nor_rand, best_obj_pos_rand = None, None, None
    best_obj_hit = None

    mifthCloneTools = bpy.context.scene.mifthCloneTools
    thePressure = max(1.0 - mifthCloneTools.drawPressure,
                      self.tabletPressure)  # The pressure of a pen!

    for obj, matrix in self.dupliList:
        # get the ray from the viewport and mouse
        view_vector_mouse = view3d_utils.region_2d_to_vector_3d(
            region, rv3d, coord)
        ray_origin_mouse = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, coord)

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

            t1, t2, t3 = mft_obj_ray_cast(
                obj, matrix, view_vector_rand, ray_origin_rand)
            # 3.0 is random addition
            if t1 is not None and (t2 - best_obj_hit).length <= mifthCloneTools.drawRandomStrokeScatter * 3.0:
                best_obj_nor, best_obj_pos = t1, t2

    # now we have the object under the mouse cursor,
    if best_obj is not None:
        objToClone = bpy.data.objects.get(random.choice(drawForClonesObj))
        best_obj_nor = best_obj_nor.normalized()

        # clone object
        #newDup = bpy.data.objects.new(objToClone.name, objToClone.data)
        bpy.ops.object.select_all(action='DESELECT')
        objToClone.select_set(True)

        bpy.ops.object.duplicate(linked=True, mode='DUMMY')
        newDup = context.selected_objects[0]
        context.view_layer.objects.active = newDup

        # Set New Location
        newDup.location = best_obj_pos

        if mifthCloneTools.drawClonesOffsetNomalBefore != 0.0:
            newDup.location += best_obj_nor * mifthCloneTools.drawClonesOffsetNomalBefore

        # Rotation To Normal
        if mifthCloneTools.drawClonesNormalRotate is True:
            # rotate To Normal
            newDupZAxis = get_obj_axis(newDup, 'Z')
            angleRotate = newDupZAxis.angle(best_obj_nor)
            rotateAxis = newDupZAxis.cross(best_obj_nor).normalized()

            bpy.ops.transform.rotate(value=-angleRotate, orient_matrix=create_z_orient(rotateAxis))

        # Change Axis
        if mifthCloneTools.drawClonesAxis == 'Y':
            bpy.ops.transform.rotate(value=math.radians(-90), orient_matrix=create_z_orient(get_obj_axis(newDup, 'X')))
            bpy.ops.transform.rotate(value=math.radians(180), orient_matrix=create_z_orient(get_obj_axis(newDup, 'Y')))
        elif mifthCloneTools.drawClonesAxis == '-Y':
            bpy.ops.transform.rotate(value=math.radians(90), orient_matrix=create_z_orient(get_obj_axis(newDup, 'X')))
            # bpy.ops.transform.rotate(value=math.radians(180), orient_matrix=create_z_orient(get_obj_axis(newDup, 'Y')))
        elif mifthCloneTools.drawClonesAxis == '-Z':
            # bpy.ops.transform.rotate(value=math.radians(180), orient_matrix=create_z_orient(get_obj_axis(newDup, 'X')))
            bpy.ops.transform.rotate(value=math.radians(180), orient_matrix=create_z_orient(get_obj_axis(newDup, 'Y')))
        elif mifthCloneTools.drawClonesAxis == 'X':
            bpy.ops.transform.rotate(value=math.radians(90), orient_matrix=create_z_orient(get_obj_axis(newDup, 'Y')))
            # bpy.ops.transform.rotate(value=math.radians(180), orient_matrix=create_z_orient(get_obj_axis(newDup, 'X')))
        elif mifthCloneTools.drawClonesAxis == '-X':
            bpy.ops.transform.rotate(value=math.radians(-90), orient_matrix=create_z_orient(get_obj_axis(newDup, 'Y')))

        # Other rotate
        if mifthCloneTools.drawClonesRadialRotate is True or mifthCloneTools.drawClonesDirectionRotate is True:

            # Ratate to Direction
            newDirRotLookAtt = None
            if mifthCloneTools.drawClonesDirectionRotate is True:
                previousHit = None
                if len(self.currentStrokeList) > 0:
                    previousHit = self.currentStrokeList[
                        -1]  # get Last Element
                else:
                    if len(self.allStrokesList) > 0:
                        previousHit = self.allStrokesList[-1][
                            -1]  # get Last Element of previous Stroke

                if previousHit is not None:
                    newDirRotLookAtt = (
                        best_obj_hit - previousHit.hitPoint).normalized()
            else:
                newDirRotLookAtt = Vector((0.0, 0.0, 1.0))

            # Get the axis to rotate
            if newDirRotLookAtt is not None:
                tempYCross = best_obj_nor.cross(newDirRotLookAtt).normalized()
                if tempYCross != Vector((0.0, 0.0, 0.0)):
                    tempYCross.negate()
                    radialVec = best_obj_nor.cross(tempYCross).normalized()

                    axisPickTemp = 'Y'
                    if mifthCloneTools.drawClonesAxis == 'Y':
                        axisPickTemp = 'Z'
                    if mifthCloneTools.drawClonesAxis == '-Y':
                        axisPickTemp = 'Z'
                    if mifthCloneTools.drawClonesAxis == '-Z':
                        axisPickTemp = 'Y'
                    if mifthCloneTools.drawClonesAxis == 'X':
                        axisPickTemp = 'Z'
                    if mifthCloneTools.drawClonesAxis == '-X':
                        axisPickTemp = 'Z'

                    tempY = get_obj_axis(newDup, axisPickTemp)
                    xyAngleRotate = Vector(radialVec).angle(tempY)

                    if tempYCross.angle(tempY) > math.radians(90.0):
                        xyAngleRotate = -xyAngleRotate

                    bpy.ops.transform.rotate(value=-xyAngleRotate, orient_matrix=create_z_orient(best_obj_nor))

        if mifthCloneTools.randNormalRotateClone > 0.0:
            randNorAngle = random.uniform(
                math.radians(-mifthCloneTools.randNormalRotateClone), math.radians(mifthCloneTools.randNormalRotateClone))
            randNorAxis = (best_obj_nor.x, best_obj_nor.y, best_obj_nor.z)
            if mifthCloneTools.drawClonesRadialRotate is False and mifthCloneTools.drawClonesNormalRotate is False:
                randNorAxis = (0.0, 0.0, 1.0)
            bpy.ops.transform.rotate(value=-randNorAngle, orient_matrix=create_z_orient(Vector(randNorAxis)))

        # Random rotation along Picked Normal
        if mifthCloneTools.randDirectionRotateClone > 0.0:
            randDirX, randDirY, randDirZ = random.uniform(
                0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)
            randDirVec = (Vector((randDirX, randDirY, randDirZ))).normalized()
            randDirAngle = random.uniform(math.radians(-mifthCloneTools.randDirectionRotateClone), math.radians(mifthCloneTools.randDirectionRotateClone))
            bpy.ops.transform.rotate(value=-randDirAngle, orient_matrix=create_z_orient(randDirVec))

        # Rotate Along Axis
        if mifthCloneTools.drawClonesRotateNomalAfter != 0.0:
            bpy.ops.transform.rotate(value=math.radians(mifthCloneTools.drawClonesRotateNomalAfter),
                                     orient_matrix=create_z_orient(best_obj_nor))

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

        newDup.select_set(False)  # Clear Selection


class MFTCloneToSelected(bpy.types.Operator):
    bl_idname = "mft.clonetoselected"
    bl_label = "Clone To Selected"
    bl_description = "Clone To Selected"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        if len(bpy.context.selected_objects) > 1:
            objToClone = context.active_object
            objectsToClone = []

            for obj in bpy.context.selected_objects:
                if obj != objToClone:
                    objectsToClone.append(obj.name)

            for name in objectsToClone:
                obj = context.scene.objects[name]
                bpy.ops.object.select_all(action='DESELECT')
                objToClone.select_set(True)

                bpy.ops.object.duplicate(linked=True, mode='DUMMY')
                newDup = bpy.context.selected_objects[0]
                # print(newDup)
                newDup.location = obj.location
                newDup.rotation_euler = obj.rotation_euler
                newDup.scale = obj.scale

            bpy.ops.object.select_all(action='DESELECT')
            for name in objectsToClone:
                context.scene.objects[name].select_set(True)
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

    create_last_clone : BoolProperty(
        name="Create Last Clone",
        description="create last clone...",
        default=False
    )

    radialClonesAngle : FloatProperty(
        default=360.0,
        min=-360.0,
        max=360.0
    )
    clonez : IntProperty(
        default=8,
        min=2,
        max=300
    )

    def execute(self, context):

        if len(bpy.context.selected_objects) > 0:
            activeObj = context.active_object
            selObjects = bpy.context.selected_objects
            mifthCloneTools = bpy.context.scene.mifthCloneTools
            # self.clonez = mifthCloneTools.radialClonesNumber

            activeObjMatrix = activeObj.matrix_world

            clones_count = self.clonez
            if self.create_last_clone is False:
                clones_count = self.clonez - 1

            for i in range(clones_count):
                bpy.ops.object.duplicate(linked=True, mode='DUMMY')
                # newObj = bpy.context.selected_objects[0]
                # print(newObj)
                # for obj in bpy.context.selected_objects:
                theAxis = None

                if mifthCloneTools.radialClonesAxis == 'X':
                    if mifthCloneTools.radialClonesAxisType == 'Local':
                        theAxis = (activeObjMatrix[0][0], activeObjMatrix[1][0], activeObjMatrix[2][0])
                    else:
                        theAxis = (1, 0, 0)

                elif mifthCloneTools.radialClonesAxis == 'Y':
                    if mifthCloneTools.radialClonesAxisType == 'Local':
                        theAxis = (activeObjMatrix[0][1], activeObjMatrix[1][1], activeObjMatrix[2][1])
                    else:
                        theAxis = (0, 1, 0)

                elif mifthCloneTools.radialClonesAxis == 'Z':
                    if mifthCloneTools.radialClonesAxisType == 'Local':
                        theAxis = (activeObjMatrix[0][2], activeObjMatrix[1][2], activeObjMatrix[2][2])
                    else:
                        theAxis = (0, 0, 1)

                rotateValue = (math.radians(self.radialClonesAngle) / float(self.clonez))
                bpy.ops.transform.rotate(value=rotateValue, orient_matrix=create_z_orient(Vector(theAxis)))

            bpy.ops.object.select_all(action='DESELECT')

            for obj in selObjects:
                obj.select_set(True)
            selObjects = None
            context.view_layer.objects.active = activeObj
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

        obj_group = bpy.data.collections.get(mifthCloneTools.getGroupsLst)
        if obj_group is not None:
            obj_group.dupli_offset[
                0] = bpy.context.space_data.cursor_location[0]
            obj_group.dupli_offset[
                1] = bpy.context.space_data.cursor_location[1]
            obj_group.dupli_offset[
                2] = bpy.context.space_data.cursor_location[2]

        return {'FINISHED'}


class MFTGroupToMesh(bpy.types.Operator):
    bl_idname = "mft.group_to_mesh"
    bl_label = "Convert Group Instance to Mesh"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):

        bpy.ops.object.duplicates_make_real()
        bpy.ops.object.make_single_user(object=True, obdata=True)

        objs = context.selected_objects
        objs_names = [i.name for i in objs]

        for name in objs_names:
            obj = context.scene.objects[name]

            if obj.type == 'EMPTY':
                bpy.data.objects.remove(bpy.data.objects[name], True)

            elif obj.type == 'MESH':
                if obj.scale[0] < 0 or obj.scale[1] < 0 or obj.scale[2] < 0:
                    for face in obj.data.polygons:
                        face.select = True

                    context.view_layer.objects.active = obj
                    bpy.ops.object.mode_set(mode = 'EDIT')
                    bpy.ops.mesh.flip_normals()
                    bpy.ops.object.mode_set(mode = 'OBJECT')

        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

        return {'FINISHED'}
