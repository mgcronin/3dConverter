"""
FastAPI application for obj2glb converter API.
"""

import time
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    ConversionRequest,
    ConversionResponse,
    BatchConversionRequest,
    BatchConversionResponse,
    ModelAnalysisRequest,
    ModelAnalysisResponse,
    CategorizationRequest,
    CategorizationResponse,
    DimensionExtractionRequest,
    DimensionExtractionResponse,
    FirebaseImportRequest,
    FirebaseImportResponse,
    HealthResponse,
)
from .services import (
    ConversionService,
    AnalysisService,
    FirebaseService,
)
from ..utils import setup_logger

logger = setup_logger()


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="OBJ2GLB Converter API",
        description="REST API for converting OBJ files to GLB format with AI-powered analysis",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize services
    conversion_service = ConversionService()
    analysis_service = AnalysisService()
    firebase_service = FirebaseService()
    
    @app.get("/health", response_model=HealthResponse)
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version="0.1.0",
            dependencies={
                "trimesh": "available",
                "pygltflib": "available",
                "firebase-admin": "available",
            }
        )
    
    @app.post("/api/convert", response_model=ConversionResponse)
    async def convert_file(request: ConversionRequest):
        """Convert a single OBJ file to GLB format."""
        try:
            start_time = time.time()
            
            result = await conversion_service.convert_single(
                input_path=request.input_path,
                output_path=request.output_path,
                overwrite=request.overwrite,
                generate_thumbnail=request.generate_thumbnail,
                thumbnail_size=request.thumbnail_size,
                generate_preview=request.generate_preview,
            )
            
            processing_time = time.time() - start_time
            
            return ConversionResponse(
                success=result["success"],
                input_path=result["input_path"],
                output_path=result["output_path"],
                file_size=result.get("file_size"),
                thumbnail_path=result.get("thumbnail_path"),
                preview_path=result.get("preview_path"),
                error_message=result.get("error_message"),
                processing_time=processing_time,
            )
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/convert/batch", response_model=BatchConversionResponse)
    async def convert_batch(request: BatchConversionRequest):
        """Convert multiple OBJ files to GLB format."""
        try:
            start_time = time.time()
            
            result = await conversion_service.convert_batch(
                input_directory=request.input_directory,
                output_directory=request.output_directory,
                recursive=request.recursive,
                overwrite=request.overwrite,
                generate_thumbnails=request.generate_thumbnails,
                thumbnail_size=request.thumbnail_size,
                generate_previews=request.generate_previews,
            )
            
            processing_time = time.time() - start_time
            
            return BatchConversionResponse(
                success=result["success"],
                total_files=result["total_files"],
                successful_conversions=result["successful_conversions"],
                failed_conversions=result["failed_conversions"],
                processing_time=processing_time,
                results=result["results"],
                error_messages=result["error_messages"],
            )
            
        except Exception as e:
            logger.error(f"Batch conversion failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/analyze/model", response_model=ModelAnalysisResponse)
    async def analyze_model(request: ModelAnalysisRequest):
        """Analyze a 3D model for categorization and metadata."""
        try:
            result = await analysis_service.analyze_model(
                model_path=request.model_path,
                analysis_type=request.analysis_type,
                include_ai_analysis=request.include_ai_analysis,
            )
            
            return ModelAnalysisResponse(**result)
            
        except Exception as e:
            logger.error(f"Model analysis failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/categorize/model", response_model=CategorizationResponse)
    async def categorize_model(request: CategorizationRequest):
        """Categorize a 3D model using AI analysis."""
        try:
            result = await analysis_service.categorize_model(
                model_path=request.model_path,
                use_ai=request.use_ai,
                confidence_threshold=request.confidence_threshold,
            )
            
            return CategorizationResponse(**result)
            
        except Exception as e:
            logger.error(f"Model categorization failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/extract/dimensions", response_model=DimensionExtractionResponse)
    async def extract_dimensions(request: DimensionExtractionRequest):
        """Extract dimensions from a 3D model."""
        try:
            result = await analysis_service.extract_dimensions(
                model_path=request.model_path,
                units=request.units,
                precision=request.precision,
            )
            
            return DimensionExtractionResponse(**result)
            
        except Exception as e:
            logger.error(f"Dimension extraction failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/firebase/import", response_model=FirebaseImportResponse)
    async def firebase_import(request: FirebaseImportRequest):
        """Import GLB files to Firebase Firestore."""
        try:
            start_time = time.time()
            
            result = await firebase_service.import_glb_files(
                glb_directory=request.glb_directory,
                dry_run=request.dry_run,
                category_filter=request.category_filter,
                firebase_credentials=request.firebase_credentials,
                firebase_project_id=request.firebase_project_id,
                update_existing=request.update_existing,
            )
            
            processing_time = time.time() - start_time
            
            return FirebaseImportResponse(
                success=result["success"],
                total_files=result["total_files"],
                successful_imports=result["successful_imports"],
                failed_imports=result["failed_imports"],
                dry_run=request.dry_run,
                processing_time=processing_time,
                collection_stats=result.get("collection_stats", {}),
                error_messages=result.get("error_messages", []),
            )
            
        except Exception as e:
            logger.error(f"Firebase import failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/upload")
    async def upload_file(file: UploadFile = File(...)):
        """Upload a file for processing."""
        try:
            # Create uploads directory if it doesn't exist
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)
            
            # Save uploaded file
            file_path = upload_dir / file.filename
            with open(file_path, "wb") as buffer:
                content = await file.read()
                buffer.write(content)
            
            return {
                "success": True,
                "filename": file.filename,
                "file_path": str(file_path),
                "file_size": len(content),
            }
            
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/models/{model_id}/preview")
    async def get_model_preview(model_id: str):
        """Get HTML preview for a model."""
        try:
            # This would return the HTML preview file
            preview_path = Path(f"previews/{model_id}.html")
            if preview_path.exists():
                return FileResponse(preview_path)
            else:
                raise HTTPException(status_code=404, detail="Preview not found")
                
        except Exception as e:
            logger.error(f"Preview retrieval failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app
