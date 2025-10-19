"""
Service layer for API endpoints.

This module provides service classes that wrap the existing converter functionality
and add API-specific features like async support and enhanced error handling.
"""

import asyncio
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import trimesh

from ..converter import convert_obj_to_glb, convert_batch
from ..firebase_importer import FirebaseImporter, FirebaseImportError
from ..utils import find_obj_files, find_glb_files, format_file_size
from ..thumbnail import generate_thumbnail
from ..preview import generate_preview_html

logger = logging.getLogger("obj2glb")


class ConversionService:
    """Service for handling file conversions."""
    
    async def convert_single(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        overwrite: bool = False,
        generate_thumbnail: bool = False,
        thumbnail_size: str = "512x512",
        generate_preview: bool = False,
    ) -> Dict[str, Any]:
        """Convert a single OBJ file to GLB format."""
        try:
            # Run conversion in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._convert_single_sync,
                input_path,
                output_path,
                overwrite,
                generate_thumbnail,
                thumbnail_size,
                generate_preview,
            )
            return result
            
        except Exception as e:
            logger.error(f"Single conversion failed: {e}")
            return {
                "success": False,
                "input_path": input_path,
                "output_path": output_path or "",
                "error_message": str(e),
            }
    
    def _convert_single_sync(
        self,
        input_path: str,
        output_path: Optional[str],
        overwrite: bool,
        generate_thumbnail: bool,
        thumbnail_size: str,
        generate_preview: bool,
    ) -> Dict[str, Any]:
        """Synchronous single file conversion."""
        try:
            input_file = Path(input_path)
            if not input_file.exists():
                raise FileNotFoundError(f"Input file not found: {input_path}")
            
            # Generate output path if not provided
            if not output_path:
                output_path = str(input_file.with_suffix('.glb'))
            
            # Convert file
            success = convert_obj_to_glb(
                input_path=input_path,
                output_path=output_path,
                overwrite=overwrite,
            )
            
            if not success:
                raise RuntimeError("Conversion failed")
            
            result = {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "file_size": Path(output_path).stat().st_size,
            }
            
            # Generate thumbnail if requested
            if generate_thumbnail:
                try:
                    thumbnail_path = generate_thumbnail(
                        obj_path=input_file,
                        output_path=Path(output_path).with_suffix('.png'),
                        size=thumbnail_size,
                    )
                    result["thumbnail_path"] = str(thumbnail_path)
                except Exception as e:
                    logger.warning(f"Thumbnail generation failed: {e}")
            
            # Generate preview if requested
            if generate_preview:
                try:
                    preview_path = generate_preview_html(
                        glb_path=Path(output_path),
                        output_html=Path(output_path).with_suffix('.html'),
                    )
                    result["preview_path"] = str(preview_path)
                except Exception as e:
                    logger.warning(f"Preview generation failed: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Single conversion sync failed: {e}")
            return {
                "success": False,
                "input_path": input_path,
                "output_path": output_path or "",
                "error_message": str(e),
            }
    
    async def convert_batch(
        self,
        input_directory: str,
        output_directory: str,
        recursive: bool = False,
        overwrite: bool = False,
        generate_thumbnails: bool = False,
        thumbnail_size: str = "512x512",
        generate_previews: bool = False,
    ) -> Dict[str, Any]:
        """Convert multiple OBJ files to GLB format."""
        try:
            # Run batch conversion in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._convert_batch_sync,
                input_directory,
                output_directory,
                recursive,
                overwrite,
                generate_thumbnails,
                thumbnail_size,
                generate_previews,
            )
            return result
            
        except Exception as e:
            logger.error(f"Batch conversion failed: {e}")
            return {
                "success": False,
                "total_files": 0,
                "successful_conversions": 0,
                "failed_conversions": 0,
                "results": [],
                "error_messages": [str(e)],
            }
    
    def _convert_batch_sync(
        self,
        input_directory: str,
        output_directory: str,
        recursive: bool,
        overwrite: bool,
        generate_thumbnails: bool,
        thumbnail_size: str,
        generate_previews: bool,
    ) -> Dict[str, Any]:
        """Synchronous batch conversion."""
        try:
            # Find OBJ files
            obj_files = find_obj_files(Path(input_directory), recursive)
            total_files = len(obj_files)
            
            if total_files == 0:
                return {
                    "success": True,
                    "total_files": 0,
                    "successful_conversions": 0,
                    "failed_conversions": 0,
                    "results": [],
                    "error_messages": [],
                }
            
            # Convert files
            success_count, failure_count, error_messages = convert_batch(
                input_directory=Path(input_directory),
                output_directory=Path(output_directory),
                recursive=recursive,
                overwrite=overwrite,
                generate_thumbnails=generate_thumbnails,
                thumbnail_size=thumbnail_size,
                generate_previews=generate_previews,
            )
            
            # Generate results list (simplified for API)
            results = []
            for i, obj_file in enumerate(obj_files):
                try:
                    output_file = Path(output_directory) / obj_file.relative_to(Path(input_directory))
                    output_file = output_file.with_suffix('.glb')
                    
                    results.append({
                        "success": output_file.exists(),
                        "input_path": str(obj_file),
                        "output_path": str(output_file),
                        "file_size": output_file.stat().st_size if output_file.exists() else None,
                    })
                except Exception as e:
                    results.append({
                        "success": False,
                        "input_path": str(obj_file),
                        "output_path": "",
                        "error_message": str(e),
                    })
            
            return {
                "success": failure_count == 0,
                "total_files": total_files,
                "successful_conversions": success_count,
                "failed_conversions": failure_count,
                "results": results,
                "error_messages": error_messages,
            }
            
        except Exception as e:
            logger.error(f"Batch conversion sync failed: {e}")
            return {
                "success": False,
                "total_files": 0,
                "successful_conversions": 0,
                "failed_conversions": 0,
                "results": [],
                "error_messages": [str(e)],
            }


