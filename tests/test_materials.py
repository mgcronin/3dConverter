"""
Tests for materials module.
"""

import pytest
from pathlib import Path
from obj2glb.materials import MaterialHandler


class TestMaterialHandler:
    """Test cases for the MaterialHandler class."""
    
    @pytest.fixture
    def temp_obj(self, tmp_path):
        """Create a temporary OBJ file."""
        obj_file = tmp_path / "test.obj"
        obj_file.write_text("v 0 0 0\n")
        return obj_file
    
    @pytest.fixture
    def temp_mtl(self, tmp_path):
        """Create a temporary MTL file."""
        mtl_file = tmp_path / "test.mtl"
        mtl_content = """
# Test MTL file
newmtl Material1
Ka 0.2 0.2 0.2
Kd 0.8 0.0 0.0
Ks 1.0 1.0 1.0
Ns 96.0
d 1.0

newmtl Material2
Ka 0.1 0.1 0.1
Kd 0.0 0.8 0.0
Ks 0.5 0.5 0.5
Ns 32.0
"""
        mtl_file.write_text(mtl_content)
        return mtl_file
    
    def test_material_handler_init(self, temp_obj):
        """Test MaterialHandler initialization."""
        handler = MaterialHandler(temp_obj)
        assert handler.obj_path == temp_obj
        assert handler.obj_dir == temp_obj.parent
    
    def test_parse_mtl_file(self, temp_obj, temp_mtl):
        """Test parsing MTL file."""
        handler = MaterialHandler(temp_obj)
        materials = handler.parse_mtl_file(temp_mtl)
        
        assert len(materials) == 2
        assert "Material1" in materials
        assert "Material2" in materials
        
        mat1 = materials["Material1"]
        assert mat1["diffuse"] == [0.8, 0.0, 0.0]
        assert mat1["shininess"] == 96.0
        
        mat2 = materials["Material2"]
        assert mat2["diffuse"] == [0.0, 0.8, 0.0]
        assert mat2["shininess"] == 32.0
    
    def test_parse_mtl_file_nonexistent(self, temp_obj, tmp_path):
        """Test parsing nonexistent MTL file."""
        handler = MaterialHandler(temp_obj)
        mtl_file = tmp_path / "nonexistent.mtl"
        materials = handler.parse_mtl_file(mtl_file)
        
        assert materials == {}
    
    def test_parse_color(self, temp_obj):
        """Test color parsing."""
        handler = MaterialHandler(temp_obj)
        
        # RGB values
        color1 = handler._parse_color("1.0 0.5 0.25")
        assert color1 == [1.0, 0.5, 0.25]
        
        # Single value
        color2 = handler._parse_color("0.5")
        assert color2 == [0.5, 0.5, 0.5]
        
        # Invalid value
        color3 = handler._parse_color("invalid")
        assert color3 == [0.8, 0.8, 0.8]  # Default
    
    def test_load_texture_nonexistent(self, temp_obj):
        """Test loading nonexistent texture."""
        handler = MaterialHandler(temp_obj)
        texture = handler.load_texture("nonexistent.png")
        assert texture is None
    
    def test_create_default_material(self, temp_obj):
        """Test creating default material."""
        handler = MaterialHandler(temp_obj)
        materials = handler.create_default_material()
        
        assert "default" in materials
        assert "diffuse" in materials["default"]
        assert "ambient" in materials["default"]
        assert "specular" in materials["default"]
    
    def test_process_materials_no_mtl(self, temp_obj):
        """Test processing materials when no MTL file exists."""
        handler = MaterialHandler(temp_obj)
        materials, textures = handler.process_materials()
        
        assert "default" in materials
        assert textures == {}

