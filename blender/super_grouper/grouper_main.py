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
import random
import string

from bpy.props import *
from bpy.types import Operator, AddonPreferences
from bpy.types import Menu, Panel, UIList, PropertyGroup
from bpy.props import StringProperty, BoolProperty, IntProperty, CollectionProperty, BoolVectorProperty, PointerProperty
from bpy.app.handlers import persistent


NUM_LAYERS = 20
SCENE_SGR = '#SGR'
UNIQUE_ID_NAME = 'sg_belong_id'


class SG_Group(PropertyGroup):
    use_toggle = BoolProperty(name="", default=True)
    use_wire = BoolProperty(name="", default=False)
    use_lock = BoolProperty(name="", default=False)
    unique_id = StringProperty(default="")


class SG_Object_Id(PropertyGroup):
    unique_id_object = StringProperty(default="")


class SG_Other_Settings(PropertyGroup):
    select_all_layers = BoolProperty(name="SelectVisibleLayers", default=True)
    unlock_obj = BoolProperty(name="UnlockObj", default=True)
    unhide_obj = BoolProperty(name="UnhideObj", default=True)


class SG_BasePanel(bpy.types.Panel):
    bl_label = "SGrouper"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = 'Relations'

    def draw(self, context):
        layout = self.layout

        scene = context.scene

        if context.scene.name.endswith(SCENE_SGR) is False:
            sg_settings = scene.sg_settings

            row = layout.row(align=True)
            row.operator(
                "super_grouper.super_group_add", icon='ZOOMIN', text="")
            row.operator(
                "super_grouper.super_group_remove", icon='ZOOMOUT', text="")

            row = layout.row(align=True)
            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='BBOX')
            op.sg_objects_changer = 'BOUND_SHADE'

            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='WIRE')
            op.sg_objects_changer = 'WIRE_SHADE'

            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='MATERIAL')
            op.sg_objects_changer = 'MATERIAL_SHADE'

            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='RETOPO')
            op.sg_objects_changer = 'SHOW_WIRE'

            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='RETOPO')
            op.sg_objects_changer = 'HIDE_WIRE'

            row = layout.row(align=True)
            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='COLOR_RED')
            op.sg_objects_changer = 'COLOR_WIRE'

            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='COLOR_GREEN')
            op.sg_objects_changer = 'DEFAULT_COLOR_WIRE'

            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='LOCKED')
            op.sg_objects_changer = 'LOCKED'

            op = row.operator(
                "super_grouper.change_selected_objects", text="", emboss=False, icon='UNLOCKED')
            op.sg_objects_changer = 'UNLOCKED'

            row = layout.row()
            row.template_list(
                "SG_named_super_groups", "", scene, "super_groups", scene, "super_groups_index")

            row = layout.row()
            row.operator("super_grouper.add_to_group", text="Add")
            row.operator(
                "super_grouper.super_remove_from_group", text="Remove")
            # layout.separator()
            layout.label(text="Selection Settings:")
            row = layout.row(align=True)
            row.prop(sg_settings, "select_all_layers", text='L')
            row.prop(sg_settings, "unlock_obj", text='L')
            row.prop(sg_settings, "unhide_obj", text='H')


class SG_named_super_groups(UIList):

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        super_group = item

        # check for lock camera and layer is active
        # view_3d = context.area.spaces.active  # Ensured it is a 'VIEW_3D' in panel's poll(), weak... :/
        # use_spacecheck = False if view_3d.lock_camera_and_layers else True

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(super_group, "name", text="", emboss=False)

            # select operator
            # icon = 'LOCKED'
            # op = layout.operator("super_grouper.toggle_select", text="", emboss=False, icon=icon)
            # op.group_idx = index

            # select operator
            icon = 'RESTRICT_SELECT_OFF' if super_group.use_toggle else 'RESTRICT_SELECT_ON'
            op = layout.operator(
                "super_grouper.toggle_select", text="", emboss=False, icon=icon)
            op.group_idx = index

            # view operator
            icon = 'RESTRICT_VIEW_OFF' if super_group.use_toggle else 'RESTRICT_VIEW_ON'
            op = layout.operator(
                "super_grouper.toggle_visibility", text="", emboss=False, icon=icon)
            op.group_idx = index

        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'