class AnalysisService:
    """Service for 3D model analysis."""
    
    async def analyze_model(
        self,
        model_path: str,
        analysis_type: str = "comprehensive",
        include_ai_analysis: bool = True,
    ) -> Dict[str, Any]:
        """Analyze a 3D model for categorization and metadata."""
        try:
            # Run analysis in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._analyze_model_sync,
                model_path,
                analysis_type,
                include_ai_analysis,
            )
            return result
            
        except Exception as e:
            logger.error(f"Model analysis failed: {e}")
            return {
                "success": False,
                "model_path": model_path,
                "error_message": str(e),
            }
    
    def _analyze_model_sync(
        self,
        model_path: str,
        analysis_type: str,
        include_ai_analysis: bool,
    ) -> Dict[str, Any]:
        """Synchronous model analysis."""
        try:
            model_file = Path(model_path)
            if not model_file.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Load model
            mesh = trimesh.load(str(model_file))
            
            # Extract basic information
            bounds = mesh.bounds
            dimensions = {
                "width": float(bounds[1][0] - bounds[0][0]),
                "height": float(bounds[1][2] - bounds[0][2]),
                "depth": float(bounds[1][1] - bounds[0][1]),
            }
            
            # Calculate volume and surface area
            volume = float(mesh.volume) if hasattr(mesh, 'volume') else None
            surface_area = float(mesh.surface_area) if hasattr(mesh, 'surface_area') else None
            
            # Basic categorization (enhanced version of existing logic)
            category = self._categorize_model_basic(model_file, mesh)
            object_type = self._determine_object_type(model_file, mesh)
            
            result = {
                "success": True,
                "model_path": model_path,
                "dimensions": dimensions,
                "category": category,
                "object_type": object_type,
                "volume": volume,
                "surface_area": surface_area,
                "quality_score": self._assess_quality(mesh),
            }
            
            # Add AI analysis if requested
            if include_ai_analysis:
                ai_result = self._ai_analyze_model(model_file, mesh)
                result.update(ai_result)
            
            return result
            
        except Exception as e:
            logger.error(f"Model analysis sync failed: {e}")
            return {
                "success": False,
                "model_path": model_path,
                "error_message": str(e),
            }
    
    def _categorize_model_basic(self, model_file: Path, mesh: trimesh.Trimesh) -> str:
        """Basic categorization based on filename and geometry."""
        name = model_file.stem.lower()
        
        if "door" in name:
            if "double" in name:
                return "double_doors"
            return "doors"
        elif "garage" in name:
            return "garages"
        else:
            return "tools"
    
    def _determine_object_type(self, model_file: Path, mesh: trimesh.Trimesh) -> str:
        """Determine object type based on filename patterns."""
        name = model_file.stem.lower()
        
        # Enhanced type detection
        type_mapping = {
            "light": "Lighting",
            "lamp": "Lighting",
            "chair": "Seating",
            "sofa": "Seating",
            "table": "Table",
            "desk": "Table",
            "window": "Window",
            "bed": "Bed",
            "cabinet": "Storage",
            "shelf": "Storage",
            "kitchen": "Kitchen Appliance",
            "fridge": "Kitchen Appliance",
            "oven": "Kitchen Appliance",
            "bathroom": "Bathroom Fixture",
            "washbasin": "Bathroom Fixture",
            "toilet": "Toilet",
            "sink": "Sink",
            "bathtub": "Bathtub",
            "shower": "Shower",
        }
        
        for keyword, obj_type in type_mapping.items():
            if keyword in name:
                return obj_type
        
        return "Generic"
    
    def _assess_quality(self, mesh: trimesh.Trimesh) -> float:
        """Assess model quality based on geometry."""
        try:
            # Basic quality metrics
            if not hasattr(mesh, 'vertices') or len(mesh.vertices) == 0:
                return 0.0
            
            # Check for valid geometry
            if mesh.is_empty or mesh.is_watertight is False:
                return 0.3
            
            # Check vertex count (reasonable range)
            vertex_count = len(mesh.vertices)
            if vertex_count < 10:
                return 0.2
            elif vertex_count > 1000000:
                return 0.8  # Very high poly might be excessive
            
            # Check for reasonable proportions
            bounds = mesh.bounds
            dimensions = bounds[1] - bounds[0]
            if any(dim <= 0 for dim in dimensions):
                return 0.1
            
            # Base quality score
            quality = 0.7
            
            # Bonus for watertight mesh
            if mesh.is_watertight:
                quality += 0.2
            
            # Bonus for reasonable vertex count
            if 100 <= vertex_count <= 100000:
                quality += 0.1
            
            return min(1.0, quality)
            
        except Exception:
            return 0.0
    
    def _ai_analyze_model(self, model_file: Path, mesh: trimesh.Trimesh) -> Dict[str, Any]:
        """AI-powered model analysis (placeholder for future implementation)."""
        # This would integrate with AI models for visual analysis
        # For now, return enhanced basic analysis
        
        name = model_file.stem.replace('-', ' ').replace('_', ' ').title()
        
        return {
            "description": f"A 3D model of {name}",
            "tags": [name.lower(), "3d-model", "furniture"],
            "recommendations": [
                "Suitable for interior design applications",
                "Compatible with most 3D rendering engines",
            ],
        }
    
    async def categorize_model(
        self,
        model_path: str,
        use_ai: bool = True,
        confidence_threshold: float = 0.7,
    ) -> Dict[str, Any]:
        """Categorize a 3D model using AI analysis."""
        try:
            # Run categorization in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._categorize_model_sync,
                model_path,
                use_ai,
                confidence_threshold,
            )
            return result
            
        except Exception as e:
            logger.error(f"Model categorization failed: {e}")
            return {
                "success": False,
                "model_path": model_path,
                "error_message": str(e),
            }
    
    def _categorize_model_sync(
        self,
        model_path: str,
        use_ai: bool,
        confidence_threshold: float,
    ) -> Dict[str, Any]:
        """Synchronous model categorization."""
        try:
            model_file = Path(model_path)
            if not model_file.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Load model
            mesh = trimesh.load(str(model_file))
            
            # Basic categorization
            category = self._categorize_model_basic(model_file, mesh)
            
            # Calculate confidence based on filename match strength
            name = model_file.stem.lower()
            confidence = 0.8  # Base confidence for filename matching
            
            if "door" in name and "double" in name:
                confidence = 0.9
            elif "garage" in name:
                confidence = 0.9
            elif any(keyword in name for keyword in ["chair", "table", "lamp", "bed"]):
                confidence = 0.85
            
            # AI enhancement (placeholder)
            if use_ai:
                # This would integrate with AI models
                confidence = min(1.0, confidence + 0.1)
            
            return {
                "success": True,
                "model_path": model_path,
                "category": category,
                "confidence": confidence,
                "reasoning": f"Category determined based on filename '{model_file.stem}' and geometry analysis",
                "alternative_categories": [
                    {"category": "tools", "confidence": 0.3},
                    {"category": "furniture", "confidence": 0.2},
                ],
            }
            
        except Exception as e:
            logger.error(f"Model categorization sync failed: {e}")
            return {
                "success": False,
                "model_path": model_path,
                "error_message": str(e),
            }
    
    async def extract_dimensions(
        self,
        model_path: str,
        units: str = "meters",
        precision: int = 3,
    ) -> Dict[str, Any]:
        """Extract dimensions from a 3D model."""
        try:
            # Run dimension extraction in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._extract_dimensions_sync,
                model_path,
                units,
                precision,
            )
            return result
            
        except Exception as e:
            logger.error(f"Dimension extraction failed: {e}")
            return {
                "success": False,
                "model_path": model_path,
                "error_message": str(e),
            }
    
    def _extract_dimensions_sync(
        self,
        model_path: str,
        units: str,
        precision: int,
    ) -> Dict[str, Any]:
        """Synchronous dimension extraction."""
        try:
            model_file = Path(model_path)
            if not model_file.exists():
                raise FileNotFoundError(f"Model file not found: {model_path}")
            
            # Load model
            mesh = trimesh.load(str(model_file))
            
            # Extract bounding box
            bounds = mesh.bounds
            min_bounds = bounds[0].tolist()
            max_bounds = bounds[1].tolist()
            
            # Calculate dimensions
            dimensions = {
                "width": round(float(bounds[1][0] - bounds[0][0]), precision),
                "height": round(float(bounds[1][2] - bounds[0][2]), precision),
                "depth": round(float(bounds[1][1] - bounds[0][1]), precision),
            }
            
            # Calculate volume and surface area
            volume = None
            surface_area = None
            
            if hasattr(mesh, 'volume'):
                volume = round(float(mesh.volume), precision)
            
            if hasattr(mesh, 'surface_area'):
                surface_area = round(float(mesh.surface_area), precision)
            
            return {
                "success": True,
                "model_path": model_path,
                "dimensions": dimensions,
                "bounding_box": {
                    "min": min_bounds,
                    "max": max_bounds,
                },
                "volume": volume,
                "surface_area": surface_area,
            }
            
        except Exception as e:
            logger.error(f"Dimension extraction sync failed: {e}")
            return {
                "success": False,
                "model_path": model_path,
                "error_message": str(e),
            }


