"""blurhash_avif - BlurHash and PNG data URL encoder/decoder for AVIF images.

This module provides utilities for:
- Encoding AVIF images to BlurHash strings for progressive loading placeholders
- Creating base64-encoded PNG data URLs from AVIF images
- Decoding BlurHash strings back to images
- Batch processing of multiple AVIF images
"""

from __future__ import annotations

import base64
import contextlib
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import blurhash
import numpy as np
import pillow_avif  # noqa: F401 RUF100 # type: ignore # Imported for its side effects
from PIL import Image


class BlurHashAvifError(Exception):
    """Base exception for blurhash_avif operations."""


class BlurHashEncodeError(BlurHashAvifError):
    """Exception raised when BlurHash encoding fails."""


class AvifPngDataUrlError(BlurHashAvifError):
    """Exception raised when PNG data URL encoding fails."""


class BlurHashDecodeError(BlurHashAvifError):
    """Exception raised when BlurHash decoding fails."""


class PathError(BlurHashAvifError):
    """Exception raised when path operations fail."""


class ImageSaveError(BlurHashAvifError):
    """Exception raised when saving an image fails."""


def encode(image_path: str | Path, x_components: int = 4, y_components: int = 4, max_dimension: int = 64) -> str:
    """Generates a BlurHash string for an AVIF image.

    The image is resized to a maximum dimension of 64 pixels before encoding by default
    to optimize performance while maintaining visual quality.

    Args:
        image_path: Path to the AVIF image file. Can be a string or Path object.
        x_components: Number of horizontal components (1-9, default: 4).
        y_components: Number of vertical components (1-9, default: 4).
        max_dimension: Maximum dimension of the resized image (default: 64).

    Returns:
        The BlurHash string representation of the image.

    Raises:
        PathError: If the image path is invalid or doesn't exist.
        BlurHashEncodeError: If the image cannot be opened or encoded.
        ValueError: If component values are out of valid range.
    """
    # Validate components
    if not 1 <= x_components <= 9:  # noqa: PLR2004
        msg = f"x_components must be between 1 and 9, got {x_components}"
        raise ValueError(msg)
    if not 1 <= y_components <= 9:  # noqa: PLR2004
        msg = f"y_components must be between 1 and 9, got {y_components}"
        raise ValueError(msg)

    # Convert to Path object and validate
    try:
        path_obj = Path(image_path)
    except (TypeError, ValueError) as e:
        msg = f"Invalid image path type: {type(image_path).__name__}"
        raise PathError(msg) from e

    if not path_obj.exists():
        msg = f"Image file does not exist: {path_obj}"
        raise PathError(msg)

    if not path_obj.is_file():
        msg = f"Path is not a file: {path_obj}"
        raise PathError(msg)

    # Process the image
    try:
        with Image.open(path_obj) as original_image:
            # Ensure RGB mode for consistent encoding
            image = original_image.convert("RGB") if original_image.mode != "RGB" else original_image

            # Guard against invalid image dimensions
            if image.width <= 0 or image.height <= 0:
                msg = f"Invalid image dimensions: {image.width}x{image.height}"
                raise BlurHashEncodeError(msg)  # noqa: TRY301

            # Resize
            if image.width > max_dimension or image.height > max_dimension:
                scale = max(image.width, image.height) / float(max_dimension)
                new_width = max(1, int(image.width / scale))
                new_height = max(1, int(image.height / scale))
                small_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                small_image = image

            # Convert to numpy array and encode
            image_array = np.array(small_image)
            return str(blurhash.encode(image_array, x_components, y_components))

    except OSError as e:
        msg = f"Failed to open image file: {path_obj}"
        raise BlurHashEncodeError(msg) from e
    except Exception as e:
        msg = f"Failed to encode image to blurhash: {path_obj}"
        raise BlurHashEncodeError(msg) from e


