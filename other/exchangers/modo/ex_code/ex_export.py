# python

import lx
#import modo
import os


export_type_old = lx.eval('user.value sceneio.fbx.save.exportType ?')
sample_type_old = lx.eval('user.value sceneio.fbx.save.sampleAnimation ?')
save_type_old = lx.eval('user.value sceneio.fbx.save.animation ?')

# change scene type
lx.eval('user.value sceneio.fbx.save.exportType FBXExportSelectionWithHierarchy')
lx.eval('user.value sceneio.fbx.save.sampleAnimation true')
lx.eval('user.value sceneio.fbx.save.animation true')

#  save scene
exp_path = lx.eval('user.value exPath ?').replace("\\", os.sep)
if exp_path.endswith(os.sep) is False:
    exp_path += os.sep
exp_path += 'exchange.fbx'
lx.eval('scene.saveAs {%s} fbx true' % exp_path)

# revert scene type
lx.eval('user.value sceneio.fbx.save.exportType %s' % export_type_old)
lx.eval('user.value sceneio.fbx.save.animation %s' % save_type_old)
lx.eval('user.value sceneio.fbx.save.sampleAnimation %s' % sample_type_old)