import unittest
from pathlib import Path

from PIL import Image

from src.blurhash_avif import (
    AvifPngDataUrlError,
    BlurHashEncodeError,
    PathError,
    encode,
    encode_blurhash_and_pda,
    encode_pdu,
)


class TestBlurhashAvif(unittest.TestCase):
    def test_generate_blurhash_from_avif(self) -> None:
        # Create a test AVIF image
        image_path = "tests/test_image.avif"
        image = Image.new("RGB", (100, 100), (255, 0, 0))  # Create a 100x100 red image
        image.save(image_path, "AVIF")

        # Generate the BlurHash
        blurhash = encode(image_path)

        # Check that the BlurHash is not None
        self.assertIsNotNone(blurhash)

        # Check that the BlurHash is a string
        self.assertIsInstance(blurhash, str)

        # Remove the test image
        Path(image_path).unlink()

    def test_generate_png_data_url_from_avif(self) -> None:
        # Create a test AVIF image
        image_path = "tests/test_image.avif"
        image = Image.new("RGB", (100, 100), (255, 0, 0))  # Create a 100x100 red image
        image.save(image_path, "AVIF")

        # Generate the PNG data URL
        data_url = encode_pdu(image_path)

        # Check that the data URL is not None
        self.assertIsNotNone(data_url)

        # Check that the data URL is a string
        self.assertIsInstance(data_url, str)

        # Check that the data URL starts with "data:image/png;base64,"
        self.assertTrue(data_url.startswith("data:image/png;base64,"))

        # Remove the test image
        Path(image_path).unlink()

    def test_generate_blurhash_and_data_url_from_avif(self) -> None:
        # Create a test AVIF image
        image_path = "tests/test_image.avif"
        image = Image.new("RGB", (100, 100), (255, 0, 0))  # Create a 100x100 red image
        image.save(image_path, "AVIF")

        # Generate the BlurHash and PNG data URL
        blurhash, data_url = encode_blurhash_and_pda(image_path)

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

    def test_encode_nonexistent_path(self) -> None:
        with self.assertRaises(PathError):
            encode("nonexistent.avif")

    def test_encode_empty_file(self) -> None:
        image_path = "tests/empty.avif"
        Path(image_path).touch()
        try:
            with self.assertRaises(BlurHashEncodeError):
                encode(image_path)
        finally:
            Path(image_path).unlink(missing_ok=True)

    def test_encode_non_image_file(self) -> None:
        image_path = "tests/bad.avif"
        Path(image_path).write_text("not an image", encoding="utf-8")
        try:
            with self.assertRaises(BlurHashEncodeError):
                encode(image_path)
        finally:
            Path(image_path).unlink(missing_ok=True)

    def test_encode_pdu_nonexistent_path(self) -> None:
        with self.assertRaises(PathError):
            encode_pdu("nonexistent.avif")

    def test_encode_pdu_empty_file(self) -> None:
        image_path = "tests/empty.avif"
        Path(image_path).touch()
        try:
            with self.assertRaises(AvifPngDataUrlError):
                encode_pdu(image_path)
        finally:
            Path(image_path).unlink(missing_ok=True)

    def test_encode_pdu_non_image_file(self) -> None:
        image_path = "tests/bad.avif"
        Path(image_path).write_text("not an image", encoding="utf-8")
        try:
            with self.assertRaises(AvifPngDataUrlError):
                encode_pdu(image_path)
        finally:
            Path(image_path).unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
