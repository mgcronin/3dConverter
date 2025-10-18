"""
Command-line interface for OBJ to GLB converter.
"""

import sys
import click
from pathlib import Path

from .converter import convert_obj_to_glb, convert_batch
from .utils import setup_logger


@click.command()
@click.argument("input", type=str)
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
@click.version_option(version="0.1.0", prog_name="obj2glb")
def main(input, output, batch, recursive, verbose, overwrite):
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
    Examples:
        obj2glb model.obj model.glb
        obj2glb model.obj model.glb --verbose
        obj2glb --batch ./obj_files/ ./glb_files/
        obj2glb --batch --recursive ./models/ ./output/
        obj2glb --batch -r ./models/ ./output/ --overwrite
    """
    # Setup logging
    logger = setup_logger(verbose)
    
    # Check for invalid --recursive usage
    if recursive and not batch:
        click.echo("Error: --recursive can only be used with --batch mode", err=True)
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
        
        success, failure = convert_batch(input, output, overwrite, recursive)
        
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
        
        success = convert_obj_to_glb(input, output, overwrite)
        
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()