def encode_pdu(image_path: str | Path, max_dimension: int = 64) -> str:  # noqa: C901
    """Generates a base64-encoded PNG data URL for an AVIF image.

    The image is resized to the specified maximum dimension to create
    a lightweight preview suitable for inline embedding.

    Args:
        image_path: Path to the AVIF image file. Can be a string or Path object.
        max_dimension: Maximum width/height for the thumbnail (default: 64).

    Returns:
        A data URL string in the format: data:image/png;base64,[base64-data]

    Raises:
        PathError: If the image path is invalid or doesn't exist.
        AvifPngDataUrlError: If the image cannot be processed or encoded.
        ValueError: If max_dimension is not positive.
    """
    # Validate max_dimension
    if max_dimension <= 0:
        msg = f"max_dimension must be positive, got {max_dimension}"
        raise ValueError(msg)

    # Convert to Path object and validate
    try:
        path_obj = Path(image_path)
    except (TypeError, ValueError) as e:
        msg = f"Invalid image path type: {type(image_path).__name__}"
        raise PathError(msg) from e

    if not path_obj.exists():
        msg = f"Image file does not exist: {path_obj}"
        raise PathError(msg)

    if not path_obj.is_file():
        msg = f"Path is not a file: {path_obj}"
        raise PathError(msg)

    # Process the image
    try:
        with Image.open(path_obj) as original_image:
            image = original_image.convert("RGB") if original_image.mode != "RGB" else original_image

            if image.width <= 0 or image.height <= 0:
                msg = f"Invalid image dimensions: {image.width}x{image.height}"
                raise AvifPngDataUrlError(msg)  # noqa: TRY301

            # Calculate resize dimensions maintaining aspect ratio (mirror logic from encode)
            if image.width > max_dimension or image.height > max_dimension:
                scale = max(image.width, image.height) / float(max_dimension)
                new_width = max(1, int(image.width / scale))
                new_height = max(1, int(image.height / scale))
                small_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                small_image = image

            # Encode to PNG in memory
            buffer = BytesIO()
            small_image.save(buffer, format="PNG", optimize=True)
            png_bytes = buffer.getvalue()

            if not png_bytes:
                msg = "Failed to encode image to PNG: empty result"
                raise AvifPngDataUrlError(msg)  # noqa: TRY301

            base64_png = base64.b64encode(png_bytes).decode("utf-8")
            return f"data:image/png;base64,{base64_png}"

    except OSError as e:
        msg = f"Failed to open image file: {path_obj}"
        raise AvifPngDataUrlError(msg) from e
    except Exception as e:
        if isinstance(e, AvifPngDataUrlError):
            raise
        msg = f"Failed to encode image to PNG data URL: {path_obj}"
        raise AvifPngDataUrlError(msg) from e


def encode_blurhash_and_pda(
    image_path: str | Path, x_components: int = 4, y_components: int = 4, max_dimension: int = 64
) -> tuple[Optional[str], Optional[str]]:
    """Generates both a BlurHash and a PNG data URL for an AVIF image.

    This is a convenience function that performs both encodings in a single call.
    Errors in one encoding don't prevent the other from being attempted.

    Args:
        image_path: Path to the AVIF image file.
        x_components: Number of horizontal BlurHash components (1-9, default: 4).
        y_components: Number of vertical BlurHash components (1-9, default: 4).
        max_dimension: Maximum dimension for the PNG thumbnail (default: 64).

    Returns:
        A tuple of (blurhash_string, png_data_url). Either value may be None
        if its respective encoding fails.
    """
    blurhash_result = None
    data_url_result = None

    with contextlib.suppress(PathError, BlurHashEncodeError, ValueError):
        blurhash_result = encode(image_path, x_components, y_components)

    with contextlib.suppress(PathError, AvifPngDataUrlError, ValueError):
        data_url_result = encode_pdu(image_path, max_dimension)

    return blurhash_result, data_url_result


def batch_encode(
    directory: str | Path, skip_path_exists_check: bool = False, x_components: int = 4, y_components: int = 4
) -> dict[str, Optional[str]]:
    """Generates BlurHash strings for all AVIF images in a directory.

    Args:
        directory: Path to the directory containing AVIF images.
        skip_path_exists_check: If True, skip directory existence check (default: False).
        x_components: Number of horizontal components (1-9, default: 4).
        y_components: Number of vertical components (1-9, default: 4).

    Returns:
        A dictionary mapping filenames to their BlurHash strings.
        Failed encodings will have None as the value.

    Raises:
        PathError: If the directory path is invalid or doesn't exist
                  (unless skip_path_exists_check is True).
    """
    try:
        directory_path = Path(directory)
    except (TypeError, ValueError) as e:
        msg = f"Invalid directory path type: {type(directory).__name__}"
        raise PathError(msg) from e

    if not skip_path_exists_check:
        if not directory_path.exists():
            msg = f"Directory does not exist: {directory}"
            raise PathError(msg)
        if not directory_path.is_dir():
            msg = f"Path is not a directory: {directory}"
            raise PathError(msg)

    result: dict[str, Optional[str]] = {}

    # Process each AVIF file
    for image_path in directory_path.glob("*.avif"):
        try:
            blurhash_str = encode(image_path, x_components, y_components)
            result[image_path.name] = blurhash_str
        # this operation is expensive
        except (BlurHashEncodeError, PathError, ValueError):  # noqa: PERF203  # intentional: allow partial batch success
            # Store None for failed encodings
            result[image_path.name] = None

    return result


