#!/usr/bin/env python3
"""
AselCam - Ultra Low-Latency Virtual Camera & Microphone Studio
Cross-platform setup and packaging definition.
"""

from setuptools import setup, find_packages
import os

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="aselcam",
    version="1.5.2",
    author="AselCam Team",
    author_description="AselCam Ultra Low-Latency Virtual Webcam and Audio Studio",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/aselcam/aselcam",
    package_dir={"": "desktop"},
    packages=find_packages(where="desktop"),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video :: Capture",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
    ],
    python_requires=">=3.10",
    install_requires=[
        "PyQt6>=6.5.0",
        "numpy>=1.24.0",
        "pyvirtualcam>=0.11.0; sys_platform == 'win32' or sys_platform == 'darwin'",
    ],
    extras_require={
        "ai": [
            "opencv-python-headless>=4.8.0",
            "mediapipe>=0.10.0; python_version < '3.13'",
        ],
    },
    entry_points={
        "console_scripts": [
            "aselcam=aselcam.main:main",
        ],
    },
)
