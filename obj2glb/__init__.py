"""
OBJ to GLB Converter

A Python library and CLI tool for converting 3D models from OBJ format to GLB format
with full material and texture support.
"""

__version__ = "0.1.0"
__author__ = "Matthew Cronin"

from .converter import convert_obj_to_glb, convert_batch

__all__ = ["convert_obj_to_glb", "convert_batch"]

