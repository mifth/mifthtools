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
#
# Inspired and many parts from mifth tools cloning 

bl_info = {
    "name": "Paint Clones",
    "author": "Stephen Leger",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D Viewport",
    "description": "Paint Clones, inspired and many parts from mifth tools cloning",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Tools"}

import bpy
from bpy_extras import view3d_utils

#import math
from math import pi
import random
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import EnumProperty, BoolProperty, FloatProperty, PointerProperty
from mathutils import Vector, Matrix

# bpy.paintClonesTools = dict()

global paintClonesSourceList
paintClonesSourceList = []  # Array of Objects Names
           
track_list ={
    'TRACK_NEGATIVE_X':3,
    'TRACK_NEGATIVE_Y':4,
    'TRACK_NEGATIVE_Z':5,
    'TRACK_POSITIVE_X':0,
    'TRACK_POSITIVE_Y':1,
    'TRACK_POSITIVE_Z':2
}
up_list ={
    'UP_X':0,
    'UP_Y':1,
    'UP_Z':2
}
cross_list={
  -2:1,
  -1:-1,
  0:0,
  1:1,
  2:-1
}

def mul_m4_m3m4(m, _m3, _m4):
    m2 = _m4.copy()
    m3 = _m3.copy()
    m[0][0] = m2[0][0] * m3[0][0] + m2[0][1] * m3[1][0] + m2[0][2] * m3[2][0]
    m[0][1] = m2[0][0] * m3[0][1] + m2[0][1] * m3[1][1] + m2[0][2] * m3[2][1]
    m[0][2] = m2[0][0] * m3[0][2] + m2[0][1] * m3[1][2] + m2[0][2] * m3[2][2]
    m[1][0] = m2[1][0] * m3[0][0] + m2[1][1] * m3[1][0] + m2[1][2] * m3[2][0]
    m[1][1] = m2[1][0] * m3[0][1] + m2[1][1] * m3[1][1] + m2[1][2] * m3[2][1]
    m[1][2] = m2[1][0] * m3[0][2] + m2[1][1] * m3[1][2] + m2[1][2] * m3[2][2]
    m[2][0] = m2[2][0] * m3[0][0] + m2[2][1] * m3[1][0] + m2[2][2] * m3[2][0]
    m[2][1] = m2[2][0] * m3[0][1] + m2[2][1] * m3[1][1] + m2[2][2] * m3[2][1]
    m[2][2] = m2[2][0] * m3[0][2] + m2[2][1] * m3[1][2] + m2[2][2] * m3[2][2]
    return m
  
def mat4_to_size(m):
    size_0 = m[0].to_3d().length
    size_1 = m[1].to_3d().length
    size_2 = m[2].to_3d().length    
    m[0][0] = size_0 
    m[0][1] = 0
    m[0][2] = 0   
    m[1][0] = 0
    m[1][1] = size_1
    m[1][2] = 0
    m[2][0] = 0
    m[2][1] = 0
    m[2][2] = size_2 
    return m
    
def dot_v3v3(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]

def project_v3_v3v3(v1, v2):
    c = Vector()
    mul = dot_v3v3(v1, v2) / dot_v3v3(v2, v2)
    c[0] = mul * v2[0]
    c[1] = mul * v2[1]
    c[2] = mul * v2[2]    
    return c
    
def vectomat(track_vec, up_vec, track_axis, up_axis):
    m = Matrix()
    n = track_vec.normalized()
    n.resize_3d() 
    u = up_vec.copy()
    u.resize_3d()
    if n[0] != n[0]:
        n[0] = 0.0
        n[1] = 0.0
        n[2] = 1.0
    if track_axis > 2:
        track_axis = track_axis-3
        n = -n
        
    proj = project_v3_v3v3(u,n)    
    proj = u-proj
    proj.normalize()
    if proj[0] != proj[0]:
        proj[0] = 0.0
        proj[1] = 1.0
        proj[2] = 0.0
    right = proj.cross(n)
    right.normalize()
    if track_axis != up_axis:
        right_index = 3-track_axis-up_axis
        neg = cross_list[track_axis-up_axis]
        m[right_index][0] = neg*right[0]
        m[right_index][1] = neg*right[1]
        m[right_index][2] = neg*right[2]
        m[up_axis][0] = proj[0]
        m[up_axis][1] = proj[1]
        m[up_axis][2] = proj[2]
        m[track_axis][0] = n[0]
        m[track_axis][1] = n[1]
        m[track_axis][2] = n[2]
    return m
    
def get_rot_quat(obj, track_vec, up_vec, track_axis, up_axis):
    cob = obj.matrix_world.transposed()
    cob = mat4_to_size(cob)
    m = vectomat(track_vec, up_vec, track_axis, up_axis)
    cob = mul_m4_m3m4(cob, m, cob)
    cob.transpose()
    return cob.to_quaternion()
		
def update_track_axis(self, context):
    if self.up_axis[-1:] == self.track_axis[-1:]:
        if self.up_axis in ['UP_X','UP_Y']:
            self.track_axis = 'TRACK_POSITIVE_Z'
        else: 
            self.track_axis = 'TRACK_POSITIVE_X'  
            
def update_up_axis(self, context):
    if self.up_axis[-1:] == self.track_axis[-1:]:
        if self.track_axis[-1:] in ['X','Y']:
            self.up_axis = 'UP_Z'
        else:
            self.up_axis = 'UP_X'  
         
    
class PaintClonesProperties(PropertyGroup):
    # Draw Cloned Settings
         
    align_mode = EnumProperty(
        name ="Align mode",
        description="Rotate clone along ..",
        items=(('NORMAL', 'Target Normal', 'Target Normal, up follow stroke'),
           ('X_AXIS', 'Absolute X', 'Absolute X axis, up follow stroke'),
           ('Y_AXIS', 'Absolute Y', 'Absolute Y axis, up follow stroke'),
           ('Z_AXIS', 'Absolute Z', 'Absolute Z axis, up follow stroke'),
           ('STROKE', 'Follow stroke', 'Follow stroke, up follow normal')
           ),
        default = 'NORMAL'
    )
    track_axis = EnumProperty(
        name="Axis",
        description="Main axis",
        items=(('TRACK_POSITIVE_X', 'X', ''),
               ('TRACK_NEGATIVE_X', '-X', ''),
               ('TRACK_POSITIVE_Y', 'Y', ''),
               ('TRACK_NEGATIVE_Y', '-Y', ''),
               ('TRACK_POSITIVE_Z', 'Z', ''),
               ('TRACK_NEGATIVE_Z', '-Z', '')
               ),
        default = 'TRACK_POSITIVE_Z',
        update=update_up_axis
    )
    up_axis = EnumProperty(
        name="Up",
        description="Up axis",
        items=(('UP_X', 'X', ''),
               ('UP_Y', 'Y', ''),
               ('UP_Z', 'Z', ''),
               ),
        default = 'UP_X',
        update=update_track_axis
    )
    drawClonesOptimize = BoolProperty(
        name="Optimize",
        description="Create linked data to optimize...",
        default=True
    )

    drawStrokeLength = FloatProperty(
        description="Spacing between clones",
        subtype="DISTANCE",
        unit="LENGTH",
        name="Spacing",
        default=0.5,
        min=0.001,
        max=10000.0
    )

    drawRandomStrokeScatter = FloatProperty(
        description="Scatter arround stroke",
        subtype="DISTANCE",
        unit="LENGTH",
        name="Scatter",
        default=0.0,
        min=0.0,
        max=10000.0
    )

    randRotationX = FloatProperty(
        description="Random rotation on x axis",
        subtype="ANGLE",
        unit="ROTATION",
        name="x",
        default=0.0,
        min=0.0,
        max=pi
    )
    randRotationY = FloatProperty(
        description="Random rotation on y axis",
        subtype="ANGLE",
        unit="ROTATION",
        name="y",
        default=0.0,
        min=0.0,
        max=pi
    )
    randRotationZ = FloatProperty(
        description="Random rotation on z axis",
        subtype="ANGLE",
        unit="ROTATION",
        name="z",
        default=0.0,
        min=0.0,
        max=pi
    )

    randScale = FloatProperty(
        subtype="PERCENTAGE",
        name="Scale",
        description="Random scale down in %",
        default=0.0,
        min=0.0,
        max=99.9
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

class TOOLS_PT_PaintClones(Panel):
    bl_label = "Paint Clones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = 'PC'
    # bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        paintClonesTools = bpy.context.scene.paintClonesTools
        row = layout.row()
        row.operator("tools.paint_clones_pick_sources")
        row.operator("tools.paint_clones")
        layout.prop(paintClonesTools, "drawClonesOptimize")
        layout.prop(paintClonesTools, "align_mode")
        row = layout.row()
        row.prop(paintClonesTools, "track_axis")
        row.prop(paintClonesTools, "up_axis")
        layout.label(text="Randomize:")
        row = layout.row()
        row.prop(paintClonesTools, "randRotationX")
        row.prop(paintClonesTools, "randRotationY")
        row.prop(paintClonesTools, "randRotationZ")
        layout.prop(paintClonesTools, "randScale")
        layout.label(text="Distribution:")
        row = layout.row()
        row.prop(paintClonesTools, "drawStrokeLength")
        row.prop(paintClonesTools, "drawRandomStrokeScatter")
        layout.label(text="Pressure:")
        layout.prop(paintClonesTools, "drawPressure", text='DrawPressure')
        row = layout.row()
        row.prop(paintClonesTools, "drawPressureRelativeStroke", text='Stroke')
        row.prop(paintClonesTools, "drawPressureScale", text='Scale')
        row.prop(paintClonesTools, "drawPressureScatter", text='Scatter')
        
class TOOLS_OP_PaintClones(Operator):
    bl_idname = "tools.paint_clones"
    bl_label = "Paint Clones"
    bl_description = "Paint Clones with mouse over selected object(s)"
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
        paintClonesTools = bpy.context.scene.paintClonesTools
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

            # Do optimization
            if paintClonesTools.drawClonesOptimize is True and self.currentStrokeList is not None:
                for point in self.currentStrokeList:
                    copy_settings_clones(point.objNew, point.objOriginal)
            self.currentStrokeList = None

        if self.doPick is True:
            self.tabletPressure = event.pressure
            pick_and_clone(self, context, event)

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        paintClonesTools = bpy.context.scene.paintClonesTools
        # global paintClonesSourceList
        if len(paintClonesSourceList) == 0 or len(context.selected_objects) == 0:
            self.report({'WARNING'}, "Pick target object(s)")
            return {'CANCELLED'}

        for obj_name in paintClonesSourceList:
            if obj_name not in context.scene.objects:
                self.report({'WARNING'}, "Picked source(s) was Deleted!")
                return {'CANCELLED'}
                break

        if context.space_data.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            prepare_drawing(self, context)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "Active space must be a View3d")
            return {'CANCELLED'}

class TOOLS_OP_PaintClonesPickSources(Operator):
    bl_idname = "tools.paint_clones_pick_sources"
    bl_label = "Pick source(s)"
    bl_description = "Use selected object(s) as Source for clone"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        paintClonesTools = context.scene.paintClonesTools

        if len(context.selected_objects) > 0:
            # global paintClonesSourceList
            paintClonesSourceList.clear()
            for obj in context.selected_objects:
                paintClonesSourceList.append(obj.name)
            if paintClonesTools.track_axis[-1:] == 'X':
                x, y = 1, 2
            if paintClonesTools.track_axis[-1:] == 'Y':
                x, y = 0, 2
            if paintClonesTools.track_axis[-1:] == 'Z':
                x, y = 0, 1
            sizes = [(obj.dimensions[x] * obj.scale[x] + obj.dimensions[y] * obj.scale[y]) / 2.0 for obj in context.selected_objects]
            paintClonesTools.drawStrokeLength = sum(sizes)/len(sizes)
        return {'FINISHED'}

class StrokePoint:

    def __init__(self, objNew, objOriginal, hitPoint, hitNormal):
        self.objNew, self.objOriginal, self.hitPoint, self.hitNormal = objNew, objOriginal, hitPoint, hitNormal

   
# Just prepare some stuff
def prepare_drawing(self, context):
    self.drawOnObjects = context.selected_objects
    for obj in self.drawOnObjects:
        obj.select = False
    self.obj_Active_True = context.scene.objects.active

    self.dupliList = selected_objects_and_duplis(self, context)
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
            if stroke is not None:
                stroke.clear()
        self.allStrokesList.clear()
    self.allStrokesList = None

    if self.currentStrokeList is not None:
        self.currentStrokeList.clear()
    self.currentStrokeList = None


def selected_objects_and_duplis(self, context):
    """Loop over (object, matrix) pairs (mesh only)"""

    listObjMatrix = []
    for obj in self.drawOnObjects:
        if obj.type == 'MESH':
            listObjMatrix.append((obj, obj.matrix_world.copy()))

        if obj.dupli_type != 'NONE':
            obj.dupli_list_create(context.scene)
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

    # copy custom settings of the old object
    for prop in oldObj.keys():
        newObj[prop] = oldObj[prop]


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


def pick_and_clone(self, context, event, ray_max=10000.0):
    """Run this function on left mouse, execute the ray cast"""
    # get the context arguments
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    def obj_ray_cast(obj, matrix, view_vector, ray_origin):
        """Wrapper for ray casting that moves the ray into object space"""

        ray_target = ray_origin + (view_vector * ray_max)

        # get the ray relative to the object
        matrix_inv = matrix.inverted()
        ray_origin_obj = matrix_inv * ray_origin
        ray_target_obj = matrix_inv * ray_target
	ray_vector_obj = ray_target_obj - ray_origin_obj
	
        # cast the ray
        hit_result, hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_vector_obj, ray_max)

        if hit_result:
            hit_world = matrix * hit

            length_squared = (hit_world - ray_origin).length_squared

            if face_index != -1:
                #normal_world = (matrix.to_quaternion() * normal).normalized()

                normal_world = (matrix.to_quaternion() * normal).to_4d()
                normal_world.w = 0
                normal_world = (matrix.to_quaternion() * (matrix_inv * normal_world).to_3d()).normalized()

                return normal_world, hit_world, length_squared

        return None, None, None

    # cast rays and find the closest object
    best_length_squared = ray_max * ray_max
    best_obj, best_obj_nor, best_obj_pos = None, None, None
    best_obj_rand, best_obj_nor_rand, best_obj_pos_rand = None, None, None
    best_obj_hit = None
    
    x_axis = Vector((1.0, 0.0, 0.0))
    y_axis = Vector((0.0, 1.0, 0.0))
    z_axis = Vector((0.0, 0.0, 1.0))
    
    paintClonesTools = context.scene.paintClonesTools
    thePressure = max(1.0 - paintClonesTools.drawPressure,
                      self.tabletPressure)  # The pressure of a pen!

    for obj, matrix in self.dupliList:
        # get the ray from the viewport and mouse
        view_vector_mouse = view3d_utils.region_2d_to_vector_3d(
            region, rv3d, coord)
        ray_origin_mouse = view3d_utils.region_2d_to_origin_3d(
            region, rv3d, coord)

        # Do RayCast! t1,t2,t3,t4 - temp values
        t1, t2, t3 = obj_ray_cast(
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
            strokeLength = paintClonesTools.drawStrokeLength
            if paintClonesTools.drawPressureScale is True and paintClonesTools.drawPressureRelativeStroke is True and self.tabletPressure < 1.0 and paintClonesTools.drawPressure > 0.0:
                strokeLength *= thePressure
            if previousHit is not None and (best_obj_pos - previousHit.hitPoint).length < strokeLength:
                best_obj = None  # Don't do cloning

    # random scatter things
    if paintClonesTools.drawRandomStrokeScatter > 0.0 and best_obj is not None and t1 is not None:
        # Random Vec
        randX = random.uniform(
            -1.0, 1.0) * paintClonesTools.drawRandomStrokeScatter  # 3.0 is random addition
        randY = random.uniform(
            -1.0, 1.0) * paintClonesTools.drawRandomStrokeScatter  # 3.0 is random addition
        randZ = random.uniform(
            -1.0, 1.0) * paintClonesTools.drawRandomStrokeScatter

        if paintClonesTools.drawPressureScatter is True and self.tabletPressure < 1.0 and paintClonesTools.drawPressure > 0.0:
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

            t1, t2, t3 = obj_ray_cast(
                obj, matrix, view_vector_rand, ray_origin_rand)
            # 3.0 is random addition
            if t1 is not None and (t2 - best_obj_hit).length <= paintClonesTools.drawRandomStrokeScatter * 3.0:
                best_obj_nor, best_obj_pos = t1, t2

    # now we have the object under the mouse cursor,
    if best_obj is not None:
        objToClone = bpy.data.objects.get(random.choice(paintClonesSourceList))
        best_obj_nor = best_obj_nor.normalized()
        
        # Rotation To LookAt
        previousHit = None
        if len(self.currentStrokeList) > 0:
            previousHit = self.currentStrokeList[-1]  # get Last Element
        else:
            if len(self.allStrokesList) > 0:
                previousHit = self.allStrokesList[-1][-1]  # get Last Element of previous Stroke
        if previousHit is not None:
            stroke_axis = (best_obj_hit - previousHit.hitPoint).normalized()
        else:
            stroke_axis = x_axis
        # clone object
        newDup = bpy.data.objects.new(objToClone.name, objToClone.data)

        # copy draw type
        newDup.draw_type = objToClone.draw_type
        newDup.show_wire = objToClone.show_wire

        # copy transformation
        newDup.matrix_world = objToClone.matrix_world
        newDup.location = best_obj_pos
        newDup.scale = objToClone.scale
        newDup.rotation_euler = objToClone.rotation_euler
        # bpy.ops.object.rotation_clear()

        context.scene.objects.link(newDup)
        newDup.select = True
        context.scene.objects.active = newDup
        
        # Random Rotation (PreRotate)
        randRotX, randRotY, randRotZ = random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0), random.uniform(-1.0, 1.0)
        bpy.ops.transform.rotate(value=randRotX*paintClonesTools.randRotationX, axis=get_obj_axis(newDup, 'X'), proportional='DISABLED')
        bpy.ops.transform.rotate(value=randRotY*paintClonesTools.randRotationY, axis=get_obj_axis(newDup, 'Y'), proportional='DISABLED')
        bpy.ops.transform.rotate(value=randRotZ*paintClonesTools.randRotationZ, axis=get_obj_axis(newDup, 'Z'), proportional='DISABLED')
        
        # Rotation To Stroke direction
        if paintClonesTools.align_mode == 'STROKE':
            track_vec = stroke_axis
            up_vec = best_obj_nor
        
        # Rotation To Normal
        if paintClonesTools.align_mode == 'NORMAL':
            track_vec = best_obj_nor
            up_vec = stroke_axis
            
        # Rotation To X_AXIS
        if paintClonesTools.align_mode == 'X_AXIS':
            track_vec = x_axis
            up_vec = stroke_axis
        
        # Rotation To Y_AXIS
        if paintClonesTools.align_mode == 'Y_AXIS':
            track_vec = y_axis
            up_vec = stroke_axis
        
        # Rotation To Z_AXIS
        if paintClonesTools.align_mode == 'Z_AXIS':
            track_vec = z_axis
            up_vec = stroke_axis
            
        up_axis = up_list.get(paintClonesTools.up_axis,5)
        track_axis = track_list.get(paintClonesTools.track_axis,0)
        q = get_rot_quat(newDup, track_vec, up_vec, track_axis, up_axis)
        
        bpy.ops.transform.rotate(value=q.angle, axis=(q.axis), proportional='DISABLED')
        
        
        # Scale
        if paintClonesTools.drawPressure > 0.0 or paintClonesTools.randScale > 0.0:
            newSize = newDup.scale
            if self.tabletPressure < 1.0 and paintClonesTools.drawPressure > 0.0 and paintClonesTools.drawPressureScale is True:
                newSize *= thePressure

            if paintClonesTools.randScale > 0.0:
                randScale = 1.0 - \
                    (random.uniform(0.0, 1.0) *
                     paintClonesTools.randScale / 100.0)
                newSize *= randScale


        # do optimization for a stroke or not
        if paintClonesTools.drawClonesOptimize is False:
            copy_settings_clones(newDup, objToClone)

        newDup.select = False  # Clear Selection

        # Add this point with all its stuff
        self.currentStrokeList.append(
            StrokePoint(newDup, objToClone, best_obj_hit, best_obj_nor))

        
def register():
    bpy.utils.register_module(__name__)

    bpy.types.Scene.paintClonesTools = PointerProperty(
        name="Paint Clones Variables",
        type=PaintClonesProperties,
        description="Paint Clones Properties"
    )


def unregister():
    import bpy
    del bpy.types.Scene.paintClonesTools
    bpy.utils.unregister_module(__name__)


if __name__ == "__main__":
    register()
