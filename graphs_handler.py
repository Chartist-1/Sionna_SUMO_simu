import pandas as pd 
import matplotlib
import ast
import matplotlib.pyplot as plt 
matplotlib.use('Qt5Agg')

data = pd.read_csv(f'scenarios/scenario_tunnel/output_data/output.csv', sep = ' ')
car_id = 9
all_data =[]
frames =[]

for i in range(len(data['Frame'])):
    row = ast.literal_eval(data['RSSI'][i]).get(f'veh{car_id}')
    if row:
        frames.append(data['Frame'][i])
        all_data.append(row)

df = pd.DataFrame(all_data)
df = df.where(df>-200)
df = df.where(df<0)
print(df)
fig,ax = plt.subplots()

for col in df.columns:
    ax.scatter(frames,df[col],label = col)
    ax.plot(frames,df[col])

    ax.legend()
plt.show()