def batch_encode_pdu(
    directory: str | Path, skip_path_exists_check: bool = False, max_dimension: int = 64
) -> dict[str, Optional[str]]:
    """Generates PNG data URLs for all AVIF images in a directory.

    Args:
        directory: Path to the directory containing AVIF images.
        skip_path_exists_check: If True, skip directory existence check (default: False).
        max_dimension: Maximum dimension for thumbnails (default: 64).

    Returns:
        A dictionary mapping filenames to their PNG data URLs.
        Failed encodings will have None as the value.

    Raises:
        PathError: If the directory path is invalid or doesn't exist
                  (unless skip_path_exists_check is True).
    """
    try:
        directory_path = Path(directory)
    except (TypeError, ValueError) as e:
        msg = f"Invalid directory path type: {type(directory).__name__}"
        raise PathError(msg) from e

    if not skip_path_exists_check:
        if not directory_path.exists():
            msg = f"Directory does not exist: {directory}"
            raise PathError(msg)
        if not directory_path.is_dir():
            msg = f"Path is not a directory: {directory}"
            raise PathError(msg)

    result: dict[str, Optional[str]] = {}

    # Process each AVIF file
    for image_path in directory_path.glob("*.avif"):
        try:
            data_url = encode_pdu(image_path, max_dimension)
            result[image_path.name] = data_url
        # this operation is expensive
        except (AvifPngDataUrlError, PathError, ValueError):  # noqa: PERF203  # intentional: allow partial batch success
            # Store None for failed encodings
            result[image_path.name] = None

    return result


def batch_encode_blurhash_and_pda(
    directory: str | Path,
    skip_path_exists_check: bool = False,
    x_components: int = 4,
    y_components: int = 4,
    max_dimension: int = 64,
) -> tuple[dict[str, Optional[str]], dict[str, Optional[str]]]:
    """Generates both BlurHash strings and PNG data URLs for all AVIF images.

    Args:
        directory: Path to the directory containing AVIF images.
        skip_path_exists_check: If True, skip directory existence check (default: False).
        x_components: Number of horizontal BlurHash components (1-9, default: 4).
        y_components: Number of vertical BlurHash components (1-9, default: 4).
        max_dimension: Maximum dimension for PNG thumbnails (default: 64).

    Returns:
        A tuple of two dictionaries:
        - First: mapping filenames to BlurHash strings
        - Second: mapping filenames to PNG data URLs
        Failed encodings will have None as the value.

    Raises:
        PathError: If the directory path is invalid or doesn't exist
                  (unless skip_path_exists_check is True).
    """
    try:
        directory_path = Path(directory)
    except (TypeError, ValueError) as e:
        msg = f"Invalid directory path type: {type(directory).__name__}"
        raise PathError(msg) from e

    if not skip_path_exists_check:
        if not directory_path.exists():
            msg = f"Directory does not exist: {directory}"
            raise PathError(msg)
        if not directory_path.is_dir():
            msg = f"Path is not a directory: {directory}"
            raise PathError(msg)

    blurhash_dict: dict[str, Optional[str]] = {}
    data_url_dict: dict[str, Optional[str]] = {}

    # Process each AVIF file
    for image_path in directory_path.glob("*.avif"):
        blurhash_str, data_url = encode_blurhash_and_pda(image_path, x_components, y_components, max_dimension)
        blurhash_dict[image_path.name] = blurhash_str
        data_url_dict[image_path.name] = data_url

    return blurhash_dict, data_url_dict


