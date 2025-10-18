# OBJ to GLB Converter

A powerful command-line tool to convert 3D models from OBJ format to GLB format with full material and texture support.

## Features

- ✨ Convert OBJ files to GLB format with high fidelity
- 🎨 Full material and texture support (diffuse, normal, specular maps)
- 📦 Single file and batch conversion modes
- 🚀 Fast and efficient processing
- 💼 Embeds textures directly into GLB files
- 🛡️ Comprehensive error handling and validation

## Installation

### From Source

```bash
git clone https://github.com/mgcronin/3dConverter.git
cd 3dConverter
pip install -e .
```

### Requirements

- Python 3.8 or higher
- See `requirements.txt` for full dependency list

## Usage

### Single File Conversion

Convert a single OBJ file to GLB:

```bash
obj2glb input.obj output.glb
```

### Batch Conversion

Convert all OBJ files in a folder:

```bash
obj2glb --batch ./obj_files/ ./glb_files/
```

### Recursive Batch Conversion

Recursively search subdirectories for OBJ files and preserve directory structure:

```bash
obj2glb --batch --recursive ./models/ ./output/
# or use the short form
obj2glb --batch -r ./models/ ./output/
```

### Command-Line Options

- `--batch`: Enable batch conversion mode
- `--recursive, -r`: Recursively search subdirectories for OBJ files (use with --batch)
- `--verbose, -v`: Enable verbose output
- `--overwrite, -o`: Overwrite existing output files
- `--help`: Show help message

### Examples

**Basic conversion:**
```bash
obj2glb model.obj model.glb
```

**Batch conversion with verbose output:**
```bash
obj2glb --batch --verbose ./models/obj/ ./models/glb/
```

**Recursive batch conversion:**
```bash
obj2glb --batch --recursive ./all_models/ ./converted/
```

**Overwrite existing files:**
```bash
obj2glb model.obj model.glb --overwrite
```

## How It Works

The converter uses `trimesh` for 3D model processing and `pygltflib` for GLB export. It:

1. Loads the OBJ file along with its MTL material file
2. Parses material properties and texture references
3. Loads and processes texture images
4. Converts the geometry and materials to GLTF format
5. Embeds textures into the GLB file
6. Exports a single, self-contained GLB file

## Material and Texture Support

The tool supports the following material properties:

- **Diffuse/Base Color**: `map_Kd` textures
- **Normal Maps**: `map_Bump` or `bump` textures
- **Specular Maps**: `map_Ks` textures
- **Material Colors**: Ambient (Ka), Diffuse (Kd), Specular (Ks)
- **Other Properties**: Shininess (Ns), Transparency (d)

## Troubleshooting

### Missing Textures

If textures are missing, the tool will:
- Log a warning message
- Continue conversion with available materials
- Use default colors where textures are unavailable

### Invalid OBJ Files

Ensure your OBJ file:
- Has valid geometry (vertices, faces)
- References a valid MTL file (if materials are used)
- Has texture paths that are relative or absolute and accessible

### Performance

For large batches:
- Use the `--batch` mode for optimal performance
- Ensure sufficient disk space for output files
- Consider processing in smaller batches if memory is limited

## Development

### Running Tests

```bash
pytest tests/
```

### Project Structure

```
3dConverter/
├── obj2glb/
│   ├── __init__.py
│   ├── converter.py      # Core conversion logic
│   ├── materials.py      # Material/texture handling
│   ├── cli.py           # CLI interface
│   └── utils.py         # Helper functions
├── tests/
│   ├── test_converter.py
│   └── test_materials.py
└── examples/
    └── sample_models/
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with [trimesh](https://github.com/mikedh/trimesh)
- Uses [pygltflib](https://gitlab.com/dodgyville/pygltflib) for GLTF handling
- CLI powered by [Click](https://click.palletsprojects.com/)

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/mgcronin/3dConverter/issues) on GitHub.

