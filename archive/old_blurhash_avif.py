# pyrefly: ignore-all-errors

import base64
import logging as logger
from pathlib import Path
from typing import TYPE_CHECKING, Any

import blurhash
import numpy as np
from PIL import Image as PilImage

if TYPE_CHECKING:
    from numpy.typing import NDArray

logger.basicConfig(level=logger.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logging = logger.getLogger(__name__)


def encode_image_to_blurhash(image_path: str) -> str | None:
    """Generates a BlurHash string for an AVIF image.

    Args:
        image_path: Path to the AVIF image file.

    Returns:
        The BlurHash string, or None if an error occurred.
    """
    try:
        with PilImage.open(image_path) as image:
            rgb_image: PilImage.Image = image
            if image.mode != "RGB":
                rgb_image = image.convert("RGB")
            max_dimension = 64
            width = min(rgb_image.width, max_dimension)
            height = int(rgb_image.height * (width / rgb_image.width))
            small_image = rgb_image.resize((width, height))
            image_array: NDArray[np.uint8] = np.array(small_image)
            return blurhash.encode(image_array, 4, 4)  # type: ignore
    except Exception:
        logging.exception("An error occurred")
        return None


def encode_image_to_png_data_url(image_path: str) -> str | None:
    """Generates a base64-encoded PNG data URL for an AVIF image.

    Args:
        image_path: Path to the AVIF image file.

    Returns:
        The base64-encoded PNG data URL, or None if an error occurred.
    """
    try:
        with PilImage.open(image_path) as image:
            rgb_image: PilImage.Image = image
            if image.mode != "RGB":
                rgb_image = image.convert("RGB")
            max_dimension = 64
            width = min(rgb_image.width, max_dimension)
            height = int(rgb_image.height * (width / rgb_image.width))
            small_image = rgb_image.resize((width, height))
            temp_file_path = Path("temp.png")
            small_image.save(temp_file_path, "PNG")
            png_bytes = temp_file_path.read_bytes()
            base64_png = base64.b64encode(png_bytes).decode("utf-8")
            data_url = f"data:image/png;base64,{base64_png}"
            temp_file_path.unlink()  # Remove temporary file
            return data_url
    except Exception:
        logging.exception("An error occurred while encoding image to PNG data URL")
        return None


def encode_image_to_blurhash_and_png_data_url(image_path: str) -> tuple[str | None, str | None]:
    """Generates a BlurHash and a base64-encoded PNG data URL for an AVIF image.

    Args:
        image_path: Path to the AVIF image file.

    Returns:
        A tuple containing the BlurHash string and the base64-encoded PNG data URL.
    """
    return encode_image_to_blurhash(image_path), encode_image_to_png_data_url(image_path)


def batch_encode_image_to_blurhash(directory: str) -> dict[str, str | None]:
    """Generates BlurHash strings for all AVIF images in a given directory.

    Args:
        directory: Path to the directory containing AVIF images.

    Returns:
        A dictionary with image names as keys and BlurHash strings as values.
    """
    result: dict[str, str | None] = {}
    for image_path in Path(directory).glob("*.avif"):
        blurhash = encode_image_to_blurhash(str(image_path))
        result[image_path.name] = blurhash
    return result


def batch_encode_image_to_png_data_url(directory: str) -> dict[str, str | None]:
    """Generates base64-encoded PNG data URLs for all AVIF images in a given directory.

    Args:
        directory: Path to the directory containing AVIF images.

    Returns:
        A dictionary with image names as keys and PNG data URLs as values.
    """
    result: dict[str, str | None] = {}
    for image_path in Path(directory).glob("*.avif"):
        data_url = encode_image_to_png_data_url(str(image_path))
        result[image_path.name] = data_url
    return result


def batch_encode_image_to_blurhash_and_png_data_url(
    directory: str,
) -> tuple[dict[str, str | None], dict[str, str | None]]:
    """Generates BlurHash strings and base64-encoded PNG data URLs for all AVIF images in a given directory.

    Args:
        directory: Path to the directory containing AVIF images.

    Returns:
        A tuple containing two dictionaries. The first dictionary has image names as keys and BlurHash strings as values.
        The second dictionary has image names as keys and PNG data URLs as values.
    """
    blurhash_dict: dict[str, str | None] = {}
    data_url_dict: dict[str, str | None] = {}
    for image_path in Path(directory).glob("*.avif"):
        blurhash, data_url = encode_image_to_blurhash_and_png_data_url(str(image_path))
        blurhash_dict[image_path.name] = blurhash
        data_url_dict[image_path.name] = data_url
    return blurhash_dict, data_url_dict


# decode blurhash to png image


def decode_blurhash_data_to_image(blurhash_string: str, width: int, height: int) -> PilImage.Image | None:
    """Decode a Blurhash string into a PIL Image.

    Args:
        blurhash_string: The BlurHash string to decode.
        width: The width of the output image.
        height: The height of the output image.

    Returns:
        A PIL Image object or None if decoding fails.
    """
    try:
        decoded: Any = blurhash.decode(blurhash_string, width, height)  # type: ignore
        return PilImage.fromarray(np.array(decoded, dtype=np.uint8))
    except Exception:
        logging.exception("Failed to decode Blurhash string")
        return None


def save_image(image: PilImage.Image, filename: Path) -> None:
    """Save a PIL Image to a file with progressive loading and optimization.

    Args:
        image: The PIL Image object to save.
        filename: The filename to save the image to.
    """
    try:
        image.save(filename, optimize=True, progressive=True, compress_level=9, interlace=True)
    except Exception:
        logging.exception("Failed to save image")


def decode_blurhash_to_image(
    output_path: Path, blurhash_string: str, filename: str = "output.png", width: int = 400, height: int = 300
) -> None:
    """Decode Blurhash strings and save the decoded images as PNG files.

    Args:
        output_path: Path to the directory where decoded images will be saved.
        blurhash_string: BlurHash string to decode.
        filename: Output filename (default: "output.png").
        width: Output image width (default: 400).
        height: Output image height (default: 300).
    """
    output_path.mkdir(parents=True, exist_ok=True)

    decoded_image: PilImage.Image | None = decode_blurhash_data_to_image(blurhash_string, width, height)
    if decoded_image is not None:
        output_filename: Path = output_path / filename.replace(".avif", ".png")
        save_image(decoded_image, output_filename)
        logging.info(f"Successfully Decoded and saved: {output_filename}")
    else:
        logging.error(f"Failed to decode Blurhash string for: {filename}")
