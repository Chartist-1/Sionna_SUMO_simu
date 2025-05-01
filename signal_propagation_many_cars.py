from xml_scripts import select_car_frames, longest_car_id
import pandas as pd
import drjit as dr
import mitsuba as mi
import numpy as np
import xml.etree.ElementTree as ET
import math
import os

# Handle Sionna RT import with fallback installation
try:
    import sionna.rt
except ImportError as e:
    import os
    os.system("pip install sionna-rt")
    import sionna.rt

from sionna.rt import load_scene, PlanarArray, Transmitter, Receiver, Camera, PathSolver, ITURadioMaterial, SceneObject





def signal_propagation_all_vehicles(scenario: str = 'scenario', 
                                  resolution: list = [650, 500], 
                                  output_video_name: str = 'render',
                                  distance: int = 500,
                                  camera_default: bool = True):
    """
    Main function to simulate signal propagation between all vehicles in a scenario.
    
    Parameters:
    - scenario (str): Name of the scenario folder
    - resolution (list): Resolution for rendered frames [width, height]
    - output_video_name (str): Base name for output files
    - distance (int): Maximum communication distance between vehicles
    - camera_default (bool): Whether to use default camera view or custom
    """
    
    

    # Load XML
    filename = f'scenarios/{scenario}/data_cars.xml'
    tree = ET.parse(filename)
    root = tree.getroot()

    # Determine frame range for simulation
    start_frame = float(root[0].attrib.get('time'))
    # stop_frame = float(root[-1].attrib.get('time'))
    stop_frame = float(10)

    print(f'Processing all vehicles in frames: {start_frame} to {stop_frame}')

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

    # Initialize data storage for all vehicles
    all_rssi_data = {}  # Dictionary to store RSSI data
    frames = []  # To store frame timestamps

    # Create directory for render frames 
    os.makedirs(f'scenarios/{scenario}/render_frames', exist_ok=True)

    tx_power = 20.0 #Power of transmitter signal on base distanse (200-500m), will be used for measuring loss
    attenuation_dict = {}

    # Process each frame in the simulation
    for stamp in root:
        vehicle = stamp.find('vehicle')
        
        # Only process frames that contain vehicles
        if vehicle is not None:
            frame_time = float(stamp.attrib.get('time'))
            print(f"Processing frame: {frame_time}")
            
            # Extract vehicle data for current frame
            veh_arr = []
            for i in range(len(stamp)):
                veh_arr.append({
                    'vehId': int(stamp[i].attrib.get('id')[3:]),
                    'x_coor': float(stamp[i].attrib.get('x')),
                    'y_coor': float(stamp[i].attrib.get('y')),
                    'z_coor': float(stamp[i].attrib.get('z')),
                    'angle': float(stamp[i].attrib.get('angle'))
                })

            # Initialize RSSI data for this frame
            frame_rssi = {v['vehId']: {} for v in veh_arr}
            
            # Create 3D car models for visualization
            cars = [SceneObject(
                fname=sionna.rt.scene.low_poly_car,
                name=f'car{veh_arr[i]["vehId"]}',
                radio_material=car_material
            ) for i in range(len(veh_arr))]
            
            scene.edit(add=cars)

            # Position and orient all vehicles in the scene
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
                print('Calculating signal paths between all vehicles...')
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
                    signal_loss = 0
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
                                a, _ = paths.cir(normalize_delays=False, out_type='numpy')
                                path_powers = np.abs(a)**2
                                total_power = np.sum(path_powers) 
                                total_power_log = 10*np.log10(total_power) if total_power > 0 else -100
                                frame_rssi[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = total_power_log

                                signal_loss += (total_power_log - tx_power)
                            else:
                                frame_rssi[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = -100  # Out of range
                        else:
                            frame_rssi[veh_arr[i]['vehId']][veh_arr[j]['vehId']] = 0  # Same vehicle
                    
                    if i not in attenuation_dict:
                        attenuation_dict[i] = []

                    attenuation_dict[i].append({
                        'frame': frame_time,
                        'signal_loss': signal_loss
                    })

            # Store RSSI data for this frame
            frames.append(frame_time)
            for veh_id in frame_rssi:
                if veh_id not in all_rssi_data:
                    all_rssi_data[veh_id] = []
                all_rssi_data[veh_id].append(frame_rssi[veh_id])

            # Set up camera view (default overview or custom)
            if camera_default:
                # Default camera shows the entire scene
                avg_x = sum(v['x_coor'] for v in veh_arr) / len(veh_arr)
                avg_y = sum(v['y_coor'] for v in veh_arr) / len(veh_arr)
                avg_z = sum(v['z_coor'] for v in veh_arr) / len(veh_arr)
                
                cam = Camera(
                    position=[avg_x, avg_y - 200, avg_z + 200],
                    look_at=[avg_x, avg_y, avg_z]
                )
            else:
                # Custom camera position and orientation
                cam = Camera(
                    position=[-11.7, -855, 477], 
                    look_at=[-392, -190.43, 90]
                )

            # Render the scene
            try:
                scene.render_to_file(
                    camera=cam,
                    filename=f'scenarios/{scenario}/render_frames/{int(frame_time)}.png',
                    resolution=resolution,
                    paths=paths if len(veh_arr) > 1 else None
                )
            except Exception as e:
                print(f"Rendering error: {e}")
                scene.render_to_file(
                    camera=cam,
                    filename=f'scenarios/{scenario}/render_frames/{int(frame_time)}.png',
                    resolution=resolution
                )

            if stop_frame <frame_time:
                break
            # Clean up for next frame
            for i in range(len(veh_arr)):
                scene.remove(f'tx-{veh_arr[i]["vehId"]}')
                scene.remove(f'rx-{veh_arr[i]["vehId"]}')
            scene.edit(remove=cars) 

    # Save RSSI data to CSV files (one per vehicle)
    for veh_id in all_rssi_data:
        # Create a DataFrame for this vehicle
        df_data = []
        for i, frame in enumerate(frames):
            row = {'Frame': frame}
            for other_id in all_rssi_data[veh_id][i]:
                row[f'RSSI_to_{other_id}'] = all_rssi_data[veh_id][i][other_id]
            df_data.append(row)
        
        df = pd.DataFrame(df_data)
        os.makedirs(f'scenarios/{scenario}/rssi_data', exist_ok=True)
        df.to_csv(f'scenarios/{scenario}/rssi_data/rssi_vehicle_{veh_id}.csv', sep=' ', index=False)

    rows = []
    for veh_id, measurements in attenuation_dict.items():
        for measurement in measurements:
            rows.append({
                'vehicle_id': veh_id,
                'frame': measurement['frame'],
                'signal_loss': measurement['signal_loss']
            })

    df = pd.DataFrame(rows)

    # Сохранение в CSV
    csv_path = f'scenarios/{scenario}/rssi_data/signal_attenuation_results.csv'
    df.to_csv(csv_path, index=False)
    print(f"Signal Loss Data has been written in: {csv_path}")
    
    print('Simulation Finished for all vehicles') 

if __name__ == '__main__':
    # Example usage with custom parameters
    signal_propagation_all_vehicles(
        scenario='scenario_strogino',
        resolution=[650, 500],
        output_video_name='output', 
        distance=100,
        camera_default=False
    )