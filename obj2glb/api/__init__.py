"""
API module for obj2glb converter.

This module provides REST API endpoints for all converter functionality,
enabling programmatic access and MCP server integration.
"""

from .app import create_app
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
)

__all__ = [
    "create_app",
    "ConversionRequest",
    "ConversionResponse", 
    "BatchConversionRequest",
    "BatchConversionResponse",
    "ModelAnalysisRequest",
    "ModelAnalysisResponse",
    "CategorizationRequest",
    "CategorizationResponse",
    "DimensionExtractionRequest",
    "DimensionExtractionResponse",
    "FirebaseImportRequest",
    "FirebaseImportResponse",
]
