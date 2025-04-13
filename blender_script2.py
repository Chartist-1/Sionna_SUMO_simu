import sys
import subprocess
import os
import xml.etree.ElementTree as ET
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
try:
    print('All packages imported seccessefully!!!')
except:
        python_exe = os.path.join(sys.prefix, 'bin', 'python3.11')

        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])

        subprocess.call([python_exe, "-m", "pip", "install", "numpy"])
        subprocess.call([python_exe, "-m", "pip", "install", "pandas"])

filename = 'sumo_data/data_cars.xml'
tree  = ET.parse(filename)
root = tree.getroot()
obj = bpy.data.objects['Terrain']
x_max = 1030.32
y_max = 748.43
print(obj)
for stamp in root:
    vehicle = stamp.find('vehicle')
    if vehicle != None:

        
        for i in range(len(stamp)):
            x = float(stamp[i].attrib.get('x')) - x_max/2
            y = float(stamp[i].attrib.get('y')) - y_max/2
            
            depsgraph = bpy.context.evaluated_depsgraph_get()
            
            bvh = BVHTree.FromObject(obj, depsgraph, deform=True, cage=False)

            start_point = Vector((x, y, 10000))  
            direction = Vector((0, 0, -1))       

            hit_location, hit_normal, hit_index, hit_distance = bvh.ray_cast(start_point, direction)
            try:
                stamp[i].set('z',str(round(hit_location[2],3)))
            except Exception as e:
                 print(stamp.attrib.get('time'))
                 print(e)

tree.write('sumo_data/new_data_cars.xml', encoding='utf8', xml_declaration=True)