def decode_to_pil_format(blurhash_string: str, width: int, height: int, punch: float = 1.0) -> Image.Image:
    """Decode a BlurHash string into a PIL Image object.

    Args:
        blurhash_string: The BlurHash string to decode.
        width: The desired width of the output image (must be positive).
        height: The desired height of the output image (must be positive).
        punch: Contrast modifier (default: 1.0, higher = more contrast).

    Returns:
        A PIL Image object decoded from the BlurHash string.

    Raises:
        ValueError: If dimensions are invalid or blurhash_string is empty.
        BlurHashDecodeError: If the BlurHash string cannot be decoded.
    """
    if not blurhash_string or not blurhash_string.strip():
        msg = "BlurHash string cannot be empty"
        raise ValueError(msg)

    if width <= 0:
        msg = f"Width must be positive, got {width}"
        raise ValueError(msg)

    if height <= 0:
        msg = f"Height must be positive, got {height}"
        raise ValueError(msg)

    if punch <= 0:
        msg = f"Punch must be positive, got {punch}"
        raise ValueError(msg)

    # Decode the BlurHash
    try:
        decoded = blurhash.decode(blurhash_string, width, height, punch=punch)

        if decoded is None:
            msg = "Decoder returned None"
            raise BlurHashDecodeError(msg)  # noqa: TRY301

        image_array = np.array(decoded, dtype=np.uint8)

        if image_array.shape[:2] != (height, width):
            msg = f"Unexpected decoded shape: {image_array.shape}, expected ({height}, {width}, 3)"
            raise BlurHashDecodeError(msg)  # noqa: TRY301

        return Image.fromarray(image_array)

    except (ValueError, TypeError) as e:
        msg = f"Invalid BlurHash string or parameters: {e!s}"
        raise BlurHashDecodeError(msg) from e
    except Exception as e:
        if isinstance(e, BlurHashDecodeError):
            raise
        msg = f"Failed to decode BlurHash: {e!s}"
        raise BlurHashDecodeError(msg) from e


def save_image_png(image: Image.Image, filename: str | Path, optimize: bool = True, progressive: bool = True) -> None:
    """Save a PIL Image to a PNG file with optional optimization.

    Args:
        image: The PIL Image to save.
        filename: The path where the image will be saved.
        optimize: If True, attempt to compress the PNG file (default: True).
        progressive: If True, save as progressive PNG (default: True).

    Raises:
        ValueError: If the image or filename is invalid.
        ImageSaveError: If the image cannot be saved.
    """
    if image is None:
        msg = "Image cannot be None"
        raise ValueError(msg)

    if not filename:
        msg = "Filename cannot be empty"
        raise ValueError(msg)

    try:
        path_obj = Path(filename)
    except (TypeError, ValueError) as e:
        msg = f"Invalid filename type: {type(filename).__name__}"
        raise ValueError(msg) from e

    parent_dir = path_obj.parent
    if parent_dir != Path() and not parent_dir.exists():
        try:
            parent_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            msg = f"Failed to create directory: {parent_dir}"
            raise ImageSaveError(msg) from e

    try:
        save_kwargs: dict[str, Any] = {"format": "PNG"}
        if optimize:
            save_kwargs["optimize"] = True
        if progressive:
            save_kwargs["interlace"] = 1
        image.save(path_obj, **save_kwargs)

    except OSError as e:
        msg = f"Failed to save image to {path_obj}: {e!s}"
        raise ImageSaveError(msg) from e
    except Exception as e:
        msg = f"Unexpected error saving image to {path_obj}: {e!s}"
        raise ImageSaveError(msg) from e


def decode(  # noqa: PLR0917
    output_path: str | Path,
    blurhash_string: str,
    filename: str = "output.png",
    width: int = 400,
    height: int = 300,
    punch: float = 1.0,
    optimize: bool = True,
    progressive: bool = True,
    verbose: bool = False,
) -> None:
    """Decode a BlurHash string and save it as a PNG file.

    Args:
        output_path: Directory where the decoded image will be saved.
        blurhash_string: The BlurHash string to decode.
        filename: Output filename (default: "output.png").
        width: Output image width in pixels (default: 400).
        height: Output image height in pixels (default: 300).
        punch: Contrast modifier (default: 1.0, higher = more contrast).
        optimize: If True, optimize the PNG file size (default: True).
        progressive: If True, save as progressive PNG (default: True).
        verbose: If True, print success message (default: False).

    Raises:
        ValueError: If parameters are invalid.
        PathError: If the output path cannot be created.
        BlurHashDecodeError: If the BlurHash cannot be decoded.
        ImageSaveError: If the image cannot be saved.
    """
    if not filename or not filename.strip():
        msg = "Filename cannot be empty"
        raise ValueError(msg)

    try:
        output_path_obj = Path(output_path)
        output_path_obj.mkdir(parents=True, exist_ok=True)
    except (TypeError, ValueError) as e:
        msg = f"Invalid output path type: {type(output_path).__name__}"
        raise PathError(msg) from e
    except OSError as e:
        msg = f"Failed to create output directory: {output_path}"
        raise PathError(msg) from e

    decoded_image = decode_to_pil_format(blurhash_string, width, height, punch)

    output_filename = output_path_obj / filename.replace(".avif", ".png")

    save_image_png(decoded_image, output_filename, optimize, progressive)

    if verbose:
        print(f"Successfully decoded and saved: {output_filename}")
