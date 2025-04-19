import matplotlib.pyplot as plt
from xml_script import select_car_frames, longest_car_id

import drjit as dr
import mitsuba as mi
import numpy as np
import xml.etree.ElementTree as ET
import math

# Import or install Sionna
try:
    import sionna.rt
except ImportError as e:
    import os
    os.system("pip install sionna-rt")
    import sionna.rt

no_preview = False # Toggle to False to use the preview widget
                  # instead of rendering for scene visualization

from sionna.rt import load_scene, PlanarArray, Transmitter, Receiver, Camera,\
                      PathSolver, ITURadioMaterial, SceneObject
scene = load_scene('scenario2/mitsuba_scenario2.xml') # Objects are merged by default
# Configure antenna array for all transmitters
scene.tx_array = PlanarArray(num_rows=1,
                             num_cols=1,
                             vertical_spacing=0.5,
                             horizontal_spacing=0.5,
                             pattern="iso",
                             polarization="V")

# Configure antenna array for all receivers
scene.rx_array = PlanarArray(num_rows=1,
                             num_cols=1,
                             vertical_spacing=0.5,
                             horizontal_spacing=0.5,
                             pattern="iso",
                             polarization="cross",
                             )

# Create transmitter

car_material = ITURadioMaterial("car-material",
                                "metal",
                                thickness=0.01,
                                color=(0.8, 0.1, 0.1))


X_max = 2183.28
Y_max = 2763.64

# car = SceneObject(fname=sionna.rt.scene.low_poly_car, name='car',radio_material=car_material)
# scene.edit(add=car)
# car.position = mi.Point3f(34.81-X_max/2, 438.98 -Y_max/2,2)
car_material = ITURadioMaterial("car-material",
                                "metal",
                                thickness=0.01,
                                color=(0.8, 0.1, 0.1))



filename = 'scenario2/data_cars.xml'
tree  = ET.parse(filename)
root = tree.getroot()
car_id = f'{longest_car_id(filename = filename)}'
car_id = '101'
# start_frame, stop_frame = select_car_frames(filename = filename, car_id=car_id)
start_frame = 420
stop_frame =500
cam = Camera([673.447, -1712.44, 694.636], look_at=[163.598, -468.019, 18.175])

for stamp in root:
    vehicle = stamp.find('vehicle')
    
    if (vehicle!=None) and (float(stamp.attrib.get('time')) >= start_frame) and (float(stamp.attrib.get('time')) <= stop_frame):
        print(float(stamp.attrib.get('time')))
        veh_arr=[]
        for i in range(len(stamp)):
            veh_arr.append({'vehId':int(stamp[i].attrib.get('id')[3:]),
                        'x_coor': float(stamp[i].attrib.get('x')),
                        'y_coor': float(stamp[i].attrib.get('y')),
                        'angle' :float(stamp[i].attrib.get('angle'))})
        for i in range(len(veh_arr)):
            if int(veh_arr[i].get('vehId')) == int(car_id):
                main_car_id = i
                break

        selected_cars =[]
        for i in range(len(veh_arr)):
            dist = math.sqrt((veh_arr[main_car_id]['x_coor']- veh_arr[i]['x_coor'])**2 +(veh_arr[main_car_id]['y_coor']- veh_arr[i]['y_coor'])**2 )

            if dist <500:

                selected_cars.append(veh_arr[i])
        cars = [SceneObject(fname=sionna.rt.scene.low_poly_car,name=f'car{veh_arr[i]['vehId']}',radio_material=car_material) for i in range(len(veh_arr))]
        veh_arr=selected_cars.copy()
        for i in range(len(veh_arr)):
            if int(veh_arr[i].get('vehId')) == int(car_id):
                main_car_id = i
                break
        print(veh_arr)
        cam = Camera(position=[(veh_arr[main_car_id]['x_coor']-X_max/2) + math.cos(float(-np.radians(veh_arr[i]['angle']+90))) * 200,(veh_arr[main_car_id]['y_coor']-Y_max/2) + math.sin(float(-np.radians(veh_arr[i]['angle']+90))) * 200,200],look_at=[veh_arr[main_car_id]['x_coor']-X_max/2,veh_arr[main_car_id]['y_coor']-Y_max/2,0])
        scene.edit(add=cars)

        tx_arr=[]
        for i in range(len(veh_arr)):
            cars[i].position = mi.Point3f(veh_arr[i]['x_coor']-X_max/2, veh_arr[i]['y_coor'] - Y_max/2, 1)
            cars[i].orientation = mi.Point3f(float(-np.radians(veh_arr[i]['angle']+90)),0,0)
            cars[i].scaling = mi.Float(1.5)
            
            
            if i == main_car_id:
                scene.add(Receiver(f'rx-{i}',position=[veh_arr[i]['x_coor']-X_max/2, veh_arr[i]['y_coor'] - Y_max/2, 3],display_radius=2))
            else:
                scene.add(Transmitter(f'tx-{i}', position=[veh_arr[i]['x_coor']-X_max/2, veh_arr[i]['y_coor'] - Y_max/2, 3],display_radius=2))
        p_solver = PathSolver()
        paths =0
        if len(veh_arr)!=1:
            paths = p_solver(scene=scene,
                            max_depth=3,
                            los=True,
                            specular_reflection=True,
                            diffuse_reflection=False,
                            refraction=True,
                            synthetic_array=False,
                            seed=42)
        print()
        print('Paths calculated')
        try:
            scene.render_to_file(camera=cam,
                             filename=f'scenario2/render1/frame{stamp.attrib.get('time')}.png',
                             resolution=[650,500],
                             paths=paths);
        except Exception as e:
            print(e)
            scene.render_to_file(camera=cam,
                             filename=f'scenario2/render1/frame{stamp.attrib.get('time')}.png',
                             resolution=[650,500]);
        for i in range(len(veh_arr)):
            scene.remove(f'tx-{i}')
            if i == main_car_id:
                scene.remove(f'rx-{i}')
        scene.edit(remove=cars)  
            