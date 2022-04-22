from osgeo import gdal
import rasterio
import folium
from ipyleaflet import *

m = Map(center=(46,64), zoom = 8, basemap=basemaps.Esri.DeLorme)

m