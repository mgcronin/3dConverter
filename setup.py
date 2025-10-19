from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="obj2glb",
    version="0.1.0",
    author="Matthew Cronin",
    description="A CLI tool to convert 3D OBJ files to GLB format with full material and texture support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mgcronin/3dConverter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "trimesh>=3.20.0",
        "pygltflib>=1.15.0",
        "Pillow>=9.0.0",
        "click>=8.0.0",
        "numpy>=1.20.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
        ],
        "thumbnails": [
            "pyrender>=0.1.45",
        ],
        "firebase": [
            "firebase-admin>=6.0.0",
        ],
        "api": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.0.0",
            "python-multipart>=0.0.6",
        ],
        "mcp": [
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0",
            "pydantic>=2.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "obj2glb=obj2glb.cli:main",
        ],
    },
)

