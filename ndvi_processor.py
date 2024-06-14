from osgeo import gdal
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use 'Agg' backend for non-interactive plotting
import matplotlib.pyplot as plt

def compute_ndvi(B4_path, B5_path, output_path):
    B4 = gdal.Open(B4_path)
    B5 = gdal.Open(B5_path)
    
    B4_Data = B4.GetRasterBand(1).ReadAsArray().astype(np.float32)
    B5_Data = B5.GetRasterBand(1).ReadAsArray().astype(np.float32)
    
    ndvi = (B5_Data - B4_Data) / (B5_Data + B4_Data)
    
    cols = B4.RasterXSize
    rows = B4.RasterYSize
    projection = B4.GetProjection()
    geotransform = B4.GetGeoTransform()
    
    def save_raster(dataset, dataset_path, cols, rows, projection, geotransform):
        raster_set = gdal.GetDriverByName('GTiff').Create(dataset_path, cols, rows, 1, gdal.GDT_Float32)
        raster_set.SetProjection(projection)
        raster_set.SetGeoTransform(geotransform)
        raster_set.GetRasterBand(1).WriteArray(dataset)
        raster_set.GetRasterBand(1).SetNoDataValue(-999)
        raster_set = None
    
    save_raster(ndvi, output_path, cols, rows, projection, geotransform)

def plot_ndvi(ndvi_image, extent_array, vmin, cmap, output_image):
    ndvi = gdal.Open(ndvi_image)
    ds = ndvi.ReadAsArray()
    plt.figure(figsize=(8, 8))
    im = plt.imshow(ds, vmin=vmin, cmap=cmap, extent=extent_array)
    plt.colorbar(im, fraction=0.015)
    plt.xlabel('East')
    plt.ylabel('North')
    plt.savefig(output_image, bbox_inches='tight')
    plt.close()  # Close the plot to avoid memory leaks

def process_ndvi_change(B4_path_1, B5_path_1, B4_path_2, B5_path_2, ndvi_path_1, ndvi_path_2, ndvi_change_path, ndvi_change_image):
    compute_ndvi(B4_path_1, B5_path_1, ndvi_path_1)
    compute_ndvi(B4_path_2, B5_path_2, ndvi_path_2)
    
    ndvi_1 = gdal.Open(ndvi_path_1).ReadAsArray().astype(np.float32)
    ndvi_2 = gdal.Open(ndvi_path_2).ReadAsArray().astype(np.float32)
    
    ndvi_change = ndvi_2 - ndvi_1
    ndvi_change = np.where((ndvi_1 > -999) & (ndvi_2 > -999), ndvi_change, -999)
    
    cols = gdal.Open(B4_path_1).RasterXSize
    rows = gdal.Open(B4_path_1).RasterYSize
    projection = gdal.Open(B4_path_1).GetProjection()
    geotransform = gdal.Open(B4_path_1).GetGeoTransform()
    
    def save_raster(dataset, dataset_path, cols, rows, projection, geotransform):
        raster_set = gdal.GetDriverByName('GTiff').Create(dataset_path, cols, rows, 1, gdal.GDT_Float32)
        raster_set.SetProjection(projection)
        raster_set.SetGeoTransform(geotransform)
        raster_set.GetRasterBand(1).WriteArray(dataset)
        raster_set.GetRasterBand(1).SetNoDataValue(-999)
        raster_set = None
    
    save_raster(ndvi_change, ndvi_change_path, cols, rows, projection, geotransform)
    
    plot_ndvi(ndvi_change_path, [geotransform[0], geotransform[0] + cols * geotransform[1], geotransform[3] + rows * geotransform[5], geotransform[3]], -0.5, 'Spectral', ndvi_change_image)
    
    plot_ndvi(ndvi_path_1, [geotransform[0], geotransform[0] + cols * geotransform[1], geotransform[3] + rows * geotransform[5], geotransform[3]], 0, 'YlGn', ndvi_path_1.replace('.tif', '.png'))
    plot_ndvi(ndvi_path_2, [geotransform[0], geotransform[0] + cols * geotransform[1], geotransform[3] + rows * geotransform[5], geotransform[3]], 0, 'YlGn', ndvi_path_2.replace('.tif', '.png'))