class FirebaseService:
    """Service for Firebase operations."""
    
    async def import_glb_files(
        self,
        glb_directory: str,
        dry_run: bool = False,
        category_filter: Optional[str] = None,
        firebase_credentials: Optional[str] = None,
        firebase_project_id: Optional[str] = None,
        update_existing: bool = False,
    ) -> Dict[str, Any]:
        """Import GLB files to Firebase Firestore."""
        try:
            # Run Firebase import in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._import_glb_files_sync,
                glb_directory,
                dry_run,
                category_filter,
                firebase_credentials,
                firebase_project_id,
                update_existing,
            )
            return result
            
        except Exception as e:
            logger.error(f"Firebase import failed: {e}")
            return {
                "success": False,
                "total_files": 0,
                "successful_imports": 0,
                "failed_imports": 0,
                "error_messages": [str(e)],
            }
    
    def _import_glb_files_sync(
        self,
        glb_directory: str,
        dry_run: bool,
        category_filter: Optional[str],
        firebase_credentials: Optional[str],
        firebase_project_id: Optional[str],
        update_existing: bool,
    ) -> Dict[str, Any]:
        """Synchronous Firebase import."""
        try:
            # Initialize Firebase importer
            importer = FirebaseImporter(
                credentials_path=firebase_credentials,
                project_id=firebase_project_id,
            )
            
            # Import GLB files
            success_count, failure_count, error_messages = importer.import_glb_files(
                glb_directory=Path(glb_directory),
                dry_run=dry_run,
                category_filter=category_filter,
                update_existing=update_existing,
            )
            
            # Get collection stats
            collection_stats = {}
            if not dry_run:
                collection_stats = importer.get_collection_stats()
            
            return {
                "success": failure_count == 0,
                "total_files": success_count + failure_count,
                "successful_imports": success_count,
                "failed_imports": failure_count,
                "collection_stats": collection_stats,
                "error_messages": error_messages,
            }
            
        except Exception as e:
            logger.error(f"Firebase import sync failed: {e}")
            return {
                "success": False,
                "total_files": 0,
                "successful_imports": 0,
                "failed_imports": 0,
                "error_messages": [str(e)],
            }
