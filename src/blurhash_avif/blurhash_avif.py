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
from typing import TYPE_CHECKING, Any, Literal

import blurhash
import numpy as np
import pillow_avif  # noqa: F401 RUF100 # type: ignore # Imported for its side effects
from PIL import Image

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage

MAX_AVIF_IMAGE_EDGE_SIZE = 65_536
MAX_COMPONENTS_SIZE = 9
ResamplingMethod = Literal["lanczos", "nearest", "bilinear", "bicubic"]


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


def _validate_and_resolve_path(image_path: str | Path, *, require_avif: bool = False) -> Path:
    """Validate and convert image_path to a Path object.

    Args:
        image_path (str | Path): Path to validate.
        require_avif (bool): If True, validate that file has .avif extension.

    Returns:
        Path: Validated Path object.

    Raises:
        PathError: If path is invalid, doesn't exist, or isn't an AVIF file when required.
    """
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

    if require_avif and path_obj.suffix.lower() != ".avif":
        msg = f"Expected AVIF file extension, got: {path_obj.suffix}"
        raise PathError(msg)

    return path_obj


def _downsample_image_if_needed(
    image: PILImage, max_dimension: float, resampling_method: ResamplingMethod = "lanczos"
) -> PILImage:
    """Downsample the image if its dimensions exceed the maximum dimension.

    Args:
        image (PILImage): The input image.
        max_dimension (float): This is the max size a single edge of the image can be in pixels,
                               when an image edge/side exceeds this value, the image will be
                               downsampled to fit within the maximum dimension.
        resampling_method (ResamplingMethod): The resampling method to use.

    Returns:
        PILImage: The possible downsampled image.

    Raises:
        ValueError: If max_dimension is not positive or if the resampling method is invalid.
    """
    if max_dimension <= 0:
        msg = f"max_dimension must be positive, got {max_dimension}"
        raise ValueError(msg)
    if max_dimension > MAX_AVIF_IMAGE_EDGE_SIZE:
        msg = f"max_dimension must be less than or equal to {MAX_AVIF_IMAGE_EDGE_SIZE}, got {max_dimension}"
        raise ValueError(msg)

    resample_map = {
        "lanczos": Image.Resampling.LANCZOS,
        "nearest": Image.Resampling.NEAREST,
        "bilinear": Image.Resampling.BILINEAR,
        "bicubic": Image.Resampling.BICUBIC,
    }
    try:
        resampling_method_id = resample_map[resampling_method]
    except KeyError as e:
        msg = f"Unknown resampling_method: {resampling_method!r}"
        raise ValueError(msg) from e

    if image.width <= max_dimension and image.height <= max_dimension:
        return image

    # Uses PIL's thumbnail for correct aspect ratio preservation
    image_copy = image.copy()
    image_copy.thumbnail((max_dimension, max_dimension), resampling_method_id)
    return image_copy


def _ensure_rgb(image: PILImage) -> PILImage:
    return image.convert("RGB") if image.mode != "RGB" else image


def _validate_component_values(x_components: int, y_components: int) -> None:
    if not 1 <= x_components <= MAX_COMPONENTS_SIZE:
        msg = f"x_components must be between 1 and 9, got {x_components}"
        raise ValueError(msg)
    if not 1 <= y_components <= MAX_COMPONENTS_SIZE:
        msg = f"y_components must be between 1 and 9, got {y_components}"
        raise ValueError(msg)


def _encode_from_image(
    image: PILImage,
    x_components: int = 4,
    y_components: int = 3,
    max_dimension: float = 64,
    resampling_method: ResamplingMethod = "lanczos",
) -> str:
    """Internal function to encode a PIL Image to BlurHash.

    Args:
        image (PILImage): Image to encode.
        x_components (int): Number of horizontal components (1-9).
        y_components (int): Number of vertical components (1-9).
        max_dimension (float): This is the max size a single edge of the image can be in pixels,
                               when an image edge/side exceeds this value, the image will be
                               downsampled to fit within the maximum dimension.
        resampling_method (ResamplingMethod): Resampling method for resizing.

    Returns:
        str: BlurHash string.

    Raises:
        BlurHashEncodeError: If encoding fails or dimensions are invalid.
        ValueError: If component values are out of range, If max_dimension is not positive,
        or if the resampling method value is invalid.
    """
    # Validate components
    _validate_component_values(x_components, y_components)

    rgb_image = _ensure_rgb(image)

    # Guard against invalid image dimensions
    if rgb_image.width <= 0 or rgb_image.height <= 0:
        msg = f"Invalid image dimensions: {rgb_image.width}x{rgb_image.height}"
        raise BlurHashEncodeError(msg)

    # Resize
    resized_image = _downsample_image_if_needed(rgb_image, max_dimension, resampling_method)

    # Convert to numpy array and encode
    image_array = np.array(resized_image)
    return str(blurhash.encode(image_array, x_components, y_components))


