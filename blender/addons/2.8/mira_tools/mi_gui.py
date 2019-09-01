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


# DROPDOWN PROPERTIES #
class DropdownMiraToolProps(bpy.types.PropertyGroup):
    """
    Fake module like class
    bpy.context.window_manager.mirawindow
    """
    display_mira_arc: bpy.props.BoolProperty(name="Make Arc", description="UI Make Arc Tools", default=False)
    display_mira_stretch: bpy.props.BoolProperty(name="Curve Stretch", description="UI Curve Stretch Tools", default=False)
    display_mira_sface: bpy.props.BoolProperty(name="Curve Surface", description="UI Curve Surface Tools", default=False)
    display_mira_guide: bpy.props.BoolProperty(name="Curve Guide", description="UI Curve Guide Tools", default=False)
    display_mira_modify: bpy.props.BoolProperty(name="Modify Tools", description="UI Modify Tools", default=False)
    display_mira_deform: bpy.props.BoolProperty(name="Deform Tools", description="UI Deform Tools", default=False)
    display_mira_modify: bpy.props.BoolProperty(name="Modify", description="UI Modify", default=False)
    display_mira_settings: bpy.props.BoolProperty(name="Settings", description="UI Settings", default=False)

    display_mira_wrap: bpy.props.BoolProperty(name="Wrap", description="UI Wrap", default=False)
    display_mira_obj_retopology: bpy.props.BoolProperty(name="Object Retopology", description="UI Object Retopology", default=False)



# PANEL LAYOUT DROPDOWN #
class MI_PT_Panel(bpy.types.Panel):
    bl_idname = "MI_PT_Panel"
    bl_label = "Mira Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "mesh_edit"
    bl_category = 'Mira'

    def draw(self, context):
        mt = context.window_manager.mirawindow
        layout = self.layout
        #layout = self.layout.column(align=True)
        layout.scale_y = 1.1

# MODIFY
# --------------------------------------------------

        col = layout.column(align = True)
        box = col.box().column(align=True)
        if mt.display_mira_modify:
            row = box.row(align=True)
            row.prop(mt, "display_mira_modify", text="", icon='TRIA_DOWN')

        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_modify", text="", icon='TRIA_RIGHT')

        row.label(text="Modify")
        if context.scene.mi_settings.surface_snap is False:
            row.prop(context.scene.mi_extrude_settings, "do_symmetry", text='', icon="MOD_MIRROR")
            if context.scene.mi_extrude_settings.do_symmetry:
                sub = row.row(align=True)
                sub.scale_x = 0.35
                sub.prop(context.scene.mi_extrude_settings, "symmetry_axys", text='')

        row.operator("mira.draw_extrude", text="", icon="VPAINT_HLT")
        row.operator("mira.unbevel", text="", icon="DRIVER_ROTATIONAL_DIFFERENCE")

        if mt.display_mira_modify:     

            box.separator()   
            box = col.box().column(align=True)
            box.separator()        
                     
            row = box.column()
            row.operator("mira.simple_extrude", text="Simple Extrude", icon="VPAINT_HLT")
         
            box.separator()   
            box = col.box().column(align=True)
            box.separator()   
            
            row = box.column()
            row.operator("mira.draw_extrude", text="Draw Extrude", icon="VPAINT_HLT")
            row.prop(context.scene.mi_extrude_settings, "extrude_step_type", text='Step')

            if context.scene.mi_extrude_settings.extrude_step_type == 'Asolute':
                row.prop(context.scene.mi_extrude_settings, "absolute_extrude_step", text='')
            else:
                row.prop(context.scene.mi_extrude_settings, "relative_extrude_step", text='')

            box.separator()   

            row = box.row()
            if context.scene.mi_settings.surface_snap is False:
                row.label(text='', icon="MOD_MIRROR")
                row.prop(context.scene.mi_extrude_settings, "do_symmetry", text='Symmetry')
                
                row = box.column()
                if context.scene.mi_extrude_settings.do_symmetry:
                    row.prop(context.scene.mi_extrude_settings, "symmetry_axys", text='Axys')

            box.separator()           
            box = col.box().column(align=True)
            box.separator()            
            
            row = box.column()
            row.operator("mira.unbevel", text="Unbevel", icon="DRIVER_ROTATIONAL_DIFFERENCE")

            box.separator()


