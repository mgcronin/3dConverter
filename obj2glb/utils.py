"""
Utility functions for OBJ to GLB conversion.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional


def setup_logger(verbose: bool = False) -> logging.Logger:
    """
    Setup and configure the logger.
    
    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("obj2glb")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger


def validate_input_file(filepath: str) -> Path:
    """
    Validate that the input file exists and is an OBJ file.
    
    Args:
        filepath: Path to the input file
        
    Returns:
        Path object for the validated file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not an OBJ file
    """
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    if not path.is_file():
        raise ValueError(f"Input path is not a file: {filepath}")
    
    if path.suffix.lower() != ".obj":
        raise ValueError(f"Input file must be an OBJ file, got: {path.suffix}")
    
    return path


def validate_output_file(filepath: str, overwrite: bool = False) -> Path:
    """
    Validate the output file path.
    
    Args:
        filepath: Path to the output file
        overwrite: If True, allow overwriting existing files
        
    Returns:
        Path object for the output file
        
    Raises:
        FileExistsError: If file exists and overwrite is False
        ValueError: If file extension is not .glb
    """
    path = Path(filepath)
    
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Output file already exists: {filepath}. Use --overwrite to replace it."
        )
    
    if path.suffix.lower() != ".glb":
        raise ValueError(f"Output file must have .glb extension, got: {path.suffix}")
    
    # Create parent directory if it doesn't exist
    path.parent.mkdir(parents=True, exist_ok=True)
    
    return path


def find_obj_files(directory: str, recursive: bool = False) -> List[Path]:
    """
    Find all OBJ files in a directory.
    
    Args:
        directory: Path to the directory to search
        recursive: If True, search subdirectories recursively
        
    Returns:
        List of Path objects for found OBJ files
        
    Raises:
        NotADirectoryError: If the path is not a directory
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    if not dir_path.is_dir():
        raise NotADirectoryError(f"Path is not a directory: {directory}")
    
    if recursive:
        # Recursive search using rglob
        obj_files = list(dir_path.rglob("*.obj"))
        obj_files.extend(dir_path.rglob("*.OBJ"))
    else:
        # Non-recursive search using glob
        obj_files = list(dir_path.glob("*.obj"))
        obj_files.extend(dir_path.glob("*.OBJ"))
    
    return sorted(set(obj_files))


def get_output_path(input_path: Path, output_dir: Optional[Path] = None, 
                    input_base_dir: Optional[Path] = None) -> Path:
    """
    Generate output path for a given input file.
    
    Args:
        input_path: Path to the input OBJ file
        output_dir: Optional output directory. If None, uses same directory as input
        input_base_dir: Base directory for input (used to preserve directory structure)
        
    Returns:
        Path object for the output GLB file
    """
    if output_dir:
        if input_base_dir:
            # Preserve directory structure relative to base directory
            try:
                relative_path = input_path.relative_to(input_base_dir)
                output_path = output_dir / relative_path.parent / f"{input_path.stem}.glb"
            except ValueError:
                # If relative path fails, just use the filename
                output_path = output_dir / f"{input_path.stem}.glb"
        else:
            # Just use the filename in the output directory
            output_path = output_dir / f"{input_path.stem}.glb"
        
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
    else:
        return input_path.parent / f"{input_path.stem}.glb"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

