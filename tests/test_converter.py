"""
Tests for converter module.
"""

import pytest
import tempfile
from pathlib import Path
from obj2glb.converter import convert_obj_to_glb, convert_batch


class TestConverter:
    """Test cases for the converter module."""
    
    def test_convert_obj_to_glb_invalid_input(self):
        """Test conversion with invalid input file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "output.glb"
            result = convert_obj_to_glb("nonexistent.obj", str(output))
            assert result is False
    
    def test_convert_obj_to_glb_invalid_output_extension(self):
        """Test conversion with invalid output extension."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a dummy OBJ file
            input_obj = Path(tmpdir) / "test.obj"
            input_obj.write_text("v 0 0 0\n")
            
            output = Path(tmpdir) / "output.txt"
            result = convert_obj_to_glb(str(input_obj), str(output))
            assert result is False
    
    def test_convert_batch_empty_directory(self):
        """Test batch conversion with empty directory."""
        with tempfile.TemporaryDirectory() as input_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                success, failure = convert_batch(input_dir, output_dir)
                assert success == 0
                assert failure == 0
    
    def test_convert_batch_nonexistent_directory(self):
        """Test batch conversion with nonexistent directory."""
        with tempfile.TemporaryDirectory() as output_dir:
            success, failure = convert_batch("/nonexistent/path", output_dir)
            assert success == 0
            assert failure == 0
    
    def test_convert_batch_recursive_empty(self):
        """Test recursive batch conversion with empty directory."""
        with tempfile.TemporaryDirectory() as input_dir:
            with tempfile.TemporaryDirectory() as output_dir:
                success, failure = convert_batch(input_dir, output_dir, recursive=True)
                assert success == 0
                assert failure == 0


class TestConverterWithValidOBJ:
    """Test cases with valid OBJ files."""
    
    @pytest.fixture
    def simple_obj(self, tmp_path):
        """Create a simple valid OBJ file."""
        obj_file = tmp_path / "cube.obj"
        obj_content = """
# Simple cube
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1

f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""
        obj_file.write_text(obj_content)
        return obj_file
    
    def test_convert_simple_obj(self, simple_obj, tmp_path):
        """Test conversion of a simple OBJ file."""
        output = tmp_path / "cube.glb"
        result = convert_obj_to_glb(str(simple_obj), str(output))
        
        assert result is True
        assert output.exists()
        assert output.stat().st_size > 0
    
    def test_convert_overwrite_existing(self, simple_obj, tmp_path):
        """Test overwriting an existing file."""
        output = tmp_path / "cube.glb"
        
        # First conversion
        result1 = convert_obj_to_glb(str(simple_obj), str(output))
        assert result1 is True
        
        # Second conversion without overwrite should fail
        result2 = convert_obj_to_glb(str(simple_obj), str(output), overwrite=False)
        assert result2 is False
        
        # Third conversion with overwrite should succeed
        result3 = convert_obj_to_glb(str(simple_obj), str(output), overwrite=True)
        assert result3 is True
    
    def test_convert_batch_recursive_with_subdirs(self, tmp_path):
        """Test recursive batch conversion with subdirectories."""
        # Create directory structure
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        
        subdir1 = input_dir / "models1"
        subdir1.mkdir()
        
        subdir2 = input_dir / "models1" / "nested"
        subdir2.mkdir()
        
        # Create simple OBJ files
        obj_content = """
v 0 0 0
v 1 0 0
v 0 1 0
f 1 2 3
"""
        
        obj1 = input_dir / "model1.obj"
        obj1.write_text(obj_content)
        
        obj2 = subdir1 / "model2.obj"
        obj2.write_text(obj_content)
        
        obj3 = subdir2 / "model3.obj"
        obj3.write_text(obj_content)
        
        # Convert recursively
        output_dir = tmp_path / "output"
        success, failure = convert_batch(str(input_dir), str(output_dir), recursive=True)
        
        # Check results
        assert success == 3
        assert failure == 0
        
        # Verify output structure preserves directory hierarchy
        assert (output_dir / "model1.glb").exists()
        assert (output_dir / "models1" / "model2.glb").exists()
        assert (output_dir / "models1" / "nested" / "model3.glb").exists()

