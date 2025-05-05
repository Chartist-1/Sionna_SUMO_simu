import pandas as pd
import drjit as dr
import mitsuba as mi
import numpy as np
import xml.etree.ElementTree as ET
import subprocess
import math
import traci
import time
import webbrowser
import os
import sionna.rt


from sionna.rt import load_scene, PlanarArray, Transmitter, Receiver, Camera, PathSolver, ITURadioMaterial, SceneObject

def timer(func):
    def wrapper(*args, **kwargs):
        start = time.perf_counter()           
        result = func(*args, **kwargs)        
        end = time.perf_counter()             
        print(f"[TIMER] {func.__name__} выполнена за {end - start:.6f} сек")
        return result
    return wrapper


def projection(scene, veh_arr, veh_arr_pred):

    new_veh_arr =[]
    for i in range (len(veh_arr)):
        x = veh_arr[i].get('x_coor')
        y = veh_arr[i].get('y_coor')
            
        ray = mi.Ray3f(
            o=mi.Point3f([x, y, 1000]),  
            d=mi.Vector3f([0, 0, -1])  
        )
        z = scene.ray_intersect(ray).p[2]
        pred_veh = next((veh for veh in veh_arr_pred if veh.get('vehId')==veh_arr[i].get('vehId')),None)
        if pred_veh:
            z_pred = pred_veh['z_coor']   
            if abs(z_pred - z) >5:
                ray = mi.Ray3f(
                    o=mi.Point3f([x, y, -1000]),  
                    d=mi.Vector3f([0, 0, 1])  
                )
                z = scene.ray_intersect(ray).p[2]
        if z!= 0 :
            new_veh_arr.append({'vehId':veh_arr[i].get('vehId'),
                            'x_coor':veh_arr[i].get('x_coor'),
                            'y_coor':veh_arr[i].get('y_coor') ,
                            'z_coor':z[0],
                            'angle':veh_arr[i].get('angle'),
                            'velocity': veh_arr[i].get('velocity')
                            })
    return new_veh_arr

def run_sumo_server(scenario:str = 'test_scenario',
                    port:int = 8813):
    process = subprocess.Popen(
    f'sumo -c scenarios/{scenario}/sumo_dir/osm.sumocfg --remote-port {port}'.split(' '),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
    )
    print (f'***Starting SUMO server on port {port} ***', process.pid)


def get_config_coordinates ():
    url = 'https://prochitecture.com/blender-osm/extent/?blender_version=4.2&addon=blosm&addon_version=2.7.14'
    webbrowser.open(url=url)
    with open('config.txt', 'w') as f:
        coords = input("Enter coordinates: ")
        f.write(coords)



def import_scenario():
    subprocess.run('blender --background --python blender_auto.py'.split(' '))
    print('Scenario installed')


