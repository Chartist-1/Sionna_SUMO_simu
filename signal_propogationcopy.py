from xml_script import select_car_frames, longest_car_id
import pandas as pd
import drjit as dr
import mitsuba as mi
import numpy as np
import xml.etree.ElementTree as ET
import math


try:
    import sionna.rt
except ImportError as e:
    import os
    os.system("pip install sionna-rt")
    import sionna.rt


from sionna.rt import load_scene, PlanarArray, Transmitter, Receiver, Camera,\
                      PathSolver, ITURadioMaterial, SceneObject



def signal_propogation(scenario:str = 'scenario', resolution:list = [650,500], output_video_name:str = 'render', main_car_id:str = '12',distance:int = 500,camera_default = True):
    
    filename = f'scenarios/{scenario}/data_cars.xml'
    
    tree  = ET.parse(filename)
    root = tree.getroot()


    if main_car_id == '0':
        car_id = f'{longest_car_id(filename = filename)}'
    else:
        car_id = main_car_id

    # start_frame, stop_frame = select_car_frames(filename = filename, car_id=car_id)
    start_frame = 215
    stop_frame = 250

    print(f'Selected Car_ID: {car_id}, Frames of this car: {start_frame} {stop_frame}')
    flag  = input('Continue simulatyion y/n: ')
    if flag =='n':
        return
    

    scene = load_scene(f'scenarios/{scenario}/scenario.xml')
    scene.tx_array = PlanarArray(num_rows=1,
                                num_cols=1,
                                vertical_spacing=0.5,
                                horizontal_spacing=0.5,
                                pattern="iso",
                                polarization="V")

    scene.rx_array = PlanarArray(num_rows=1,
                                num_cols=1,
                                vertical_spacing=0.5,
                                horizontal_spacing=0.5,
                                pattern="iso",
                                polarization="cross",
                                )
    car_material = ITURadioMaterial("car-material",
                                "metal",
                                thickness=0.01,
                                color=(0.8, 0.1, 0.1))

    rssi = []
    frames = []
    for stamp in root:
        vehicle = stamp.find('vehicle')
        if (vehicle!=None) and (float(stamp.attrib.get('time')) >= start_frame) and (float(stamp.attrib.get('time')) <= stop_frame):
            print(float(stamp.attrib.get('time')))
            veh_arr=[]
            for i in range(len(stamp)):
                veh_arr.append({'vehId':int(stamp[i].attrib.get('id')[3:]),
                            'x_coor': float(stamp[i].attrib.get('x')),
                            'y_coor': float(stamp[i].attrib.get('y')) ,
                            'z_coor': float(stamp[i].attrib.get('z')),
                            'angle' :float(stamp[i].attrib.get('angle'))})
            for i in range(len(veh_arr)):
                if int(veh_arr[i].get('vehId')) == int(car_id):
                    main_car_id = i
                    break

            selected_cars =[]

            for i in range(len(veh_arr)):
                dist = math.sqrt((veh_arr[main_car_id]['x_coor']- veh_arr[i]['x_coor'])**2 +(veh_arr[main_car_id]['y_coor']- veh_arr[i]['y_coor'])**2 + (veh_arr[main_car_id]['z_coor']- veh_arr[i]['z_coor'])**2)
                if dist <distance:
                    selected_cars.append(veh_arr[i])

            veh_arr=selected_cars.copy()
            cars = [SceneObject(fname=sionna.rt.scene.low_poly_car,name=f'car{veh_arr[i]['vehId']}',radio_material=car_material) for i in range(len(veh_arr))]
            scene.edit(add=cars)
            

            for i in range(len(veh_arr)):
                if int(veh_arr[i].get('vehId')) == int(car_id):
                    main_car_id = i
                    break
            print(veh_arr)
            if camera_default:
                #Дэфолтная камера следует за машиной вид сверху
                cam = Camera(position=[(veh_arr[main_car_id]['x_coor']) + math.cos(float(-np.radians(veh_arr[main_car_id]['angle']+90))) * 200,(veh_arr[main_car_id]['y_coor']) + math.sin(float(-np.radians(veh_arr[main_car_id]['angle']+90))) * 200, veh_arr[main_car_id]['z_coor'] + 200],look_at=[veh_arr[main_car_id]['x_coor'],veh_arr[main_car_id]['y_coor'],veh_arr[main_car_id]['z_coor']])
            else:
                #Здесь прописывать кастомные камеры
                cam = Camera(position=[-69.6934 ,434.79  ,594.99], look_at=[579.051,-196.43,29.058 ])
            

            for i in range(len(veh_arr)):
                cars[i].position = mi.Point3f(veh_arr[i]['x_coor'], veh_arr[i]['y_coor'] , veh_arr[i]['z_coor']+1)
                cars[i].orientation = mi.Point3f(float(veh_arr[i]['angle']),0,0)
                cars[i].scaling = mi.Float(1.5)
                
                
                if i == main_car_id:
                    scene.add(Receiver(f'rx-{i}',position=[veh_arr[i]['x_coor'], veh_arr[i]['y_coor'] , veh_arr[i]['z_coor']+3],display_radius=2))
                else:
                    scene.add(Transmitter(f'tx-{i}', position=[veh_arr[i]['x_coor'], veh_arr[i]['y_coor'] , veh_arr[i]['z_coor']+3],display_radius=2))
            p_solver = PathSolver()
            paths =0
            frames.append(float(stamp.attrib.get('time')))
            if len(veh_arr)!=1:
                print('calculating_paths')
                paths = p_solver(scene=scene,
                                max_depth=4,
                                los=True,
                                specular_reflection=True,
                                diffuse_reflection=True,
                                refraction=True,
                                synthetic_array=False,
                                seed=42)
                a,_ = paths.cir(normalize_delays=False,out_type='numpy')
                path_powers = np.abs(a)**2
                total_power = np.sum(path_powers) 
                rssi.append(total_power)
            else:
                rssi.append(0)
            try:
                scene.render_to_file(camera=cam,
                                filename=f'scenarios/{scenario}/render_frames/{int(float(stamp.attrib.get('time')))}.png',
                                resolution=resolution,
                                paths=paths);
            except Exception as e:
                print(e)
                scene.render_to_file(camera=cam,
                                filename=f'scenarios/{scenario}/render_frames/{int(float(stamp.attrib.get('time')))}.png',
                                resolution=resolution);
            for i in range(len(veh_arr)):
                scene.remove(f'tx-{i}')
                if i == main_car_id:
                    scene.remove(f'rx-{i}')
            scene.edit(remove=cars) 
    df = pd.DataFrame(data={'Frame':frames,
                            'RSSI' : rssi})
    df.to_csv(f'scenarios/{scenario}/rssi_data.csv', sep= ' ',index=False )
    print('Simulation Finished') 
    
if __name__=='__main__':
    signal_propogation(scenario='scenario4',
                        resolution=[1920,1080],
                        output_video_name='output', 
                        main_car_id='17', 
                        distance= 500,
                        camera_default= False)