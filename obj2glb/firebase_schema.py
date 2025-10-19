"""
Firebase database schema definitions for GLB model import.

This module defines the data structures and validation for importing
3D models into Firebase Firestore collections.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Union, Any
from pathlib import Path
import logging

logger = logging.getLogger("obj2glb")


@dataclass
class Dimensions:
    """3D model dimensions."""
    width: float
    height: float
    depth: float
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to Firebase-compatible dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "depth": self.depth
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'Dimensions':
        """Create from Firebase dictionary."""
        return cls(
            width=data.get("width", 0.0),
            height=data.get("height", 0.0),
            depth=data.get("depth", 0.0)
        )


@dataclass
class SimpleObject:
    """Simple object schema for doors, double_doors, garages."""
    name: str
    path: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to Firebase-compatible dictionary."""
        return {
            "name": self.name,
            "path": self.path
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'SimpleObject':
        """Create from Firebase dictionary."""
        return cls(
            name=data.get("name", ""),
            path=data.get("path", "")
        )


@dataclass
class ToolObject:
    """Complex object schema for tools collection."""
    name: str
    path_3d: str  # Maps to "3d" field in Firebase
    dimensions: Dimensions
    svg_icon: str
    object_type: str  # Maps to "type" field in Firebase
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firebase-compatible dictionary."""
        return {
            "name": self.name,
            "3d": self.path_3d,
            "dimensions": self.dimensions.to_dict(),
            "svgIcon": self.svg_icon,
            "type": self.object_type,
            "createdAt": self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolObject':
        """Create from Firebase dictionary."""
        dimensions_data = data.get("dimensions", {})
        dimensions = Dimensions.from_dict(dimensions_data) if dimensions_data else Dimensions(0, 0, 0)
        
        created_at = data.get("createdAt")
        if isinstance(created_at, str):
            # Handle string timestamps if needed
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        elif created_at is None:
            created_at = datetime.utcnow()
        
        return cls(
            name=data.get("name", ""),
            path_3d=data.get("3d", ""),
            dimensions=dimensions,
            svg_icon=data.get("svgIcon", ""),
            object_type=data.get("type", ""),
            created_at=created_at
        )


class FirebaseSchemaValidator:
    """Validates data before Firebase import."""
    
    @staticmethod
    def validate_simple_object(obj: SimpleObject) -> bool:
        """Validate simple object data."""
        if not obj.name or not obj.name.strip():
            logger.error("Simple object name cannot be empty")
            return False
        
        if not obj.path or not obj.path.strip():
            logger.error("Simple object path cannot be empty")
            return False
        
        # Validate path format
        if not obj.path.startswith("/3dData/"):
            logger.warning(f"Path should start with '/3dData/': {obj.path}")
        
        if not obj.path.endswith(".glb"):
            logger.warning(f"Path should end with '.glb': {obj.path}")
        
        return True
    
    @staticmethod
    def validate_tool_object(obj: ToolObject) -> bool:
        """Validate tool object data."""
        if not obj.name or not obj.name.strip():
            logger.error("Tool object name cannot be empty")
            return False
        
        if not obj.path_3d or not obj.path_3d.strip():
            logger.error("Tool object 3D path cannot be empty")
            return False
        
        # Validate path format
        if not obj.path_3d.startswith("/3dData/"):
            logger.warning(f"3D path should start with '/3dData/': {obj.path_3d}")
        
        if not obj.path_3d.endswith(".glb"):
            logger.warning(f"3D path should end with '.glb': {obj.path_3d}")
        
        # Validate dimensions
        if obj.dimensions.width <= 0 or obj.dimensions.height <= 0 or obj.dimensions.depth <= 0:
            logger.warning(f"Invalid dimensions: {obj.dimensions.width}x{obj.dimensions.height}x{obj.dimensions.depth}")
        
        # Validate SVG icon
        if not obj.svg_icon or not obj.svg_icon.strip():
            logger.warning("SVG icon is empty")
        
        if obj.svg_icon and not obj.svg_icon.strip().startswith("<?xml"):
            logger.warning("SVG icon should be valid XML")
        
        # Validate object type
        if not obj.object_type or not obj.object_type.strip():
            logger.warning("Object type is empty")
        
        return True


def categorize_glb_file(glb_path: Path) -> str:
    """
    Categorize a GLB file based on its path structure.
    
    Args:
        glb_path: Path to the GLB file
        
    Returns:
        Category name: 'doors', 'double_doors', 'garages', or 'tools'
    """
    path_str = str(glb_path).lower()
    
    # Check for specific categories in path
    if 'door' in path_str and 'double' in path_str:
        return 'double_doors'
    elif 'door' in path_str and 'garage' in path_str:
        return 'garages'
    elif 'door' in path_str:
        return 'doors'
    elif 'garage' in path_str:
        return 'garages'
    else:
        return 'tools'


def determine_object_type(glb_path: Path, category: str) -> str:
    """
    Determine the object type based on file path and category.
    
    Args:
        glb_path: Path to the GLB file
        category: Category determined by categorize_glb_file
        
    Returns:
        Object type string (e.g., 'Lighting', 'Furniture', 'Door', etc.)
    """
    path_str = str(glb_path).lower()
    filename = glb_path.stem.lower()
    
    # Category-specific types
    if category == 'doors':
        return 'Door'
    elif category == 'double_doors':
        return 'Double Door'
    elif category == 'garages':
        return 'Garage'
    
    # Tool-specific types based on path/filename
    if 'light' in path_str or 'lamp' in path_str:
        return 'Lighting'
    elif 'chair' in path_str or 'sofa' in path_str or 'table' in path_str:
        return 'Furniture'
    elif 'window' in path_str:
        return 'Window'
    elif 'bath' in path_str or 'toilet' in path_str or 'sink' in path_str:
        return 'Bathroom'
    elif 'kitchen' in path_str or 'cooker' in path_str or 'stove' in path_str:
        return 'Kitchen'
    elif 'bed' in path_str or 'wardrobe' in path_str:
        return 'Bedroom'
    elif 'plant' in path_str or 'tree' in path_str:
        return 'Garden'
    elif 'car' in path_str or 'vehicle' in path_str:
        return 'Vehicle'
    else:
        return 'Tool'


def generate_firebase_path(glb_path: Path, base_path: Path) -> str:
    """
    Generate Firebase-compatible path from GLB file path.
    
    Args:
        glb_path: Path to the GLB file
        base_path: Base path to make relative
        
    Returns:
        Firebase path string (e.g., "/3dData/lights/ceiling-lamp.glb")
    """
    try:
        # Make path relative to base
        relative_path = glb_path.relative_to(base_path)
        
        # Convert to forward slashes and ensure it starts with /3dData/
        path_str = str(relative_path).replace('\\', '/')
        
        # If it doesn't start with /3dData/, add it
        if not path_str.startswith('/3dData/'):
            path_str = f"/3dData/{path_str}"
        
        return path_str
    except ValueError:
        # If we can't make it relative, use the filename
        return f"/3dData/{glb_path.name}"
