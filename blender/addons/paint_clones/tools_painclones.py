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
# Inspired by mifth tools cloning and Animation Nodes

bl_info = {
    "name": "Paint Clones",
    "author": "Stephen Leger",
    "version": (0, 1, 0),
    "blender": (2, 77, 0),
    "location": "3D View -> Tool Shelf -> Object Tools Panel (at the bottom)",
    "description": "Paint Clones",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "https://github.com/mifth/mifthtools/edit/master/blender/addons/paint_clones/",
    "category": "Tools"}

import bpy
from bpy_extras import view3d_utils

from math import pi
import random
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import EnumProperty, BoolProperty, FloatProperty, PointerProperty, StringProperty
from mathutils import Vector, Matrix

global paintClonesSourceList
paintClonesSourceList = []  # Array of Objects Names

# source : Animation Nodes
def generateRotationMatrix(direction, guide, trackAxis = "Z", guideAxis = "X"):
    '''
    trackAxis in ("X", "Y", "Z", "-X", "-Y", "-Z")
    guideAxis in ("X", "Y", "Z")
    '''

    matrix = Matrix.Identity(4)

    if guideAxis[-1:] == trackAxis[-1:]:
        return matrix

    if direction == zero:
        return matrix

    z = direction.normalized()
    y = z.cross(guide.normalized())
    if y == zero:
        if guideAxis == "X":
            if z.cross(xAxis) != zero: y = z.cross(xAxis)
            else: y = zAxis
        elif guideAxis == "Y":
            if z.cross(yAxis) != zero: y = z.cross(yAxis)
            else: y = zAxis
        elif guideAxis == "Z":
            if z.cross(zAxis) != zero: y = z.cross(zAxis)
            else: y = yAxis

    x = y.cross(z)

    mx, my, mz = changeAxesDict[(trackAxis, guideAxis)](x, y, z)
    matrix.col[0][:3] = mx
    matrix.col[1][:3] = my
    matrix.col[2][:3] = mz
    return matrix

changeAxesDict = {
    ( "X", "Z"): lambda x, y, z: ( z, -y,  x),
    ( "X", "Y"): lambda x, y, z: ( z,  x,  y),
    ( "Y", "Z"): lambda x, y, z: ( y,  z,  x),
    ( "Y", "X"): lambda x, y, z: ( x,  z, -y),

    ( "Z", "X"): lambda x, y, z: ( x,  y,  z),
    ( "Z", "Y"): lambda x, y, z: (-y,  x,  z),
    ("-X", "Z"): lambda x, y, z: (-z,  y,  x),
    ("-X", "Y"): lambda x, y, z: (-z,  x, -y),

    ("-Y", "Z"): lambda x, y, z: (-y, -z,  x),
    ("-Y", "X"): lambda x, y, z: ( x, -z,  y),
    ("-Z", "X"): lambda x, y, z: ( x, -y, -z),
    ("-Z", "Y"): lambda x, y, z: ( y,  x, -z),
}

zero = Vector((0, 0, 0))
xAxis = Vector((1, 0, 0))
yAxis = Vector((0, 1, 0))
zAxis = Vector((0, 0, 1))
  
def get_rot_quat(obj, track_vec, up_vec, track_axis, up_axis):
    m1 = generateRotationMatrix(track_vec, up_vec, track_axis, up_axis)
    return obj.rotation_quaternion.rotation_difference(m1.to_quaternion())
		
def update_track_axis(self, context):
    if self.up_axis[-1:] == self.track_axis[-1:]:
        if self.up_axis in ['X','Y']:
            self.track_axis = 'Z'
        else: 
            self.track_axis = 'X'  
            
def update_up_axis(self, context):
    if self.up_axis[-1:] == self.track_axis[-1:]:
        if self.track_axis[-1:] in ['X','Y']:
            self.up_axis = 'Z'
        else:
            self.up_axis = 'X'  
         
