"""
Thumbnail generation for 3D models.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import numpy as np

logger = logging.getLogger("obj2glb")


def get_thumbnail_path(glb_path: Path) -> Path:
    """
    Generate the thumbnail path for a given GLB file.
    
    Args:
        glb_path: Path to the GLB file
        
    Returns:
        Path where the thumbnail PNG should be saved
    """
    return glb_path.with_suffix(".png")


def find_matching_image(obj_path: Path) -> Optional[Path]:
    """
    Find a JPG or PNG file with the same base name as the OBJ file.
    Searches in:
    1. Same directory as OBJ
    2. Parent directory
    3. Any subdirectory of parent (recursive search)
    
    Args:
        obj_path: Path to the OBJ file
        
    Returns:
        Path to the matching image file, or None if not found
    """
    base_name = obj_path.stem  # filename without extension
    
    # Extensions to search for (in order of preference)
    extensions = ['.png', '.PNG', '.jpg', '.JPG', '.jpeg', '.JPEG']
    
    # Directories to search (in order)
    search_dirs = [
        obj_path.parent,          # Same directory
        obj_path.parent.parent,   # Parent directory
    ]
    
    # First, try exact name match in search directories
    for directory in search_dirs:
        if not directory.exists():
            continue
            
        for ext in extensions:
            image_path = directory / f"{base_name}{ext}"
            if image_path.exists():
                logger.debug(f"Found matching image: {image_path.relative_to(obj_path.parent.parent)}")
                return image_path
    
    # If not found, try recursive search in parent directory
    try:
        parent_dir = obj_path.parent.parent
        if parent_dir.exists():
            for ext in extensions:
                # Search recursively for matching filename
                matches = list(parent_dir.rglob(f"{base_name}{ext}"))
                if matches:
                    logger.debug(f"Found matching image (recursive): {matches[0].relative_to(parent_dir)}")
                    return matches[0]
    except Exception as e:
        logger.debug(f"Error during recursive image search: {e}")
    
    logger.debug(f"No matching image found for {base_name}")
    return None


def render_3d_thumbnail(scene, size: Tuple[int, int]) -> Optional[Image.Image]:
    """
    Render a 3D scene to a PIL Image using matplotlib.
    
    Args:
        scene: trimesh.Scene object
        size: Tuple of (width, height)
        
    Returns:
        PIL Image or None if rendering fails
    """
    try:
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        
        # Create figure with no padding
        fig = plt.figure(figsize=(size[0]/100, size[1]/100), dpi=100)
        ax = fig.add_subplot(111, projection='3d')
        
        # Get meshes from scene
        if hasattr(scene, 'geometry'):
            meshes = list(scene.geometry.values())
        else:
            meshes = [scene]
        
        # Plot each mesh with solid faces, no edges for cleaner look
        for mesh in meshes:
            if hasattr(mesh, 'vertices') and hasattr(mesh, 'faces'):
                vertices = mesh.vertices
                faces = mesh.faces
                
                # Create solid mesh without wireframe edges
                poly3d = [[vertices[j] for j in face] for face in faces]
                collection = Poly3DCollection(
                    poly3d, 
                    alpha=0.95,
                    facecolor='#87CEEB',  # Sky blue
                    edgecolor='none',  # No edges for cleaner look
                    linewidths=0
                )
                ax.add_collection3d(collection)
        
        # Set the aspect ratio and limits
        if hasattr(scene, 'bounds'):
            bounds = scene.bounds
        else:
            bounds = meshes[0].bounds
        
        # Set axis limits
        ax.set_xlim(bounds[0][0], bounds[1][0])
        ax.set_ylim(bounds[0][1], bounds[1][1])
        ax.set_zlim(bounds[0][2], bounds[1][2])
        
        # Set viewing angle for better perspective
        ax.view_init(elev=20, azim=45)
        
        # COMPLETELY HIDE ALL AXES, LABELS, AND GRID
        ax.set_axis_off()  # This removes all axis elements
        ax.set_facecolor('white')
        fig.patch.set_facecolor('white')
        
        # Remove all padding and margins
        ax.set_position([0, 0, 1, 1])
        
        # Save to a BytesIO object with no padding
        from io import BytesIO
        buf = BytesIO()
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                   pad_inches=0, facecolor='white', edgecolor='none')
        buf.seek(0)
        img = Image.open(buf).copy()  # Copy to keep after closing buffer
        plt.close(fig)
        buf.close()
        
        return img
        
    except Exception as e:
        logger.debug(f"3D rendering failed: {e}")
        return None


def generate_thumbnail(
    scene,  # trimesh.Scene
    output_path: Path,
    size: Tuple[int, int] = (512, 512),
    obj_path: Optional[Path] = None
) -> bool:
    """
    Generate a PNG thumbnail. Tries the following methods in order:
    1. Convert a JPG from the OBJ directory (if available)
    2. Render the 3D scene
    3. Create a placeholder image
    
    Args:
        scene: The trimesh scene to render
        output_path: Where to save the PNG thumbnail
        size: Thumbnail dimensions (width, height)
        obj_path: Path to the original OBJ file (to search for JPGs)
        
    Returns:
        True if thumbnail was created successfully, False otherwise
    """
    logger.debug(f"Generating thumbnail {size[0]}x{size[1]}...")
    
    img = None
    
    # Method 1: Try to find and use a matching image file (PNG/JPG) first
    if obj_path:
        image_path = find_matching_image(obj_path)
        if image_path:
            try:
                logger.debug(f"Using existing image: {image_path.name}")
                
                # Open and resize the image to thumbnail size
                img = Image.open(image_path)
                
                # Convert to RGB if necessary (handle RGBA, grayscale, etc.)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize to thumbnail size while maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create a new image with the exact size on white background
                thumb = Image.new('RGB', size, (255, 255, 255))
                
                # Center the resized image
                offset = ((size[0] - img.size[0]) // 2, (size[1] - img.size[1]) // 2)
                thumb.paste(img, offset)
                
                img = thumb
                
            except Exception as e:
                logger.debug(f"Failed to convert image to thumbnail: {e}")
                img = None
    
    # Method 2: If no matching image found or failed, try rendering the 3D scene
    if img is None and scene is not None:
        logger.debug("No matching image found, rendering 3D model...")
        img = render_3d_thumbnail(scene, size)
    
    # Method 3: If rendering failed, create a placeholder
    if img is None:
        logger.debug("Creating placeholder thumbnail...")
        try:
            img = Image.new('RGB', size, color=(240, 240, 240))
            from PIL import ImageDraw
            draw = ImageDraw.Draw(img)
            text = "No Preview\nAvailable"
            bbox = draw.textbbox((0, 0), text)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
            draw.text(position, text, fill=(128, 128, 128))
        except Exception as e:
            logger.error(f"Failed to create placeholder thumbnail: {e}")
            return False
    
    # Save the thumbnail
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the image
        img.save(output_path, 'PNG', optimize=True)
        logger.debug(f"Thumbnail saved to {output_path.name}")
        
        return True
    except Exception as e:
        logger.error(f"Failed to save thumbnail: {e}")
        return False
