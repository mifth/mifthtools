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
import bgl
import blf

from bpy.props import *
import math
import mathutils as mathu
import random
from mathutils import Vector


# Curve Colors
cur_point_base = (0.5, 0.8, 1.0, 1.0)
cur_point_selected = (0.9, 0.5, 0.1, 1.0)
cur_point_active = (0.9, 0.7, 0.3, 1.0)

cur_point_closed_start = (0.7, 0.4, 0.9, 1.0)
cur_point_closed_end = (0.3, 0.4, 0.9, 1.0)

cur_line_base = (0.5, 0.8, 0.9, 1.0)

cur_handle_1_base = (0.0, 0.5, 1.0, 1.0)
cur_handle_2_base = (1.0, 0.5, 0.0, 1.0)


# Draw Extrude Colors
dre_point_base = (0.5, 0.8, 1.0, 1.0)

# PolyLoop colors
pl_point_col = (0.95, 0.7, 1.0, 1.0)