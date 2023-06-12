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


from bpy.props import *
from bpy.types import Operator, AddonPreferences

import gpu
from gpu_extras import presets
from gpu_extras.batch import batch_for_shader


shader3d = gpu.shader.from_builtin('UNIFORM_COLOR')
shader2d = gpu.shader.from_builtin('UNIFORM_COLOR')


def draw_circle_select(m_coords, radius = 16, p_col = (0.7,0.8,1.0,0.6), enabled = False, sub = False):
    if(enabled):
        f_col = p_col

        if sub:
            f_col = (1.0, 0.5, 0.4, 0.6)

        gpu.state.line_width_set(1)

        radius = int(radius)

        presets.draw_circle_2d(m_coords, (f_col[0], f_col[1], f_col[2], f_col[3]), radius, segments=64)


def draw_box_select(anchor, m_coords, region,  p_col = (0.7,0.8,1.0,0.6), enabled = False, dragging = False, sub = False):

    if enabled:
        f_col = p_col
        if sub:
            f_col = (1.0, 0.5, 0.4, 0.6)

        point_x = m_coords[0]
        point_y = m_coords[1]

        coords = []

        coords.append( (point_x, 0) )
        coords.append( (point_x, region.height) )

        coords.append( (0, point_y) )
        coords.append( (region.width, point_y) )

        gpu.state.line_width_set(1)

        batch = batch_for_shader(shader2d, 'LINES', {"pos": coords})
        shader2d.bind()
        shader2d.uniform_float("color", (f_col[0], f_col[1], f_col[2], f_col[3]))
        batch.draw(shader2d)


        if dragging:
            point_x = m_coords[0]
            point_y = m_coords[1]

            anc_x = anchor[0]
            anc_y = anchor[1]

            coords_2 = []

            coords_2.append( (anc_x, anc_y) )
            coords_2.append( (point_x, anc_y) )
            coords_2.append( (point_x, point_y) )
            coords_2.append( (anc_x, point_y) )

            batch = batch_for_shader(shader2d, 'LINE_LOOP', {"pos": coords_2})
            shader2d.bind()
            shader2d.uniform_float("color", (f_col[0], f_col[1], f_col[2], f_col[3]))
            batch.draw(shader2d)

            coords_3 = []

            coords_3.append( (anc_x, anc_y) )
            coords_3.append( (point_x, anc_y) )
            coords_3.append( (point_x, point_y) )
            coords_3.append( (anc_x, point_y) )

            batch = batch_for_shader(shader2d, 'LINE_STRIP', {"pos": coords_3})
            shader2d.bind()
            shader2d.uniform_float("color", (f_col[0], f_col[1], f_col[2], f_col[3]))
            batch.draw(shader2d)
