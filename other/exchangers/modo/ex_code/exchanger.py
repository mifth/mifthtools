# python

import lx
import modo
import os


def select_items(scene, items_names):
	for item in scene.items(itype='locator', superType=True):
		if item.name in items_names and item.selected is False:
			item.select(False)


def parse_rename_item(item, orig_item_names, new_item_names, idx_name):
	if item.name not in new_item_names:
		orig_name = item.name
		orig_item_names.append(orig_name)
	
		new_name = 'temp_temp_really_temp_name_' + str(idx_name)
		item.name = new_name
		new_item_names.append(new_name)

class ExExport():
	current_scene = modo.Scene()
	current_scene_2 = lx.eval('scene.set ?')
	idx_name = 1
	new_item_names = []
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
			parse_rename_item(item, orig_item_names, new_item_names, idx_name)
			idx_name += 1

			#  parse item's children
			for item_2 in item.children(recursive=True, itemType=None):
				parse_rename_item(item_2, orig_item_names, new_item_names, idx_name)
				idx_name += 1

	#  new scene
	lx.eval('scene.new')
	new_scene = modo.Scene()
	new_scene_2 = lx.eval('scene.set ?')

	for item in new_scene.items(itype='locator', superType=True):
		new_scene.removeItems(item)

	lx.eval('scene.set %s '  % current_scene_2)

	select_items(current_scene, new_item_names)
	lx.eval('layer.import %s {} move:true position:0' % new_scene_2)
	lx.eval('scene.set %s ' % new_scene_2)

	#  rename to origins
	for item in new_scene.items(itype='locator', superType=True):
		if item.name in new_item_names:
			item.name = orig_item_names[new_item_names.index(item.name)]

	#  save scene
	exp_path = lx.eval('user.value exPath ?')
	if exp_path.endswith(os.sep) is False:
		exp_path += os.sep
	exp_path += 'export.fbx'
	lx.eval('scene.saveAs %s fbx true' % exp_path)

	#  rename to temp again
	for item in new_scene.items(itype='locator', superType=True):
		if item.name in orig_item_names:
			item.name = new_item_names[orig_item_names.index(item.name)]

	#  move items back to original scene
	select_items(new_scene, new_item_names)
	lx.eval('layer.import %s {} move:true position:0' % current_scene_2)
	lx.eval('scene.set %s '  % new_scene_2)

	# close temp scene
	lx.eval('!scene.close')
	lx.eval('scene.set %s '  % current_scene_2)
	select_items(current_scene, new_item_names)

	#  rename back and deselect
	for item in current_scene.items(itype='locator', superType=True):
		if item.name in new_item_names:
			item.name = orig_item_names[new_item_names.index(item.name)]
		else:
			item.deselect()

	#  fix parenting of objects
	for item_stuff in item_parents:
		if item_stuff[1] and item_stuff[1] not in orig_item_names:
			current_scene.item(item_stuff[0]).setParent(newParent=current_scene.item(item_stuff[1]))

	#  clear lists
	new_item_names = None
	orig_item_names = None
	item_parents  = None


if os.path.isdir(lx.eval('user.value exPath ?')):
	ExExport()