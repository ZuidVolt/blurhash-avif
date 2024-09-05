from setuptools import setup, find_packages

with open("README.md", "r") as f:  # noqa
    long_description = f.read()

setup(
    name="blurhash-avif",
    version="0.6.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=["pillow-avif-plugin", "numpy", "Pillow[avif]", "blurhash", "pathlib", "typing",],
    author="ZuidVolt",
    description="A library to generate BlurHash and PNG data URLs for AVIF images",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ZuidVolt/blurhash-avif",
    project_urls={
        "Issue Tracker": "https://github.com/ZuidVolt/blurhash-avif/issues",
        "Changelog": "https://github.com/ZuidVolt/blurhash-avif/releases",
        "source: ": "https://github.com/ZuidVolt/blurhash-avif",
        "Documentation": "https://github.com/ZuidVolt/blurhash-avif/blob/main/README.md",
    },
    license="Apache Software License",
    keywords="blurhash avif image processing",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    package_data={"": ["*.txt", "*.md", "py.typed"]},
    include_package_data=True,
    zip_safe=False,  # Required for mypy to work
    test_suite="tests",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "blurhash-avif=blurhash_avif:generate_blurhash_and_data_url_from_avif",
        ],
    },
)
