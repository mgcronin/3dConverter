"""
Material and texture handling for OBJ to GLB conversion.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
import numpy as np
from PIL import Image

logger = logging.getLogger("obj2glb")


class MaterialHandler:
    """
    Handles material and texture processing for OBJ to GLB conversion.
    """
    
    def __init__(self, obj_path: Path):
        """
        Initialize the material handler.
        
        Args:
            obj_path: Path to the OBJ file
        """
        self.obj_path = obj_path
        self.obj_dir = obj_path.parent
        self.materials = {}
        self.textures = {}
    
    def parse_mtl_file(self, mtl_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Parse an MTL file and extract material properties.
        
        Args:
            mtl_path: Path to the MTL file
            
        Returns:
            Dictionary mapping material names to their properties
        """
        if not mtl_path.exists():
            logger.warning(f"MTL file not found: {mtl_path}")
            return {}
        
        materials = {}
        current_material = None
        
        try:
            with open(mtl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue
                    
                    parts = line.split(None, 1)
                    if len(parts) < 1:
                        continue
                    
                    command = parts[0]
                    
                    # New material
                    if command == "newmtl":
                        if len(parts) < 2:
                            continue
                        current_material = parts[1]
                        materials[current_material] = {
                            "ambient": [0.2, 0.2, 0.2],
                            "diffuse": [0.8, 0.8, 0.8],
                            "specular": [1.0, 1.0, 1.0],
                            "shininess": 32.0,
                            "transparency": 1.0,
                            "textures": {}
                        }
                    
                    elif current_material:
                        value = parts[1] if len(parts) > 1 else ""
                        
                        # Ambient color
                        if command == "Ka":
                            materials[current_material]["ambient"] = self._parse_color(value)
                        
                        # Diffuse color
                        elif command == "Kd":
                            materials[current_material]["diffuse"] = self._parse_color(value)
                        
                        # Specular color
                        elif command == "Ks":
                            materials[current_material]["specular"] = self._parse_color(value)
                        
                        # Shininess
                        elif command == "Ns":
                            try:
                                materials[current_material]["shininess"] = float(value)
                            except ValueError:
                                pass
                        
                        # Transparency
                        elif command in ["d", "Tr"]:
                            try:
                                alpha = float(value)
                                if command == "Tr":
                                    alpha = 1.0 - alpha
                                materials[current_material]["transparency"] = alpha
                            except ValueError:
                                pass
                        
                        # Diffuse texture map
                        elif command == "map_Kd":
                            materials[current_material]["textures"]["diffuse"] = value
                        
                        # Normal/bump map
                        elif command in ["map_Bump", "bump"]:
                            materials[current_material]["textures"]["normal"] = value
                        
                        # Specular map
                        elif command == "map_Ks":
                            materials[current_material]["textures"]["specular"] = value
                        
                        # Ambient occlusion map
                        elif command == "map_Ka":
                            materials[current_material]["textures"]["ambient"] = value
            
            logger.info(f"Parsed {len(materials)} materials from {mtl_path.name}")
            return materials
            
        except Exception as e:
            logger.error(f"Error parsing MTL file {mtl_path}: {e}")
            return {}
    
    def _parse_color(self, value: str) -> List[float]:
        """
        Parse RGB color values from a string.
        
        Args:
            value: String containing RGB values
            
        Returns:
            List of 3 float values [R, G, B]
        """
        try:
            parts = value.split()
            if len(parts) >= 3:
                return [float(parts[0]), float(parts[1]), float(parts[2])]
            elif len(parts) == 1:
                # Single value - use for all channels
                val = float(parts[0])
                return [val, val, val]
        except (ValueError, IndexError):
            pass
        
        return [0.8, 0.8, 0.8]  # Default gray
    
    def load_texture(self, texture_path: str) -> Optional[Image.Image]:
        """
        Load a texture image from the given path.
        
        Args:
            texture_path: Path to the texture file (relative or absolute)
            
        Returns:
            PIL Image object or None if loading fails
        """
        # Try different possible paths
        possible_paths = [
            Path(texture_path),
            self.obj_dir / texture_path,
            self.obj_dir / Path(texture_path).name,
        ]
        
        for path in possible_paths:
            try:
                if path.exists() and path.is_file():
                    logger.debug(f"Loading texture: {path}")
                    img = Image.open(path)
                    # Convert to RGB if necessary
                    if img.mode not in ["RGB", "RGBA"]:
                        img = img.convert("RGB")
                    return img
            except Exception as e:
                logger.debug(f"Failed to load texture from {path}: {e}")
                continue
        
        logger.warning(f"Texture not found: {texture_path}")
        return None
    
    def load_all_textures(self, materials: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Image.Image]]:
        """
        Load all textures referenced in materials.
        
        Args:
            materials: Dictionary of material properties
            
        Returns:
            Dictionary mapping material names to their loaded texture images
        """
        loaded_textures = {}
        
        for mat_name, mat_props in materials.items():
            if "textures" not in mat_props:
                continue
            
            loaded_textures[mat_name] = {}
            
            for tex_type, tex_path in mat_props["textures"].items():
                img = self.load_texture(tex_path)
                if img:
                    loaded_textures[mat_name][tex_type] = img
                    logger.info(f"Loaded {tex_type} texture for material '{mat_name}'")
        
        return loaded_textures
    
    def create_default_material(self) -> Dict[str, Any]:
        """
        Create a default material for models without materials.
        
        Returns:
            Dictionary containing default material properties
        """
        return {
            "default": {
                "ambient": [0.2, 0.2, 0.2],
                "diffuse": [0.8, 0.8, 0.8],
                "specular": [1.0, 1.0, 1.0],
                "shininess": 32.0,
                "transparency": 1.0,
                "textures": {}
            }
        }
    
    def process_materials(self) -> tuple:
        """
        Process all materials and textures for the OBJ file.
        
        Returns:
            Tuple of (materials_dict, textures_dict)
        """
        # Look for MTL file
        mtl_path = self.obj_path.with_suffix(".mtl")
        
        if mtl_path.exists():
            materials = self.parse_mtl_file(mtl_path)
            if materials:
                textures = self.load_all_textures(materials)
                return materials, textures
        
        # No materials found - use default
        logger.info("No materials found, using default material")
        return self.create_default_material(), {}

