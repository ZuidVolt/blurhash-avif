from setuptools import setup, find_packages

setup(
    name="blurhash-avif",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "Pillow[avif]",
        "blurhash",
    ],
    author="Zuidvolt",
    description="A library to generate BlurHash and PNG data URLs for AVIF images",
    long_description=open("README.md").read(),  # noqa
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/blurhash-avif",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
