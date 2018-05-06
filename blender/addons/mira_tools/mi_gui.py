# BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# END GPL LICENSE BLOCK #####

import bpy
from bpy import*


############----------------------############
############  Props for DROPDOWN  ############
############----------------------############

class DropdownMiraToolProps(bpy.types.PropertyGroup):
    """
    Fake module like class
    bpy.context.window_manager.mirawindow
    """
    display_mira_arc = bpy.props.BoolProperty(name="Make Arc", description="UI Make Arc Tools", default=False)
    display_mira_stretch = bpy.props.BoolProperty(name="Curve Stretch", description="UI Curve Stretch Tools", default=False)
    display_mira_sface = bpy.props.BoolProperty(name="Curve Surface", description="UI Curve Surface Tools", default=False)
    display_mira_guide = bpy.props.BoolProperty(name="Curve Guide", description="UI Curve Guide Tools", default=False)
    display_mira_modify = bpy.props.BoolProperty(name="Modify Tools", description="UI Modify Tools", default=False)
    display_mira_deform = bpy.props.BoolProperty(name="Deform Tools", description="UI Deform Tools", default=False)
    display_mira_extrude = bpy.props.BoolProperty(name="Draw Extrude", description="UI Draw Extrude", default=False)
    display_mira_settings = bpy.props.BoolProperty(name="Settings", description="UI Settings", default=False)

    display_mira_wrap = bpy.props.BoolProperty(name="Wrap", description="UI Wrap", default=False)


############-----------------------------############
############  DROPDOWN Layout for PANEL  ############
############-----------------------------############

class MIRA_Panel(bpy.types.Panel):
    bl_label = "Mira Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "mesh_edit"
    bl_category = 'Mira'

    def draw(self, context):
        mt = context.window_manager.mirawindow
        layout = self.layout
        #mi_settings = context.scene.mi_settings

# --------------------------------------------------

        #col = layout.column(align = True)
        if mt.display_mira_extrude:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_extrude", text="", icon='TRIA_DOWN')

        else:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_extrude", text="", icon='TRIA_RIGHT')

        row.label("Extrude")
        if context.scene.mi_settings.surface_snap is False:
            row.prop(context.scene.mi_extrude_settings, "do_symmetry", text='', icon="UV_ISLANDSEL")
            if context.scene.mi_extrude_settings.do_symmetry:
                sub = row.row(1)
                sub.scale_x = 0.15
                sub.prop(context.scene.mi_extrude_settings, "symmetry_axys", text='')

        row.operator("mira.draw_extrude", text="", icon="VPAINT_HLT")

        ###space###
        if mt.display_mira_extrude:
            ###space###
            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column()
            row.operator("mira.draw_extrude", text="Draw Extrude", icon="VPAINT_HLT")
            #row.prop(context.scene.mi_extrude_settings, "extrude_mode", text='Mode')

            row.prop(context.scene.mi_extrude_settings, "extrude_step_type", text='Step')

            if context.scene.mi_extrude_settings.extrude_step_type == 'Asolute':
                row.prop(context.scene.mi_extrude_settings, "absolute_extrude_step", text='')
            else:
                row.prop(context.scene.mi_extrude_settings, "relative_extrude_step", text='')

            row = col_top.column()
            if context.scene.mi_settings.surface_snap is False:
                row.prop(context.scene.mi_extrude_settings, "do_symmetry", text='Symmetry')

                if context.scene.mi_extrude_settings.do_symmetry:
                    row.prop(context.scene.mi_extrude_settings, "symmetry_axys", text='Axys')

            box.separator()       
                    
