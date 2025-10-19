"""
MCP (Model Context Protocol) server for obj2glb converter.

This module implements an MCP server that can analyze 3D models and provide
intelligent categorization and dimension extraction using AI.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import asyncio

from .services import AnalysisService, ConversionService, FirebaseService
from ..utils import setup_logger

logger = setup_logger()


class MCPServer:
    """MCP server for 3D model analysis and conversion."""
    
    def __init__(self):
        """Initialize MCP server."""
        self.analysis_service = AnalysisService()
        self.conversion_service = ConversionService()
        self.firebase_service = FirebaseService()
        self.tools = self._register_tools()
    
    def _register_tools(self) -> Dict[str, Dict[str, Any]]:
        """Register available MCP tools."""
        return {
            "analyze_3d_model": {
                "description": "Analyze a 3D model for categorization, dimensions, and metadata",
                "parameters": {
                    "model_path": {"type": "string", "description": "Path to 3D model file"},
                    "analysis_type": {"type": "string", "description": "Type of analysis to perform", "default": "comprehensive"},
                    "include_ai": {"type": "boolean", "description": "Whether to include AI analysis", "default": True},
                },
            },
            "categorize_3d_model": {
                "description": "Categorize a 3D model using AI analysis",
                "parameters": {
                    "model_path": {"type": "string", "description": "Path to 3D model file"},
                    "use_ai": {"type": "boolean", "description": "Whether to use AI for categorization", "default": True},
                    "confidence_threshold": {"type": "number", "description": "Minimum confidence threshold", "default": 0.7},
                },
            },
            "extract_dimensions": {
                "description": "Extract dimensions from a 3D model",
                "parameters": {
                    "model_path": {"type": "string", "description": "Path to 3D model file"},
                    "units": {"type": "string", "description": "Units for dimensions", "default": "meters"},
                    "precision": {"type": "integer", "description": "Decimal precision", "default": 3},
                },
            },
            "convert_obj_to_glb": {
                "description": "Convert an OBJ file to GLB format",
                "parameters": {
                    "input_path": {"type": "string", "description": "Path to input OBJ file"},
                    "output_path": {"type": "string", "description": "Path to output GLB file", "optional": True},
                    "overwrite": {"type": "boolean", "description": "Whether to overwrite existing files", "default": False},
                    "generate_thumbnail": {"type": "boolean", "description": "Whether to generate thumbnail", "default": False},
                    "generate_preview": {"type": "boolean", "description": "Whether to generate HTML preview", "default": False},
                },
            },
            "batch_convert": {
                "description": "Convert multiple OBJ files to GLB format",
                "parameters": {
                    "input_directory": {"type": "string", "description": "Path to input directory"},
                    "output_directory": {"type": "string", "description": "Path to output directory"},
                    "recursive": {"type": "boolean", "description": "Whether to process subdirectories", "default": False},
                    "overwrite": {"type": "boolean", "description": "Whether to overwrite existing files", "default": False},
                },
            },
            "firebase_import": {
                "description": "Import GLB files to Firebase Firestore",
                "parameters": {
                    "glb_directory": {"type": "string", "description": "Path to directory containing GLB files"},
                    "dry_run": {"type": "boolean", "description": "Whether to perform dry run only", "default": False},
                    "category_filter": {"type": "string", "description": "Filter by specific category", "optional": True},
                    "update_existing": {"type": "boolean", "description": "Whether to update existing documents", "default": False},
                },
            },
        }
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request."""
        try:
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [
                            {
                                "name": tool_name,
                                "description": tool_info["description"],
                                "inputSchema": {
                                    "type": "object",
                                    "properties": tool_info["parameters"],
                                    "required": [
                                        key for key, value in tool_info["parameters"].items()
                                        if not value.get("optional", False)
                                    ],
                                },
                            }
                            for tool_name, tool_info in self.tools.items()
                        ]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_params = params.get("arguments", {})
                
                if tool_name not in self.tools:
                    return {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32601,
                            "message": f"Tool '{tool_name}' not found",
                        }
                    }
                
                # Call the appropriate tool
                result = await self._call_tool(tool_name, tool_params)
                
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2),
                            }
                        ]
                    }
                }
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method '{method}' not found",
                    }
                }
                
        except Exception as e:
            logger.error(f"MCP request handling failed: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}",
                }
            }
    
    async def _call_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool with parameters."""
        try:
            if tool_name == "analyze_3d_model":
                result = await self.analysis_service.analyze_model(
                    model_path=params["model_path"],
                    analysis_type=params.get("analysis_type", "comprehensive"),
                    include_ai_analysis=params.get("include_ai", True),
                )
                return result
            
            elif tool_name == "categorize_3d_model":
                result = await self.analysis_service.categorize_model(
                    model_path=params["model_path"],
                    use_ai=params.get("use_ai", True),
                    confidence_threshold=params.get("confidence_threshold", 0.7),
                )
                return result
            
            elif tool_name == "extract_dimensions":
                result = await self.analysis_service.extract_dimensions(
                    model_path=params["model_path"],
                    units=params.get("units", "meters"),
                    precision=params.get("precision", 3),
                )
                return result
            
            elif tool_name == "convert_obj_to_glb":
                result = await self.conversion_service.convert_single(
                    input_path=params["input_path"],
                    output_path=params.get("output_path"),
                    overwrite=params.get("overwrite", False),
                    generate_thumbnail=params.get("generate_thumbnail", False),
                    generate_preview=params.get("generate_preview", False),
                )
                return result
            
            elif tool_name == "batch_convert":
                result = await self.conversion_service.convert_batch(
                    input_directory=params["input_directory"],
                    output_directory=params["output_directory"],
                    recursive=params.get("recursive", False),
                    overwrite=params.get("overwrite", False),
                )
                return result
            
            elif tool_name == "firebase_import":
                result = await self.firebase_service.import_glb_files(
                    glb_directory=params["glb_directory"],
                    dry_run=params.get("dry_run", False),
                    category_filter=params.get("category_filter"),
                    update_existing=params.get("update_existing", False),
                )
                return result
            
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
                
        except Exception as e:
            logger.error(f"Tool call failed for {tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def run_server(self, host: str = "localhost", port: int = 8000):
        """Run the MCP server."""
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        
        app = FastAPI(title="OBJ2GLB MCP Server")
        
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        @app.post("/mcp")
        async def mcp_endpoint(request: Dict[str, Any]):
            """MCP endpoint."""
            return await self.handle_request(request)
        
        logger.info(f"Starting MCP server on {host}:{port}")
        await uvicorn.run(app, host=host, port=port)


# CLI entry point for MCP server
async def main():
    """Main entry point for MCP server."""
    server = MCPServer()
    await server.run_server()


if __name__ == "__main__":
    asyncio.run(main())
