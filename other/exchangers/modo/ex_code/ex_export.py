# python

import lx
import modo
import os


def select_items(scene, items_names):
	for item in scene.items(itype='locator', superType=True):
		if item.name in items_names and item.selected is False:
			item.select(False)


def parse_item(item, orig_item_names):
	if item.name not in orig_item_names:
		orig_name = item.name
		orig_item_names.append(orig_name)


current_scene = modo.Scene()
if current_scene.selected:

	current_scene_2 = lx.eval('scene.set ?')
	orig_item_names = []
	item_parents = []

	#  get parents of selected items
	for item in current_scene.items(itype='locator', superType=True):
		if item.selected is True:
			parent_name = None

			if item.parent:
				parent_name = item.parent.name

			item_parents.append((item.name, parent_name))

	#  get list of selected items
	for item in current_scene.items(itype='locator', superType=True):

		if item.selected is True:
			item_parents.append

			#  change itm's name
			parse_item(item, orig_item_names)
			#idx_name += 1

			#  parse item's children
			for item_2 in item.children(recursive=True, itemType=None):
				parse_item(item_2, orig_item_names)
				#idx_name += 1

	#  new scene
	lx.eval('scene.new')
	new_scene = modo.Scene()
	new_scene_2 = lx.eval('scene.set ?')

	for item in new_scene.items(itype='locator', superType=True):
		new_scene.removeItems(item)

	lx.eval('scene.set %s '  % current_scene_2)

	# copy to new scene
	select_items(current_scene, orig_item_names)
	lx.eval('layer.import %s {} move:false position:0' % new_scene_2)
	lx.eval('scene.set %s ' % new_scene_2)

	#  save scene
	exp_path = lx.eval('user.value exPath ?').replace("\\","/")
	if exp_path.endswith(os.sep) is False:
		exp_path += os.sep
	exp_path += 'exchange.fbx'
	lx.eval('scene.saveAs %s fbx true' % exp_path)

	# close temp scene
	lx.eval('scene.set %s '  % new_scene_2)
	lx.eval('!scene.close')
	lx.eval('scene.set %s '  % current_scene_2)
	select_items(current_scene, orig_item_names)

	#  deselect weird selected items
	for item in current_scene.items(itype='locator', superType=True):
		if item.name not in orig_item_names:
			item.deselect()

	#  clear lists
	new_item_names = None
	orig_item_names = None
	item_parents  = None

