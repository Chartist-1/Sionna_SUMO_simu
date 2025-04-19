import sys
import subprocess
import os
import bpy
try:
    import pandas as pd
    import numpy as np
    print('All packages imported seccessefully!!!')
except:
        python_exe = os.path.join(sys.prefix, 'bin', 'python3.11')

        subprocess.call([python_exe, "-m", "ensurepip"])
        subprocess.call([python_exe, "-m", "pip", "install", "--upgrade", "pip"])

        subprocess.call([python_exe, "-m", "pip", "install", "numpy"])
        subprocess.call([python_exe, "-m", "pip", "install", "pandas"])

frames = 5
number_of_cars = 2
obj_arr=[]
for i in range (number_of_cars):
    obj_arr.append(bpy.data.objects[i])

obj_corrs = []
for i in range(frames):
    bpy.context.scene.frame_set(i)
    corr_arr = []
    for i in range(len(obj_arr)):
        coordinates = obj_arr[i].matrix_world.to_translation()
        corr_arr.append(coordinates)
    obj_corrs.append(corr_arr)

arr1=[[],[],[]]
arr2=[[],[],[]]

for i in range(len(obj_corrs)):

    temp1 = (obj_corrs[i][0].x, obj_corrs[i][0].y, obj_corrs[i][0].z)
    temp2 = (obj_corrs[i][1].x, obj_corrs[i][1].y, obj_corrs[i][1].z)

    arr1[0].append(temp1[0])
    arr1[1].append(temp1[1])
    arr1[2].append(temp1[2])

    arr2[0].append(temp2[0])
    arr2[1].append(temp2[1])
    arr2[2].append(temp2[2])



data = pd.DataFrame({'Car1x':arr1[0],
                     'Car1y':arr1[1],
                     'Car1z':arr1[2],
                     'Car2x':arr2[0],
                     'Car2y':arr2[1],
                     'Car2z':arr2[2],})
data.to_csv(f'data.csv',sep = ' ',index = True)
