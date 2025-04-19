import sys
import subprocess
import os
import math
import xml.etree.ElementTree as ET
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

try:
    import numpy as np
    print('All packages imported seccessefully!!!')
except:
        python_exe = os.path.join(sys.prefix, 'bin', 'python3.11')

        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])

        subprocess.call([python_exe, "-m", "pip", "install", "numpy"])


filename = 'sumo_data/data_cars.xml'
offset = [2.96,-5.63]
tree  = ET.parse(filename)
root = tree.getroot()
obj = bpy.data.objects['Terrain']
x_max = 2232.27
y_max = 1767.49
print(obj)
for stamp in root:
    vehicle = stamp.find('vehicle')
    print(stamp.attrib.get('time'))
    if vehicle != None:

        
        for i in range(len(stamp)):
            
            x = float(stamp[i].attrib.get('x')) - x_max/2 + offset[0]
            y = float(stamp[i].attrib.get('y')) - y_max/2 + offset[1]
            
            depsgraph = bpy.context.evaluated_depsgraph_get()
            
            bvh = BVHTree.FromObject(obj, depsgraph, deform=True, cage=False)

            start_point = Vector((x, y, 10000))  
            direction = Vector((0, 0, -1))       

            hit_location, hit_normal, hit_index, hit_distance = bvh.ray_cast(start_point, direction)
            try:
                stamp[i].set('x',str(round(hit_location[0],3)))
                stamp[i].set('y',str(round(hit_location[1],3)))
                stamp[i].set('z',str(round(hit_location[2],3)))
                stamp[i].set('angle',str(round(-np.radians(float(stamp[i].attrib.get('angle'))+90),3)))
            except Exception as e:
                 print(stamp.attrib.get('time'))
                 print(e)

tree.write('sumo_data/new_data_cars.xml', encoding='utf8', xml_declaration=True)