# RETOPO
# --------------------------------------------------

        col = layout.column(align = True)
        box = col.box().column(align=True)
        if mt.display_mira_sface:
            row = box.row(align=True)
            row.prop(mt, "display_mira_sface", text="", icon='TRIA_DOWN')
        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_sface", text="", icon='TRIA_RIGHT')

        row.label(text="Retopo")

        row.operator("mira.snap_points", text="", icon="MOD_VERTEX_WEIGHT")
        row.operator("mira.poly_loop", text="", icon="OUTLINER_DATA_GP_LAYER")
        sub = row.row(align=True)
        sub.scale_x = 0.35
        sub.prop(context.scene.mi_cur_surfs_settings, "spread_loops_type", text='', icon="COLLAPSEMENU")
        row.operator("mira.curve_surfaces", text="", icon="SURFACE_NCURVE")

        if mt.display_mira_sface:
            
            box.separator()   
            box = col.box().column(align=True)
            box.separator()   

            row = box.column(align=True)
            row.operator("mira.poly_loop", text="Poly Loop", icon="OUTLINER_DATA_GP_LAYER")

            box.separator()   
            box = col.box().column(align=True)
            box.separator()  

            row = box.column()
            row.operator("mira.curve_surfaces", text="CurveSurfaces", icon="SURFACE_NCURVE")
            row.prop(context.scene.mi_cur_surfs_settings, "spread_loops_type", text='Points')

            box.separator()   
            box = col.box().column(align=True)
            box.separator()  

            row = box.column()
            row.operator("mira.snap_points", text="Snap Points", icon="MOD_VERTEX_WEIGHT")

            box.separator()  
            
# DEFORM           
# --------------------------------------------------

        col = layout.column(align = True)
        box = col.box().column(align=True)
        if mt.display_mira_deform:
            row = box.row(align=True)
            row.prop(mt, "display_mira_deform", text="", icon='TRIA_DOWN')
        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_deform", text="", icon='TRIA_RIGHT')

        row.label(text="Deform")
        row.operator("mira.noise", text="", icon="RNDCURVE")
        row.prop(context.scene.mi_ldeformer_settings, "manual_update", text='', icon="DISK_DRIVE")
        row.operator("mira.linear_deformer", text="", icon="OUTLINER_OB_MESH")

        if mt.display_mira_deform:

            box.separator()   
            box = col.box().column(align=True)
            box.separator()     

            row = box.column()
            row.operator("mira.noise", text="NoiseDeform", icon="RNDCURVE")
            row.operator("mira.deformer", text="Deformer")
          
            box.separator()   
            box = col.box().column(align=True)
            box.separator()  

            row.operator("mira.linear_deformer", text="LinearDeformer", icon="OUTLINER_OB_MESH")
            row.prop(context.scene.mi_ldeformer_settings, "manual_update", text='ManualUpdate')

            box.separator()
            

# ARC            
# --------------------------------------------------

        col = layout.column(align = True)
        box = col.box().column(align=True)
        if mt.display_mira_arc:
            row = box.row(align=True)
            row.prop(mt, "display_mira_arc", text="", icon='TRIA_DOWN')
        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_arc", text="", icon='TRIA_RIGHT')

        row.label(text="Arc")
        row.operator("mira.make_arc", text="", icon ="SPHERECURVE")
        row.operator("mira.make_arc_get_axis", text="", icon ="FACESEL")

        if mt.display_mira_arc:

            box.separator()   
            box = col.box().column(align=True)
            box.separator()   

            row = box.row(align=True)
            row.label(text="Arc Creation")

            box.separator()

            row = box.column(align=True)
            row.operator("mira.make_arc", text="Make Arc", icon ="SPHERECURVE")
            row.operator("mira.make_arc_get_axis", text="Get Axis", icon ="FACESEL")

            box.separator()

            row = box.column()
            row.prop(context.scene.mi_makearc_settings, "arc_axis", text="ArcAxis")

            box.separator()



# CURVE GUIDE            
# --------------------------------------------------

        col = layout.column(align = True)
        box = col.box().column(align=True)
        if mt.display_mira_guide:
            row = box.row(align=True)
            row.prop(mt, "display_mira_guide", text="", icon='TRIA_DOWN')
        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_guide", text="", icon='TRIA_RIGHT')

        row.label(text="CGuide")

        sub = row.row(align=True)
        sub.scale_x = 0.5
        sub.prop(context.scene.mi_curguide_settings, "points_number", text='')
       
        sub1 = row.row(align=True)
        sub1.scale_x = 0.35
        sub1.prop(context.scene.mi_curguide_settings, "deform_type", text='', icon="COLLAPSEMENU")
        row.operator("mira.curve_guide", text='', icon="RNA")

        if mt.display_mira_guide:

            box.separator()   
            box = col.box().column(align=True)
            box.separator() 

            row = box.column(align=True)
            row.operator("mira.curve_guide", text="CurveGuide", icon="RNA")
            row.prop(context.scene.mi_curguide_settings, "points_number", text='LoopSpread')
         
            box.separator()            

            row = box.row()                      
            row.label(text='DeformType')                      
            row.prop(context.scene.mi_curguide_settings, "deform_type", text='')

            box.separator()



# CURVE STRETCH
# --------------------------------------------------

        col = layout.column(align = True)
        box = col.box().column(align=True)
        if mt.display_mira_stretch:
            row = box.row(align=True)
            row.prop(mt, "display_mira_stretch", text="", icon='TRIA_DOWN')
        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_stretch", text="", icon='TRIA_RIGHT')

        row.label(text="CStretch")
        sub = row.row(align=True)
        sub.scale_x = 0.5
        sub.prop(context.scene.mi_cur_stretch_settings, "points_number", text='')
        row.operator("mira.curve_stretch", text="", icon="STYLUS_PRESSURE")

        if mt.display_mira_stretch:

            box.separator()   
            box = col.box().column(align=True)
            box.separator()   

            row = box.column(align=True)
            row.operator("mira.curve_stretch", text="CurveStretch", icon="STYLUS_PRESSURE")
            row.prop(context.scene.mi_cur_stretch_settings, "points_number", text='PointsNumber')
            
            box.separator()



