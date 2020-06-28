#!/usr/bin/env python3
import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

if len(sys.argv) > 1:
    filename = sys.argv[1]
else:
    filename = sorted(glob.glob("tm_status_*.csv"))[-1]

print("Loading", filename)
df = pd.read_csv(filename)

ax = plt.axes(projection=ccrs.PlateCarree())
ax.stock_img()
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5)
gl.xlabels_top = False
gl.ylabels_right = False
gl.xformatter = LONGITUDE_FORMATTER
gl.yformatter = LATITUDE_FORMATTER
plt.title(filename)
#_plot = plt.scatter(df['dat_ads_lon'], df['dat_ads_lat'], c=df['node'])

for n in range(1,4):
    d = df[df['node'] == n]
    plt.plot(d['dat_ads_lon'], d['dat_ads_lat'], '--')
    
_plot = plt.scatter([], [], cmap="jet", vmin=1, vmax=3)
def update(i, data, _plt):
    data = data[(i-1)*2:i*2]
    _plt.set_offsets(data[['dat_ads_lon', 'dat_ads_lat']])
    _plt.set_array(data['node'])
    _plt.set_sizes(data['dat_obc_opmode']+2000)
    return _plt,

ani = animation.FuncAnimation(plt.gcf(), update, interval=10, fargs=(df, _plot), blit=True)

plt.show()
