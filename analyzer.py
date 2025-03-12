import numpy as np
import webcolors
from sklearn.cluster import KMeans
from PIL import Image


def resize_image(image):
    return image.resize((200, 200))


def convert_image_to_array(image):
    return np.array(image)


def flatten_image_array(image_array):
    return image_array.reshape(-1, image_array.shape[-1])


def get_rgb_and_hex_colors(colors):
    rgb_colors = [
        tuple(int(color_value) for color_value in color[:3]) for color in colors
    ]
    hex_colors = [webcolors.rgb_to_hex(color) for color in rgb_colors]
    return rgb_colors, hex_colors


class ImageColorAnalyzer:
    def __init__(self, image, num_colors):
        self.image = image.convert("RGB")
        self.num_colors = num_colors

    def analyze_colors(self):
        resized_image = resize_image(self.image)
        image_array = convert_image_to_array(resized_image)
        pixels = flatten_image_array(image_array)

        # Perform KMeans clustering
        kmeans = KMeans(n_clusters=self.num_colors, random_state=None, n_init=10)
        kmeans.fit(pixels)
        colors = kmeans.cluster_centers_

        rgb_colors, hex_colors = get_rgb_and_hex_colors(colors)

        return hex_colors, rgb_colors
