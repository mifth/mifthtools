# python

import os
import modo
import lx


#  load scene
ex_path = lx.eval('user.value exPath ?').replace("\\","/")
if ex_path.endswith(os.sep) is False:
    ex_path += os.sep
ex_path += 'exchange.fbx'
lx.eval('loaderOptions.fbx false true false true true true true true false false true true false true 0')

if lx.eval('user.value importDialog ?') == 1:
    lx.eval('scene.open %s import' % ex_path)
else:
    lx.eval('!scene.open %s import' % ex_path)