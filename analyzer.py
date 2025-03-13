import numpy as np
import webcolors
from sklearn.cluster import KMeans
from PIL import Image


def resize_image(image, size=(200, 200)):
    """Resize the image to reduce computation time."""
    return image.resize(size)


def convert_image_to_array(image):
    """Convert image to NumPy array."""
    return np.array(image)


def flatten_image_array(image_array):
    """Flatten the image array to a list of pixels."""
    return image_array.reshape(-1, image_array.shape[-1])


def get_rgb_and_hex_colors(colors):
    """Convert RGB colors to HEX values."""
    rgb_colors = [tuple(map(int, color[:3])) for color in colors]
    hex_colors = [webcolors.rgb_to_hex(color) for color in rgb_colors]
    return rgb_colors, hex_colors


def get_color_percentages(labels, num_colors):
    """Calculate the percentage of each color in the image."""
    unique_labels, counts = np.unique(labels, return_counts=True)
    percentages = (counts / counts.sum()) * 100
    sorted_indices = np.argsort(-percentages)  # Sort in descending order
    return sorted_indices, percentages[sorted_indices]


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
        labels = kmeans.fit_predict(pixels)
        colors = kmeans.cluster_centers_

        # Get RGB, HEX, and color percentages
        sorted_indices, percentages = get_color_percentages(labels, self.num_colors)
        rgb_colors, hex_colors = get_rgb_and_hex_colors(colors[sorted_indices])

        return hex_colors, rgb_colors, percentages
