import rasterio
from rasterio import plot
import matplotlib.pyplot as plt
from osgeo import gdal, ogr
import numpy as np
import os
import sys
import geopandas as gp
from rasterio.plot import show
import osgeo.osr as osr

# Function to get info from html's forms
def get_ndwi(green, nir, res):

    dst_crs = 'EPSG:4326'
    # To specife the main folders
    # a = os.listdir(r"C:/Users/rkoen/OneDrive/Документы/Cartometria/clipped" + r"/green_one")
    # b = os.listdir(r"C:/Users/rkoen/OneDrive/Документы/Cartometria/clipped" + r"/nir_one")
    path1 = green + "/"
    path2 = nir + "/"
    a = os.listdir(path1)
    b = os.listdir(path2)

    for i, y in zip(a, b):

        # Reading images
        # band3 = rasterio.open(path1 + i)
        # band5 = rasterio.open(path2 + y)
        ds_band3 = gdal.Open(path1 + i)
        ds_band5 = gdal.Open(path2 + y)
        
        dsReprj_3 = gdal.Warp(res + '/reprjct_' + i[13:27] + '_' + i[-6:], ds_band3, dstSRS="EPSG:4326")
        name_3 = res + '/reprjct_' + i[13:27] + '_' + i[-6:]
        dsReprj_5 = gdal.Warp(res + '/reprjct_' + y[13:27] + '_' + y[-6:], ds_band5, dstSRS='EPSG:4326')
        name_5 = res + '/reprjct_' + y[13:27] + '_' + y[-6:]
        
        band3 = rasterio.open(name_3)
        band5 = rasterio.open(name_5)
        
        # band3 = rasterio.open(r"C:/Users/rkoen/OneDrive/Документы/Cartometria/clipped/green_one/" + i)
        # band5 = rasterio.open(r"C:/Users/rkoen/OneDrive/Документы/Cartometria/clipped/nir_one/" + y)
        green = band3.read(1).astype('float64')
        nir = band5.read(1).astype('float64')


        # Calculating NDWI
        ndwi = np.where(
            (green - nir)==0., 
            0, 
        (green-nir)/(green + nir))
        ndwi[:5,:5]
        
        # Saving NDWI
        ndwiImage = rasterio.open(res + '/ndwi_' + i,'w',driver='Gtiff',
                            width=band3.width, 
                            height = band3.height, 
                            count=1, 
                            crs=band3.crs, 
                            transform=band3.transform, 
                            dtype='float64')
        ndwiImage.write(ndwi,1)
        ndwiImage.close()
        
        #Classyfing Index (Selecting only water objects >0.4)
        raster = rasterio.open(res + '/ndwi_' + i)
        raster_r = raster.read()
        lista = raster_r.copy()
        lista[np.where(lista >= 0.2)] = 1
        lista[np.where(lista < 0.2)] = 0
        with rasterio.open(res + '/ndwi_' + i + '_class' + '.TIF', 'w',
                           driver=raster.driver,
                           height=raster.height,
                           width=raster.width,
                           count=raster.count,
                           crs=raster.crs,
                           transform=raster.transform,
                           dtype=rasterio.float64
                          ) as dst:
            dst.write(lista)
        
        #Vectorize image
        b = gdal.Open(res + '/ndwi_' + i + '_class' + '.TIF')
        b.RasterCount
        d = b.GetRasterBand(1) 
        print(b.RasterCount)
        drv = ogr.GetDriverByName('ESRI Shapefile')
        outfile = drv.CreateDataSource(res + '/ndwi_' + i + '_class' + '.shp') 
        outlayer = outfile.CreateLayer('polygonized raster', srs = None )
        newField = ogr.FieldDefn('Water', ogr.OFTReal)
        outlayer.CreateField(newField)
        gdal.Polygonize(d, None, outlayer, 0, [])
        outfile = None
        
        #Querying only vector water objects
        vec_crs = gp.read_file(res + '/ndwi_' + i + '_class' + '.shp')
        vec_crs = vec_crs.set_crs("EPSG:3857")
        vec3 = vec_crs[vec_crs["Water"].isin([1])]
        vec3 = vec3.set_crs("EPSG:3857")
        vec3.to_file(res + '/ndwi_' + i + '_class_selected.shp')   
        gdf = gp.read_file(res + '/ndwi_' + i + '_class_selected.shp')
        gdf_lat_lng = gdf.to_crs(4326)
        gdf_save = gdf_lat_lng.to_file(res + '/ndwi_' + i + '_class_selected_latlng.geojson', driver='GeoJSON')
        
                           

        