# tests/__init__.py
import unittest
from blurhash_avif.py import (
    generate_blurhash_from_avif,
    generate_png_data_url_from_avif,
    generate_blurhash_and_data_url_from_avif,
)


class TestBlurhashAvif(unittest.TestCase):
    def test_generate_blurhash_from_avif(self):
        # Add your test here
        pass

    def test_generate_png_data_url_from_avif(self):
        # Add your test here
        pass

    def test_generate_blurhash_and_data_url_from_avif(self):
        # Add your test here
        pass


if __name__ == "__main__":
    unittest.main()
