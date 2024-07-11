from celery import Celery

celery = Celery('app', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')

@celery.task
def process_ndvi_change(path1, path2, ndvi_change_path, ndvi_change_image):
    def read_in_chunks(dataset, chunk_size=1024):
        band = dataset.GetRasterBand(1)
        cols = dataset.RasterXSize
        rows = dataset.RasterYSize
        
        for i in range(0, rows, chunk_size):
            num_rows = min(chunk_size, rows - i)
            for j in range(0, cols, chunk_size):
                num_cols = min(chunk_size, cols - j)
                data = band.ReadAsArray(j, i, num_cols, num_rows)
                yield data, i, j, num_rows, num_cols

    def save_raster(dataset, dataset_path, cols, rows, projection, geotransform):
        raster_set = gdal.GetDriverByName('GTiff').Create(dataset_path, cols, rows, 1, gdal.GDT_Float32)
        raster_set.SetProjection(projection)
        raster_set.SetGeoTransform(geotransform)
        raster_set.GetRasterBand(1).WriteArray(dataset)
        raster_set.GetRasterBand(1).SetNoDataValue(-999)
        raster_set = None

    def plot_ndvi(ndvi_image, extent_array, vmin, cmap, output_image):
        ndvi = gdal.Open(ndvi_image)
        ds = ndvi.ReadAsArray()
        plt.figure(figsize=(8, 8))
        im = plt.imshow(ds, vmin=vmin, cmap=cmap, extent=extent_array)
        plt.colorbar(im, fraction=0.015)
        plt.xlabel('East')
        plt.ylabel('North')
        plt.savefig(output_image, bbox_inches='tight')
        plt.close()

    ds1 = gdal.Open(path1)
    ds2 = gdal.Open(path2)
    
    cols = ds1.RasterXSize
    rows = ds1.RasterYSize
    projection = ds1.GetProjection()
    geotransform = ds1.GetGeoTransform()
    
    driver = gdal.GetDriverByName('GTiff')
    ndvi_change_ds = driver.Create(ndvi_change_path, cols, rows, 1, gdal.GDT_Float32)
    ndvi_change_ds.SetProjection(projection)
    ndvi_change_ds.SetGeoTransform(geotransform)
    out_band = ndvi_change_ds.GetRasterBand(1)
    out_band.SetNoDataValue(-999)
    
    chunk_size = 1024
    
    for chunk1, i, j, num_rows1, num_cols1 in read_in_chunks(ds1, chunk_size):
        chunk2, _, _, num_rows2, num_cols2 = next(read_in_chunks(ds2, chunk_size))
        
        if num_rows1 != num_rows2 or num_cols1 != num_cols2:
            chunk2 = chunk2[:num_rows1, :num_cols1]
        
        chunk1 = chunk1.astype(np.float32)
        chunk2 = chunk2.astype(np.float32)
        
        ndvi_1 = (chunk1 - chunk2) / (chunk1 + chunk2)
        ndvi_2 = (chunk2 - chunk1) / (chunk2 + chunk1)
        
        ndvi_change = ndvi_2 - ndvi_1
        ndvi_change = np.where((chunk1 > -999) & (chunk2 > -999), ndvi_change, -999)
        
        out_band.WriteArray(ndvi_change, j, i)
    
    ndvi_change_ds = None
    
    plot_ndvi(ndvi_change_path, [geotransform[0], geotransform[0] + cols * geotransform[1], geotransform[3] + rows * geotransform[5], geotransform[3]], -0.5, 'Spectral', ndvi_change_image)
    plot_ndvi(path1, [geotransform[0], geotransform[0] + cols * geotransform[1], geotransform[3] + rows * geotransform[5], geotransform[3]], 0, 'YlGn', path1.replace('.tif', '.png'))
    plot_ndvi(path2, [geotransform[0], geotransform[0] + cols * geotransform[1], geotransform[3] + rows * geotransform[5], geotransform[3]], 0, 'YlGn', path2.replace('.tif', '.png'))