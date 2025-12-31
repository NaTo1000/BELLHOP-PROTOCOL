"""
Setup script for BELLHOP Protocol
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="bellhop-protocol",
    version="1.0.0",
    author="BELLHOP Protocol Contributors",
    description="Comprehensive security suite for Meshtastic mesh networks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/NaTo1000/BELLHOP-PROTOCOL",
    project_urls={
        "Bug Tracker": "https://github.com/NaTo1000/BELLHOP-PROTOCOL/issues",
        "Documentation": "https://github.com/NaTo1000/BELLHOP-PROTOCOL",
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Networking",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bellhop=bellhop.cli:main",
        ],
    },
)
