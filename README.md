
# BlurHash-AVIF

A Python library extending the Python BlurHash implementation to generate BlurHash strings and PNG data URLs for AVIF images.

**Disclaimer:** This is an unofficial extension and has no affiliation with the original BlurHash developers. All credit for the BlurHash concept and implementation goes to its creators.

## Table of Contents

1. [Installation](#installation)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Usage](#usage)
5. [Troubleshooting](#troubleshooting)
6. [Contributing](#contributing)
7. [Attribution](#attribution)
8. [License](#license)

## Installation

Install the library using pip:

```bash
pip install blurhash-avif
```

## Features

- Generate BlurHash strings from AVIF images
- Create base64-encoded PNG data URLs from AVIF images
- Maintain image aspect ratio during processing
- Support RGB mode images
- Optimize image loading for improved website performance

## Requirements

- Python 3.x
- Pillow (PIL) library with AVIF support
- NumPy library
- base64 library
- blurhash library

## Usage

The library provides six main functions:

1. `generate_blurhash_from_avif`: Create a BlurHash string from an AVIF image.
2. `generate_png_data_url_from_avif`: Generate a base64-encoded PNG data URL from an AVIF image.
3. `generate_blurhash_and_data_url_from_avif`: Produce both a BlurHash string and a PNG data URL.
4. `batch_generate_blurhash_from_avif`: Generates BlurHash strings for all AVIF images in a given directory.
5. `batch_generate_png_data_url_from_avif`: Generates base64-encoded PNG data URLs for all AVIF images in a given directory.
6. `batch_generate_blurhash_and_data_url_from_avif`: Generates BlurHash strings and base64-encoded PNG data URLs for all AVIF images in a given directory.

### Example Usage

```python
from blurhash_avif import (
    generate_blurhash_from_avif,
    generate_png_data_url_from_avif,
    generate_blurhash_and_data_url_from_avif,
    batch_generate_blurhash_from_avif,
    batch_generate_png_data_url_from_avif,
    batch_generate_blurhash_and_data_url_from_avif,
)

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
    print(f"PNG Data URL: {data_url[:50]}...") # Print first 50 characters
else:
    print("Failed to generate PNG Data URL")

# Generate both BlurHash and PNG data URL
blurhash, data_url = generate_blurhash_and_data_url_from_avif(avif_path)
if blurhash and data_url:
    print(f"BlurHash: {blurhash}")
    print(f"PNG Data URL: {data_url[:50]}...") # Print first 50 characters
else:
    print("Failed to generate BlurHash and PNG Data URL")

# Batch generate BlurHash strings
directory = "path/to/your/images"
blurhash_dict = batch_generate_blurhash_from_avif(directory)
print(blurhash_dict)

# Batch generate PNG data URLs
data_url_dict = batch_generate_png_data_url_from_avif(directory)
print(data_url_dict)

# Batch generate BlurHash strings and PNG data URLs
blurhash_dict, data_url_dict = batch_generate_blurhash_and_data_url_from_avif(directory)
print(blurhash_dict)
print(data_url_dict)
```

## Troubleshooting

If you encounter issues with Pillow's AVIF support, try:

```bash
pip uninstall pillow
pip install "pillow[avif]"
```

you man need to install the `aviflib` library.

To install the required `aviflib` library, follow these steps:

**On macOS (using Homebrew):**

```bash
brew install libavif
```

**On Ubuntu/Debian:**

```bash
sudo apt-get install libavif-dev
```

**On windows**

```bash
pip install aom
```

or

**On windows (vcpkg)**

```bash
vcpkg install libavif
```

## Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## Attribution

This package extends the Python BlurHash library. BlurHash was originally created by Dag Ågren for Wolt. The BlurHash algorithm and official implementations are available at the [BlurHash GitHub repository](https://github.com/woltapp/blurhash).

## License

This project is licensed under the Apache License, Version 2.0 with important additional terms, including specific commercial use conditions. Users are strongly advised to read the full [LICENSE](LICENSE) file carefully before using, modifying, or distributing this work. The additional terms contain crucial information about liability, data collection, indemnification, and commercial usage requirements that may significantly affect your rights and obligations.

---

Keywords: BlurHash, AVIF, image processing, Python, base64, PNG, data URL, image optimization, web performance, placeholder images
