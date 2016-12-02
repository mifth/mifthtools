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

    display_mirastretch = bpy.props.BoolProperty(name="Curve Stretch", description="UI Curve Stretch Tools", default=False)
    display_mirasface = bpy.props.BoolProperty(name="Curve Surface", description="UI Curve Surface Tools", default=False)
    display_miraguide = bpy.props.BoolProperty(name="Curve Guide", description="UI Curve Guide Tools", default=False)
    display_miramodify = bpy.props.BoolProperty(name="Modify Tools", description="UI Modify Tools", default=False)
    display_miradeform = bpy.props.BoolProperty(name="Deform Tools", description="UI Deform Tools", default=False)
    display_miraextrude = bpy.props.BoolProperty(name="Draw Extrude", description="UI Draw Extrude", default=False)
    display_mirasettings = bpy.props.BoolProperty(name="Settings", description="UI Settings", default=False)


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
        lt = context.window_manager.mirawindow
        layout = self.layout
        #mi_settings = context.scene.mi_settings

# --------------------------------------------------

        #col = layout.column(align = True)
        if lt.display_miraextrude:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_miraextrude", text="", icon='TRIA_DOWN')

        else:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_miraextrude", text="", icon='TRIA_RIGHT')

        row.label("Extrude")
        if context.scene.mi_settings.surface_snap is False:
            row.prop(context.scene.mi_extrude_settings, "do_symmetry", text='', icon="UV_ISLANDSEL")
            if context.scene.mi_extrude_settings.do_symmetry:
                sub = row.row(1)
                sub.scale_x = 0.15
                sub.prop(context.scene.mi_extrude_settings, "symmetry_axys", text='')

        row.operator("mira.draw_extrude", text="", icon="VPAINT_HLT")

        ###space###
        if lt.display_miraextrude:
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

# --------------------------------------------------

        #col = layout.column(align = True)
        if lt.display_mirasface:

            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_mirasface", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_mirasface", text="", icon='TRIA_RIGHT')

        row.label("Surfaces")

        row.operator("mira.poly_loop", text="", icon="MESH_GRID")
        sub = row.row(1)
        sub.scale_x = 0.15
        sub.prop(context.scene.mi_cur_surfs_settings, "spread_loops_type", text='', icon="COLLAPSEMENU")
        row.operator("mira.curve_surfaces", text="", icon="SURFACE_NCURVE")

        ###space###
        if lt.display_mirasface:
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

# --------------------------------------------------

        #col = layout.column(align = True)
        if lt.display_miradeform:

            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_miradeform", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_miradeform", text="", icon='TRIA_RIGHT')

        row.label("Deform")
        row.operator("mira.noise", text="", icon="RNDCURVE")
        row.prop(context.scene.mi_ldeformer_settings, "manual_update", text='', icon="DISK_DRIVE")
        row.operator("mira.linear_deformer", text="", icon="OUTLINER_OB_MESH")

        ###space###
        if lt.display_miradeform:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column()
            row.operator("mira.noise", text="NoiseDeform", icon="RNDCURVE")
            row.operator("mira.deformer", text="Deformer")

            row.operator("mira.linear_deformer", text="LinearDeformer", icon="OUTLINER_OB_MESH")
            row.prop(context.scene.mi_ldeformer_settings, "manual_update", text='ManualUpdate')

            row.operator("mira.make_arc", text="MakeArc")

# --------------------------------------------------

        #col = layout.column(align = True)
        if lt.display_miraguide:

            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_miraguide", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_miraguide", text="", icon='TRIA_RIGHT')

        row.label("CGuide")

        row.prop(context.scene.mi_curguide_settings, "points_number", text='')

        sub = row.row(1)
        sub.scale_x = 0.15
        sub.prop(context.scene.mi_curguide_settings, "deform_type", text='', icon="COLLAPSEMENU")
        row.operator("mira.curve_guide", text='', icon="RNA")

        ###space###
        if lt.display_miraguide:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column(align=True)
            row.operator("mira.curve_guide", text="CurveGuide", icon="RNA")
            row.prop(context.scene.mi_curguide_settings, "points_number", text='LoopSpread')

            row = col_top.column(align=True)
            row.prop(context.scene.mi_curguide_settings, "deform_type", text='DeformType')

# --------------------------------------------------

        #col = layout.column(align = True)
        if lt.display_mirastretch:

            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_mirastretch", text="", icon='TRIA_DOWN')
        else:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_mirastretch", text="", icon='TRIA_RIGHT')

        row.label("CStretch")
        sub = row.row(1)
        sub.scale_x = 0.5
        sub.prop(context.scene.mi_cur_stretch_settings, "points_number", text='')
        row.operator("mira.curve_stretch", text="", icon="STYLUS_PRESSURE")

        ###space###
        if lt.display_mirastretch:
            ###space###

            col = layout.column(align=True)
            box = col.column(align=True).box().column()
            col_top = box.column(align=True)

            row = col_top.column(align=True)
            row.operator("mira.curve_stretch", text="CurveStretch", icon="STYLUS_PRESSURE")
            row.prop(context.scene.mi_cur_stretch_settings, "points_number", text='PointsNumber')

# --------------------------------------------------

        if lt.display_mirasettings:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_mirasettings", text="", icon='TRIA_DOWN')

        else:
            box = layout.box()
            row = box.row(1)
            row.prop(lt, "display_mirasettings", text="", icon='TRIA_RIGHT')

        row.label("Settings")
        row.prop(context.scene.mi_settings, "convert_instances", text='', icon="BOIDS")
        sub = row.row(1)
        sub.scale_x = 0.15
        sub.prop(context.scene.mi_settings, "snap_objects", text='', icon="VISIBLE_IPO_ON")
        row.prop(context.scene.mi_settings, "surface_snap", text='', icon="SNAP_SURFACE")

        ###space###
        if lt.display_mirasettings:
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
