from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt
from celery import Celery

# sudo service redis-server start
# Starting redis-server: redis-server.
# mahek@DESKTOP-91B30J6:~$ redis-cli ping
# PONG

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/output'
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

def clear_output_folder():
    """Clear the contents of the output folder."""
    for filename in os.listdir(app.config['UPLOAD_FOLDER']):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        year1 = request.files['year1']
        year2 = request.files['year2']
        
        if year1 and year2:
            year1_filename = secure_filename(year1.filename)
            year2_filename = secure_filename(year2.filename)
            
            year1_year = extract_year(year1_filename)
            year2_year = extract_year(year2_filename)
            
            year1_path = os.path.join(app.config['UPLOAD_FOLDER'], f'geo_merged.tif')
            year2_path = os.path.join(app.config['UPLOAD_FOLDER'], f'geo_merged_1.tif')
            
            year1.save(year1_path)
            year2.save(year2_path)
            
            ndvi_change_path = os.path.join(app.config['UPLOAD_FOLDER'], 'NDVIChange.tif')
            ndvi_change_image = os.path.join(app.config['UPLOAD_FOLDER'], 'NDVIChange.png')
                
            process_ndvi_change.delay(year1_path, year2_path, ndvi_change_path, ndvi_change_image)

            ndvi_2014_png = url_for('static', filename=f'output/NDVI_{year1_year}.png')
            ndvi_2019_png = url_for('static', filename=f'output/NDVI_{year2_year}.png')
            
            return render_template('index.html')
    
    return render_template('index.html')

@app.route('/result')
def result():
    ndvi_change_png = url_for('static', filename='output/NDVIChange.png')
    return render_template('result.html', ndvi_change_png=ndvi_change_png)

@app.route('/clear', methods=['POST'])
def clear_files():
    clear_output_folder()
    return redirect(url_for('index'))

def extract_year(filename):
    """Extracts the year from the filename in the format 'YYYY'."""
    parts = filename.split('_')
    for part in parts:
        if len(part) >= 4 and part[:4].isdigit():
            year = part[:4]
            return year
    return None

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

if __name__ == '__main__':
    app.run(debug=True)