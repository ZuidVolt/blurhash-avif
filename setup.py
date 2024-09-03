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
    url="https://github.com/ZuidVolt/blurhash-avif",
    project_urls={
        "Issue Tracker": "https://github.com/ZuidVolt/blurhash-avif/issues",
        "Changelog": "https://github.com/ZuidVolt/blurhash-avif/blob/main/CHANGELOG.md",
    },
    license="Apache Software License",
    keywords="blurhash avif image processing",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    package_data={"": ["*.txt", "*.md"]},  # Include README and other text files
    include_package_data=True,
    test_suite="tests",
    tests_require=["pytest"],
)
