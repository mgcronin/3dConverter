"""
Pydantic models for API requests and responses.
"""

from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field
from datetime import datetime


class ConversionRequest(BaseModel):
    """Request model for single file conversion."""
    input_path: str = Field(..., description="Path to input OBJ file")
    output_path: Optional[str] = Field(None, description="Path to output GLB file")
    overwrite: bool = Field(False, description="Whether to overwrite existing files")
    generate_thumbnail: bool = Field(False, description="Whether to generate thumbnail")
    thumbnail_size: str = Field("512x512", description="Thumbnail size (WIDTHxHEIGHT)")
    generate_preview: bool = Field(False, description="Whether to generate HTML preview")


class ConversionResponse(BaseModel):
    """Response model for single file conversion."""
    success: bool = Field(..., description="Whether conversion was successful")
    input_path: str = Field(..., description="Path to input file")
    output_path: str = Field(..., description="Path to output file")
    file_size: Optional[int] = Field(None, description="Output file size in bytes")
    thumbnail_path: Optional[str] = Field(None, description="Path to generated thumbnail")
    preview_path: Optional[str] = Field(None, description="Path to generated preview")
    error_message: Optional[str] = Field(None, description="Error message if conversion failed")
    processing_time: float = Field(..., description="Processing time in seconds")


class BatchConversionRequest(BaseModel):
    """Request model for batch conversion."""
    input_directory: str = Field(..., description="Path to input directory")
    output_directory: str = Field(..., description="Path to output directory")
    recursive: bool = Field(False, description="Whether to process subdirectories recursively")
    overwrite: bool = Field(False, description="Whether to overwrite existing files")
    generate_thumbnails: bool = Field(False, description="Whether to generate thumbnails")
    thumbnail_size: str = Field("512x512", description="Thumbnail size (WIDTHxHEIGHT)")
    generate_previews: bool = Field(False, description="Whether to generate HTML previews")


class BatchConversionResponse(BaseModel):
    """Response model for batch conversion."""
    success: bool = Field(..., description="Whether batch conversion was successful")
    total_files: int = Field(..., description="Total number of files processed")
    successful_conversions: int = Field(..., description="Number of successful conversions")
    failed_conversions: int = Field(..., description="Number of failed conversions")
    processing_time: float = Field(..., description="Total processing time in seconds")
    results: List[ConversionResponse] = Field(..., description="Individual conversion results")
    error_messages: List[str] = Field(default_factory=list, description="Error messages")


class ModelAnalysisRequest(BaseModel):
    """Request model for 3D model analysis."""
    model_path: str = Field(..., description="Path to 3D model file")
    analysis_type: str = Field("comprehensive", description="Type of analysis to perform")
    include_ai_analysis: bool = Field(True, description="Whether to include AI-powered analysis")


class ModelAnalysisResponse(BaseModel):
    """Response model for 3D model analysis."""
    success: bool = Field(..., description="Whether analysis was successful")
    model_path: str = Field(..., description="Path to analyzed model")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Model dimensions")
    category: Optional[str] = Field(None, description="Suggested category")
    object_type: Optional[str] = Field(None, description="Suggested object type")
    description: Optional[str] = Field(None, description="AI-generated description")
    tags: List[str] = Field(default_factory=list, description="Generated tags")
    quality_score: Optional[float] = Field(None, description="Model quality score (0-1)")
    recommendations: List[str] = Field(default_factory=list, description="Usage recommendations")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")


class CategorizationRequest(BaseModel):
    """Request model for model categorization."""
    model_path: str = Field(..., description="Path to 3D model file")
    use_ai: bool = Field(True, description="Whether to use AI for categorization")
    confidence_threshold: float = Field(0.7, description="Minimum confidence threshold")


class CategorizationResponse(BaseModel):
    """Response model for model categorization."""
    success: bool = Field(..., description="Whether categorization was successful")
    model_path: str = Field(..., description="Path to categorized model")
    category: str = Field(..., description="Determined category")
    confidence: float = Field(..., description="Confidence score (0-1)")
    reasoning: Optional[str] = Field(None, description="Explanation for categorization")
    alternative_categories: List[Dict[str, float]] = Field(default_factory=list, description="Alternative categories with confidence scores")
    error_message: Optional[str] = Field(None, description="Error message if categorization failed")


class DimensionExtractionRequest(BaseModel):
    """Request model for dimension extraction."""
    model_path: str = Field(..., description="Path to 3D model file")
    units: str = Field("meters", description="Units for dimensions")
    precision: int = Field(3, description="Decimal precision for dimensions")


class DimensionExtractionResponse(BaseModel):
    """Response model for dimension extraction."""
    success: bool = Field(..., description="Whether extraction was successful")
    model_path: str = Field(..., description="Path to analyzed model")
    dimensions: Dict[str, float] = Field(..., description="Extracted dimensions")
    bounding_box: Dict[str, List[float]] = Field(..., description="Bounding box coordinates")
    volume: Optional[float] = Field(None, description="Model volume")
    surface_area: Optional[float] = Field(None, description="Model surface area")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")


class FirebaseImportRequest(BaseModel):
    """Request model for Firebase import."""
    glb_directory: str = Field(..., description="Path to directory containing GLB files")
    dry_run: bool = Field(False, description="Whether to perform dry run only")
    category_filter: Optional[str] = Field(None, description="Filter by specific category")
    firebase_credentials: Optional[str] = Field(None, description="Path to Firebase credentials file")
    firebase_project_id: Optional[str] = Field(None, description="Firebase project ID")
    update_existing: bool = Field(False, description="Whether to update existing documents")


class FirebaseImportResponse(BaseModel):
    """Response model for Firebase import."""
    success: bool = Field(..., description="Whether import was successful")
    total_files: int = Field(..., description="Total number of files processed")
    successful_imports: int = Field(..., description="Number of successful imports")
    failed_imports: int = Field(..., description="Number of failed imports")
    dry_run: bool = Field(..., description="Whether this was a dry run")
    processing_time: float = Field(..., description="Total processing time in seconds")
    collection_stats: Dict[str, int] = Field(default_factory=dict, description="Document counts per collection")
    error_messages: List[str] = Field(default_factory=list, description="Error messages")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Service version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency status")
