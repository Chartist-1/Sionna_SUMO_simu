import pandas as pd 
import matplotlib
import matplotlib.pyplot as plt 
matplotlib.use('Qt5Agg')

data = pd.read_csv(f'scenario4/rssi_data.csv', sep = ' ')

fig,ax = plt.subplots()
ax.plot(data['Frame'], data['RSSI'])
plt.show()