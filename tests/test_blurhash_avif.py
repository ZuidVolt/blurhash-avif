import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

try:
    from src.blurhash_avif import (
        AvifPngDataUrlError,
        PathError,
        _simple_blurhash_validation,
        batch_encode,
        batch_encode_blurhash_and_pdu,
        batch_encode_pdu,
        decode,
        decode_to_pil_format,
        encode,
        encode_blurhash_and_pdu,
        encode_pdu,
        save_image_png,
    )
except ImportError:
    from blurhash_avif import (
        AvifPngDataUrlError,
        PathError,
        _simple_blurhash_validation,  # noqa: PLC2701
        batch_encode,
        batch_encode_blurhash_and_pdu,
        batch_encode_pdu,
        decode,
        decode_to_pil_format,
        encode,
        encode_blurhash_and_pdu,
        encode_pdu,
        save_image_png,
    )


class TestBlurhashAvif(unittest.TestCase):  # noqa: PLR0904
    """Test suite for blurhash_avif module."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create test directory."""
        Path("tests").mkdir(exist_ok=True)

    def _create_test_image(
        self, filename: str, size: tuple[int, int] = (100, 100), color: tuple[int, int, int] = (255, 0, 0)
    ) -> Path:
        """Helper to create a test AVIF image."""
        image_path = Path("tests") / filename
        image = Image.new("RGB", size, color)
        image.save(image_path, "AVIF")
        return image_path

    def _cleanup(self, *paths: Path) -> None:
        """Helper to clean up test files."""
        for path in paths:
            path.unlink(missing_ok=True)

    # ===== Basic Encoding Tests =====

    def test_generate_blurhash_from_avif(self) -> None:
        """Test basic BlurHash generation from AVIF image."""
        image_path = self._create_test_image("test_image.avif")

        try:
            blurhash = encode(image_path)

            self.assertIsNotNone(blurhash)
            self.assertIsInstance(blurhash, str)
            self.assertGreater(len(blurhash), 0)
        finally:
            self._cleanup(image_path)

    def test_generate_png_data_url_from_avif(self) -> None:
        """Test PNG data URL generation from AVIF image."""
        image_path = self._create_test_image("test_image.avif")

        try:
            data_url = encode_pdu(image_path)

            self.assertIsNotNone(data_url)
            self.assertIsInstance(data_url, str)
            self.assertTrue(data_url.startswith("data:image/png;base64,"))
        finally:
            self._cleanup(image_path)

    def test_generate_blurhash_and_data_url_from_avif(self) -> None:
        """Test combined BlurHash and PNG data URL generation."""
        image_path = self._create_test_image("test_image.avif")

        try:
            blurhash, data_url = encode_blurhash_and_pdu(image_path)

            self.assertIsNotNone(blurhash)
            self.assertIsInstance(blurhash, str)
            self.assertIsNotNone(data_url)
            self.assertIsInstance(data_url, str)
            self.assertTrue(data_url.startswith("data:image/png;base64,"))
        finally:
            self._cleanup(image_path)

    # ===== Path Validation Tests =====

    def test_encode_nonexistent_path(self) -> None:
        """Test that encoding nonexistent file raises PathError."""
        with self.assertRaises(PathError):
            encode("nonexistent.avif")

    def test_encode_pdu_nonexistent_path(self) -> None:
        """Test that PDU encoding nonexistent file raises PathError."""
        with self.assertRaises(PathError):
            encode_pdu("nonexistent.avif")

    def test_encode_directory_path(self) -> None:
        """Test that encoding a directory raises PathError."""
        test_dir = Path("tests/test_dir")
        test_dir.mkdir(exist_ok=True)

        try:
            with self.assertRaises(PathError):
                encode(test_dir)
        finally:
            test_dir.rmdir()

    # ===== Invalid Image File Tests =====

    def test_encode_empty_file(self) -> None:
        """Test that encoding empty file raises OSError (changed from BlurHashEncodeError)."""
        image_path = Path("tests/empty.avif")
        image_path.touch()

        try:
            with self.assertRaises(OSError):
                encode(image_path)
        finally:
            self._cleanup(image_path)

    def test_encode_non_image_file(self) -> None:
        """Test that encoding non-image file raises OSError (changed from BlurHashEncodeError)."""
        image_path = Path("tests/bad.avif")
        image_path.write_text("not an image", encoding="utf-8")

        try:
            with self.assertRaises(OSError):
                encode(image_path)
        finally:
            self._cleanup(image_path)

    def test_encode_pdu_empty_file(self) -> None:
        """Test that PDU encoding empty file raises AvifPngDataUrlError."""
        image_path = Path("tests/empty.avif")
        image_path.touch()

        try:
            with self.assertRaises(AvifPngDataUrlError):
                encode_pdu(image_path)
        finally:
            self._cleanup(image_path)

    def test_encode_pdu_non_image_file(self) -> None:
        """Test that PDU encoding non-image file raises AvifPngDataUrlError."""
        image_path = Path("tests/bad.avif")
        image_path.write_text("not an image", encoding="utf-8")

        try:
            with self.assertRaises(AvifPngDataUrlError):
                encode_pdu(image_path)
        finally:
            self._cleanup(image_path)

    # ===== Component Validation Tests =====

    def test_encode_invalid_x_components(self) -> None:
        """Test that invalid x_components raises ValueError."""
        image_path = self._create_test_image("test_image.avif")

        try:
            with self.assertRaises(ValueError):
                encode(image_path, x_components=0)

            with self.assertRaises(ValueError):
                encode(image_path, x_components=10)
        finally:
            self._cleanup(image_path)

    def test_encode_invalid_y_components(self) -> None:
        """Test that invalid y_components raises ValueError."""
        image_path = self._create_test_image("test_image.avif")

        try:
            with self.assertRaises(ValueError):
                encode(image_path, y_components=0)

            with self.assertRaises(ValueError):
                encode(image_path, y_components=10)
        finally:
            self._cleanup(image_path)

    def test_encode_pdu_invalid_max_dimension(self) -> None:
        """Test that invalid max_dimension raises ValueError."""
        image_path = self._create_test_image("test_image.avif")

        try:
            with self.assertRaises(ValueError):
                encode_pdu(image_path, max_dimension=0)

            with self.assertRaises(ValueError):
                encode_pdu(image_path, max_dimension=-1)
        finally:
            self._cleanup(image_path)

    # ===== Image Size Tests =====

    def test_encode_small_image(self) -> None:
        """Test encoding of image smaller than max_dimension."""
        image_path = self._create_test_image("small_image.avif", size=(32, 32))

        try:
            blurhash = encode(image_path, max_dimension=64)
            self.assertIsNotNone(blurhash)
        finally:
            self._cleanup(image_path)

    def test_encode_large_image(self) -> None:
        """Test encoding of image larger than max_dimension."""
        image_path = self._create_test_image("large_image.avif", size=(200, 150))

        try:
            blurhash = encode(image_path, max_dimension=64)
            self.assertIsNotNone(blurhash)
        finally:
            self._cleanup(image_path)

    def test_encode_different_aspect_ratios(self) -> None:
        """Test encoding images with different aspect ratios."""
        # Wide image
        wide_path = self._create_test_image("wide_image.avif", size=(200, 100))
        # Tall image
        tall_path = self._create_test_image("tall_image.avif", size=(100, 200))

        try:
            wide_hash = encode(wide_path)
            tall_hash = encode(tall_path)

            self.assertIsNotNone(wide_hash)
            self.assertIsNotNone(tall_hash)
            self.assertNotEqual(wide_hash, tall_hash)
        finally:
            self._cleanup(wide_path, tall_path)

    # ===== Batch Processing Tests =====

    def test_batch_encode(self) -> None:
        """Test batch encoding of multiple AVIF files."""
        test_dir = Path("tests/batch_test")
        test_dir.mkdir(exist_ok=True)

        try:
            # Create multiple test images
            img1 = test_dir / "image1.avif"
            img2 = test_dir / "image2.avif"
            Image.new("RGB", (100, 100), (255, 0, 0)).save(img1, "AVIF")
            Image.new("RGB", (100, 100), (0, 255, 0)).save(img2, "AVIF")

            results = batch_encode(test_dir)

            self.assertEqual(len(results), 2)
            self.assertIn("image1.avif", results)
            self.assertIn("image2.avif", results)
            self.assertIsNotNone(results["image1.avif"])
            self.assertIsNotNone(results["image2.avif"])
        finally:
            for file in test_dir.glob("*.avif"):
                file.unlink()
            test_dir.rmdir()

    def test_batch_encode_pdu(self) -> None:
        """Test batch PDU encoding of multiple AVIF files."""
        test_dir = Path("tests/batch_pdu_test")
        test_dir.mkdir(exist_ok=True)

        try:
            img1 = test_dir / "image1.avif"
            img2 = test_dir / "image2.avif"
            Image.new("RGB", (100, 100), (255, 0, 0)).save(img1, "AVIF")
            Image.new("RGB", (100, 100), (0, 255, 0)).save(img2, "AVIF")

            results = batch_encode_pdu(test_dir)

            self.assertEqual(len(results), 2)
            self.assertIn("image1.avif", results)
            self.assertIn("image2.avif", results)
            self.assertTrue(results["image1.avif"].startswith("data:image/png;base64,"))
            self.assertTrue(results["image2.avif"].startswith("data:image/png;base64,"))
        finally:
            for file in test_dir.glob("*.avif"):
                file.unlink()
            test_dir.rmdir()

    def test_batch_encode_blurhash_and_pdu(self) -> None:
        """Test combined batch encoding."""
        test_dir = Path("tests/batch_combined_test")
        test_dir.mkdir(exist_ok=True)

        try:
            img1 = test_dir / "image1.avif"
            Image.new("RGB", (100, 100), (255, 0, 0)).save(img1, "AVIF")

            blurhash_results, pdu_results = batch_encode_blurhash_and_pdu(test_dir)

            self.assertEqual(len(blurhash_results), 1)
            self.assertEqual(len(pdu_results), 1)
            self.assertIn("image1.avif", blurhash_results)
            self.assertIn("image1.avif", pdu_results)
            self.assertIsNotNone(blurhash_results["image1.avif"])
            self.assertIsNotNone(pdu_results["image1.avif"])
        finally:
            for file in test_dir.glob("*.avif"):
                file.unlink()
            test_dir.rmdir()

    def test_batch_encode_with_failures(self) -> None:
        """Test batch encoding handles failures gracefully."""
        test_dir = Path("tests/batch_failure_test")
        test_dir.mkdir(exist_ok=True)

        try:
            # Create one valid and one invalid image
            valid_img = test_dir / "valid.avif"
            invalid_img = test_dir / "invalid.avif"
            Image.new("RGB", (100, 100), (255, 0, 0)).save(valid_img, "AVIF")
            invalid_img.write_text("not an image")

            results = batch_encode(test_dir)

            self.assertEqual(len(results), 2)
            self.assertIsNotNone(results["valid.avif"])
            self.assertIsNone(results["invalid.avif"])
        finally:
            for file in test_dir.glob("*.avif"):
                file.unlink()
            test_dir.rmdir()

    def test_batch_encode_empty_directory(self) -> None:
        """Test batch encoding on empty directory."""
        test_dir = Path("tests/empty_batch_test")
        test_dir.mkdir(exist_ok=True)

        try:
            results = batch_encode(test_dir)
            self.assertEqual(len(results), 0)
        finally:
            test_dir.rmdir()

    # ===== BlurHash Validation Tests =====

    def test_is_valid_blurhash_valid(self) -> None:
        """Test validation of valid BlurHash strings."""
        valid_hashes = [
            "LKO2?U%2Tw=w]~RBVZRi};RPxuwH",
            "LEHV6nWB2yk8pyo0adR*.7kCMdnj",
            "L6PZfSi_.AyE_3t7t7R**0o#DgR4",
        ]

        for hash_str in valid_hashes:
            self.assertTrue(_simple_blurhash_validation(hash_str), f"Failed for: {hash_str}")

    def test_is_valid_blurhash_invalid(self) -> None:
        """Test validation of invalid BlurHash strings."""
        invalid_hashes = [
            "",
            "short",
            "invalid characters!@#",
            None,
        ]

        for hash_str in invalid_hashes:
            if hash_str is not None:
                self.assertFalse(_simple_blurhash_validation(hash_str), f"Should fail for: {hash_str}")

    # ===== Decoding Tests =====

    def test_decode_to_pil_format(self) -> None:
        """Test decoding BlurHash to PIL Image."""
        # First encode an image to get a valid hash
        image_path = self._create_test_image("decode_test.avif")

        try:
            blurhash = encode(image_path)
            decoded_image = decode_to_pil_format(blurhash, 100, 100)

            self.assertIsInstance(decoded_image, Image.Image)
            self.assertEqual(decoded_image.size, (100, 100))
            self.assertEqual(decoded_image.mode, "RGB")
        finally:
            self._cleanup(image_path)

    def test_decode_to_pil_format_invalid_hash(self) -> None:
        """Test decoding with invalid BlurHash string."""
        with self.assertRaises(ValueError):
            decode_to_pil_format("invalid!", 100, 100)

    def test_decode_to_pil_format_empty_hash(self) -> None:
        """Test decoding with empty BlurHash string."""
        with self.assertRaises(ValueError):
            decode_to_pil_format("", 100, 100)

    def test_decode_to_pil_format_invalid_dimensions(self) -> None:
        """Test decoding with invalid dimensions."""
        image_path = self._create_test_image("decode_test.avif")

        try:
            blurhash = encode(image_path)

            with self.assertRaises(ValueError):
                decode_to_pil_format(blurhash, 0, 100)

            with self.assertRaises(ValueError):
                decode_to_pil_format(blurhash, 100, -1)
        finally:
            self._cleanup(image_path)

    def test_decode_to_pil_format_invalid_punch(self) -> None:
        """Test decoding with invalid punch value."""
        image_path = self._create_test_image("decode_test.avif")

        try:
            blurhash = encode(image_path)

            with self.assertRaises(ValueError):
                decode_to_pil_format(blurhash, 100, 100, punch=0)

            with self.assertRaises(ValueError):
                decode_to_pil_format(blurhash, 100, 100, punch=-1)
        finally:
            self._cleanup(image_path)

    # ===== Image Saving Tests =====

    def test_save_image_png(self) -> None:
        """Test saving PIL Image as PNG."""
        image = Image.new("RGB", (100, 100), (255, 0, 0))
        output_path = Path("tests/saved_image.png")

        try:
            save_image_png(image, output_path)
            self.assertTrue(output_path.exists())

            # Verify it's a valid PNG
            loaded = Image.open(output_path)
            self.assertEqual(loaded.size, (100, 100))
        finally:
            self._cleanup(output_path)

    def test_save_image_png_creates_directories(self) -> None:
        """Test that save_image_png creates parent directories."""
        image = Image.new("RGB", (100, 100), (255, 0, 0))
        output_path = Path("tests/nested/dir/saved_image.png")

        try:
            save_image_png(image, output_path)
            self.assertTrue(output_path.exists())
        finally:
            self._cleanup(output_path)
            output_path.parent.rmdir()
            output_path.parent.parent.rmdir()

    def test_save_image_png_none_image(self) -> None:
        """Test saving None image raises ValueError."""
        with self.assertRaises(ValueError):
            save_image_png(None, "output.png")

    def test_save_image_png_empty_filename(self) -> None:
        """Test saving with empty filename raises ValueError."""
        image = Image.new("RGB", (100, 100), (255, 0, 0))
        with self.assertRaises(ValueError):
            save_image_png(image, "")

    # ===== Full Decode Function Tests =====

    def test_decode_function(self) -> None:
        """Test full decode function that saves to file."""
        image_path = self._create_test_image("decode_func_test.avif")
        output_dir = Path("tests/decode_output")
        output_file = output_dir / "decoded.png"

        try:
            blurhash = encode(image_path)
            decode(output_dir, blurhash, filename="decoded.png", width=100, height=100)

            self.assertTrue(output_file.exists())

            # Verify it's a valid image
            loaded = Image.open(output_file)
            self.assertEqual(loaded.size, (100, 100))
        finally:
            self._cleanup(image_path, output_file)
            output_dir.rmdir()

    def test_decode_function_empty_filename(self) -> None:
        """Test decode with empty filename raises ValueError."""
        with self.assertRaises(ValueError):
            decode("tests", "LKO2?U%2Tw=w]~RBVZRi};RPxuwH", filename="")

    # ===== Edge Cases =====

    def test_encode_different_component_values(self) -> None:
        """Test encoding with different component values produces different hashes."""
        image_path = self._create_test_image("component_test.avif")

        try:
            hash1 = encode(image_path, x_components=4, y_components=4)
            hash2 = encode(image_path, x_components=9, y_components=9)

            self.assertNotEqual(hash1, hash2)
        finally:
            self._cleanup(image_path)

    def test_encode_blurhash_and_pdu_single_file_open(self) -> None:
        """Test that encode_blurhash_and_pdu only opens file once."""
        image_path = self._create_test_image("single_open_test.avif")

        try:
            with patch("PIL.Image.open", wraps=Image.open) as mock_open:
                blurhash, data_url = encode_blurhash_and_pdu(image_path)

                # Verify file was only opened once
                self.assertEqual(mock_open.call_count, 1)
                self.assertIsNotNone(blurhash)
                self.assertIsNotNone(data_url)
        finally:
            self._cleanup(image_path)

    def test_type_hints_path_vs_string(self) -> None:
        """Test that both Path and string types work for image_path."""
        image_path_str = "tests/type_test.avif"
        image_path_path = Path(image_path_str)
        Image.new("RGB", (100, 100), (255, 0, 0)).save(image_path_str, "AVIF")

        try:
            # Test with string
            hash1 = encode(image_path_str)
            # Test with Path
            hash2 = encode(image_path_path)

            # Both should produce the same result
            self.assertEqual(hash1, hash2)
        finally:
            self._cleanup(image_path_path)


if __name__ == "__main__":
    unittest.main()
