import sys
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

ax = plt.axes(projection=ccrs.PlateCarree())
ax.stock_img()
gl = ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True, linewidth=1, color='gray', alpha=0.5)
gl.xlabels_top = False
gl.ylabels_right = False
gl.xformatter = LONGITUDE_FORMATTER
gl.yformatter = LATITUDE_FORMATTER

filename = sys.argv[1]
df = pd.read_csv(filename)
plt.scatter(df['dat_ads_lon'], df['dat_ads_lat'], c=df['node'])
plt.show()
