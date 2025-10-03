# blurhash-avif

A small library for generating **BlurHash** placeholders and lightweight **PNG data URLs** from AVIF images — ideal for fast, progressive image loading in web apps and static sites.

**Disclaimer:** This is an unofficial extension and has no affiliation with the original BlurHash developers. All credit for the BlurHash concept and implementation goes to its creators.

This README is intentionally concise: every function is fully documented in the code. Here you will find quick installation, practical examples (single-file + batch + decoding) and troubleshooting guidance that is easier to find here than in the docstrings.

---

## Highlights

* Generate BlurHash strings from `.avif` images (compact, text-based placeholders).
* Produce small PNG data URLs (base64) suitable for inline `src` or `srcset` placeholders.
* Safe, defensive handling of invalid paths and image issues with explicit exceptions.
* Batch helpers for directories of AVIFs.
* Decode BlurHash back into a PNG and save to disk.

---

## Installation

**From PyPI (recommended):**

```bash
pip install blurhash-avif
```

**From source (editable / dev):**

```bash
git clone https://github.com/ZuidVolt/blurhash-avif.git
cd blurhash-avif
pip install -e .[dev]
```

### Native image codec requirements

`Pillow` needs AVIF support. The package depends on `pillow-avif-plugin` (the recommended plugin). You may also need the system `libavif` (or equivalent) for AVIF decoding/encoding.

* macOS (Homebrew):

```bash
brew install libavif
```

* Debian/Ubuntu:

```bash
sudo apt-get install libavif-dev
```

If Pillow cannot read AVIF after installing `pillow-avif-plugin`, reinstall Pillow with AVIF extras or ensure the plugin is installed in the same environment.

---

## Quickstart

```python
import blurhash_avif as bha
from pathlib import Path

avif_path = Path("assets/photo.avif")

# 1) Single-file: BlurHash only
bh = bha.encode(avif_path, x_components=4, y_components=3)
print("BlurHash preview:", bh[:12].upper(), "…", "len=", len(bh))

# 2) Single-file: PNG data URL (thumbnail) and quick inspect of payload
pdu = bha.encode_pdu(avif_path, max_dimension=64)
# split and show the first 60 bytes of the base64 payload
print("PNG payload (head):", pdu.split(",", 1)[1][:60] + "...")

# 3) Convenience: both (returns tuple[Optional[str], Optional[str]])
bh, pdu = bha.encode_blurhash_and_pda(avif_path, x_components=4, y_components=4, max_dimension=48)
print("got both ->", bool(bh), bool(pdu))

# 4) Batch: all .avif files in a directory
results: dict[str, Optional[str]] = bha.batch_encode("assets/") # returns dict(filename -> blurhash_or_None)
valid_files = [name for name, h in results.items() if h]
print("Valid blurhash files:", ", ".join(valid_files) or "<none>")

# 5) Decode a blurhash back to disk then check existence
if bh:
    bha.decode("./decoded/", bh, filename="decoded.png", width=400, height=300, verbose=True)
    print(Path("./decoded/decoded.png").exists())

# 6) Decode to PIL image and save with PIL API
if bh:
    img = bha.decode_to_pil_format(bh, 200, 150, punch=1.1)
    out_path = Path("./decoded") / "from_pil.png"
    img.save(out_path)  # PIL.Image.Image.save returns None; we use pathlib to inspect
    print(out_path.name, "->", out_path.exists())
```

---

## Example: Using in a web page

Use the PNG data URL as an inline placeholder while the full AVIF loads.

```html
<!-- small inline placeholder generated with encode_pdu(...) -->
<img
  src="data:image/png;base64,iVBORw0KGgoAAAANS..."
  data-full-src="/images/photo.avif"
  alt="Example"
  width="600"
  height="400"
/>

<!-- or use the BlurHash string client-side (if you decode in JS) -->
<div id="placeholder"></div>
<script>
  // decode using a BlurHash JS library to paint a canvas until AVIF is ready
  // blurhashString is the string returned by encode(...)
</script>
```

This package produces the blurhash string and inline data URL; how you integrate that into your web framework or static generator is up to you.

---
## Exceptions

The library raises a small, intentional set of typed exceptions so you can handle errors ergonomically:

* `BlurHashAvifError` — base class for all library exceptions
* `BlurHashEncodeError` — blurhash encoding failed
* `AvifPngDataUrlError` — png data URL creation failed
* `BlurHashDecodeError` — blurhash decoding failed
* `PathError` — invalid path or I/O issues
* `ImageSaveError` — failure when saving decoded images

Use `except BlurHashAvifError:` to catch all library-level errors.

---

## Troubleshooting

* *Pillow can't open `.avif` files:* ensure `pillow-avif-plugin` is installed and that your environment's Pillow is compatible with the plugin. Reinstall Pillow after installing the plugin if needed.
  ```bash
  pip uninstall pillow
  pip install "pillow[avif]"
  ```
* *`MemoryError` or slow performance on huge images:* rely on the library's default resize behavior or pre-scale images.
* *Unexpected `None` in batch maps:* the library stores `None` for any file that failed to encode; inspect logs or call the functions individually for more detailed exceptions.

---

## Attribution & License

This package extends the Python BlurHash library. BlurHash was originally created by Dag Ågren for Wolt. The BlurHash algorithm and official implementations are available at the [BlurHash GitHub repository](https://github.com/woltapp/blurhash).

This project is licensed under the Apache License, Version 2.0

---
