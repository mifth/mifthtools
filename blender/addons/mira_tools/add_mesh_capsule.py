import bpy
from bpy.types import Operator
from bpy.props import FloatProperty
from bpy.props import IntProperty
from bpy_extras.object_utils import object_data_add
from mathutils import Vector
from math import cos
from math import degrees
from math import radians
from math import sin

# "The author is David Ludwig. The code was taken from here https://www.youtube.com/watch?v=O-Yhxhjx_VY "

def add_capsule(length, radius, rings, segments, context):

	topRings = []
	bottomRings = []
	topCap = []
	bottomCap = []

	vertId = 0

	for j in range(0, rings + 1):

		if j == rings:
			
			topVertex = Vector((0, 0, ((length / 2) + radius)))
			bottomVertex = Vector((0, 0, -((length / 2) + radius)))

			topCap.append(topVertex)
			bottomCap.append(bottomVertex)
		else:

			heightAngle = radians((90 / rings) * (j + 1))

			topRing = []
			bottomRing = []

			for i in range(0, segments):

				zAngle = radians((360 / segments) * i)

				x = radius * cos(zAngle) * sin(heightAngle)
				y = radius * sin(zAngle) * sin(heightAngle)
				z = radius * cos(heightAngle)

				topVertex = Vector((x, y, z + (length / 2)))
				bottomVertex = Vector((x, y, -(z + (length / 2))))

				topRing.append(vertId)
				bottomRing.append(vertId + ((rings * segments) + 1))
				topCap.append(topVertex)
				bottomCap.append(bottomVertex)

				vertId += 1

			topRings.append(topRing)
			bottomRings.append(bottomRing)

	verts = topCap + bottomCap

	faces = []

	ringIndex = len(topRings) - 1
	while ringIndex > 0:
		
		topRing = topRings[ringIndex]
		topNextRing = topRings[ringIndex - 1]

		bottomRing = bottomRings[ringIndex]
		bottomNextRing = bottomRings[ringIndex - 1]
		
		for i in range(0, segments):

			index1 = i
			index2 = 0 if i + 1 == segments else i + 1

			topCapFace = [topRing[index1], topRing[index2], topNextRing[index2], topNextRing[index1]]
			bottomCapFace = [bottomRing[index2], bottomRing[index1], bottomNextRing[index1], bottomNextRing[index2]]
			faces.append(topCapFace)
			faces.append(bottomCapFace)

		ringIndex -= 1

	topRing = topRings[rings - 1]
	bottomRing = bottomRings[rings - 1]

	topCapRing = topRings[0]
	bottomCapRing = bottomRings[0]

	topCapFaces = []
	bottomCapFaces = []

	for i in range(0, segments):
		
		index1 = i
		index2 = 0 if i + 1 == segments else i + 1

		bodyFace = [topRing[index2], topRing[index1], bottomRing[index1], bottomRing[index2]]
		topCapFace = [topCapRing[index1], topCapRing[index2], rings * segments]
		bottomCapFace = [bottomCapRing[index2], bottomCapRing[index1], ((rings * segments) * 2) + 1]

		faces.append(bodyFace)
		topCapFaces.append(topCapFace)
		bottomCapFaces.append(bottomCapFace)

	faces += topCapFaces + bottomCapFaces

	mesh = bpy.data.meshes.new(name="Capsule")
	mesh.from_pydata(verts, [], faces)
	mesh.update()
	
	return object_data_add(context, mesh, operator=None)