# --------------------------------------------------

        #col = layout.column(align = True)
        if mt.display_mira_sface:

            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_sface", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_sface", text="", icon='TRIA_RIGHT')

        row.label("Surfaces")

        row.operator("mira.poly_loop", text="", icon="MESH_GRID")
        sub = row.row(1)
        sub.scale_x = 0.15
        sub.prop(context.scene.mi_cur_surfs_settings, "spread_loops_type", text='', icon="COLLAPSEMENU")
        row.operator("mira.curve_surfaces", text="", icon="SURFACE_NCURVE")

        ###space###
        if mt.display_mira_sface:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column(1)
            row.operator("mira.poly_loop", text="Poly Loop", icon="MESH_GRID")

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column()
            row.operator("mira.curve_surfaces", text="CurveSurfaces", icon="SURFACE_NCURVE")
            row.prop(context.scene.mi_cur_surfs_settings, "spread_loops_type", text='Points')

            box.separator()
            
            
# --------------------------------------------------

        #col = layout.column(align = True)
        if mt.display_mira_deform:

            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_deform", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_deform", text="", icon='TRIA_RIGHT')

        row.label("Deform")
        row.operator("mira.noise", text="", icon="RNDCURVE")
        row.prop(context.scene.mi_ldeformer_settings, "manual_update", text='', icon="DISK_DRIVE")
        row.operator("mira.linear_deformer", text="", icon="OUTLINER_OB_MESH")

        ###space###
        if mt.display_mira_deform:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column()
            row.operator("mira.noise", text="NoiseDeform", icon="RNDCURVE")
            row.separator()

            row.operator("mira.deformer", text="Deformer")
            row.operator("mira.linear_deformer", text="LinearDeformer", icon="OUTLINER_OB_MESH")
            row.prop(context.scene.mi_ldeformer_settings, "manual_update", text='ManualUpdate')

            box.separator()
            
            
# --------------------------------------------------


        if mt.display_mira_arc:

            box = layout.box()
            row = box.row(align=True)
            row.prop(mt, "display_mira_arc", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(align=True)
            row.prop(mt, "display_mira_arc", text="", icon='TRIA_RIGHT')

        row.label("Arc")

        sub = row.row(1)
        sub.scale_x = 1.7
        sub.operator("mira.make_arc", text="", icon ="SPHERECURVE")
        row.operator("mira.make_arc_get_axis", text="", icon ="FACESEL")
        
        ###space###
        if mt.display_mira_arc:
            ###space###

            box = layout.box().column(align=True)

            row = box.row(align=True)
            row.label("Arc Creation")

            box.separator()

            row = box.row(align=True)
            row.operator("mira.make_arc", text="MakeArc")
            row.operator("mira.make_arc_get_axis", text="GetAxis")

            box.separator()

            row = box.column()
            row.prop(context.scene.mi_makearc_settings, "arc_axis", text="ArcAxis")

            box.separator()

            
# --------------------------------------------------

        #col = layout.column(align = True)
        if mt.display_mira_guide:

            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_guide", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_guide", text="", icon='TRIA_RIGHT')

        row.label("CGuide")

        row.prop(context.scene.mi_curguide_settings, "points_number", text='')

        sub = row.row(1)
        sub.scale_x = 0.15
        sub.prop(context.scene.mi_curguide_settings, "deform_type", text='', icon="COLLAPSEMENU")
        row.operator("mira.curve_guide", text='', icon="RNA")

        ###space###
        if mt.display_mira_guide:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column(align=True)
            row.operator("mira.curve_guide", text="CurveGuide", icon="RNA")
            row.prop(context.scene.mi_curguide_settings, "points_number", text='LoopSpread')

            row = col_top.column(align=True)
            row.prop(context.scene.mi_curguide_settings, "deform_type", text='DeformType')

            box.separator()


# --------------------------------------------------

        #col = layout.column(align = True)
        if mt.display_mira_stretch:

            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_stretch", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_stretch", text="", icon='TRIA_RIGHT')

        row.label("CStretch")
        sub = row.row(1)
        sub.scale_x = 0.5
        sub.prop(context.scene.mi_cur_stretch_settings, "points_number", text='')
        row.operator("mira.curve_stretch", text="", icon="STYLUS_PRESSURE")

        ###space###
        if mt.display_mira_stretch:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column(align=True)
            row.operator("mira.curve_stretch", text="CurveStretch", icon="STYLUS_PRESSURE")
            row.prop(context.scene.mi_cur_stretch_settings, "points_number", text='PointsNumber')
            
            box.separator()