class SG_super_group_add(bpy.types.Operator):

    """Add and select a new layer group"""
    bl_idname = "super_grouper.super_group_add"
    bl_label = "Add Layer Group"
    bl_options = {'REGISTER', 'UNDO'}

    # layers = BoolVectorProperty(name="Layers", default=([False] *
    # NUM_LAYERS), size=NUM_LAYERS)

    @classmethod
    def poll(cls, context):
        return bool(context.scene)

    def execute(self, context):
        scene = context.scene
        super_groups = scene.super_groups
        # layers = self.layers

        # Generate unique id
        uni_numb = None
        while True:
            uniq_id_temp = ''.join(random.choice(string.ascii_uppercase + string.digits)
                                   for _ in range(10))
            is_un = True
            for gp in super_groups:
                if gp.unique_id == uniq_id_temp:
                    is_un = False
            if is_un is True:
                uni_numb = uniq_id_temp
                break

        group_idx = len(super_groups)
        s_group = super_groups.add()
        s_group.name = "SG.%.3d" % group_idx
        # s_group.layers = layers
        s_group.unique_id = uni_numb
        scene.super_groups_index = group_idx

        for obj in context.selected_objects:
            # add the unique id of selected objects
            SG_add_property_to_obj(scene.super_groups, s_group.unique_id, obj)

        return {'FINISHED'}


class SG_super_group_remove(bpy.types.Operator):

    """Remove selected layer group"""
    bl_idname = "super_grouper.super_group_remove"
    bl_label = "Remove Layer Group"
    bl_options = {'REGISTER', 'UNDO'}

    # group_idx = bpy.props.IntProperty()

    @classmethod
    def poll(cls, context):
        return bool(context.scene)

    def execute(self, context):
        scene = context.scene

        # if a scene contains goups
        if scene.super_groups:
            s_group_id = scene.super_groups[scene.super_groups_index].unique_id

            # get all ids
            s_groups = []
            for s_group in scene.super_groups:
                s_groups.append(s_group.unique_id)

            # clear context scene
            for obj in scene.objects:
                SG_del_properties_from_obj(UNIQUE_ID_NAME, [s_group_id], obj)

            # clear SGR scene
            sgr_scene_name = scene.name + SCENE_SGR
            if sgr_scene_name in bpy.data.scenes:
                sgr_scene = bpy.data.scenes[scene.name + SCENE_SGR]
                for obj in sgr_scene.objects:
                    SGR_switch_object(obj, sgr_scene, scene, s_group_id)
                    SG_del_properties_from_obj(
                        UNIQUE_ID_NAME, [s_group_id], obj)

                # remove group_scene if it's empty
                if len(sgr_scene.objects) == 0:
                    bpy.data.scenes.remove(sgr_scene)

            # finally remove s_group
            scene.super_groups.remove(scene.super_groups_index)
            if scene.super_groups_index > len(scene.super_groups) - 1:
                scene.super_groups_index = len(scene.super_groups) - 1

        return {'FINISHED'}


def SGR_get_group_scene(context):
    group_scene_name = context.scene.name + SCENE_SGR

    if group_scene_name in bpy.data.scenes:
        return bpy.data.scenes[group_scene_name]

    return None


def SGR_create_group_scene(context):
    group_scene_name = context.scene.name + SCENE_SGR

    if context.scene.name.endswith(SCENE_SGR) is False:
        if group_scene_name in bpy.data.scenes:
            return bpy.data.scenes[group_scene_name]
        else:
            return bpy.data.scenes.new(group_scene_name)

    return None


