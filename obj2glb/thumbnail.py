"""
Thumbnail generation for 3D models.
"""

import logging
from pathlib import Path
from typing import Optional, Tuple
import trimesh
import numpy as np
from PIL import Image

logger = logging.getLogger("obj2glb")


def generate_thumbnail(
    scene: trimesh.Scene,
    output_path: Path,
    size: Tuple[int, int] = (512, 512),
    background_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
) -> bool:
    """
    Generate a PNG thumbnail image of a 3D scene.
    
    Args:
        scene: Trimesh Scene object to render
        output_path: Path where the thumbnail PNG should be saved
        size: Tuple of (width, height) for the thumbnail
        background_color: RGBA tuple for background color (default: white)
        
    Returns:
        True if thumbnail was created successfully, False otherwise
    """
    try:
        logger.debug(f"Generating thumbnail {size[0]}x{size[1]}...")
        
        # Get the scene bounds to properly frame the model
        if isinstance(scene, trimesh.Scene):
            bounds = scene.bounds
        else:
            # Single mesh
            bounds = scene.bounds
        
        # Calculate the center and scale of the model
        center = (bounds[0] + bounds[1]) / 2
        scale = np.linalg.norm(bounds[1] - bounds[0])
        
        # Set up camera to view the entire model
        # Position camera to look at model from a nice angle
        camera_distance = scale * 2.5  # Move camera back enough to see whole model
        
        # Create camera position (angled view from front-right-top)
        camera_position = center + np.array([
            camera_distance * 0.5,  # Right
            camera_distance * 0.5,  # Forward  
            camera_distance * 0.7   # Up
        ])
        
        # Try to use pyrender for better quality rendering
        try:
            import pyrender
            
            # Convert trimesh scene to pyrender scene
            if isinstance(scene, trimesh.Scene):
                pyrender_scene = scene.to_pyrender_scene()
            else:
                # Single mesh
                pyrender_scene = pyrender.Scene()
                mesh = pyrender.Mesh.from_trimesh(scene)
                pyrender_scene.add(mesh)
            
            # Add camera
            camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
            camera_pose = np.eye(4)
            camera_pose[:3, 3] = camera_position
            
            # Point camera at center
            forward = center - camera_position
            forward = forward / np.linalg.norm(forward)
            
            # Create rotation matrix to look at center
            up = np.array([0, 0, 1])
            right = np.cross(forward, up)
            right = right / np.linalg.norm(right)
            up = np.cross(right, forward)
            
            camera_pose[:3, 0] = right
            camera_pose[:3, 1] = up
            camera_pose[:3, 2] = -forward
            
            pyrender_scene.add(camera, pose=camera_pose)
            
            # Add lighting
            light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)
            pyrender_scene.add(light, pose=camera_pose)
            
            # Add ambient light
            ambient = pyrender.DirectionalLight(color=np.ones(3), intensity=1.0)
            ambient_pose = np.eye(4)
            ambient_pose[:3, 3] = center + np.array([0, 0, scale])
            pyrender_scene.add(ambient, pose=ambient_pose)
            
            # Render
            renderer = pyrender.OffscreenRenderer(size[0], size[1])
            color, depth = renderer.render(pyrender_scene)
            renderer.delete()
            
            # Convert to PIL Image and save
            img = Image.fromarray(color, mode='RGB')
            
        except ImportError:
            logger.debug("pyrender not available, falling back to matplotlib rendering")
            # Fall back to matplotlib rendering
            try:
                import matplotlib
                matplotlib.use('Agg')  # Use non-interactive backend
                import matplotlib.pyplot as plt
                from mpl_toolkits.mplot3d import Axes3D
                from mpl_toolkits.mplot3d.art3d import Poly3DCollection
                
                # Create figure
                fig = plt.figure(figsize=(size[0]/100, size[1]/100), dpi=100)
                ax = fig.add_subplot(111, projection='3d')
                
                # Get meshes from scene
                if isinstance(scene, trimesh.Scene):
                    meshes = list(scene.geometry.values())
                else:
                    meshes = [scene]
                
                # Plot each mesh
                for mesh in meshes:
                    if hasattr(mesh, 'vertices') and hasattr(mesh, 'faces'):
                        # Create 3D polygon collection
                        vertices = mesh.vertices
                        faces = mesh.faces
                        
                        # Create the mesh3d
                        poly3d = [[vertices[j] for j in face] for face in faces]
                        collection = Poly3DCollection(poly3d, alpha=0.8, 
                                                     facecolor='lightblue', 
                                                     edgecolor='darkblue', 
                                                     linewidths=0.1)
                        ax.add_collection3d(collection)
                
                # Set the aspect ratio and limits
                if isinstance(scene, trimesh.Scene):
                    bounds = scene.bounds
                else:
                    bounds = scene.bounds
                
                # Set axis limits
                ax.set_xlim(bounds[0][0], bounds[1][0])
                ax.set_ylim(bounds[0][1], bounds[1][1])
                ax.set_zlim(bounds[0][2], bounds[1][2])
                
                # Set viewing angle for better perspective
                ax.view_init(elev=20, azim=45)
                
                # Remove axis labels and grid for cleaner look
                ax.set_xlabel('')
                ax.set_ylabel('')
                ax.set_zlabel('')
                ax.grid(False)
                ax.set_facecolor('white')
                
                # Save to a BytesIO object
                from io import BytesIO
                buf = BytesIO()
                plt.tight_layout()
                plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', 
                           facecolor='white', edgecolor='none')
                buf.seek(0)
                img = Image.open(buf)
                plt.close(fig)
                
            except Exception as e:
                logger.debug(f"Matplotlib rendering failed: {e}, trying basic trimesh")
                # Try trimesh's save_image as another fallback
                try:
                    # Use trimesh scene's save_image if available
                    if isinstance(scene, trimesh.Scene):
                        png_data = scene.save_image(resolution=size, visible=True)
                    else:
                        # Create a scene from single mesh
                        temp_scene = trimesh.Scene(scene)
                        png_data = temp_scene.save_image(resolution=size, visible=True)
                    
                    # Save the PNG data
                    img = Image.open(png_data)
                    
                except Exception as e2:
                    logger.debug(f"All rendering methods failed: {e2}, using simple wireframe")
                    # Create a simple 2D projection as last resort
                    try:
                        import matplotlib
                        matplotlib.use('Agg')
                        import matplotlib.pyplot as plt
                        
                        fig, ax = plt.subplots(figsize=(size[0]/100, size[1]/100), dpi=100)
                        
                        # Get vertices
                        if isinstance(scene, trimesh.Scene):
                            meshes = list(scene.geometry.values())
                        else:
                            meshes = [scene]
                        
                        for mesh in meshes:
                            if hasattr(mesh, 'vertices'):
                                # Simple 2D projection (top view)
                                vertices = mesh.vertices
                                ax.scatter(vertices[:, 0], vertices[:, 1], s=1, c='blue', alpha=0.5)
                        
                        ax.set_aspect('equal')
                        ax.set_facecolor('white')
                        ax.axis('off')
                        
                        from io import BytesIO
                        buf = BytesIO()
                        plt.tight_layout()
                        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight',
                                   facecolor='white', edgecolor='none')
                        buf.seek(0)
                        img = Image.open(buf)
                        plt.close(fig)
                        
                    except Exception as e3:
                        logger.warning(f"All rendering attempts failed: {e3}")
                        # Very last resort: create a simple placeholder
                        img = Image.new('RGB', size, color=(240, 240, 240))
                        from PIL import ImageDraw
                        draw = ImageDraw.Draw(img)
                        text = "Preview\nNot Available"
                        bbox = draw.textbbox((0, 0), text)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
                        draw.text(position, text, fill=(128, 128, 128))
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the image
        img.save(output_path, 'PNG')
        
        logger.debug(f"Thumbnail saved to {output_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to generate thumbnail: {e}")
        logger.debug("Thumbnail generation error details:", exc_info=True)
        return False


def get_thumbnail_path(glb_path: Path, thumbnail_dir: Optional[Path] = None) -> Path:
    """
    Generate the thumbnail path for a given GLB file.
    
    Args:
        glb_path: Path to the GLB file
        thumbnail_dir: Optional separate directory for thumbnails.
                      If None, thumbnail is saved next to GLB file.
        
    Returns:
        Path where the thumbnail should be saved
    """
    if thumbnail_dir:
        # Save in separate thumbnails directory, preserving structure
        thumbnail_path = thumbnail_dir / f"{glb_path.stem}.png"
    else:
        # Save next to the GLB file
        thumbnail_path = glb_path.with_suffix('.png')
    
    return thumbnail_path

