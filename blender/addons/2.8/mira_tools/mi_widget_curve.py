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


import gpu
from gpu_extras.batch import batch_for_shader

from bpy.props import *

from . import mi_utils_base as ut_base


shader3d = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
shader2d = gpu.shader.from_builtin('2D_UNIFORM_COLOR')


def draw_2d_point(point_x, point_y, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
    gpu.state.point_size_set(p_size)

    coords = ((point_x, point_y), (point_x, point_y))
    batch = batch_for_shader(shader2d, 'POINTS', {"pos": coords})
    shader2d.bind()
    shader2d.uniform_float("color", (p_col[0], p_col[1], p_col[2], p_col[3]))
    batch.draw(shader2d)


def draw_3d_polyline(points, p_size, l_size, p_col, x_ray):

    gpu.state.line_width_set(l_size)

    # if x_ray is True:
    #     # bgl.glDisable(bgl.GL_DEPTH_TEST)
    #     gpu.state.depth_test_set("NONE")

    coords = [(point[0], point[1], point[2]) for point in points]
    batch = batch_for_shader(shader3d, 'LINE_STRIP', {"pos": coords})
    shader3d.bind()
    shader3d.uniform_float("color", (p_col[0], p_col[1], p_col[2], p_col[3]))
    batch.draw(shader3d)

