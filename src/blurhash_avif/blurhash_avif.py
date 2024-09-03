import numpy as np
from PIL import Image
import base64
import blurhash
from pathlib import Path
from typing import Tuple, Optional


def generate_blurhash_from_avif(image_path: str) -> Optional[str]:
    """
    Generates a BlurHash string for an AVIF image.

    :param image_path: Path to the AVIF image file.
    :return: The BlurHash string, or None if an error occurred.
    """
    try:
        with Image.open(image_path) as image:
            if image.mode != "RGB":
                image = image.convert("RGB")

            max_dimension = 64
            width = min(image.width, max_dimension)
            height = int(image.height * (width / image.width))

            small_image = image.resize((width, height))
            image_array = np.array(small_image)

            return blurhash.encode(image_array, 4, 4)
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def generate_png_data_url_from_avif(image_path: str) -> Optional[str]:
    """
    Generates a base64-encoded PNG data URL for an AVIF image.

    :param image_path: Path to the AVIF image file.
    :return: The base64-encoded PNG data URL, or None if an error occurred.

    """
    try:
        with Image.open(image_path) as image:
            if image.mode != "RGB":
                image = image.convert("RGB")

            max_dimension = 64
            width = min(image.width, max_dimension)
            height = int(image.height * (width / image.width))

            small_image = image.resize((width, height))

            temp_file_path = Path("temp.png")
            small_image.save(temp_file_path, "PNG")
            png_bytes = temp_file_path.read_bytes()
            base64_png = base64.b64encode(png_bytes).decode("utf-8")
            data_url = f"data:image/png;base64,{base64_png}"
            temp_file_path.unlink()  # Remove temporary file

            return data_url
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def generate_blurhash_and_data_url_from_avif(image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates a BlurHash and a base64-encoded PNG data URL for an AVIF image.

    :param image_path: Path to the AVIF image file.
    :return: A tuple containing the BlurHash string and the base64-encoded PNG data URL.
    """
    return generate_blurhash_from_avif(image_path), generate_png_data_url_from_avif(image_path)
