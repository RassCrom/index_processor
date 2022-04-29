import rasterio
from osgeo import gdal, ogr
import numpy as np
import os
import geopandas as gp

# Function
def get_ndwi(green, nir, res):

    dst_crs = 'EPSG:4326'
    path1 = green + "/"
    path2 = nir + "/"
    a = os.listdir(path1)
    b = os.listdir(path2)

    for i, y in zip(a, b):

        # Reading images
        ds_band3 = gdal.Open(path1 + i)
        ds_band5 = gdal.Open(path2 + y)
        
        # Reprojecting images for web based projection
        dsReprj_3 = gdal.Warp(res + '/reprjct_' + i[13:27] + '_' + i[-6:], ds_band3, dstSRS=dst_crs)
        name_3 = res + '/reprjct_' + i[13:27] + '_' + i[-6:]
        dsReprj_5 = gdal.Warp(res + '/reprjct_' + y[13:27] + '_' + y[-6:], ds_band5, dstSRS=dst_crs)
        name_5 = res + '/reprjct_' + y[13:27] + '_' + y[-6:]
        
        # Re-open images in rasterio
        band3 = rasterio.open(name_3)
        band5 = rasterio.open(name_5)

        # Getting first band of images
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
        
        # Classyfing Index (Selecting only water objects >0.2)
        raster = rasterio.open(res + '/ndwi_' + i)
        raster_r = raster.read()
        lista = raster_r.copy()
        lista[np.where(lista >= 0.2)] = 1
        lista[np.where(lista < 0.2)] = 0

        # Saving index
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
        d = b.GetRasterBand(1) 
        drv = ogr.GetDriverByName('ESRI Shapefile')
        outfile = drv.CreateDataSource(res + '/ndwi_' + i + '_class' + '.shp') 
        outlayer = outfile.CreateLayer('polygonized raster', srs = None )
        newField = ogr.FieldDefn('Water', ogr.OFTReal)
        outlayer.CreateField(newField)
        gdal.Polygonize(d, None, outlayer, 0, [])
        outfile = None
        
        #Querying only vector water objects
        vec_crs = gp.read_file(res + '/ndwi_' + i + '_class' + '.shp')
        vec_crs = vec_crs.set_crs(dst_crs)
        vec3 = vec_crs[vec_crs["Water"].isin([1])]
        vec3 = vec3.set_crs(dst_crs)
        vec3.to_file(res + '/ndwi_' + i + '_class_selected.shp')   
        gdf = gp.read_file(res + '/ndwi_' + i + '_class_selected.shp')
        gdf_lat_lng = gdf.to_crs(4326)
        gdf_save = gdf_lat_lng.to_file(res + '/ndwi_' + i + '_class_selected_latlng.geojson', driver='GeoJSON')

get_ndwi('D:/diplom/data/green', 'D:/diplom/data/nir', 'D:/diplom/data_process')
                           

        