# SETTINGS
# --------------------------------------------------
    
        col = layout.column(align = True)
        box = col.box().column(align=True)
        if mt.display_mira_settings:
            row = box.row(align=True)
            row.prop(mt, "display_mira_settings", text="", icon='TRIA_DOWN')

        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_settings", text="", icon='TRIA_RIGHT')

        row.label(text="Settings")
        row.prop(context.scene.mi_settings, "convert_instances", text='', icon="BOIDS")
        sub = row.row(align=True)
        sub.scale_x = 0.35
        sub.prop(context.scene.mi_settings, "snap_objects", text='', icon="HIDE_OFF")
        row.prop(context.scene.mi_settings, "surface_snap", text='', icon="SNAP_ON")

        if mt.display_mira_settings:

            box.separator()   
            box = col.box().column(align=True)
            box.separator()   

            row = box.row()
            row.label(text='', icon="SNAP_ON")
            row.prop(context.scene.mi_settings, "surface_snap", text='Surface Snapping')

            row = box.row()
            row.label(text='', icon="BOIDS")
            row.prop(context.scene.mi_settings, "convert_instances", text='Convert Instances')

            row = box.row()
            row.label(text='', icon="MOD_VERTEX_WEIGHT")
            row.prop(context.scene.mi_settings, "snap_points", text='Snap Points')

            row = box.row()
            row.label(text='SnapObjects')
            row.prop(context.scene.mi_settings, "snap_objects", text='')

            box.separator()   
            box = col.box().column(align=True)
            box.separator()   

            row = box.column()
            row.prop(context.scene.mi_settings, "spread_mode", text='Spread')
            row.prop(context.scene.mi_settings, "curve_resolution", text='Resolution')

            row.prop(context.scene.mi_settings, "draw_handlers", text='Handlers')
            row.operator("mira.curve_test", text="Curve Test")
            
            box.separator()




class MI_PT_Object_Panel(bpy.types.Panel):
    bl_idname = "MI_PT_Object_Panel"
    bl_label = "Mira Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_context = "objectmode"
    bl_category = 'Mira'

    def draw(self, context):

        mt = context.window_manager.mirawindow
        layout = self.layout
        #layout = self.layout.column(align=True)
        layout.scale_y = 1.1
        mi_settings = context.scene.mi_settings


# WRAP
# --------------------------------------------------

        col = layout.column(align=True) 
        box = col.box().column(align=True)
        if mt.display_mira_wrap:
            row = box.row(align=True)
            row.prop(mt, "display_mira_wrap", text="", icon='TRIA_DOWN')
        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_wrap", text="", icon='TRIA_RIGHT')

        row.label(text="Wrap")

        row.operator("mira.wrap_object", text="", icon ="MOD_LATTICE")
        row.operator("mira.wrap_scale", text="", icon ="KEYFRAME")
        row.operator("mira.wrap_master", text="", icon ="MOD_SHRINKWRAP")
 
        if mt.display_mira_wrap:          

            box.separator()   
            box = col.box().column(align=True)
            box.separator()    
          
            row = box.column(align=True)
            row.operator("mira.wrap_object", text="Wrap Object", icon ="MOD_LATTICE")
            row.operator("mira.wrap_scale", text="Wrap Scale", icon ="KEYFRAME")
            row.operator("mira.wrap_master", text="Wrap Master", icon ="MOD_SHRINKWRAP")
            
            box.separator()  



# OBJECT RETOPOLOGY
# --------------------------------------------------
        
        col = layout.column(align=True) 
        box = col.box().column(align=True)
        if mt.display_mira_obj_retopology:
            row = box.row(align=True)
            row.prop(mt, "display_mira_obj_retopology", text="", icon='TRIA_DOWN')
        else:
            row = box.row(align=True)
            row.prop(mt, "display_mira_obj_retopology", text="", icon='TRIA_RIGHT')

        row.label(text="Retopo")
        row.operator("mira.retopo_loops", text="", icon ="XRAY")
  
        if mt.display_mira_obj_retopology:          

            box.separator()   
            box = col.box().column(align=True)
            box.separator()               
            
            row = box.column()
            row.operator("mira.retopo_loops", text="Retopo Loops", icon ="XRAY")

            box.separator()  
           


# PRIMITIVES MENU
def mifth_prim_menu(self, context):
    #self.layout.operator_context = 'INVOKE_REGION_WIN'

    self.layout.menu("PRISM_MT_Menu",
                     text="MiraPrimitives", icon="PLUGIN")

    self.layout.separator()


class PRISM_MT_Menu(bpy.types.Menu):
    # Define the "Torus Objects" menu
    bl_idname = "PRISM_MT_Menu"
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
