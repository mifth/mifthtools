import bpy
import blf
import string
import bmesh

from bpy.props import *
from bpy.types import Operator, AddonPreferences

from bpy_extras import view3d_utils

import math
import mathutils as mathu
import random
from mathutils import Vector

from . import mi_utils_base as ut_base


class MI_OT_Noise(bpy.types.Operator):
    bl_idname = "mira.noise"
    bl_label = "Noise"
    bl_description = "Noise"
    bl_options = {'REGISTER', 'UNDO'}

    noise_type: EnumProperty(
        items=(('Turbulence', 'Turbulence', ''),
               ('Fractal', 'Fractal', ''),
               ('HeteroTerrain', 'HeteroTerrain', ''),
               ),
        default = 'Turbulence'
    )

    frequency: FloatProperty(default=1.0, soft_min=0)
    intensity: FloatProperty(default=1.0, soft_min=0)
    offset_x: FloatProperty(default=0.0)
    offset_y: FloatProperty(default=0.0)
    offset_z: FloatProperty(default=0.0)
    octaves: IntProperty(default=2)
    amplitude_scale: FloatProperty(default=0.5, soft_min=0)
    frequency_scale: FloatProperty(default=2.0, soft_min=0)
    hard: BoolProperty(default=True)


    def execute(self, context):

        obj = context.active_object
        noise_obj(obj, context, self)

        return {'FINISHED'}

    def invoke(self, context, event):
        # if context.area.type == 'VIEW_3D':
            # change startup
            # self.select_mouse_mode = context.preferences.inputs.select_mouse
            # context.preferences.inputs.select_mouse = 'RIGHT'

        return self.execute(context)
        # else:
            # self.report({'WARNING'}, "View3D not found, cannot run operator")
            # return {'CANCELLED'}


def noise_obj(obj, context, self):
    bm = bmesh.from_edit_mesh(obj.data)
    verts = [v for v in bm.verts if v.select]
    if not verts:
        verts = [v for v in bm.verts if v.hide is False]

    for vert in verts:
        noise_pos = self.frequency * vert.co.copy()
        noise_pos.x += self.offset_x
        noise_pos.z += self.offset_y
        noise_pos.z += self.offset_z

        noise_val = None
        if self.noise_type == 'Turbulence':
            noise_val = mathu.noise.turbulence(noise_pos, self.octaves, self.hard, noise_basis="PERLIN_ORIGINAL", amplitude_scale=self.amplitude_scale, frequency_scale=self.frequency_scale)
        elif self.noise_type == 'Fractal':
            noise_val = mathu.noise.fractal(noise_pos, self.amplitude_scale, self.frequency_scale, self.octaves, noise_basis="PERLIN_ORIGINAL")
        else:
            noise_val = mathu.noise.hetero_terrain(noise_pos, self.amplitude_scale, self.frequency_scale, self.octaves, 0, noise_basis="PERLIN_ORIGINAL")

        vert_offset = vert.normal.copy().normalized() * noise_val
        vert.co += vert_offset * self.intensity

    bm.normal_update()
    bmesh.update_edit_mesh(obj.data)
