# tests/__init__.py
import unittest
from pathlib import Path
from PIL import Image
from src.blurhash_avif import (
    generate_blurhash_from_avif,
    generate_png_data_url_from_avif,
    generate_blurhash_and_data_url_from_avif,
)


class TestBlurhashAvif(unittest.TestCase):
    def test_generate_blurhash_from_avif(self):
        # Create a test AVIF image
        image_path = "tests/test_image.avif"
        image = Image.new("RGB", (100, 100), (255, 0, 0))  # Create a 100x100 red image
        image.save(image_path, "AVIF")

        # Generate the BlurHash
        blurhash = generate_blurhash_from_avif(image_path)

        # Check that the BlurHash is not None
        self.assertIsNotNone(blurhash)

        # Check that the BlurHash is a string
        self.assertIsInstance(blurhash, str)

        # Remove the test image
        Path(image_path).unlink()

    def test_generate_png_data_url_from_avif(self):
        # Create a test AVIF image
        image_path = "tests/test_image.avif"
        image = Image.new("RGB", (100, 100), (255, 0, 0))  # Create a 100x100 red image
        image.save(image_path, "AVIF")

        # Generate the PNG data URL
        data_url = generate_png_data_url_from_avif(image_path)

        # Check that the data URL is not None
        self.assertIsNotNone(data_url)

        # Check that the data URL is a string
        self.assertIsInstance(data_url, str)

        # Check that the data URL starts with "data:image/png;base64,"
        self.assertTrue(data_url.startswith("data:image/png;base64,"))

        # Remove the test image
        Path(image_path).unlink()

    def test_generate_blurhash_and_data_url_from_avif(self):
        # Create a test AVIF image
        image_path = "tests/test_image.avif"
        image = Image.new("RGB", (100, 100), (255, 0, 0))  # Create a 100x100 red image
        image.save(image_path, "AVIF")

        # Generate the BlurHash and PNG data URL
        blurhash, data_url = generate_blurhash_and_data_url_from_avif(image_path)

        # Check that the BlurHash is not None
        self.assertIsNotNone(blurhash)

        # Check that the BlurHash is a string
        self.assertIsInstance(blurhash, str)

        # Check that the data URL is not None
        self.assertIsNotNone(data_url)

        # Check that the data URL is a string
        self.assertIsInstance(data_url, str)

        # Check that the data URL starts with "data:image/png;base64,"
        self.assertTrue(data_url.startswith("data:image/png;base64,"))

        # Remove the test image
        Path(image_path).unlink()


if __name__ == "__main__":
    unittest.main()
