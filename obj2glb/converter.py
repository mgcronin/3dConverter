"""
Core OBJ to GLB conversion functionality.
"""

import logging
from pathlib import Path
from typing import Optional, List
import trimesh
import numpy as np

from .materials import MaterialHandler
from .thumbnail import generate_thumbnail, get_thumbnail_path
from .preview import generate_preview_html
from .utils import (
    validate_input_file,
    validate_output_file,
    find_obj_files,
    get_output_path,
    format_file_size
)

logger = logging.getLogger("obj2glb")


def convert_obj_to_glb(
    input_path: str,
    output_path: str,
    overwrite: bool = False,
    generate_thumbnail_image: bool = False,
    thumbnail_size: tuple = (512, 512),
    generate_preview: bool = False
) -> bool:
    """
    Convert a single OBJ file to GLB format.
    
    Args:
        input_path: Path to the input OBJ file
        output_path: Path to the output GLB file
        overwrite: If True, overwrite existing output files
        generate_thumbnail_image: If True, generate a PNG thumbnail
        thumbnail_size: Tuple of (width, height) for thumbnail
        
    Returns:
        True if conversion was successful, False otherwise
    """
    try:
        # Validate paths
        input_file = validate_input_file(input_path)
        output_file = validate_output_file(output_path, overwrite)
        
        logger.info(f"Converting {input_file.name} to GLB format...")
        
        # Initialize material handler
        mat_handler = MaterialHandler(input_file)
        materials, textures = mat_handler.process_materials()
        
        # Load the OBJ file with trimesh
        logger.debug("Loading OBJ file...")
        scene = trimesh.load(
            str(input_file),
            force="scene",
            process=False
        )
        
        # Handle both Scene and single mesh
        if isinstance(scene, trimesh.Scene):
            meshes = list(scene.geometry.values())
            logger.debug(f"Loaded scene with {len(meshes)} meshes")
        else:
            meshes = [scene]
            logger.debug("Loaded single mesh")
        
        # Verify we have geometry
        if not meshes or all(len(m.vertices) == 0 for m in meshes):
            logger.error("No valid geometry found in OBJ file")
            return False
        
        # Apply materials and textures to meshes
        for i, mesh in enumerate(meshes):
            if hasattr(mesh, "visual") and hasattr(mesh.visual, "material"):
                # Mesh already has material from OBJ
                logger.debug(f"Mesh {i} has existing material")
            else:
                # Apply default material
                logger.debug(f"Applying default material to mesh {i}")
                mesh.visual = trimesh.visual.TextureVisuals(
                    material=trimesh.visual.material.SimpleMaterial()
                )
        
        # Export to GLB
        logger.debug(f"Exporting to {output_file}...")
        
        if isinstance(scene, trimesh.Scene):
            # Export scene
            scene.export(
                str(output_file),
                file_type="glb"
            )
        else:
            # Export single mesh
            scene.export(
                str(output_file),
                file_type="glb"
            )
        
        # Check output file was created
        if output_file.exists():
            file_size = format_file_size(output_file.stat().st_size)
            logger.info(f"✓ Successfully converted to {output_file.name} ({file_size})")
            
            # Generate thumbnail if requested
            if generate_thumbnail_image:
                thumbnail_path = get_thumbnail_path(output_file)
                if generate_thumbnail(scene, thumbnail_path, size=thumbnail_size, obj_path=input_file):
                    thumb_size = format_file_size(thumbnail_path.stat().st_size)
                    logger.info(f"✓ Generated thumbnail: {thumbnail_path.name} ({thumb_size})")
                else:
                    logger.warning(f"Failed to generate thumbnail for {output_file.name}")
            
            # Generate HTML preview if requested
            if generate_preview:
                try:
                    preview_path = generate_preview_html(output_file)
                    preview_size = format_file_size(preview_path.stat().st_size)
                    logger.info(f"✓ Generated preview: {preview_path.name} ({preview_size})")
                except Exception as e:
                    logger.warning(f"Failed to generate preview: {e}")
            
            return True
        else:
            logger.error("Output file was not created")
            return False
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return False
    except ValueError as e:
        logger.error(f"Invalid input: {e}")
        return False
    except FileExistsError as e:
        logger.error(f"File exists: {e}")
        return False
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        logger.debug(f"Error details:", exc_info=True)
        return False


def convert_batch(
    input_dir: str,
    output_dir: str,
    overwrite: bool = False,
    recursive: bool = False,
    generate_thumbnail_image: bool = False,
    thumbnail_size: tuple = (512, 512),
    generate_preview: bool = False
) -> tuple:
    """
    Convert all OBJ files in a directory to GLB format.
    
    Args:
        input_dir: Path to directory containing OBJ files
        output_dir: Path to output directory for GLB files
        overwrite: If True, overwrite existing output files
        recursive: If True, search subdirectories recursively
        generate_thumbnail_image: If True, generate PNG thumbnails
        thumbnail_size: Tuple of (width, height) for thumbnails
        
    Returns:
        Tuple of (success_count, failure_count)
    """
    try:
        # Find all OBJ files
        obj_files = find_obj_files(input_dir, recursive=recursive)
        
        if not obj_files:
            search_type = "recursively" if recursive else ""
            logger.warning(f"No OBJ files found {search_type} in {input_dir}")
            return 0, 0
        
        search_type = "recursively " if recursive else ""
        logger.info(f"Found {len(obj_files)} OBJ file(s) {search_type}to convert")
        
        # Create output directory
        input_base_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Convert each file
        success_count = 0
        failure_count = 0
        
        for i, obj_file in enumerate(obj_files, 1):
            # Show relative path if recursive, otherwise just filename
            if recursive:
                try:
                    display_path = obj_file.relative_to(input_base_path)
                except ValueError:
                    display_path = obj_file.name
            else:
                display_path = obj_file.name
            
            logger.info(f"\n[{i}/{len(obj_files)}] Processing {display_path}")
            
            # Generate output path (preserving directory structure if recursive)
            if recursive:
                output_file = get_output_path(obj_file, output_path, input_base_path)
            else:
                output_file = get_output_path(obj_file, output_path)
            
            # Convert
            if convert_obj_to_glb(
                str(obj_file), 
                str(output_file), 
                overwrite,
                generate_thumbnail_image,
                thumbnail_size,
                generate_preview
            ):
                success_count += 1
            else:
                failure_count += 1
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info(f"Batch conversion complete!")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {failure_count}")
        logger.info(f"  Total: {len(obj_files)}")
        logger.info("="*60)
        
        return success_count, failure_count
        
    except FileNotFoundError as e:
        logger.error(f"Directory not found: {e}")
        return 0, 0
    except NotADirectoryError as e:
        logger.error(f"Invalid directory: {e}")
        return 0, 0
    except Exception as e:
        logger.error(f"Batch conversion failed: {e}")
        logger.debug(f"Error details:", exc_info=True)
        return 0, 0

