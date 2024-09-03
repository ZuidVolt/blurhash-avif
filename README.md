
# blurhash-avif

A Python library to extend the Python Blurhash library to generate BlurHash and PNG data URLs for AVIF images.

**Disclaimer:** This is an unofficial extension and has no affiliation with the team or community that developed Blurhash. All credit for the original Blurhash concept and implementation goes to the creators of Blurhash.

## Table of Contents

1. [Installation](#installation)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Usage](#usage)
5. [Troubleshooting](#troubleshooting)
6. [Contributing](#contributing)
7. [License](#license)

## Installation

You can install the library using pip:

```zsh
pip install blurhash-avif
```

## Features

- Generate BlurHash strings for AVIF images
- Create base64-encoded PNG data URLs for resized images
- Maintain aspect ratio during image resizing
- Support for RGB mode images
- Optimize image loading and improve website performance

## Requirements

- Python 3.x
- Pillow (PIL) library with AVIF support
- NumPy library
- base64 library
- blurhash library

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

## Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## Attribution

This package is an unofficial extension of the Python Blurhash library. Blurhash was originally created by Dag Ågren for Wolt. The Blurhash algorithm and its official implementations can be found at the official [Blurhash GitHub repository](https://github.com/woltapp/blurhash).

---

## license

This project is licensed under the Apache License, Version 2.0 with Additional commercial terms. See the [LICENSE](LICENSE) file for full detail
