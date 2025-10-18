"""
Core OBJ to GLB conversion functionality.
"""

import logging
from pathlib import Path
from typing import Optional, List
import trimesh
import numpy as np

from .materials import MaterialHandler
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
    overwrite: bool = False
) -> bool:
    """
    Convert a single OBJ file to GLB format.
    
    Args:
        input_path: Path to the input OBJ file
        output_path: Path to the output GLB file
        overwrite: If True, overwrite existing output files
        
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
    overwrite: bool = False
) -> tuple:
    """
    Convert all OBJ files in a directory to GLB format.
    
    Args:
        input_dir: Path to directory containing OBJ files
        output_dir: Path to output directory for GLB files
        overwrite: If True, overwrite existing output files
        
    Returns:
        Tuple of (success_count, failure_count)
    """
    try:
        # Find all OBJ files
        obj_files = find_obj_files(input_dir)
        
        if not obj_files:
            logger.warning(f"No OBJ files found in {input_dir}")
            return 0, 0
        
        logger.info(f"Found {len(obj_files)} OBJ file(s) to convert")
        
        # Create output directory
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Convert each file
        success_count = 0
        failure_count = 0
        
        for i, obj_file in enumerate(obj_files, 1):
            logger.info(f"\n[{i}/{len(obj_files)}] Processing {obj_file.name}")
            
            # Generate output path
            output_file = get_output_path(obj_file, output_path)
            
            # Convert
            if convert_obj_to_glb(str(obj_file), str(output_file), overwrite):
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

