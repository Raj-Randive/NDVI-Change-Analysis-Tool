from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from ndvi_processor import process_ndvi_change

app = Flask(__name__)
UPLOAD_FOLDER = 'static/output'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def clear_output_folder():
    """Clear the contents of the output folder."""
    for filename in os.listdir(UPLOAD_FOLDER):
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        b4_2014 = request.files['b4_2014']
        b5_2014 = request.files['b5_2014']
        b4_2019 = request.files['b4_2019']
        b5_2019 = request.files['b5_2019']
        
        if b4_2014 and b5_2014 and b4_2019 and b5_2019:
            # Save files with their respective years
            b4_2014_filename = secure_filename(b4_2014.filename)
            b5_2014_filename = secure_filename(b5_2014.filename)
            b4_2019_filename = secure_filename(b4_2019.filename)
            b5_2019_filename = secure_filename(b5_2019.filename)
            
            b4_2014_year = extract_year(b4_2014_filename)
            b5_2014_year = extract_year(b5_2014_filename)
            b4_2019_year = extract_year(b4_2019_filename)
            b5_2019_year = extract_year(b5_2019_filename)
            
            b4_2014_path = os.path.join(app.config['UPLOAD_FOLDER'], f'B4_{b4_2014_year}.tif')
            b5_2014_path = os.path.join(app.config['UPLOAD_FOLDER'], f'B5_{b5_2014_year}.tif')
            b4_2019_path = os.path.join(app.config['UPLOAD_FOLDER'], f'B4_{b4_2019_year}.tif')
            b5_2019_path = os.path.join(app.config['UPLOAD_FOLDER'], f'B5_{b5_2019_year}.tif')
            
            b4_2014.save(b4_2014_path)
            b5_2014.save(b5_2014_path)
            b4_2019.save(b4_2019_path)
            b5_2019.save(b5_2019_path)
            
            ndvi_2014_path = os.path.join(app.config['UPLOAD_FOLDER'], f'NDVI_{b4_2014_year}.tif')
            ndvi_2019_path = os.path.join(app.config['UPLOAD_FOLDER'], f'NDVI_{b4_2019_year}.tif')
            ndvi_change_path = os.path.join(app.config['UPLOAD_FOLDER'], 'NDVIChange.tif')
            ndvi_change_image = os.path.join(app.config['UPLOAD_FOLDER'], 'NDVIChange.png')
                
            process_ndvi_change(b4_2014_path, b5_2014_path, b4_2019_path, b5_2019_path, ndvi_2014_path, ndvi_2019_path, ndvi_change_path, ndvi_change_image)

            ndvi_2014_png = url_for('static', filename=f'output/NDVI_{b4_2014_year}.png')
            ndvi_2019_png = url_for('static', filename=f'output/NDVI_{b4_2019_year}.png')
            return render_template('index.html', ndvi_2014_png=ndvi_2014_png, ndvi_2019_png=ndvi_2019_png, 
                                   ndvi_2014_year=b4_2014_year, ndvi_2019_year=b4_2019_year)
    
    # Render the index template with the Clear Files button
    return render_template('index.html')

@app.route('/result')
def result():
    ndvi_change_png = url_for('static', filename='output/NDVIChange.png')
    return render_template('result.html', ndvi_change_png=ndvi_change_png)

@app.route('/clear', methods=['POST'])
def clear_files():
    """Route to handle clearing all files in the output folder."""
    clear_output_folder()
    return redirect(url_for('index'))

def extract_year(filename):
    """Extracts the year from the filename in the format 'YYYY'."""
    # Split filename by underscores to isolate date sections
    parts = filename.split('_')
    
    # Look for sections that start with 'YYYY'
    for part in parts:
        if len(part) >= 4 and part[:4].isdigit():
            year = part[:4]  # Extract the first four digits
            return year
    return None


if __name__ == '__main__':
    app.run(debug=True)