@timer
def frame_handler(scene, 
                veh_arr,
                car_material,
                distance = 100,
                render: bool = False,
                scenario:str = 'scenario',
                camera_default:bool = True,
                resolution = [650,500],
                step:int = 0):

    # Only process frames that contain vehicles
    if len(veh_arr)!=0:
        frame_rssi = {v['vehId']: {} for v in veh_arr}
        frame_loss = {v['vehId']: {} for v in veh_arr}
        
        # Create 3D car models for visualization
        cars = [SceneObject(
            fname= sionna.rt.scene.low_poly_car,
            name=f'{veh_arr[i]["vehId"]}',
            radio_material=car_material
        ) for i in range(len(veh_arr))]
        
        scene.edit(add=cars)

        
        for i in range(len(veh_arr)):
            cars[i].position = mi.Point3f(
                veh_arr[i]['x_coor'], 
                veh_arr[i]['y_coor'], 
                veh_arr[i]['z_coor']+1
            )
            cars[i].orientation = mi.Point3f(float(veh_arr[i]['angle']), 0, 0)
            cars[i].scaling = mi.Float(1.5)
            
            # Add all vehicles as both transmitters and receivers
            scene.add(Transmitter(
                f'tx-{veh_arr[i]["vehId"]}',
                position=[veh_arr[i]['x_coor'], veh_arr[i]['y_coor'], veh_arr[i]['z_coor']+3],
                display_radius=2
            ))
            scene.add(Receiver(
                f'rx-{veh_arr[i]["vehId"]}',
                position=[veh_arr[i]['x_coor'], veh_arr[i]['y_coor'], veh_arr[i]['z_coor']+3],
                display_radius=2
            ))

        # Calculate signal paths between all pairs of vehicles
        if len(veh_arr) > 1:
            p_solver = PathSolver()
            paths = p_solver(
                scene=scene,
                max_depth=4,
                los=True,
                specular_reflection=True,
                diffuse_reflection=True,
                refraction=True,
                synthetic_array=False,
                seed=42
            )
            
            # Extract channel impulse response and calculate power for each pair
            for i in range(len(veh_arr)):
                for j in range(len(veh_arr)):
                    if i != j:
                        # Calculate distance between vehicles
                        dist = math.sqrt(
                            (veh_arr[i]['x_coor'] - veh_arr[j]['x_coor'])**2 +
                            (veh_arr[i]['y_coor'] - veh_arr[j]['y_coor'])**2 +
                            (veh_arr[i]['z_coor'] - veh_arr[j]['z_coor'])**2
                        )
                        
                        if dist < distance:
                            # Get CIR between this pair
                            
                            a, _ = paths.cir(normalize_delays=False, 
                                            out_type='numpy')
                            path_powers = np.abs(a[i][0][j][0])**2
                            total_power = np.sum(path_powers) 
                            total_power_log = 10*np.log10(total_power) if total_power > 0 else -200
                            frame_rssi[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = total_power_log

                            freq = scene.frequency
                            fspl = 20*np.log10(dist) + 20*np.log10(freq) + 20*np.log10(4 * np.pi / 3e8) # free-space path loss
                            tx_power = 20  # dBm, typical V2X transmission power
                            path_loss = np.abs(tx_power - total_power_log - fspl.item()) #Power of Tx - free space loss - power of Rx
                            frame_loss[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = path_loss
                        else:
                            frame_rssi[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = -200  # Out of range
                            frame_loss[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = 0
                    else:
                        frame_rssi[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = 0  # Same vehicle
                        frame_loss[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = 0

        

        if render:
            if camera_default:
                avg_x = sum(v['x_coor'] for v in veh_arr) / len(veh_arr)
                avg_y = sum(v['y_coor'] for v in veh_arr) / len(veh_arr)
                avg_z = sum(v['z_coor'] for v in veh_arr) / len(veh_arr)

                cam = Camera(
                    position=[avg_x, avg_y - 200, avg_z + 200],
                    look_at=[avg_x, avg_y, avg_z]
                )
            else:

                cam = Camera(
                    # position=[0,0, 1000], 
                    # look_at=[0,0,0]
                    position=[365.2,369.65, 293.3], 
                    look_at=[0,0,0]
                )
            try:
                scene.render_to_file(
                    camera=cam,
                    filename=f'scenarios/{scenario}/render_frames/{int(step)}.png',
                    resolution=resolution,
                    paths=paths if len(veh_arr) > 1 else None
                )
            except Exception as e:
                print(f"Rendering error: {e}")
                scene.render_to_file(
                    camera=cam,
                    filename=f'scenarios/{scenario}/render_frames/{int(step)}.png',
                    resolution=resolution
                )


        for i in range(len(veh_arr)):
            scene.remove(f'tx-{veh_arr[i]["vehId"]}')
            scene.remove(f'rx-{veh_arr[i]["vehId"]}')
        scene.edit(remove=cars) 
        
        return frame_rssi,frame_loss
    



def signal_propogation(scenario: str = 'scenario', 
                      begin_frame:int = 0,
                      stop_frame:int =100,
                      distance: int = 500,
                      render:bool =False,
                      camera_default: bool = True,
                      resolution: list = [650, 500], 
                      output_video_name: str = 'render', 
                      port:int = 8813):


    
    flag = input('Continue simulation y/n: ')
    if flag == 'n':
        return

    # Load the scene and configure antenna arrays
    scene = load_scene(f'scenarios/{scenario}/scenario.xml')
    
    # Configure transmitter array properties
    scene.tx_array = PlanarArray(num_rows=1,
                               num_cols=1,
                               vertical_spacing=0.5,
                               horizontal_spacing=0.5,
                               pattern="iso",
                               polarization="V")

    # Configure receiver array properties
    scene.rx_array = PlanarArray(num_rows=1,
                               num_cols=1,
                               vertical_spacing=0.5,
                               horizontal_spacing=0.5,
                               pattern="iso",
                               polarization="cross")

    # Create radio material for vehicles
    car_material = ITURadioMaterial("car-material",
                                  "metal",
                                  thickness=0.01,
                                  color=(0.8, 0.1, 0.1))


   

    os.makedirs(f'scenarios/{scenario}/render_frames', exist_ok=True)
    os.makedirs(f'scenarios/{scenario}/output_data', exist_ok=True)


    try:
        # Connect to the SUMO server
        traci.init(port)
        print(f"Connected to SUMO server on port {port}")
        step = 0

        x_max =float(traci.simulation.getNetBoundary()[1][0])
        y_max =float(traci.simulation.getNetBoundary()[1][1])

        columns = ['Frame','Cars_Data', 'RSSI']
        all_rssi_df = pd.DataFrame(columns=columns)

        veh_arr_pred =[]
        terrain = mi.load_file(f'scenarios/{scenario}/terrain.xml')
        while step < stop_frame:  # Run for 1000 simulation steps
            traci.simulationStep()  # Advance the simulation by one step
            step += 1
            if step<begin_frame:
                continue

            vehicle_ids = traci.vehicle.getIDList()

            offset = [5,0]
            veh_arr = []
            for vehID in vehicle_ids:
                veh_arr.append({'vehId':vehID,
                                'x_coor':float(traci.vehicle.getPosition(vehID=vehID)[0]-x_max/2) + offset[0],
                                'y_coor':float(traci.vehicle.getPosition(vehID=vehID)[1]-y_max/2) + offset[1],
                                'angle':-np.radians(float(traci.vehicle.getAngle(vehID=vehID) + 90)),
                                'velocity':float(traci.vehicle.getSpeed(vehID=vehID))})
            veh_arr = projection(terrain,veh_arr=veh_arr,veh_arr_pred=veh_arr_pred)
            veh_arr_pred = veh_arr
            print(f'Frame: {step}, Number of vehicles: {len(veh_arr)}')
            result, loss = frame_handler(scene=scene,
                                   veh_arr=veh_arr,
                                   car_material=car_material,
                                   distance=distance,
                                   render=render,
                                   scenario=scenario,
                                   camera_default=camera_default,
                                   resolution=resolution,
                                   step=step
                                   )
            
            
            new_row = pd.DataFrame([{
                'Frame': step,
                'Cars_Data': veh_arr,
                'RSSI': result,
                'SignalLoss': loss
            }])
            all_rssi_df = pd.concat([all_rssi_df,new_row],ignore_index=True)
            all_rssi_df.to_csv(f'scenarios/{scenario}/output_data/output.csv',sep = ';', index = False)

            

 
        print('Simulation Finished for all vehicles') 

    
    except KeyboardInterrupt:
        print('Interrrupted')

   
    finally:
        # Close the connection to SUMO
        traci.close()
        print("Disconnected from SUMO server.")
    
    return

    

if __name__ == '__main__':
    # Example usage with custom parameters
    scenario = 'test_scenario'
    run_sumo_server(scenario=scenario)
    signal_propogation(
        scenario=scenario,
        begin_frame = 80,
        stop_frame = 81,
        distance=500,
        render=True,
        camera_default=False,
        resolution=[650,500]
    )
    # get_config_coordinates()

    #sumo -c scenarios/test_scenario/2025-04-21-16-39-58/osm.sumocfg --remote-port 8813