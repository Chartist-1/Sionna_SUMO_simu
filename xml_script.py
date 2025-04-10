import xml.etree.ElementTree as ET
import numpy as np



def select_car_frames(filename:str = 'data_cars.xml', car_id:int ='12'):
    tree  = ET.parse(filename)
    root = tree.getroot()
    flag = False
    for timestamp in root:
        vehicle = timestamp.find('vehicle')
        if vehicle!=None:
            veh_arr =[]
            for vehicles in timestamp:
                veh_arr.append(vehicles.attrib.get('id')[3:])
            if (car_id in veh_arr) and (flag == False):
                begin_frame = float(timestamp.attrib.get('time'))
                flag = True
            if (not car_id in veh_arr) and (flag):
                return begin_frame, float(timestamp.attrib.get('time'))-1

def longest_car_id(filename:str = 'data_cars.xml'):
    tree  = ET.parse(filename)
    root = tree.getroot()
    veh_arr =np.zeros(5000)
    for timestamp in root:
        vehicle = timestamp.find('vehicle')
        if vehicle!=None:
            for vehicles in timestamp:
                veh_arr[int(vehicles.attrib.get('id')[3:])]+=1
    return(np.argmax(veh_arr))
            
if __name__ =='__main__':
    select_car_frames(filename='data_cars.xml',car_id=f'{longest_car_id(filename='data_cars.xml')}')
    