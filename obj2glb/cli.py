"""
Command-line interface for OBJ to GLB converter.
"""

import sys
import click
from pathlib import Path

from .converter import convert_obj_to_glb, convert_batch
from .utils import setup_logger
from .firebase_importer import FirebaseImporter, FirebaseImportError


@click.command()
@click.argument("input", type=str, required=False)
@click.argument("output", type=str, required=False)
@click.option(
    "--batch",
    is_flag=True,
    help="Enable batch conversion mode (INPUT and OUTPUT are directories)"
)
@click.option(
    "--recursive", "-r",
    is_flag=True,
    help="Recursively search subdirectories for OBJ files (use with --batch)"
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output"
)
@click.option(
    "--overwrite", "-o",
    is_flag=True,
    help="Overwrite existing output files"
)
@click.option(
    "--thumbnail", "-t",
    is_flag=True,
    help="Generate PNG thumbnail images of converted models"
)
@click.option(
    "--thumbnail-size",
    type=str,
    default="512x512",
    help="Thumbnail size in WIDTHxHEIGHT format (default: 512x512)"
)
@click.option(
    "--preview", "-p",
    is_flag=True,
    help="Generate interactive HTML preview of converted models"
)
@click.option(
    "--firebase-import",
    is_flag=True,
    help="Import converted GLB files to Firebase Firestore database"
)
@click.option(
    "--firebase-credentials",
    type=str,
    help="Path to Firebase service account JSON file"
)
@click.option(
    "--firebase-project-id",
    type=str,
    help="Firebase project ID"
)
@click.option(
    "--firebase-category",
    type=click.Choice(['doors', 'double_doors', 'garages', 'tools']),
    help="Only import specific category to Firebase"
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Validate Firebase import without actually importing (use with --firebase-import)"
)
@click.option(
    "--firebase-update-existing",
    is_flag=True,
    help="Update existing documents instead of skipping them (use with --firebase-import)"
)
@click.option(
    "--api-server",
    is_flag=True,
    help="Start the REST API server"
)
@click.option(
    "--api-host",
    type=str,
    default="localhost",
    help="API server host (default: localhost)"
)
@click.option(
    "--api-port",
    type=int,
    default=8000,
    help="API server port (default: 8000)"
)
@click.option(
    "--mcp-server",
    is_flag=True,
    help="Start the MCP (Model Context Protocol) server"
)
@click.version_option(version="0.1.0", prog_name="obj2glb")
def main(input, output, batch, recursive, verbose, overwrite, thumbnail, thumbnail_size, preview, firebase_import, firebase_credentials, firebase_project_id, firebase_category, dry_run, firebase_update_existing, api_server, api_host, api_port, mcp_server):
    """
    Convert 3D models from OBJ format to GLB format.
    
    \b
    Single File Mode:
        obj2glb INPUT.obj OUTPUT.glb
    
    \b
    Batch Mode:
        obj2glb --batch INPUT_DIR/ OUTPUT_DIR/
    
    \b
    Recursive Batch Mode:
        obj2glb --batch --recursive INPUT_DIR/ OUTPUT_DIR/
    
    \b
    Firebase Import Mode:
        obj2glb --firebase-import GLB_DIR/
        obj2glb --firebase-import --dry-run GLB_DIR/
        obj2glb --firebase-import --firebase-category tools GLB_DIR/
        obj2glb --firebase-import --firebase-update-existing GLB_DIR/
    
    \b
    API Server Mode:
        obj2glb --api-server
        obj2glb --api-server --api-host 0.0.0.0 --api-port 8080
    
    \b
    MCP Server Mode:
        obj2glb --mcp-server
        obj2glb --mcp-server --api-host 0.0.0.0 --api-port 8080
    
    \b
    Examples:
        obj2glb model.obj model.glb
        obj2glb model.obj model.glb --verbose --thumbnail
        obj2glb --batch ./obj_files/ ./glb_files/
        obj2glb --batch --recursive ./models/ ./output/ --thumbnail
        obj2glb --batch -r ./models/ ./output/ --overwrite -t
        obj2glb model.obj model.glb -t --thumbnail-size 1024x768
        obj2glb --firebase-import ./glb_files/ --firebase-credentials ./firebase-key.json
        obj2glb --firebase-import --dry-run ./glb_files/
        obj2glb --api-server --api-host 0.0.0.0 --api-port 8080
        obj2glb --mcp-server
    """
    # Setup logging
    logger = setup_logger(verbose)
    
    # Parse thumbnail size
    try:
        width, height = map(int, thumbnail_size.lower().split('x'))
        thumb_size = (width, height)
    except (ValueError, AttributeError):
        click.echo(f"Error: Invalid thumbnail size format: {thumbnail_size}", err=True)
        click.echo("Use format: WIDTHxHEIGHT (e.g., 512x512, 1024x768)", err=True)
        sys.exit(1)
    
    # Check for invalid --recursive usage
    if recursive and not batch:
        click.echo("Error: --recursive can only be used with --batch mode", err=True)
        sys.exit(1)
    
    # Check for invalid --dry-run usage
    if dry_run and not firebase_import:
        click.echo("Error: --dry-run can only be used with --firebase-import mode", err=True)
        sys.exit(1)
    
    # Check if we're in server mode
    if api_server or mcp_server:
        # Server mode - no input/output required
        pass
    elif firebase_import:
        # Firebase import mode - input required
        if not input:
            click.echo("Error: GLB directory required for Firebase import", err=True)
            click.echo("Usage: obj2glb --firebase-import GLB_DIR/", err=True)
            sys.exit(1)
    else:
        # Regular conversion mode - input required
        if not input:
            click.echo("Error: Input file or directory required", err=True)
            click.echo("Usage: obj2glb INPUT [OUTPUT]", err=True)
            sys.exit(1)
    
    # API Server mode
    if api_server:
        logger.info("="*60)
        logger.info("Starting OBJ2GLB API Server")
        logger.info("="*60)
        logger.info(f"Host: {api_host}")
        logger.info(f"Port: {api_port}")
        logger.info(f"API Documentation: http://{api_host}:{api_port}/docs")
        
        try:
            import uvicorn
            from .api.app import create_app
            
            app = create_app()
            uvicorn.run(app, host=api_host, port=api_port)
        except ImportError:
            logger.error("FastAPI dependencies not installed. Install with: pip install fastapi uvicorn")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to start API server: {e}")
            sys.exit(1)
    
    # MCP Server mode
    if mcp_server:
        logger.info("="*60)
        logger.info("Starting OBJ2GLB MCP Server")
        logger.info("="*60)
        logger.info(f"Host: {api_host}")
        logger.info(f"Port: {api_port}")
        
        try:
            import asyncio
            from .api.mcp_server import MCPServer
            
            server = MCPServer()
            asyncio.run(server.run_server(host=api_host, port=api_port))
        except ImportError:
            logger.error("MCP server dependencies not installed. Install with: pip install fastapi uvicorn")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to start MCP server: {e}")
            sys.exit(1)
    
    # Firebase import mode
    if firebase_import:
        
        glb_directory = Path(input)
        if not glb_directory.exists():
            click.echo(f"Error: Directory does not exist: {glb_directory}", err=True)
            sys.exit(1)
        
        logger.info("="*60)
        logger.info("Firebase GLB Import")
        logger.info("="*60)
        
        try:
            # Initialize Firebase importer
            importer = FirebaseImporter(
                credentials_path=firebase_credentials,
                project_id=firebase_project_id
            )
            
            # Import GLB files
            success_count, failure_count, error_messages = importer.import_glb_files(
                glb_directory=glb_directory,
                dry_run=dry_run,
                category_filter=firebase_category,
                update_existing=firebase_update_existing
            )
            
            # Display results
            logger.info("="*60)
            logger.info("Firebase Import Results")
            logger.info("="*60)
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {failure_count}")
            
            if error_messages:
                logger.info("Error Details:")
                for error in error_messages:
                    logger.error(f"  - {error}")
            
            if dry_run:
                logger.info("✓ Dry run completed - no data was imported")
            else:
                logger.info("✓ Firebase import completed")
            
            # Show collection stats if not dry run
            if not dry_run:
                stats = importer.get_collection_stats()
                logger.info("Collection Statistics:")
                for collection, count in stats.items():
                    logger.info(f"  {collection}: {count} documents")
            
            # Exit with error code if any imports failed
            if failure_count > 0:
                sys.exit(1)
                
        except FirebaseImportError as e:
            logger.error(f"Firebase import error: {e}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error during Firebase import: {e}")
            sys.exit(1)
    
    # Batch mode
    if batch:
        if not output:
            click.echo("Error: OUTPUT directory required for batch mode", err=True)
            click.echo("Usage: obj2glb --batch INPUT_DIR OUTPUT_DIR", err=True)
            sys.exit(1)
        
        logger.info("="*60)
        if recursive:
            logger.info("OBJ to GLB Recursive Batch Converter")
        else:
            logger.info("OBJ to GLB Batch Converter")
        logger.info("="*60)
        
        success, failure = convert_batch(
            input, output, overwrite, recursive, thumbnail, thumb_size, preview
        )
        
        # Exit with error code if any conversions failed
        if failure > 0:
            sys.exit(1)
    
    # Single file mode
    else:
        if not output:
            # Auto-generate output filename
            input_path = Path(input)
            output = str(input_path.with_suffix(".glb"))
            logger.info(f"No output specified, using: {output}")
        
        logger.info("="*60)
        logger.info("OBJ to GLB Converter")
        logger.info("="*60)
        
        success = convert_obj_to_glb(input, output, overwrite, thumbnail, thumb_size, preview)
        
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()

