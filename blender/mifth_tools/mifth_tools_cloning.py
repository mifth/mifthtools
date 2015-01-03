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

bpy.mifthTools = dict()

global drawForClonesObj
drawForClonesObj = []  # Array of Objects Names


class MFTDrawClones(bpy.types.Operator):
    bl_idname = "mft.draw_clones"
    bl_label = "Draw Clones"
    bl_description = "Draw Clones with Mouse"
    bl_options = {'REGISTER', 'UNDO'}

    prevClonePos = None  # PreviousClone position
    doPick = False
    tabletPressure = 1.0

    def modal(self, context, event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            # allow navigation
            return {'PASS_THROUGH'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            return {'FINISHED'}
        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.doPick = True
        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.doPick = False
            self.prevClonePos = None

        if self.doPick is True:
                mft_pick_and_clone(self, context, event)
                self.tabletPressure = event.pressure

        return {'RUNNING_MODAL'}


    def invoke(self, context, event):
        mifthTools = bpy.context.scene.mifthTools
        #global drawForClonesObj
        if len(drawForClonesObj) == 0 or len(context.selected_objects) == 0:
            self.report({'WARNING'}, "Pick Objects to Clone")
            return {'CANCELLED'}

        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
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
        mifthTools = context.scene.mifthTools

        if len(context.selected_objects) > 0:
            #global drawForClonesObj
            drawForClonesObj.clear()
            for obj in context.selected_objects:
                drawForClonesObj.append(obj.name)

        return {'FINISHED'}


def mft_pick_and_clone(self, context, event, ray_max=1000.0):
    """Run this function on left mouse, execute the ray cast"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y


    def mft_selected_objects_and_duplis():
        """Loop over (object, matrix) pairs (mesh only)"""

        for obj in context.selected_objects:
            if obj.type == 'MESH':
                yield (obj, obj.matrix_world.copy())

            if obj.dupli_type != 'NONE':
                obj.dupli_list_create(scene)
                for dob in obj.dupli_list:
                    obj_dupli = dob.object
                    if obj_dupli.type == 'MESH':
                        yield (obj_dupli, dob.matrix.copy())

            obj.dupli_list_clear()


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

    mifthTools = bpy.context.scene.mifthTools

    for obj, matrix in mft_selected_objects_and_duplis():
        if obj.type == 'MESH':

            # get the ray from the viewport and mouse
            view_vector_mouse = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
            ray_origin_mouse = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

            # Random Vec
            if mifthTools.drawRandomStrokeLength > 0.0:
                randX_mouse = random.uniform(-10.0, 10.0)
                randY_mouse = random.uniform(-10.0, 10.0)
                coordRandAdd =  (coord[0] + randX_mouse, coord[1] + randY_mouse)
                ray_origin_rand = view3d_utils.region_2d_to_origin_3d(region, rv3d, coordRandAdd)
                view_vector_rand = view3d_utils.region_2d_to_vector_3d(region, rv3d, coordRandAdd)
                ray_origin_rand_vec = (ray_origin_rand - ray_origin_mouse).normalized() * random.uniform(0.0, mifthTools.drawRandomStrokeLength)
                ray_origin_rand = ray_origin_mouse + ray_origin_rand_vec

            if rv3d.view_perspective != 'PERSP':
                # move ortho origin back
                ray_origin_mouse = ray_origin_mouse - (view_vector_mouse * (ray_max / 2.0))
                if mifthTools.drawRandomStrokeLength > 0.0:
                    ray_origin_rand = ray_origin_rand - (view_vector_rand * (ray_max / 2.0))

            # Do RayCast! t1,t2,t3,t4 - temp values
            t1,t2,t3 = mft_obj_ray_cast(obj, matrix, view_vector_mouse, ray_origin_mouse)
            if t1 is not None and t3 < best_length_squared:
                best_obj = obj
                best_obj_nor, best_obj_pos, best_length_squared = t1,t2,t3
                best_obj_hit = best_obj_pos

            # Check for stroke length
            if best_obj is not None:
                if self.prevClonePos is not None and (best_obj_pos - self.prevClonePos).length <= mifthTools.drawStrokeLength:
                    best_obj = None  # Don't do cloning

            # random scatter things
            if mifthTools.drawRandomStrokeLength > 0.0 and best_obj is not None:
                t1,t2,t3 = mft_obj_ray_cast(obj, matrix, view_vector_rand, ray_origin_rand)
                if t1 is not None:
                    best_obj_nor, best_obj_pos = t1,t2

    # now we have the object under the mouse cursor,
    if best_obj is not None:
        selected_Obj_True = context.selected_objects
        obj_Active_True = context.scene.objects.active
        bpy.ops.object.select_all(action='DESELECT')

        objToClone = bpy.data.objects.get(random.choice(drawForClonesObj))
        objToClone.select = True
        context.scene.objects.active = objToClone

        bpy.ops.object.duplicate(linked=True, mode='DUMMY')
        newDup = bpy.context.selected_objects[0]
        newDup.location = best_obj_pos
        bpy.ops.object.rotation_clear()


        xyNor = best_obj_nor.copy()
        xyNor.z = 0.0

        if xyNor.length == 0:
            rotatePlaneAngle = math.radians(90.0)
            if best_obj_nor.z > 0:
                bpy.ops.transform.rotate(value=-rotatePlaneAngle, axis=(1.0, 0.0, 0.0), proportional='DISABLED')
            else:
                bpy.ops.transform.rotate(value=rotatePlaneAngle, axis=(1.0, 0.0, 0.0), proportional='DISABLED')
        else:
            xyNor = xyNor.normalized()

            if mifthTools.drawClonesRadialRotate is True:
                #xyRot = ((best_obj_pos.copy() + xyNor) - best_obj_pos.copy()).normalized()
                xyAngleRotate = mathutils.Vector((0.0, -1.0, 0.0)).angle(xyNor)

                if xyNor.x < 0:
                    xyAngleRotate = -xyAngleRotate
                xyRotateAxis = mathutils.Vector((0.0, 0.0, 1.0))
                bpy.ops.transform.rotate(value=xyAngleRotate, axis=(0.0, 0.0, 1.0), proportional='DISABLED')

            if mifthTools.drawClonesNormalRotate is True:
                # Other rotate
                
                xRotateAxis = xyNor.cross(best_obj_nor).normalized()
                angleRotate = xyNor.angle(best_obj_nor)
                
                if mifthTools.drawClonesRadialRotate is False:
                    newDupMatrix = newDup.matrix_world

                    newDupYAxisTuple = (newDupMatrix[0][1], newDupMatrix[1][1], newDupMatrix[2][1])
                    newDupYAxis = mathutils.Vector(newDupYAxisTuple).normalized()
                    newDupYAxis.negate()

                    xRotateAxis = newDupYAxis.cross(best_obj_nor).normalized()
                    angleRotate = newDupYAxis.angle(best_obj_nor)

                bpy.ops.transform.rotate(value=angleRotate, axis=( (xRotateAxis.x, xRotateAxis.y, xRotateAxis.z) ), proportional='DISABLED')

        # Ratate to Direction
        #global prevClonePos
        if mifthTools.drawClonesDirectionRotate is True and self.prevClonePos is not None:
            newDirRotLookAtt = (self.prevClonePos - best_obj_pos).normalized()

            newDupMatrix2 = newDup.matrix_world
            newDupZAxisTuple2 = (newDupMatrix2[0][2], newDupMatrix2[1][2], newDupMatrix2[2][2])
            newDupZAxis2 = (mathutils.Vector(newDupZAxisTuple2)).normalized()

            newDirRotVec2 = ( newDirRotLookAtt.cross(best_obj_nor) ).normalized().cross(best_obj_nor).normalized()

            newDirRotAngle = newDirRotVec2.angle(newDupZAxis2)

            fixDirRotAngle = newDirRotLookAtt.cross(best_obj_nor).angle(newDupZAxis2)

            if fixDirRotAngle < math.radians(90.0):
                newDirRotAngle = -newDirRotAngle # As we do it in negative axis

            # Main rotation
            bpy.ops.transform.rotate(value= newDirRotAngle, axis=( (best_obj_nor.x, best_obj_nor.y, best_obj_nor.z) ), proportional='DISABLED')

        # set PreviousClone position
        self.prevClonePos = best_obj_hit

        # Change Axis
        objMatrix = newDup.matrix_world
        if mifthTools.drawClonesDirectionRotate or mifthTools.drawClonesRadialRotate:
            if mifthTools.drawClonesAxis == 'Y':
                objFixAxisTuple = (objMatrix[0][2], objMatrix[1][2], objMatrix[2][2])
                bpy.ops.transform.rotate(value= math.radians(180), axis=( objFixAxisTuple ), proportional='DISABLED')
            elif mifthTools.drawClonesAxis == 'Z':
                objFixAxisTuple = (objMatrix[0][0], objMatrix[1][0], objMatrix[2][0])
                bpy.ops.transform.rotate(value= math.radians(90), axis=( objFixAxisTuple ), proportional='DISABLED')
            elif mifthTools.drawClonesAxis == '-Z':
                objFixAxisTuple = (objMatrix[0][0], objMatrix[1][0], objMatrix[2][0])
                bpy.ops.transform.rotate(value= math.radians(-90), axis=( objFixAxisTuple ), proportional='DISABLED')
            elif mifthTools.drawClonesAxis == 'X':
                objFixAxisTuple = (objMatrix[0][2], objMatrix[1][2], objMatrix[2][2])
                bpy.ops.transform.rotate(value= math.radians(-90), axis=( objFixAxisTuple ), proportional='DISABLED')
            elif mifthTools.drawClonesAxis == '-X':
                objFixAxisTuple = (objMatrix[0][2], objMatrix[1][2], objMatrix[2][2])
                bpy.ops.transform.rotate(value= math.radians(90), axis=( objFixAxisTuple ), proportional='DISABLED')

        # Random rotation along Picked Normal
        if mifthTools.randNormalRotateClone > 0.0:
            randNorAngle = random.uniform(math.radians(-mifthTools.randNormalRotateClone), math.radians(mifthTools.randNormalRotateClone))
            randNorAxis = (best_obj_nor.x, best_obj_nor.y, best_obj_nor.z)
            if mifthTools.drawClonesRadialRotate is False and mifthTools.drawClonesNormalRotate is False:
                randNorAxis = (0.0, 0.0, 1.0)
            bpy.ops.transform.rotate(value=randNorAngle, axis=( randNorAxis ), proportional='DISABLED')

        # Random rotation along Picked Normal
        if mifthTools.randDirectionRotateClone > 0.0:
            randDirX, randDirY, randDirZ = random.uniform(0.0, 1.0), random.uniform(0.0, 1.0), random.uniform(0.0, 1.0)
            randDirVec = (mathutils.Vector((randDirX, randDirY, randDirZ))).normalized()
            randDirAngle = random.uniform(math.radians(-mifthTools.randDirectionRotateClone), math.radians(mifthTools.randDirectionRotateClone))
            bpy.ops.transform.rotate(value=randDirAngle, axis=( randDirVec ), proportional='DISABLED')

        # Pressure sensetivity for scale
        if self.tabletPressure < 1.0:
            thePressure = max(1.0 - mifthTools.drawPressure, self.tabletPressure)
            bpy.ops.transform.resize(value=(thePressure, thePressure, thePressure), constraint_axis=(False, False, False), constraint_orientation='GLOBAL')

        # Random Scale
        if mifthTools.randScaleClone > 0.0:
            randScaleClone = 1.0 - (random.uniform(0.0, 0.99) * mifthTools.randScaleClone)
            bpy.ops.transform.resize(value=(randScaleClone, randScaleClone, randScaleClone), constraint_axis=(False, False, False), constraint_orientation='GLOBAL')

        bpy.ops.object.select_all(action='DESELECT')

        for obj in selected_Obj_True:
            obj.select = True
        context.scene.objects.active = obj_Active_True

        #best_obj.select = True
        #context.scene.objects.active = best_obj


def register():
    bpy.utils.register_module(__name__)


def unregister():
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
