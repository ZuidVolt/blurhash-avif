import numpy as np
from PIL import Image
import pillow_avif  # noqa: F401 RUF100 # type: ignore # Imported for its side effects
import base64
import blurhash
from pathlib import Path
from typing import Tuple, Optional, Dict
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def encode_image_to_blurhash(image_path: str) -> Optional[str]:
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
        logging.error(f"An error occurred: {e}")
        return None


def encode_image_to_png_data_url(image_path: str) -> Optional[str]:
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
        logging.error(f"An error occurred: {e}")
        return None


def encode_image_to_blurhash_and_png_data_url(image_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Generates a BlurHash and a base64-encoded PNG data URL for an AVIF image.
    :param image_path: Path to the AVIF image file.
    :return: A tuple containing the BlurHash string and the base64-encoded PNG data URL.
    """
    return encode_image_to_blurhash(image_path), encode_image_to_png_data_url(image_path)


def batch_encode_image_to_blurhash(directory: str) -> Dict[str, Optional[str]]:
    """
    Generates BlurHash strings for all AVIF images in a given directory.
    :param directory: Path to the directory containing AVIF images.
    :return: A dictionary with image names as keys and BlurHash strings as values.
    """
    result = {}
    for image_path in Path(directory).glob("*.avif"):
        blurhash = encode_image_to_blurhash(str(image_path))
        result[image_path.name] = blurhash
    return result


def batch_encode_image_to_png_data_url(directory: str) -> Dict[str, Optional[str]]:
    """
    Generates base64-encoded PNG data URLs for all AVIF images in a given directory.
    :param directory: Path to the directory containing AVIF images.
    :return: A dictionary with image names as keys and PNG data URLs as values.
    """
    result = {}
    for image_path in Path(directory).glob("*.avif"):
        data_url = encode_image_to_png_data_url(str(image_path))
        result[image_path.name] = data_url
    return result


def batch_encode_image_to_blurhash_and_png_data_ur(
    directory: str,
) -> Tuple[Dict[str, Optional[str]], Dict[str, Optional[str]]]:
    """
    Generates BlurHash strings and base64-encoded PNG data URLs for all AVIF images in a given directory.
    :param directory: Path to the directory containing AVIF images.
    :return: A tuple containing two dictionaries. The first dictionary has image names as keys and BlurHash strings as values.
             The second dictionary has image names as keys and PNG data URLs as values.
    """
    blurhash_dict = {}
    data_url_dict = {}
    for image_path in Path(directory).glob("*.avif"):
        blurhash, data_url = encode_image_to_blurhash_and_png_data_url(str(image_path))
        blurhash_dict[image_path.name] = blurhash
        data_url_dict[image_path.name] = data_url
    return blurhash_dict, data_url_dict


# decode blurhash to png image


def decode_blurhash_data_to_image(blurhash_string: str, width: int, height: int) -> Image:
    """Decode a Blurhash string into a PIL Image."""
    try:
        decoded = blurhash.decode(blurhash_string, width, height)
        return Image.fromarray(np.array(decoded, dtype=np.uint8))
    except Exception as e:
        logging.error(f"Failed to decode Blurhash string: {e}")
        return None


def save_image(image: Image, filename: str) -> None:
    """Save a PIL Image to a file with progressive loading and optimization"""
    try:
        image.save(filename, optimize=True, progressive=True, compress_level=9, interlace=True)
    except Exception as e:
        logging.error(f"Failed to save image: {e}")


def decode_blurhash_to_image(
    output_path: str, blurhash_string: str, filename: str = "output.png", width: int = 400, height: int = 300
) -> None:
    """
    Decode Blurhash strings and save the decoded images as PNG files.
    :param output_path: Path to the directory where decoded images will be saved.
    :param blurhash_string: BlurHash string to decode.
    :param filename: Output filename (default: "output.png").
    :param width: Output image width (default: 400).
    :param height: Output image height (default: 300).
    """
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    decoded_image = decode_blurhash_data_to_image(blurhash_string, width, height)
    if decoded_image is not None:
        output_filename = output_path / filename.replace(".avif", ".png")
        save_image(decoded_image, output_filename)
        logging.info(f"Successfully Decoded and saved: {output_filename}")
    else:
        logging.error(f"Failed to decode Blurhash string for: {filename}")