# --------------------------------------------------

        if mt.display_mira_settings:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_settings", text="", icon='TRIA_DOWN')

        else:
            box = layout.box()
            row = box.row(1)
            row.prop(mt, "display_mira_settings", text="", icon='TRIA_RIGHT')

        row.label("Settings")
        row.prop(context.scene.mi_settings, "convert_instances", text='', icon="BOIDS")
        sub = row.row(1)
        sub.scale_x = 0.15
        sub.prop(context.scene.mi_settings, "snap_objects", text='', icon="VISIBLE_IPO_ON")
        row.prop(context.scene.mi_settings, "surface_snap", text='', icon="SNAP_SURFACE")

        ###space###
        if mt.display_mira_settings:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column()
            row.prop(context.scene.mi_settings, "surface_snap", text='Surface Snapping')
            row.prop(context.scene.mi_settings, "convert_instances", text='Convert Instances')
            row.prop(context.scene.mi_settings, "snap_objects", text='SnapObjects')

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column()
            row.prop(context.scene.mi_settings, "spread_mode", text='Spread')
            row.prop(context.scene.mi_settings, "curve_resolution", text='Resolution')

            row.prop(context.scene.mi_settings, "draw_handlers", text='Handlers')
            row.operator("mira.curve_test", text="Curve Test")
            
            box.separator()


class MIRA_Object_Panel(bpy.types.Panel):
    bl_label = "Wrap"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_context = "objectmode"
    bl_category = 'Mira'

    def draw(self, context):

        mt = context.window_manager.mirawindow
        layout = self.layout
        mi_settings = context.scene.mi_settings

        if mt.display_mira_wrap:

            box = layout.box()
            row = box.row(align=True)
            row.prop(mt, "display_mira_wrap", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(align=True)
            row.prop(mt, "display_mira_wrap", text="", icon='TRIA_RIGHT')

        row.label("Wrap")

        #sub = row.row(1)
        #sub.scale_x = 1.7
        row.operator("mira.wrap_object", text="", icon ="MOD_LATTICE")
        row.operator("mira.wrap_scale", text="", icon ="MAN_SCALE")
        row.operator("mira.wrap_master", text="", icon ="MOD_SHRINKWRAP")

        ###space###    
        if mt.display_mira_wrap:
            ###space###

            box = layout.box().column(align=True)

            col_top = box.column(align=True)
            row = col_top.column()

            row.operator("mira.wrap_object", text="WrapObject")
            row.operator("mira.wrap_scale", text="WrapScale")
            row.operator("mira.wrap_master", text="WrapMaster")


# PRIMITIVES MENU
def mifth_prim_menu(self, context):
    #self.layout.operator_context = 'INVOKE_REGION_WIN'

    self.layout.menu("MI_Prims_Menu",
                     text="MiraPrimitives", icon="PLUGIN")

    self.layout.separator()


class MI_PrimsMenu(bpy.types.Menu):
    # Define the "Torus Objects" menu
    bl_idname = "MI_Prims_Menu"
    bl_label = "Primitives Menu"

    def draw(self, context):
        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraPlane", icon='MESH_PLANE')
        op.prim_type = 'Plane'
        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraCube", icon='MESH_CUBE')
        op.prim_type = 'Cube'
        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraCircle", icon='MESH_CIRCLE')
        op.prim_type = 'Circle'
        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraSphere", icon='MESH_UVSPHERE')
        op.prim_type = 'Sphere'
        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraCylinder", icon='MESH_CYLINDER')
        op.prim_type = 'Cylinder'
        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraCapsule", icon='MESH_CAPSULE')
        op.prim_type = 'Capsule'
        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraCone", icon='MESH_CONE')
        op.prim_type = 'Cone'
        self.layout.separator()

        op = self.layout.operator("mi_prims.mifth_make_prim", text="MiraClone", icon='MESH_MONKEY')
        op.prim_type = 'Clone'