def SGR_select_objects(scene, ids):
    for obj in scene.objects:
        if len(obj.sg_belong_id.values()) > 0:
            for prop in obj.sg_belong_id:
                if prop.unique_id_object in ids:
                    for i in range(len(scene.layers)):
                        if obj.layers[i] is True:
                            if scene.layers[i] is True or scene.sg_settings.select_all_layers:
                                # unlock
                                if scene.sg_settings.unlock_obj:
                                    obj.hide_select = False
                                # unhide
                                if scene.sg_settings.unhide_obj:
                                    obj.hide = False

                                # select
                                obj.select = True

                                # break if we need to select only visible
                                # layers
                                if scene.sg_settings.select_all_layers is False:
                                    break
                                else:
                                    scene.layers[i] = obj.layers[i]


class SG_toggle_select(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "super_grouper.toggle_select"
    bl_label = "Toggle Visibility"
    bl_description = "Toggle Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    group_idx = IntProperty()

    def execute(self, context):
        scene = context.scene
        if self.group_idx < len(scene.super_groups):
            s_group = scene.super_groups[self.group_idx]

            if s_group.use_toggle is True:
                SGR_select_objects(scene, [s_group.unique_id])

        return {'FINISHED'}


class SG_toggle_visibility(bpy.types.Operator):

    """Draw a line with the mouse"""
    bl_idname = "super_grouper.toggle_visibility"
    bl_label = "Toggle Visibility"
    bl_description = "Toggle Visibility"
    bl_options = {'REGISTER', 'UNDO'}

    group_idx = IntProperty()

    def execute(self, context):
        scene = context.scene
        if self.group_idx < len(scene.super_groups):
            s_group = scene.super_groups[self.group_idx]

            # Try to get or create new GroupScene
            group_scene = SGR_get_group_scene(context)
            if group_scene is None and s_group.use_toggle is True:
                group_scene = SGR_create_group_scene(context)

            # if GroupScene exists now we can switch objects
            if group_scene is not None:
                if s_group.use_toggle is True:
                    for obj in scene.objects:
                        SGR_switch_object(
                            obj, scene, group_scene, s_group.unique_id)
                else:
                    for obj in group_scene.objects:
                        SGR_switch_object(
                            obj, group_scene, scene, s_group.unique_id)
                    if len(group_scene.objects) == 0:
                        bpy.data.scenes.remove(group_scene)

            s_group.use_toggle = not s_group.use_toggle  # switch visibility

        return {'FINISHED'}


def SGR_switch_object(obj, scene_source, scene_terget, s_group_id):
    do_switch = False
    if len(obj.sg_belong_id.values()) > 0:
        for prop in obj.sg_belong_id:
            if prop.unique_id_object == s_group_id:
                do_switch = True

        if do_switch is True:
            layers = obj.layers[:]  # copy layers
            obj.select = False

            # if object is not already linked
            if obj.name not in scene_terget.objects:
                obj2 = scene_terget.objects.link(obj)
                obj2.layers = layers  # paste layers

            scene_source.objects.unlink(obj)


class SG_change_selected_objects(bpy.types.Operator):
    bl_idname = "super_grouper.change_selected_objects"
    bl_label = "Change Selected"
    bl_description = "Change Selected"
    bl_options = {'REGISTER', 'UNDO'}

    sg_objects_changer = EnumProperty(
        items=(('BOUND_SHADE', 'BOUND_SHADE', ''),
               ('WIRE_SHADE', 'WIRE_SHADE', ''),
               ('MATERIAL_SHADE', 'MATERIAL_SHADE', ''),
               ('SHOW_WIRE', 'SHOW_WIRE', ''),
               ('HIDE_WIRE', 'HIDE_WIRE', ''),
               ('COLOR_WIRE', 'COLOR_WIRE', ''),
               ('DEFAULT_COLOR_WIRE', 'DEFAULT_COLOR_WIRE', ''),
               ('LOCKED', 'LOCKED', ''),
               ('UNLOCKED', 'UNLOCKED', '')
               ),
        default = 'MATERIAL_SHADE'
    )

    def execute(self, context):
        for obj in context.selected_objects:
            if self.sg_objects_changer == 'BOUND_SHADE':
                obj.draw_type = 'BOUNDS'
            elif self.sg_objects_changer == 'WIRE_SHADE':
                obj.draw_type = 'WIRE'
            elif self.sg_objects_changer == 'MATERIAL_SHADE':
                obj.draw_type = 'TEXTURED'
            elif self.sg_objects_changer == 'SHOW_WIRE':
                obj.show_wire = True
            elif self.sg_objects_changer == 'HIDE_WIRE':
                obj.show_wire = False
            elif self.sg_objects_changer == 'COLOR_WIRE':
                r = random.uniform(0.0, 1.0)
                g = random.uniform(0.0, 1.0)
                b = random.uniform(0.0, 1.0)
                obj.color = (r, g, b, 1)
                obj.show_wire_color = True
            elif self.sg_objects_changer == 'DEFAULT_COLOR_WIRE':
                obj.show_wire_color = False
            elif self.sg_objects_changer == 'LOCKED':
                    obj.hide_select = True
            elif self.sg_objects_changer == 'UNLOCKED':
                    obj.hide_select = False

        return {'FINISHED'}


class SG_add_to_group(bpy.types.Operator):
    bl_idname = "super_grouper.add_to_group"
    bl_label = "Add"
    bl_description = "Add To Group"
    bl_options = {'REGISTER', 'UNDO'}

    # group_idx = bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene

        if len(scene.super_groups) > 0:
            s_group = scene.super_groups[scene.super_groups_index]
            for obj in context.selected_objects:
                # add the unique id of selected group
                SG_add_property_to_obj(
                    scene.super_groups, s_group.unique_id, obj)

                # check if the group is hidden
                if s_group.use_toggle is False:
                    # Try to get or create new GroupScene
                    group_scene = SGR_get_group_scene(context)
                    if group_scene is None:
                        group_scene = SGR_create_group_scene(context)

                    # Unlink object
                    if group_scene is not None:
                        group_scene.objects.link(obj)
                        context.scene.objects.unlink(obj)

        return {'FINISHED'}


class SG_remove_from_group(bpy.types.Operator):
    bl_idname = "super_grouper.super_remove_from_group"
    bl_label = "Add"
    bl_description = "Add To Group"
    bl_options = {'REGISTER', 'UNDO'}

    # group_idx = bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene

        if len(scene.super_groups) > 0:
            # get all ids
            s_groups = []
            for s_group in scene.super_groups:
                s_groups.append(s_group.unique_id)

            # remove s_groups
            for obj in context.selected_objects:
                SG_del_properties_from_obj(UNIQUE_ID_NAME, s_groups, obj)
            s_groups = None  # clear

        return {'FINISHED'}


def SG_add_property_to_obj(s_groups, prop_value, obj):
    prop = obj.sg_belong_id

    if len(prop.values()) > 0:

        has_value = False
        for s_group in s_groups:
            prop_len = len(prop)
            index_prop = 0
            for i in range(prop_len):
                prop_obj = prop[index_prop]
                is_removed = False
                if prop_obj.unique_id_object != prop_value:
                    if prop_obj.unique_id_object == s_group.unique_id:
                        prop.remove(index_prop)
                        is_removed = True
                else:
                    has_value = True

                if is_removed is False:
                    index_prop += 1

        # add the value if it does not exist
        if has_value == False:
            added_prop = prop.add()
            added_prop.unique_id_object = prop_value
    else:
        added_prop = prop.add()
        added_prop.unique_id_object = prop_value
    # print(added_prop.unique_id_object)
    # print(obj.sg_belong_id.values().index(obj.sg_belong_id.values()[0]))


def SG_del_properties_from_obj(prop_name, s_groups, obj):
    prop = obj.sg_belong_id

    if len(prop.values()) > 0:

        # remove item
        prop_len = len(prop)
        index_prop = 0
        for i in range(prop_len):
            prop_obj = prop[index_prop]
            is_removed = False
            if prop_obj.unique_id_object in s_groups:
                prop.remove(index_prop)
                is_removed = True

            if is_removed is False:
                index_prop += 1

        if len(prop.values()) == 0:
            del bpy.data.objects[obj.name][prop_name]
