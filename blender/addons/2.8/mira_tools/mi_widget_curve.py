import gpu
from gpu_extras.batch import batch_for_shader

from bpy.props import *

from . import mi_utils_base as ut_base


shader3d = gpu.shader.from_builtin('UNIFORM_COLOR')
shader2d = gpu.shader.from_builtin('UNIFORM_COLOR')


def draw_2d_point(point_x, point_y, p_size=4, p_col=(1.0,1.0,1.0,1.0)):
    gpu.state.point_size_set(p_size)

    coords = ((point_x, point_y), (point_x, point_y))
    batch = batch_for_shader(shader2d, 'POINTS', {"pos": coords})
    shader2d.bind()
    shader2d.uniform_float("color", (p_col[0], p_col[1], p_col[2], p_col[3]))
    batch.draw(shader2d)


def draw_3d_polyline(points, p_size, l_size, p_col, x_ray):

    gpu.state.line_width_set(l_size)

    coords = [(point[0], point[1], point[2]) for point in points]
    batch = batch_for_shader(shader3d, 'LINE_STRIP', {"pos": coords})
    shader3d.bind()
    shader3d.uniform_float("color", (p_col[0], p_col[1], p_col[2], p_col[3]))
    batch.draw(shader3d)

