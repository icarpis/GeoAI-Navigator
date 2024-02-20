try:
    import ee
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", 'pip'])
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'wheel'])
    subprocess.check_call([sys.executable, "-m", "pip", "install", 'earthengine-api'])
finally:
    import ee



import requests
from datetime import datetime
import zipfile
import io

ee.Authenticate() 

# Initialize Google Earth Engine
ee.Initialize(project="ee-itaycarpis")

def generate_rectangle(center_point, width_meters, height_meters, height_from_ground):
    """
    Generate a rectangle based on center point, width, height, and height from ground.
    """
    center_lon, center_lat = center_point
    half_width = width_meters / 2
    half_height = height_meters / 2

    # Convert the width and height from meters to degrees
    degrees_per_meter = 1 / 111000  # Approximate conversion
    half_width_deg = half_width * degrees_per_meter
    half_height_deg = half_height * degrees_per_meter

    # Create rectangle vertices
    top_left = (center_lon - half_width_deg, center_lat + half_height_deg)
    top_right = (center_lon + half_width_deg, center_lat + half_height_deg)
    bottom_left = (center_lon - half_width_deg, center_lat - half_height_deg)
    bottom_right = (center_lon + half_width_deg, center_lat - half_height_deg)

    # Create rectangle geometry
    rectangle = ee.Geometry.Polygon([top_left, top_right, bottom_right, bottom_left])

    # Buffer the rectangle by height_from_ground
    buffered_rectangle = rectangle.buffer(height_from_ground)

    return buffered_rectangle

def collect_data(center_point, width_meters, height_meters, height_from_ground, output_folder, num_images):
    """
    Collect satellite images and GPS locations within a specified rectangle.
    """
    # Generate rectangle geometry
    rectangle = generate_rectangle(center_point, width_meters, height_meters, height_from_ground)

    # Filter satellite imagery
    dataset = ee.ImageCollection('LANDSAT/LC08/C01/T1_SR') \
        .filterBounds(rectangle) \
        .filterDate('2015-01-01', '2020-12-31') \
        .sort('CLOUD_COVER') \
        .limit(num_images)

    # Iterate over images
    for i, image in enumerate(dataset.getInfo()['features']):
        # Get image ID
        image_id = image['id']
        print(f'Downloading image {i + 1}/{num_images}: {image_id}')

        # Get image metadata
        image_metadata = ee.Image(image_id).getInfo()

        # Get GPS coordinates
        coordinates = image_metadata['properties']['system:footprint']['coordinates']
        gps_coords = [(coord[0], coord[1]) for coord in coordinates]

        # Download image
        image_url = ee.Image(image_id).getDownloadURL({
            'scale': 250,  # Adjust scale as needed
            'crs': 'EPSG:4326',  # WGS84 coordinate system
            'region': gps_coords
        })

        # Save image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Construct file name with timestamp
        filename = f"{timestamp}.zip"
        response = requests.get(image_url)

        if (response.status_code == 200):
            zip_file_bytes = io.BytesIO(response.content)
    
            # Create a ZipFile object from the file-like object
            with zipfile.ZipFile(zip_file_bytes, 'r') as zip_ref:
                # Extract all the contents to the specified folder
                zip_ref.extractall(timestamp + '\\')

                print("File downloaded successfully.")
        else:
            print("Failed to download file. Status code:", response.status_code)

# Example usage
center_point = (-122.084, 37.422)  # San Francisco coordinates
width_meters = 1000
height_meters = 1000
height_from_ground = 100
output_folder = './/'
num_images = 1

# Collect data
collect_data(center_point, width_meters, height_meters, height_from_ground, output_folder, num_images)
