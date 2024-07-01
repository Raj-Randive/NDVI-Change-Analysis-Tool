
from osgeo import ogr, gdal, osr
import numpy as np
import os
import matplotlib.pyplot as plt

#Input Raster and Vector Paths
#Image-2014
path_B5_2014= "E:\\Just_Code\\BISAG-INTERN\\ML_Task\\Data\\2016-11-04-00_00_2016-11-04-23_59_Sentinel-2_L2A_B05_(Raw).tiff"
path_B4_2014= "E:\\Just_Code\\BISAG-INTERN\\ML_Task\\Data\\2016-11-04-00_00_2016-11-04-23_59_Sentinel-2_L2A_B04_(Raw).tiff"

#Image-2019
path_B5_2019= "E:\\Just_Code\\BISAG-INTERN\\ML_Task\\Data\\2024-06-05-00_00_2024-06-05-23_59_Sentinel-2_L2A_B05_(Raw).tiff"
path_B4_2019="E:\\Just_Code\\BISAG-INTERN\\ML_Task\\Data\\2024-06-05-00_00_2024-06-05-23_59_Sentinel-2_L2A_B04_(Raw).tiff"

#Output NDVI Rasters 
path_NDVI_2019 = 'E:\\Just_Code\\BISAG-INTERN\\ML_Task\\output\\NDVI2024.tif'
path_NDVI_2014 = 'E:\\Just_Code\\BISAG-INTERN\\ML_Task\\output\\NDVI2016.tif'

path_NDVIChange_19_14 = 'E:\\Just_Code\\BISAG-INTERN\\ML_Task\\output\\NDVIChange_24_16.tif'
#NDVI Contours
contours_NDVIChange_19_14 = 'E:\\Just_Code\\BISAG-INTERN\\ML_Task\\output\\NDVIChange_24_16.shp'

#Open raster bands
B5_2019 = gdal.Open(path_B5_2019)
B4_2019 = gdal.Open(path_B4_2019)
B5_2014 = gdal.Open(path_B5_2014)
B4_2014 = gdal.Open(path_B4_2014)

#Read bands as matrix arrays
B52019_Data = B5_2019.GetRasterBand(1).ReadAsArray().astype(np.float32)
B42019_Data = B4_2019.GetRasterBand(1).ReadAsArray().astype(np.float32)
B52014_Data = B5_2014.GetRasterBand(1).ReadAsArray().astype(np.float32)
B42014_Data = B4_2014.GetRasterBand(1).ReadAsArray().astype(np.float32)

print(B5_2014.GetProjection()[:80])
print(B5_2019.GetProjection()[:80])
if B5_2014.GetProjection()[:80]==B5_2019.GetProjection()[:80]: print('SRC OK')

B52019_Data = B52019_Data[:1448, :2147]  # Select the first 1448 rows
print(B52014_Data.shape)
print(B52019_Data.shape)
if B52014_Data.shape==B52019_Data.shape: print('Array Size OK')

print(B5_2014.GetGeoTransform())
print(B5_2019.GetGeoTransform())
if B5_2014.GetGeoTransform()==B5_2019.GetGeoTransform(): print('Geotransformation OK')

geotransform = B5_2014.GetGeoTransform()

originX,pixelWidth,empty,finalY,empty2,pixelHeight=geotransform
cols =  B5_2014.RasterXSize
rows =  B5_2014.RasterYSize

projection = B5_2014.GetProjection()

finalX = originX + pixelWidth * cols
originY = finalY + pixelHeight * rows

ndvi2014 = np.divide(B52014_Data - B42014_Data, B52014_Data+ B42014_Data,where=(B52014_Data - B42014_Data)!=0)
ndvi2014[ndvi2014 == 0] = -999

ndvi2019 = np.divide(B52019_Data - B42019_Data, B52019_Data+ B42019_Data,where=(B52019_Data - B42019_Data)!=0)
ndvi2019[ndvi2019 == 0] = -999

def saveRaster(dataset,datasetPath,cols,rows,projection):
    rasterSet = gdal.GetDriverByName('GTiff').Create(datasetPath, cols, rows,1,gdal.GDT_Float32)
    rasterSet.SetProjection(projection)
    rasterSet.SetGeoTransform(geotransform)
    rasterSet.GetRasterBand(1).WriteArray(dataset)
    rasterSet.GetRasterBand(1).SetNoDataValue(-999)
    rasterSet = None

saveRaster(ndvi2014,path_NDVI_2014,cols,rows,projection)

saveRaster(ndvi2019,path_NDVI_2019,cols,rows,projection)

extentArray = [originX,finalX,originY,finalY]
def plotNDVI(ndviImage,extentArray,vmin,cmap):
    ndvi = gdal.Open(ndviImage)
    ds2019 = ndvi.ReadAsArray()
    plt.figure(figsize=(20,15))
    im = plt.imshow(ds2019, vmin=vmin, cmap=cmap, extent=extentArray)#
    plt.colorbar(im, fraction=0.015)
    plt.xlabel('Este')
    plt.ylabel('Norte')
    plt.show()
    
    # Save the plot to a file
    output_file = os.path.join("E:\\Just_Code\\BISAG-INTERN\\ML_Small_Task\\output\\", "res.png")
    plt.savefig(output_file)
    plt.close()  # Close the plot to free memory
    # return output_file

# ********************************************************************************* PLOT 1
plotNDVI(path_NDVI_2014,extentArray,0,'YlGn')

# ********************************************************************************* PLOT 2
plotNDVI(path_NDVI_2019,extentArray,0,'YlGn')
5
ndviChange = ndvi2019-ndvi2014
ndviChange = np.where((ndvi2014>-999) & (ndvi2019>-999),ndviChange,-999)
ndviChange
saveRaster(ndviChange,path_NDVIChange_19_14,cols,rows,projection)

# ********************************************************************************* PLOT 3
plotNDVI(path_NDVIChange_19_14,extentArray,-0.5,'Spectral')

Dataset_ndvi = gdal.Open(path_NDVIChange_19_14)#path_NDVI_2014
ndvi_raster = Dataset_ndvi.GetRasterBand(1)

ogr_ds = ogr.GetDriverByName("ESRI Shapefile").CreateDataSource(contours_NDVIChange_19_14)

prj=Dataset_ndvi.GetProjectionRef()#GetProjection()

srs = osr.SpatialReference(wkt=prj)#
#srs.ImportFromProj4(prj)

contour_shp = ogr_ds.CreateLayer('contour', srs)
field_defn = ogr.FieldDefn("ID", ogr.OFTInteger)
contour_shp.CreateField(field_defn)
field_defn = ogr.FieldDefn("ndviChange", ogr.OFTReal)
contour_shp.CreateField(field_defn)
#Generate Contourlines
gdal.ContourGenerate(ndvi_raster, 0.1, 0, [], 1, -999, contour_shp, 0, 1)
ogr_ds = None