def enumerate_groups(self, context):
    items = [(group.name, group.name, '') for group in bpy.data.groups]
    items.append(('GRONONE','Dont group',''))
    items.append(('GROCREATE','Create a new group'))
    return tuple(items)
  
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
        items=(('X', 'X', ''),
               ('-X', '-X', ''),
               ('Y', 'Y', ''),
               ('-Y', '-Y', ''),
               ('Z', 'Z', ''),
               ('-Z', '-Z', '')
               ),
        default = 'Z',
        update=update_up_axis
    )
    up_axis = EnumProperty(
        name="Up",
        description="Up axis",
        items=(('X', 'X', ''),
               ('Y', 'Y', ''),
               ('Z', 'Z', ''),
               ),
        default = 'X',
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
        name = "Pressure",
        default=0.7,
        min=0.0,
        max=0.95
    )
    drawPressureRelativeStroke = BoolProperty(
        name="PStroke",
        description="Relative Stroke To Scale and Pressure",
        default=True
    )
    drawPressureScale = BoolProperty(
        name="PScale",
        description="Pressure for Scale",
        default=True
    )
    drawPressureScatter = BoolProperty(
        name="PScatter",
        description="Pressure for Scatter",
        default=True
    )
    group_use = BoolProperty(
        name="Use source group(s)",
        description="Group in source group(s)",
        default=True
    )
    group_add_use = BoolProperty(
        name="Group",
        description="Add to existing group",
        default=False
    )    
    group_add = StringProperty(
        name="Group",
        description="Add to existing group",
        default=""
    )
    group_name_use = BoolProperty(
        name="Create",
        description="Create new group and add objects",
        default=False
    )
    group_name = StringProperty(
        name="Create",
        description="New group name",
        default="PaintClones"
    )
    
class TOOLS_PT_PaintClones(Panel):
    bl_label = "Paint Clones"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = 'Tools'
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        pct = bpy.context.scene.paintClonesTools
        row = layout.row()
        row.operator("tools.paint_clones_pick_sources", icon="GROUP")
        row.operator("tools.paint_clones", icon="BRUSH_DATA")
        layout.separator()
        layout.prop(pct, "drawClonesOptimize")
        layout.separator()
        layout.prop(pct, "align_mode")
        row = layout.row()
        row.prop(pct, "track_axis")
        row.prop(pct, "up_axis")
        layout.separator()
        layout.label(text="Randomize:")
        row = layout.row()
        row.prop(pct, "randRotationX")
        row.prop(pct, "randRotationY")
        row.prop(pct, "randRotationZ")
        layout.prop(pct, "randScale")
        layout.separator()
        layout.label(text="Distribution:")
        row = layout.row()
        row.prop(pct, "drawStrokeLength")
        row.prop(pct, "drawRandomStrokeScatter")
        layout.separator()
        layout.label(text="Grouping:")
        layout.prop(pct, "group_use")
        row = layout.row()
        col = row.column()
        col.prop(pct, "group_add_use")
        col_add = row.column()
        col_add.prop_search(pct, "group_add", bpy.data, "groups","")
        col_add.active = pct.group_add_use
        row = layout.row()
        col = row.column()
        col.prop(pct, "group_name_use")
        col_name = row.column()
        col_name.prop(pct, "group_name","")
        col_name.active = pct.group_name_use
        layout.separator()
        layout.label(text="Pressure:")
        layout.prop(pct, "drawPressure")
        row = layout.row()
        row.prop(pct, "drawPressureRelativeStroke")
        row.prop(pct, "drawPressureScale")
        row.prop(pct, "drawPressureScatter")
        
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
        pct = bpy.context.scene.paintClonesTools
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
            if len(self.currentStrokeList) > 0:
                self.allStrokesList.append(self.currentStrokeList)

            # Do optimization
            if pct.drawClonesOptimize is True and self.currentStrokeList is not None:
                for point in self.currentStrokeList:
                    copy_settings_clones(pct, point.objNew, point.objOriginal)
            self.currentStrokeList = None

        if self.doPick is True:
            self.tabletPressure = event.pressure
            pick_and_clone(self, context, event)

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
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
        pct = context.scene.paintClonesTools

        if len(context.selected_objects) > 0:
            # global paintClonesSourceList
            paintClonesSourceList.clear()
            for obj in context.selected_objects:
                paintClonesSourceList.append(obj.name)
            if pct.track_axis[-1:] == 'X':
                x, y = 1, 2
            if pct.track_axis[-1:] == 'Y':
                x, y = 0, 2
            if pct.track_axis[-1:] == 'Z':
                x, y = 0, 1
            sizes = [(obj.dimensions[x] * obj.scale[x] + obj.dimensions[y] * obj.scale[y]) / 2.0 for obj in context.selected_objects]
            pct.drawStrokeLength = sum(sizes)/len(sizes)
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