def _encode_pdu_from_image(
    image: PILImage,
    max_dimension: float = 64,
    resampling_method: ResamplingMethod = "lanczos",
) -> str:
    """Internal function to encode a PIL Image to PNG data URL.

    Args:
        image (PILImage): Image to encode. (Any source image is converted to 8-bit sRGB before processing.)
        max_dimension (float): This is the max size a single edge of the image can be in pixels,
                               when an image edge/side exceeds this value, the image will be
                               downsampled to fit within the maximum dimension.
        resampling_method (ResamplingMethod): Resampling method to use when resizing.

    Returns:
        str: PNG data URL string.

    Raises:
        AvifPngDataUrlError: If encoding fails or dimensions are invalid.
        ValueError: If max_dimension is not positive or if the resampling method value is invalid.
    """
    # Validate max_dimension
    if max_dimension <= 0:
        msg = f"max_dimension must be positive, got {max_dimension}"
        raise ValueError(msg)

    rgb_image = _ensure_rgb(image)

    if rgb_image.width <= 0 or rgb_image.height <= 0:
        msg = f"Invalid image dimensions: {rgb_image.width}x{rgb_image.height}"
        raise AvifPngDataUrlError(msg)

    resized_image = _downsample_image_if_needed(rgb_image, max_dimension, resampling_method)

    # Encode to PNG in memory
    with BytesIO() as buffer:
        resized_image.save(buffer, format="PNG", optimize=True)
        png_bytes = buffer.getvalue()

    if not png_bytes:
        msg = "Failed to encode image to PNG: empty result"
        raise AvifPngDataUrlError(msg)

    base64_png = base64.b64encode(png_bytes).decode("utf-8")
    return f"data:image/png;base64,{base64_png}"


