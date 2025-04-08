from sklearn.cluster import MiniBatchKMeans
import numpy as np
from PIL import Image


class ImageColorAnalyzer:
    def __init__(self, image, num_colors):
        self.image = image.convert("RGB")
        self.num_colors = num_colors

    def analyze_colors(self):
        resized_image = self.resize_image(self.image)
        image_array = self.convert_image_to_array(resized_image)
        pixels = self.flatten_image_array(image_array)

        # Use extra clusters to allow filtering
        kmeans = MiniBatchKMeans(
            n_clusters=self.num_colors + 5, random_state=None, n_init=10
        )
        labels = kmeans.fit_predict(pixels)
        colors = kmeans.cluster_centers_

        sorted_indices, percentages = self.get_color_percentages(labels, len(colors))
        rgb_colors, hex_colors = self.get_rgb_and_hex_colors(colors[sorted_indices])

        # Filter out near-white shades
        filtered = [
            (hex_code, rgb, perc)
            for hex_code, rgb, perc in zip(hex_colors, rgb_colors, percentages)
            if not self.is_white(rgb)
        ]

        # Trim to requested number of colors
        filtered = filtered[: self.num_colors]

        if not filtered:
            return [], [], []

        # Normalize percentages
        total = sum(perc for _, _, perc in filtered)
        normalized = [
            (hex_code, rgb, (perc / total) * 100) for hex_code, rgb, perc in filtered
        ]

        hex_colors, rgb_colors, percentages = zip(*normalized)
        return list(hex_colors), list(rgb_colors), list(percentages)

    def is_white(self, rgb, brightness_threshold=239):  # Lowered by 1
        r, g, b = rgb
        brightness = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return brightness >= brightness_threshold

    def resize_image(self, image, size=(150, 150)):
        return image.resize(size)

    def convert_image_to_array(self, image):
        return np.array(image)

    def flatten_image_array(self, array):
        return array.reshape(-1, 3)

    def get_color_percentages(self, labels, num_clusters):
        counts = np.bincount(labels, minlength=num_clusters)
        total = np.sum(counts)
        sorted_indices = np.argsort(counts)[::-1]  # descending
        percentages = (counts[sorted_indices] / total) * 100
        return sorted_indices, percentages

    def get_rgb_and_hex_colors(self, colors):
        rgb_colors = [tuple(map(int, color)) for color in colors]
        hex_colors = [self.rgb_to_hex(rgb) for rgb in rgb_colors]
        return rgb_colors, hex_colors

    def rgb_to_hex(self, rgb):
        return "#{:02x}{:02x}{:02x}".format(*rgb)