def copy_settings_clones(pct, newObj, oldObj):
    # Copy Groups
    if pct.group_use:
        for thisGroup in bpy.data.groups:
            if oldObj.name in thisGroup.objects:
                thisGroup.objects.link(newObj)
    
    if pct.group_add_use and pct.group_add != "":
        addToGroup = bpy.data.groups.get(pct.group_add)
        if addToGroup is None:
            addToGroup = bpy.data.groups.new(pct.group_add)
        if newObj.name not in addToGroup.objects:
            addToGroup.objects.link(newObj)
 
    if pct.group_name_use and pct.group_name  != "":
        addToGroup = bpy.data.groups.get(pct.group_name)
        if addToGroup is None:
            addToGroup = bpy.data.groups.new(pct.group_name)
        if newObj.name not in addToGroup.objects:
            addToGroup.objects.link(newObj)
    
    
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
    
    pct = context.scene.paintClonesTools
    thePressure = max(1.0 - pct.drawPressure,
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
            strokeLength = pct.drawStrokeLength
            if pct.drawPressureScale is True and pct.drawPressureRelativeStroke is True and self.tabletPressure < 1.0 and pct.drawPressure > 0.0:
                strokeLength *= thePressure
            if previousHit is not None and (best_obj_pos - previousHit.hitPoint).length < strokeLength:
                best_obj = None  # Don't do cloning

    # random scatter things
    if pct.drawRandomStrokeScatter > 0.0 and best_obj is not None and t1 is not None:
        # Random Vec
        randX = random.uniform(
            -1.0, 1.0) * pct.drawRandomStrokeScatter  # 3.0 is random addition
        randY = random.uniform(
            -1.0, 1.0) * pct.drawRandomStrokeScatter  # 3.0 is random addition
        randZ = random.uniform(
            -1.0, 1.0) * pct.drawRandomStrokeScatter

        if pct.drawPressureScatter is True and self.tabletPressure < 1.0 and pct.drawPressure > 0.0:
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
            if t1 is not None and (t2 - best_obj_hit).length <= pct.drawRandomStrokeScatter * 3.0:
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
            stroke_axis = xAxis
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
        bpy.ops.transform.rotate(value=randRotX*pct.randRotationX, axis=get_obj_axis(newDup, 'X'), proportional='DISABLED')
        bpy.ops.transform.rotate(value=randRotY*pct.randRotationY, axis=get_obj_axis(newDup, 'Y'), proportional='DISABLED')
        bpy.ops.transform.rotate(value=randRotZ*pct.randRotationZ, axis=get_obj_axis(newDup, 'Z'), proportional='DISABLED')
        
        # Rotation To Stroke direction
        if pct.align_mode == 'STROKE':
            track_vec = stroke_axis
            up_vec = best_obj_nor
        
        # Rotation To Normal
        if pct.align_mode == 'NORMAL':
            track_vec = best_obj_nor
            up_vec = stroke_axis
            
        # Rotation To X_AXIS
        if pct.align_mode == 'X_AXIS':
            track_vec = xAxis
            up_vec = stroke_axis
        
        # Rotation To Y_AXIS
        if pct.align_mode == 'Y_AXIS':
            track_vec = yAxis
            up_vec = stroke_axis
        
        # Rotation To Z_AXIS
        if pct.align_mode == 'Z_AXIS':
            track_vec = zAxis
            up_vec = stroke_axis
            
        q = get_rot_quat(newDup, track_vec, up_vec, pct.track_axis, pct.up_axis)
        
        bpy.ops.transform.rotate(value=q.angle, axis=(q.axis), proportional='DISABLED')
        
        
        # Scale
        if pct.drawPressure > 0.0 or pct.randScale > 0.0:
            newSize = newDup.scale
            if self.tabletPressure < 1.0 and pct.drawPressure > 0.0 and pct.drawPressureScale is True:
                newSize *= thePressure

            if pct.randScale > 0.0:
                randScale = 1.0 - \
                    (random.uniform(0.0, 1.0) *
                     pct.randScale / 100.0)
                newSize *= randScale


        # do optimization for a stroke or not
        if pct.drawClonesOptimize is False:
            copy_settings_clones(pct, newDup, objToClone)

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
