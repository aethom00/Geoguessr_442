import random
import requests
import os
import numpy as np
from city_image import CityImage
import geocoder

extreme_points = {'N': 50, 'S': 24, 'E': -66, 'W': -126}

MAX_LIMIT = 1000

def generate_random_coordinate():
    lat = random.uniform(extreme_points['S'], extreme_points['N'])
    long = random.uniform(extreme_points['W'], extreme_points['E'])
    return (long, lat)

    
def save_image(image_url, coordinates):
    # Ensure the 'Data' folder exists
    if not os.path.exists('Data'):
        os.makedirs('Data')

    # Format the filename using the coordinates, rounded to an appropriate number of decimal places
    filename = f"{round(coordinates[1], 6)}_{round(coordinates[0], 6)}.jpg"  # Latitude followed by Longitude

    # Full path to save the image
    file_path = os.path.join('Data', filename)

    # Download and save the image
    response = requests.get(image_url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
        #print(f"Saved image to {file_path}")
    else:
        print(f"Error downloading image: {response.status_code}, URL: {image_url}")


def find_images_in_bbox(bbox, token, limit):
    url = f'https://graph.mapillary.com/images?access_token={token}&fields=id&bbox={bbox}&limit={limit}&is_pano=false'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return [item['id'] for item in data['data']] if data.get('data') else []
    else:
        print(f"Error fetching data: {response.status_code}")
        return []
    
def get_image_url_from_id(image_id, token):
    url = f'https://graph.mapillary.com/{image_id}?access_token={token}&fields=id,thumb_1024_url,computed_geometry'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        image_url = data.get('thumb_1024_url')

        # Check if 'computed_geometry' and 'coordinates' are present
        if 'computed_geometry' in data and 'coordinates' in data['computed_geometry']:
            coordinates = data['computed_geometry']['coordinates']
            return image_url, coordinates
        else:
            return None, None
    else:
        print(f"Error fetching image details: {response.status_code}")
        return None, None

    
def generate_image(gui, app_access_token, limit):
    while True:
        i = random.randint(0, gui.num_rects_width - 1)
        j = random.randint(0, gui.num_rects_height - 1)
        top_left = gui.pixel_loc_to_lat_long(i * gui.square_amount[0], j * gui.square_amount[1])
        bottom_right = gui.pixel_loc_to_lat_long((i + 1) * gui.square_amount[0], (j + 1) * gui.square_amount[1])
        bbox = f"{top_left[1]},{bottom_right[0]},{bottom_right[1]},{top_left[0]}"
        print("Finding new image")
        image_ids = find_images_in_bbox(bbox, app_access_token, (limit if limit else MAX_LIMIT))
        if image_ids:
            # print(f"Found {len(image_ids)} images")
            for image_id in image_ids:
                image_url, image_coordinates = get_image_url_from_id(image_id, app_access_token)

                if not image_coordinates or not is_within_countries(image_coordinates, ['USA', 'CAN', 'MEX']):
                    # print(f"Image is not within the United States, Canada, or Mexico. Trying again...")
                    continue
            
                if image_url and image_coordinates:
                    save_image(image_url, image_coordinates)  
                else:
                    print(f"No valid image URL or coordinates for image ID: {image_id}")
            # print(f"Generated {len(image_ids)} Image(s)")
            print(f"Image Generated\n")
            return
        print(f"Couldn't find any images in the bounding box: [({top_left[1]}, {bottom_right[0]}), ({bottom_right[1]}, {top_left[0]})]. Trying again...")
                
def get_images(amount=float('inf'), shape=(100, 100)):
    images = []
    folder_path = 'Data'

    # Check if the directory exists
    if not os.path.exists(folder_path):
        print(f"Directory '{folder_path}' not found.")
        return np.array(images)

    for i, filename in enumerate(os.listdir(folder_path)):
        if i >= amount:  # Limit the number of images processed
            break

        if filename.endswith(".jpg") or filename.endswith(".png"):
            # Extract longitude and latitude from filename
            try:
                # Split the filename at the underscore and then remove the file extension
                lat_str, long_str = filename[:-4].split('_')
                lat, long = float(lat_str), float(long_str)
            except ValueError:
                print(f"Invalid filename format: {filename}")
                continue

            img_location = os.path.join(folder_path, filename)
            city_image = CityImage(img_location, shape)
            city_image.set_loc(long, lat)  # Ensure that the coordinates are set in the correct order
            images.append(city_image)

    return np.array(images)

import geocoder

def is_within_countries(coordinates, countries):
    g = geocoder.arcgis(coordinates[::-1], method='reverse')
    # print(g.country)
    return g.country in countries


