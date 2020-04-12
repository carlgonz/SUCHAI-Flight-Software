import sys
import glob
import pandas as pd
import matplotlib.pyplot as plt
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
plt.scatter(df['dat_ads_lon'], df['dat_ads_lat'], c=df['node'])
plt.show()