def _validate_directory(directory: str | Path, skip_path_exists_check: bool = False) -> Path:  # noqa: FBT001, FBT002
    """Validate and convert directory to a Path object.

    Raises:
        PathError: If directory is invalid or doesn't exist (unless skipped).
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

    return directory_path


def encode(
    image_path: str | Path,
    x_components: int = 4,
    y_components: int = 3,
    max_dimension: float = 64,
    resampling_method: ResamplingMethod = "lanczos",
) -> str:
    """Generates a BlurHash string for an AVIF image.

    The image is resized to a maximum dimension of 64 pixels before encoding by default
    to optimize performance while maintaining visual quality.

    Args:
        image_path (str | Path): Path to the AVIF image file.
        x_components (int): Number of horizontal components (1-9, default: 4).
        y_components (int): Number of vertical components (1-9, default: 3).
        max_dimension (float): This is the max size a single edge of the image can be in pixels,
                               when an image edge/side exceeds this value, the image will be
                               downsampled to fit within the maximum dimension..
        resampling_method (ResamplingMethod): Resampling method to use for resizing (default: "lanczos").

    Returns:
        str: The BlurHash string representation of the image.

    Raises:
        PathError: If the image path is invalid or doesn't exist.
        BlurHashEncodeError: If the dimensions are invalid.
        ValueError: If component values are out of valid range.
        OSError: If the image cannot be opened.
    """
    _validate_component_values(x_components, y_components)

    path_obj = _validate_and_resolve_path(image_path, require_avif=True)

    try:
        with Image.open(path_obj) as original_image:
            return _encode_from_image(original_image, x_components, y_components, max_dimension, resampling_method)
    except OSError as e:
        msg = f"Failed to open image file: {path_obj}. Original error: {e}"
        raise OSError(msg) from e


def encode_pdu(
    image_path: str | Path, max_dimension: float = 64, resampling_method: ResamplingMethod = "lanczos"
) -> str:
    """Generates a base64-encoded PNG data URL for an AVIF image.

    The image is resized to the specified maximum dimension to create
    a lightweight preview suitable for inline embedding.

    Args:
        image_path (str | Path): Path to the AVIF image file.
        max_dimension (float): This is the max size a single edge of the image can be in pixels,
                               when an image edge/side exceeds this value, the image will be
                               downsampled to fit within the maximum dimension.
        resampling_method (ResamplingMethod): Resampling method to use when resizing the image (default: "lanczos").

    Returns:
        str: A data URL string in the format: data:image/png;base64,[base64-data]

    Raises:
        PathError: If the image path is invalid or doesn't exist.
        AvifPngDataUrlError: If the image cannot be processed or encoded.
        ValueError: If max_dimension is not positive.
        OSError: If the image cannot be opened.
    """
    path_obj = _validate_and_resolve_path(image_path)

    try:
        with Image.open(path_obj) as original_image:
            return _encode_pdu_from_image(original_image, max_dimension, resampling_method)
    except OSError as e:
        msg = f"Failed to open image file: {path_obj}. Original error: {e}"
        raise AvifPngDataUrlError(msg) from e


def encode_blurhash_and_pdu(
    image_path: str | Path,
    x_components: int = 4,
    y_components: int = 3,
    max_dimension: float = 64,
    resampling_method: ResamplingMethod = "lanczos",
) -> tuple[str | None, str | None]:
    """Generates both a BlurHash and a PNG data URL for an AVIF image.

    This is a convenience function that performs both encodings in a single call.
    The image is opened once and processed for both outputs. Errors in one encoding
    don't prevent the other from being attempted.

    Args:
        image_path (str | Path): Path to the AVIF image file.
        x_components (int): Number of horizontal BlurHash components (1-9, default: 4).
        y_components (int): Number of vertical BlurHash components (1-9, default: 4).
        max_dimension (float): Maximum dimension for resizing (default: 64).
        resampling_method (ResamplingMethod): Resampling method for resizing (default: "lanczos").

    Returns:
        tuple[Optional[str], Optional[str]]: A tuple of (blurhash_string, png_data_url).
            Either value may be None if its respective encoding fails.

    Raises:
        PathError: If the image path is invalid or doesn't exist.
        OSError: If the image file cannot be opened.
    """
    path_obj = _validate_and_resolve_path(image_path)

    blurhash_result = None
    data_url_result = None

    try:
        with Image.open(path_obj) as original_image:
            # Try BlurHash encoding
            with contextlib.suppress(ValueError, BlurHashEncodeError):
                blurhash_result = _encode_from_image(
                    original_image, x_components, y_components, max_dimension, resampling_method
                )

            # Try PNG data URL encoding
            with contextlib.suppress(ValueError, AvifPngDataUrlError):
                data_url_result = _encode_pdu_from_image(original_image, max_dimension, resampling_method)

    except OSError as e:
        msg = f"Failed to open image file: {path_obj}. Original error: {e}"
        raise OSError(msg) from e

    return blurhash_result, data_url_result


def batch_encode(
    directory: str | Path,
    x_components: int = 4,
    y_components: int = 3,
    skip_path_exists_check: bool = False,  # noqa: FBT001, FBT002
    raise_on_error: bool = False,  # noqa: FBT001, FBT002
) -> dict[str, str | None]:
    """Generates BlurHash strings for all AVIF images in a directory.

    Args:
        directory (str | Path): Path to the directory containing AVIF images.
        skip_path_exists_check (bool): If True, skip directory existence check (default: False).
        x_components (int): Number of horizontal components (1-9, default: 4).
        y_components (int): Number of vertical components (1-9, default: 4).
        raise_on_error (bool): If True, raise an exception on error (default: False).

    Returns:
        dict[str, Optional[str]]: Dictionary mapping filenames to their BlurHash strings.
            Failed encodings will have None as the value.

    Raises:
        PathError: If the directory path is invalid or doesn't exist
            (unless skip_path_exists_check is True).
    """
    _validate_component_values(x_components, y_components)
    directory_path = _validate_directory(directory, skip_path_exists_check=skip_path_exists_check)

    result: dict[str, str | None] = {}

    for image_path in directory_path.glob("*.avif"):
        try:
            blurhash_str = encode(image_path, x_components, y_components)
            result[image_path.name] = blurhash_str
        except (BlurHashEncodeError, PathError, ValueError, OSError):  # noqa: PERF203
            if raise_on_error:
                raise
            result[image_path.name] = None

    return result


def batch_encode_pdu(
    directory: str | Path,
    max_dimension: float = 64,
    skip_path_exists_check: bool = False,  # noqa: FBT001, FBT002
    raise_on_error: bool = False,  # noqa: FBT001, FBT002
) -> dict[str, str | None]:
    """Generates PNG data URLs for all AVIF images in a directory.

    Args:
        directory (str | Path): Path to the directory containing AVIF images.
        skip_path_exists_check (bool): If True, skip directory existence check (default: False).
        max_dimension (float): This is the max size a single edge of the image can be in pixels,
                               when an image edge/side exceeds this value, the image will be
                               downsampled to fit within the maximum dimension.
        raise_on_error (bool): If True, raise an exception on error (default: False).

    Returns:
        dict[str, Optional[str]]: Dictionary mapping filenames to their PNG data URLs.
            Failed encodings will have None as the value.

    Raises:
        PathError: If the directory path is invalid or doesn't exist
            (unless skip_path_exists_check is True).
    """
    directory_path = _validate_directory(directory, skip_path_exists_check=skip_path_exists_check)

    result: dict[str, str | None] = {}

    for image_path in directory_path.glob("*.avif"):
        try:
            data_url = encode_pdu(image_path, max_dimension)
            result[image_path.name] = data_url
        except (AvifPngDataUrlError, PathError, ValueError, OSError):  # noqa: PERF203
            if raise_on_error:
                raise
            result[image_path.name] = None

    return result


def batch_encode_blurhash_and_pdu(  # noqa: PLR0917
    directory: str | Path,
    x_components: int = 4,
    y_components: int = 3,
    max_dimension: float = 64,
    skip_path_exists_check: bool = False,  # noqa: FBT001, FBT002
    raise_on_error: bool = False,  # noqa: FBT001, FBT002
) -> tuple[dict[str, str | None], dict[str, str | None]]:
    """Generates both BlurHash strings and PNG data URLs for all AVIF images.

    Args:
        directory (str | Path): Path to the directory containing AVIF images.
        skip_path_exists_check (bool): If True, skip directory existence check (default: False).
        x_components (int): Number of horizontal BlurHash components (1-9, default: 4).
        y_components (int): Number of vertical BlurHash components (1-9, default: 4).
        max_dimension (float): This is the max size a single edge of the image can be in pixels,
                               when an image edge/side exceeds this value, the image will be
                               downsampled to fit within the maximum dimension.
        raise_on_error (bool): If True, raise an exception on error (default: False).

    Returns:
        tuple[dict[str, Optional[str]], dict[str, Optional[str]]]: A tuple of two dictionaries:
            - First: mapping filenames to BlurHash strings
            - Second: mapping filenames to PNG data URLs
            Failed encodings will have None as the value.

    Raises:
        PathError: If the directory path is invalid or doesn't exist
            (unless skip_path_exists_check is True).
    """
    _validate_component_values(x_components, y_components)
    directory_path = _validate_directory(directory, skip_path_exists_check=skip_path_exists_check)

    blurhash_dict: dict[str, str | None] = {}
    data_url_dict: dict[str, str | None] = {}

    for image_path in directory_path.glob("*.avif"):
        try:
            blurhash_str, data_url = encode_blurhash_and_pdu(image_path, x_components, y_components, max_dimension)
            blurhash_dict[image_path.name] = blurhash_str
            data_url_dict[image_path.name] = data_url
        except (PathError, OSError):  # noqa: PERF203
            if raise_on_error:
                raise
            blurhash_dict[image_path.name] = None
            data_url_dict[image_path.name] = None

    return blurhash_dict, data_url_dict


def _simple_blurhash_validation(blurhash_string: str) -> bool:
    """Check if a string appears to be a valid BlurHash."""
    if not blurhash_string or len(blurhash_string) < 6:  # noqa: PLR2004
        return False
    # Base83 character set used by BlurHash
    valid_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz#$%*+,-.:;=?@[]^_{|}~"
    return all(c in valid_chars for c in blurhash_string)


def decode_to_pil_format(blurhash_string: str, width: int, height: int, punch: float = 1.0) -> PILImage:
    """Decode a BlurHash string into a PIL Image object.

    Args:
        blurhash_string (str): The BlurHash string to decode.
        width (int): The desired width of the output image (must be positive).
        height (int): The desired height of the output image (must be positive).
        punch (float): Contrast adjustment factor (default: 1.0).
                    - Values < 1.0 reduce contrast (softer, more blurred)
                    - Values > 1.0 increase contrast (sharper, more defined)
                    - Typical range: 0.5 to 2.0
                    - Must be positive

    Returns:
        PILImage: A PIL Image object decoded from the BlurHash string.

    Raises:
        ValueError: If dimensions are invalid, blurhash_string is empty or invalid format.
        BlurHashDecodeError: If the BlurHash string cannot be decoded.
    """
    if not blurhash_string or not blurhash_string.strip():
        msg = "BlurHash string cannot be empty"
        raise ValueError(msg)

    if not _simple_blurhash_validation(blurhash_string):
        msg = f"BlurHash string appears to be invalid format: {blurhash_string[:20]}..."
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

    try:
        decoded: list[list[int]] = blurhash.decode(blurhash_string, width, height, punch=punch)

        image_array = np.array(decoded, dtype=np.uint8)

        if image_array.shape[:2] != (height, width):
            msg = f"Unexpected decoded shape: {image_array.shape}, expected ({height}, {width}, 3)"
            raise BlurHashDecodeError(msg)

        return Image.fromarray(image_array)

    except (ValueError, TypeError) as e:
        msg = f"Invalid BlurHash string or parameters: {e!s}"
        raise BlurHashDecodeError(msg) from e


def save_image_png(image: PILImage, filename: str | Path, *, optimize: bool = True, interlaced: bool = True) -> None:
    """Save a PIL Image to a PNG file with optional optimization.

    Args:
        image (PILImage): The PIL Image to save.
        filename (str | Path): The path where the image will be saved.
        optimize (bool): If True, attempt to compress the PNG file (default: True).
        interlaced (bool): If True, save as interlaced PNG using Adam7 algorithm (default: True).

    Raises:
        ValueError: If the image or filename is invalid.
        ImageSaveError: If the image cannot be saved.
    """
    if image is None:
        msg = "Image cannot be of type None"
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
            msg = f"Failed to create directory: {parent_dir}. Original error: {e}"
            raise ImageSaveError(msg) from e

    try:
        save_kwargs: dict[str, Any] = {"format": "PNG"}
        if optimize:
            save_kwargs["optimize"] = True
        if interlaced:
            save_kwargs["interlace"] = 1
        image.save(path_obj, **save_kwargs)

    except OSError as e:
        msg = f"Failed to save image to {path_obj}: {e!s}"
        raise ImageSaveError(msg) from e
    except ValueError as e:
        msg = f"Invalid image data: {e}"
        raise ImageSaveError(msg) from e


def decode(  # noqa: PLR0917
    output_path: str | Path,
    blurhash_string: str,
    filename: str = "output.png",
    width: int = 400,
    height: int = 300,
    punch: float = 1.0,
    optimize: bool = True,  # noqa: FBT001, FBT002
    interlaced: bool = True,  # noqa: FBT001, FBT002
) -> None:
    """Decode a BlurHash string and save it as a PNG file.

    Args:
        output_path (str | Path): Directory where the decoded image will be saved.
        blurhash_string (str): The BlurHash string to decode.
        filename (str): Output filename (default: "output.png").
        width (int): Output image width in pixels (default: 400).
        height (int): Output image height in pixels (default: 300).
        punch (float): Contrast adjustment factor (default: 1.0).
                    - Values < 1.0 reduce contrast (softer, more blurred)
                    - Values > 1.0 increase contrast (sharper, more defined)
                    - Typical range: 0.5 to 2.0
                    - Must be positive
        optimize (bool): If True, optimize the PNG file size (default: True).
        interlaced (bool): If True, save as interlaced PNG using Adam7 (default: True).

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
        msg = f"Failed to create output directory: {output_path}. Original error: {e}"
        raise PathError(msg) from e

    decoded_image = decode_to_pil_format(blurhash_string, width, height, punch)

    output_filename = output_path_obj / filename.replace(".avif", ".png")

    save_image_png(decoded_image, output_filename, optimize=optimize, interlaced=interlaced)
