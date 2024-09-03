
# blurhash-avif

A Python library to extend the Python Blurhash library to generate BlurHash and PNG data URLs for AVIF images.

**Disclaimer:** This is an unofficial extension and has no affiliation with the team or community that developed Blurhash. All credit for the original Blurhash concept and implementation goes to the creators of Blurhash.

## Installation

You can install the library using pip:

```zsh
pip install blurhash-avif
```

## Usage

The library provides three main functions:

1. `generate_blurhash_from_avif`: Generates a BlurHash string for an AVIF image.
2. `generate_png_data_url_from_avif`: Generates a base64-encoded PNG data URL for an AVIF image.
3. `generate_blurhash_and_data_url_from_avif`: Generates both a BlurHash string and a PNG data URL.

### Example Usage

```python
from blurhash_avif import generate_blurhash_from_avif, generate_png_data_url_from_avif, generate_blurhash_and_data_url_from_avif

# Path to your AVIF file
avif_path = "path/to/your/image.avif"

# Generate BlurHash string
blurhash = generate_blurhash_from_avif(avif_path)
if blurhash:
    print(f"BlurHash: {blurhash}")
else:
    print("Failed to generate BlurHash")

# Generate PNG data URL
data_url = generate_png_data_url_from_avif(avif_path)
if data_url:
    print(f"PNG Data URL: {data_url[:50]}...")  # Print first 50 characters
else:
    print("Failed to generate PNG Data URL")

# Generate both BlurHash and PNG data URL
blurhash, data_url = generate_blurhash_and_data_url_from_avif(avif_path)
if blurhash and data_url:
    print(f"BlurHash: {blurhash}")
    print(f"PNG Data URL: {data_url[:50]}...")  # Print first 50 characters
else:
    print("Failed to generate BlurHash and PNG Data URL")
```

## Troubleshooting

- For issues with Pillow's AVIF support, try:

  ```markdown
  pip uninstall pillow
  pip install "pillow[avif]"
  ```

## Attribution

This package is an unofficial extension of the Python Blurhash library. Blurhash was originally created by Dag Ågren for Wolt. The Blurhash algorithm and its official implementations can be found at the official [Blurhash GitHub repository](https://github.com/woltapp/blurhash).

---

## Licensing

This project is licensed under the Apache License, Version 2.0 with Additional commercial terms. See the [LICENSE](LICENSE) file for full detail
