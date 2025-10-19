"""
Firebase Firestore integration for GLB model import.

This module handles the actual Firebase operations including
batch imports, progress tracking, and error handling.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    firebase_admin = None
    credentials = None
    firestore = None

from .firebase_schema import (
    SimpleObject, ToolObject, Dimensions,
    FirebaseSchemaValidator, categorize_glb_file,
    determine_object_type, generate_firebase_path
)

logger = logging.getLogger("obj2glb")


class FirebaseImportError(Exception):
    """Custom exception for Firebase import errors."""
    pass


class FirebaseImporter:
    """Handles Firebase Firestore imports for GLB models."""
    
    def __init__(self, credentials_path: Optional[str] = None, project_id: Optional[str] = None):
        """
        Initialize Firebase importer.
        
        Args:
            credentials_path: Path to Firebase service account JSON file
            project_id: Firebase project ID
        """
        if not FIREBASE_AVAILABLE:
            raise FirebaseImportError(
                "Firebase Admin SDK not available. Install with: pip install firebase-admin"
            )
        
        self.db = None
        self.project_id = project_id
        self._initialize_firebase(credentials_path)
    
    def _initialize_firebase(self, credentials_path: Optional[str] = None):
        """Initialize Firebase Admin SDK."""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                logger.debug("Firebase already initialized")
                self.db = firestore.client()
                return
            
            # Initialize Firebase
            if credentials_path and Path(credentials_path).exists():
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {'projectId': self.project_id})
                logger.info(f"Firebase initialized with credentials: {credentials_path}")
            else:
                # Try to use default credentials (e.g., from environment)
                if self.project_id:
                    firebase_admin.initialize_app(options={'projectId': self.project_id})
                    logger.info(f"Firebase initialized with project ID: {self.project_id}")
                else:
                    # For testing purposes, create a mock client
                    logger.warning("No Firebase credentials or project ID provided - using mock mode")
                    self.db = None
                    return
            
            self.db = firestore.client()
            logger.info("Firebase Firestore client initialized")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Firebase: {e}")
            logger.info("Continuing in mock mode for testing")
            self.db = None
    
    def import_glb_files(
        self,
        glb_directory: Path,
        dry_run: bool = False,
        category_filter: Optional[str] = None
    ) -> Tuple[int, int, List[str]]:
        """
        Import GLB files from directory to Firebase.
        
        Args:
            glb_directory: Directory containing GLB files
            dry_run: If True, only validate without importing
            category_filter: Only import specific category ('doors', 'double_doors', 'garages', 'tools')
            
        Returns:
            Tuple of (success_count, failure_count, error_messages)
        """
        if not glb_directory.exists():
            raise FirebaseImportError(f"Directory does not exist: {glb_directory}")
        
        logger.info(f"Starting GLB import from: {glb_directory}")
        logger.info(f"Dry run: {dry_run}")
        logger.info(f"Category filter: {category_filter}")
        
        # Find all GLB files
        glb_files = list(glb_directory.rglob("*.glb"))
        logger.info(f"Found {len(glb_files)} GLB files")
        
        if not glb_files:
            logger.warning("No GLB files found in directory")
            return 0, 0, ["No GLB files found"]
        
        success_count = 0
        failure_count = 0
        error_messages = []
        
        # Group files by category
        files_by_category = {}
        for glb_file in glb_files:
            category = categorize_glb_file(glb_file)
            if category_filter and category != category_filter:
                continue
            
            if category not in files_by_category:
                files_by_category[category] = []
            files_by_category[category].append(glb_file)
        
        logger.info(f"Files by category: {dict((k, len(v)) for k, v in files_by_category.items())}")
        
        # Import each category
        for category, files in files_by_category.items():
            logger.info(f"Processing {len(files)} files in category: {category}")
            
            for i, glb_file in enumerate(files, 1):
                try:
                    logger.info(f"[{i}/{len(files)}] Processing: {glb_file.name}")
                    
                    if dry_run:
                        # Just validate the data structure
                        self._validate_glb_file(glb_file, category)
                        logger.info(f"✓ Validation passed for {glb_file.name}")
                        success_count += 1
                    else:
                        # Actually import to Firebase
                        self._import_single_glb_file(glb_file, category)
                        logger.info(f"✓ Successfully imported {glb_file.name}")
                        success_count += 1
                
                except Exception as e:
                    error_msg = f"Failed to process {glb_file.name}: {e}"
                    logger.error(error_msg)
                    error_messages.append(error_msg)
                    failure_count += 1
        
        logger.info(f"Import complete: {success_count} success, {failure_count} failures")
        return success_count, failure_count, error_messages
    
    def _validate_glb_file(self, glb_file: Path, category: str):
        """Validate a single GLB file without importing."""
        # Generate object data
        obj_data = self._generate_object_data(glb_file, category)
        
        # Validate based on category
        if category == 'tools':
            validator = FirebaseSchemaValidator.validate_tool_object(obj_data)
        else:
            validator = FirebaseSchemaValidator.validate_simple_object(obj_data)
        
        if not validator:
            raise FirebaseImportError(f"Validation failed for {glb_file.name}")
    
    def _import_single_glb_file(self, glb_file: Path, category: str):
        """Import a single GLB file to Firebase."""
        # Generate object data
        obj_data = self._generate_object_data(glb_file, category)
        
        # Validate data
        if category == 'tools':
            if not FirebaseSchemaValidator.validate_tool_object(obj_data):
                raise FirebaseImportError(f"Validation failed for {glb_file.name}")
        else:
            if not FirebaseSchemaValidator.validate_simple_object(obj_data):
                raise FirebaseImportError(f"Validation failed for {glb_file.name}")
        
        # Convert to Firebase format
        firebase_data = obj_data.to_dict()
        
        # Generate document ID (use filename without extension)
        doc_id = glb_file.stem
        
        # Mock mode - just log what would be imported
        if self.db is None:
            logger.info(f"[MOCK] Would import to {category}/{doc_id}: {firebase_data}")
            return
        
        # Add to Firebase collection
        collection_ref = self.db.collection(category)
        doc_ref = collection_ref.document(doc_id)
        
        # Check if document already exists
        if doc_ref.get().exists:
            logger.warning(f"Document {doc_id} already exists in {category} collection")
            # Update existing document
            doc_ref.update(firebase_data)
            logger.info(f"Updated existing document: {doc_id}")
        else:
            # Create new document
            doc_ref.set(firebase_data)
            logger.info(f"Created new document: {doc_id}")
    
    def _generate_object_data(self, glb_file: Path, category: str):
        """Generate object data from GLB file."""
        # Generate Firebase path
        firebase_path = generate_firebase_path(glb_file, glb_file.parent)
        
        # Generate name from filename
        name = glb_file.stem.replace('_', ' ').replace('-', ' ').title()
        
        if category == 'tools':
            # Generate tool object with all required fields
            dimensions = self._extract_dimensions(glb_file)
            svg_icon = self._generate_svg_icon(glb_file)
            object_type = determine_object_type(glb_file, category)
            
            return ToolObject(
                name=name,
                path_3d=firebase_path,
                dimensions=dimensions,
                svg_icon=svg_icon,
                object_type=object_type,
                created_at=datetime.utcnow()
            )
        else:
            # Generate simple object
            return SimpleObject(
                name=name,
                path=firebase_path
            )
    
    def _extract_dimensions(self, glb_file: Path) -> Dimensions:
        """Extract dimensions from GLB file using trimesh."""
        try:
            import trimesh
            
            # Load the GLB file
            scene = trimesh.load(str(glb_file))
            
            if isinstance(scene, trimesh.Scene):
                # Get bounds from scene
                bounds = scene.bounds
            else:
                # Single mesh
                bounds = scene.bounds
            
            # Calculate dimensions
            width = bounds[1][0] - bounds[0][0]
            height = bounds[1][1] - bounds[0][1]
            depth = bounds[1][2] - bounds[0][2]
            
            logger.debug(f"Extracted dimensions for {glb_file.name}: {width}x{height}x{depth}")
            
            return Dimensions(width=width, height=height, depth=depth)
            
        except Exception as e:
            logger.warning(f"Failed to extract dimensions from {glb_file.name}: {e}")
            # Return default dimensions
            return Dimensions(width=1.0, height=1.0, depth=1.0)
    
    def _generate_svg_icon(self, glb_file: Path) -> str:
        """Generate SVG icon from GLB file thumbnail."""
        try:
            # Look for existing PNG thumbnail
            png_path = glb_file.with_suffix('.png')
            
            if png_path.exists():
                # Convert PNG to SVG (simple placeholder for now)
                # In a real implementation, you might want to use a library like PIL
                # to convert PNG to SVG or generate a more sophisticated icon
                svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>
  <text x="32" y="35" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">
    {glb_file.stem[:8]}
  </text>
</svg>'''
                return svg_content
            else:
                # Generate a simple placeholder SVG
                svg_content = f'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" fill="#e0e0e0" stroke="#999" stroke-width="1"/>
  <text x="32" y="35" text-anchor="middle" font-family="Arial" font-size="10" fill="#666">
    {glb_file.stem[:6]}
  </text>
</svg>'''
                return svg_content
                
        except Exception as e:
            logger.warning(f"Failed to generate SVG icon for {glb_file.name}: {e}")
            # Return a simple fallback SVG
            return '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg version="1.1" width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <rect width="64" height="64" fill="#f0f0f0" stroke="#ccc" stroke-width="1"/>
  <text x="32" y="35" text-anchor="middle" font-family="Arial" font-size="12" fill="#666">3D</text>
</svg>'''
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get document counts for each collection."""
        stats = {}
        collections = ['doors', 'double_doors', 'garages', 'tools']
        
        # Mock mode - return zeros
        if self.db is None:
            logger.info("Mock mode: Collection stats not available")
            return {collection: 0 for collection in collections}
        
        for collection_name in collections:
            try:
                collection_ref = self.db.collection(collection_name)
                docs = collection_ref.stream()
                count = len(list(docs))
                stats[collection_name] = count
                logger.info(f"Collection {collection_name}: {count} documents")
            except Exception as e:
                logger.error(f"Failed to get stats for {collection_name}: {e}")
                stats[collection_name] = 0
        
        return stats
