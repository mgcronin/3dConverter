"""
HTML preview generation for GLB models.
"""

import logging
from pathlib import Path
import base64

logger = logging.getLogger("obj2glb")


def generate_preview_html(glb_path: Path, output_html: Path = None) -> Path:
    """
    Generate an interactive HTML preview of a GLB model using Three.js.
    
    Args:
        glb_path: Path to the GLB file
        output_html: Optional path for the HTML file (defaults to same name as GLB)
        
    Returns:
        Path to the generated HTML file
    """
    if output_html is None:
        output_html = glb_path.with_suffix(".html")
    
    # Read the GLB file and encode as base64
    with open(glb_path, 'rb') as f:
        glb_data = f.read()
    glb_base64 = base64.b64encode(glb_data).decode('utf-8')
    
    # Generate HTML with Three.js viewer
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{glb_path.stem} - 3D Preview</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            overflow: hidden;
        }}
        #container {{
            width: 100vw;
            height: 100vh;
            position: relative;
        }}
        #info {{
            position: absolute;
            top: 20px;
            left: 20px;
            background: rgba(255, 255, 255, 0.95);
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 100;
        }}
        #info h1 {{
            font-size: 20px;
            margin-bottom: 8px;
            color: #333;
        }}
        #info p {{
            font-size: 14px;
            color: #666;
            margin-bottom: 4px;
        }}
            #file-browser {{
                position: absolute;
                top: 20px;
                left: 20px;
                background: rgba(255, 255, 255, 0.95);
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 100;
                width: 280px;
                max-height: 80vh;
                overflow-y: auto;
            }}
            #file-picker {{
                display: flex;
                gap: 8px;
                margin-bottom: 15px;
            }}
            .file-btn {{
                flex: 1;
                padding: 8px 12px;
                background: #667eea;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 12px;
                transition: background 0.2s;
            }}
            .file-btn:hover {{
                background: #5a6fd8;
            }}
            .file-btn:active {{
                background: #4e5bc4;
            }}
            #file-list {{
                max-height: 400px;
                overflow-y: auto;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                background: #f8f8f8;
            }}
            .file-item {{
                padding: 10px 12px;
                border-bottom: 1px solid #e0e0e0;
                cursor: pointer;
                transition: background 0.2s;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            .file-item:hover {{
                background: #e8eaff;
            }}
            .file-item.selected {{
                background: #667eea;
                color: white;
            }}
            .file-item:last-child {{
                border-bottom: none;
            }}
            .file-icon {{
                font-size: 16px;
            }}
            .file-name {{
                flex: 1;
                font-size: 13px;
                font-weight: 500;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            .file-path {{
                font-size: 11px;
                color: #666;
                margin-top: 2px;
            }}
            .file-item.selected .file-path {{
                color: rgba(255, 255, 255, 0.8);
            }}
            #materials-panel {{
                position: absolute;
                top: 20px;
                right: 20px;
                background: rgba(255, 255, 255, 0.95);
                padding: 15px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 100;
                max-width: 300px;
                max-height: 80vh;
                overflow-y: auto;
            }}
        #materials-panel h2 {{
            font-size: 16px;
            margin-bottom: 12px;
            color: #333;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .material-item {{
            background: white;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 6px;
            border: 1px solid #e0e0e0;
            cursor: pointer;
            transition: all 0.2s;
        }}
        .material-item:hover {{
            background: #f8f8f8;
            border-color: #667eea;
            transform: translateX(-2px);
        }}
        .material-item.selected {{
            background: #e8eaff;
            border-color: #667eea;
            border-width: 2px;
            box-shadow: 0 2px 4px rgba(102, 126, 234, 0.2);
        }}
        .material-name {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }}
        .material-name input {{
            flex: 1;
            padding: 4px 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 13px;
        }}
        .material-name input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .material-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #ccc;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .material-color:hover {{
            transform: scale(1.1);
            border-color: #667eea;
        }}
        .color-picker {{
            display: none;
            margin-top: 8px;
            padding: 8px;
            background: #f8f8f8;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}
        .color-picker.show {{
            display: block;
        }}
        .color-controls {{
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 6px;
        }}
        .color-input {{
            width: 40px;
            height: 30px;
            border: 1px solid #ccc;
            border-radius: 4px;
            cursor: pointer;
        }}
        .save-btn, .reset-btn {{
            padding: 4px 8px;
            font-size: 11px;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            transition: background 0.2s;
        }}
        .save-btn {{
            background: #28a745;
            color: white;
        }}
        .save-btn:hover {{
            background: #218838;
        }}
        .reset-btn {{
            background: #6c757d;
            color: white;
        }}
        .reset-btn:hover {{
            background: #5a6268;
        }}
        .material-item.modified {{
            border-left: 3px solid #ffc107;
        }}
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(40, 167, 69, 0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(40, 167, 69, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(40, 167, 69, 0); }}
        }}
        .material-textures {{
            font-size: 11px;
            color: #666;
            margin-top: 4px;
        }}
        .texture-badge {{
            display: inline-block;
            background: #f0f0f0;
            padding: 2px 6px;
            border-radius: 3px;
            margin-right: 4px;
            margin-top: 2px;
        }}
        #controls {{
            position: absolute;
            bottom: 20px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.95);
            padding: 12px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 100;
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        .control-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        .control-btn:hover {{
            background: #764ba2;
        }}
        #loading {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 255, 255, 0.95);
            padding: 30px 40px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
            z-index: 200;
        }}
        .spinner {{
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="container"></div>
    <div id="loading">
        <div class="spinner"></div>
        <p>Loading 3D Model...</p>
    </div>
    <div id="info">
        <h1>📦 {glb_path.name}</h1>
        <p>🎨 Drag to rotate • Scroll to zoom • Right-click to pan</p>
    </div>
        <div id="file-browser">
            <h2>📁 GLB Files</h2>
            <div id="file-picker">
                <button id="open-folder-btn" class="file-btn">📂 Open Folder</button>
                <button id="open-file-btn" class="file-btn">📄 Open File</button>
            </div>
            <div id="file-list">
                <p style="color: #999; font-size: 12px; text-align: center; padding: 20px;">Select a folder or file to browse GLB models</p>
            </div>
        </div>
        <div id="materials-panel">
            <h2>🎨 Materials</h2>
            <p style="color: #666; font-size: 11px; margin-bottom: 10px;">💡 Click to highlight • 🎨 Click color to edit</p>
            <div id="materials-list">
                <p style="color: #999; font-size: 12px;">Loading materials...</p>
            </div>
        </div>
        <div id="controls">
            <button class="control-btn" onclick="resetCamera()">↺ Reset View</button>
            <button class="control-btn" onclick="toggleWireframe()">◻ Wireframe</button>
            <button class="control-btn" onclick="toggleAnimation()">▶ Play/Pause</button>
            <button class="control-btn" onclick="exportModifiedGLB()" id="export-btn" style="background: #28a745; display: none; animation: pulse 2s infinite;">💾 Export Modified GLB</button>
        </div>
        
        <div id="save-info" style="display: none; position: fixed; bottom: 80px; left: 50%; transform: translateX(-50%); background: rgba(40, 167, 69, 0.95); color: white; padding: 12px 20px; border-radius: 6px; font-size: 14px; z-index: 100;">
            <div style="display: flex; align-items: center; gap: 8px;">
                <span>💡</span>
                <div>
                    <div style="font-weight: bold;">Changes Saved in Session</div>
                    <div style="font-size: 12px; opacity: 0.9;">Export GLB to download file with your changes</div>
                </div>
            </div>
        </div>

    <script type="importmap">
    {{
        "imports": {{
            "three": "https://unpkg.com/three@0.160.0/build/three.module.js",
            "three/addons/": "https://unpkg.com/three@0.160.0/examples/jsm/"
        }}
    }}
    </script>

        <script type="module">
            import * as THREE from 'three';
            import {{ OrbitControls }} from 'three/addons/controls/OrbitControls.js';
            import {{ GLTFLoader }} from 'three/addons/loaders/GLTFLoader.js';
            import {{ GLTFExporter }} from 'three/addons/exporters/GLTFExporter.js';

            let scene, camera, renderer, controls, model, mixer, clock;
            let wireframeMode = false;
            let animationPaused = false;
            let materialsMap = new Map();
            let selectedMaterial = null;
            let originalMaterialStates = new Map();
            let modifiedMaterials = new Set();
            let hasUnsavedChanges = false;
            let currentGLBData = null;
            let glbFiles = [];
            let selectedFileIndex = -1;
            
            // Get the base filename from the current page title
            const baseFilename = document.title.replace('3D Model Preview: ', '').replace('.glb', '');

        init();
        animate();

        function init() {{
            // Scene
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0xf0f0f0);
            scene.fog = new THREE.Fog(0xf0f0f0, 10, 50);

            // Camera
            camera = new THREE.PerspectiveCamera(
                50,
                window.innerWidth / window.innerHeight,
                0.1,
                1000
            );
            camera.position.set(2, 2, 5);

            // Renderer
            renderer = new THREE.WebGLRenderer({{ antialias: true }});
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            renderer.shadowMap.enabled = true;
            renderer.shadowMap.type = THREE.PCFSoftShadowMap;
            renderer.outputEncoding = THREE.sRGBEncoding;
            document.getElementById('container').appendChild(renderer.domElement);

            // Controls
            controls = new OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.screenSpacePanning = false;
            controls.minDistance = 0.5;
            controls.maxDistance = 50;

            // Lights
            const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
            scene.add(ambientLight);

            const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
            directionalLight.position.set(5, 10, 7);
            directionalLight.castShadow = true;
            directionalLight.shadow.mapSize.width = 2048;
            directionalLight.shadow.mapSize.height = 2048;
            scene.add(directionalLight);

            const directionalLight2 = new THREE.DirectionalLight(0xffffff, 0.3);
            directionalLight2.position.set(-5, 5, -5);
            scene.add(directionalLight2);

            // Ground
            const groundGeometry = new THREE.PlaneGeometry(100, 100);
            const groundMaterial = new THREE.ShadowMaterial({{ opacity: 0.2 }});
            const ground = new THREE.Mesh(groundGeometry, groundMaterial);
            ground.rotation.x = -Math.PI / 2;
            ground.receiveShadow = true;
            scene.add(ground);

            // Grid
            const gridHelper = new THREE.GridHelper(20, 20, 0x888888, 0xdddddd);
            scene.add(gridHelper);

            // Setup file browser event listeners
            setupFileBrowser();
            
            // Store current GLB data
            currentGLBData = atob('{glb_base64}');
            
            // Load GLB model
            const loader = new GLTFLoader();
            
            // Decode base64 GLB data
            const glbData = currentGLBData;
            const glbArray = new Uint8Array(glbData.length);
            for (let i = 0; i < glbData.length; i++) {{
                glbArray[i] = glbData.charCodeAt(i);
            }}

            loader.parse(glbArray.buffer, '', function(gltf) {{
                model = gltf.scene;
                
                // Enable shadows
                model.traverse(function(node) {{
                    if (node.isMesh) {{
                        node.castShadow = true;
                        node.receiveShadow = true;
                    }}
                }});

                // Center and scale model
                const box = new THREE.Box3().setFromObject(model);
                const center = box.getCenter(new THREE.Vector3());
                const size = box.getSize(new THREE.Vector3());
                const maxDim = Math.max(size.x, size.y, size.z);
                const scale = 2 / maxDim;
                
                model.position.sub(center);
                model.position.multiplyScalar(scale);
                model.scale.multiplyScalar(scale);

                scene.add(model);

                // Setup animations if present
                if (gltf.animations && gltf.animations.length > 0) {{
                    mixer = new THREE.AnimationMixer(model);
                    gltf.animations.forEach((clip) => {{
                        mixer.clipAction(clip).play();
                    }});
                    clock = new THREE.Clock();
                }}

                // Populate materials panel
                populateMaterialsPanel(gltf);

                document.getElementById('loading').style.display = 'none';
            }}, undefined, function(error) {{
                console.error('Error loading model:', error);
                document.getElementById('loading').innerHTML = 
                    '<p style="color: red;">Error loading model</p>';
            }});

            // Handle window resize
            window.addEventListener('resize', onWindowResize);
        }}

        function animate() {{
            requestAnimationFrame(animate);
            controls.update();
            
            if (mixer && !animationPaused) {{
                mixer.update(clock.getDelta());
            }}
            
            renderer.render(scene, camera);
        }}

        function onWindowResize() {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }}

        window.resetCamera = function() {{
            camera.position.set(2, 2, 5);
            controls.target.set(0, 0, 0);
            controls.update();
        }}

        window.toggleWireframe = function() {{
            wireframeMode = !wireframeMode;
            if (model) {{
                model.traverse(function(node) {{
                    if (node.isMesh) {{
                        node.material.wireframe = wireframeMode;
                    }}
                }});
            }}
        }}

        window.toggleAnimation = function() {{
            animationPaused = !animationPaused;
            if (!animationPaused && !clock) {{
                clock = new THREE.Clock();
            }}
        }}

        function populateMaterialsPanel(gltf) {{
            // Collect all unique materials from the model
            gltf.scene.traverse(function(node) {{
                if (node.isMesh && node.material) {{
                    const materials = Array.isArray(node.material) ? node.material : [node.material];
                    materials.forEach(mat => {{
                        if (!materialsMap.has(mat.uuid)) {{
                            materialsMap.set(mat.uuid, mat);
                            // Store original material state for reset
                            originalMaterialStates.set(mat.uuid, {{
                                emissive: mat.emissive ? mat.emissive.clone() : new THREE.Color(0x000000),
                                emissiveIntensity: mat.emissiveIntensity || 0,
                                color: mat.color ? mat.color.clone() : new THREE.Color(0xffffff),
                                name: mat.name || 'Unnamed'
                            }});
                        }}
                    }});
                }}
            }});

            const materialsList = document.getElementById('materials-list');
            
            if (materialsMap.size === 0) {{
                materialsList.innerHTML = '<p style="color: #999; font-size: 12px;">No materials found</p>';
                return;
            }}

            // Create material items
            let html = '';
            let index = 0;
            materialsMap.forEach((material, uuid) => {{
                const color = material.color ? material.color.getHexString() : 'ffffff';
                const hasMap = material.map ? '📷 Diffuse' : '';
                const hasNormalMap = material.normalMap ? '🗺️ Normal' : '';
                const hasMetalMap = material.metalnessMap ? '✨ Metalness' : '';
                const textures = [hasMap, hasNormalMap, hasMetalMap].filter(t => t).join(' ');
                
                html += `
                    <div class="material-item" data-uuid="${{uuid}}" onclick="highlightMaterial('${{uuid}}')">
                        <div class="material-name">
                            <div class="material-color" 
                                 style="background-color: #${{color}};" 
                                 onclick="event.stopPropagation(); toggleColorPicker('${{uuid}}')"
                                 title="Click to change color"></div>
                            <input 
                                type="text" 
                                value="${{material.name || 'Material_' + index}}"
                                data-uuid="${{uuid}}"
                                onchange="updateMaterialName(this)"
                                onclick="event.stopPropagation()"
                                placeholder="Material name">
                        </div>
                        <div class="color-picker" id="color-picker-${{uuid}}">
                            <div style="font-size: 11px; color: #666; margin-bottom: 4px;">Change Color:</div>
                            <div class="color-controls">
                                <input type="color" 
                                       class="color-input" 
                                       value="#${{color}}" 
                                       onchange="updateMaterialColor('${{uuid}}', this.value)"
                                       onclick="event.stopPropagation()">
                                <button class="save-btn" onclick="event.stopPropagation(); saveMaterialChanges('${{uuid}}')">Save</button>
                                <button class="reset-btn" onclick="event.stopPropagation(); resetMaterialColor('${{uuid}}')">Reset</button>
                            </div>
                        </div>
                        ${{textures ? `<div class="material-textures">${{textures}}</div>` : ''}}
                    </div>
                `;
                index++;
            }});
            
            materialsList.innerHTML = html;
        }}

        window.updateMaterialName = function(input) {{
            const uuid = input.getAttribute('data-uuid');
            const newName = input.value;
            
            // Update the material name in the model
            if (model) {{
                model.traverse(function(node) {{
                    if (node.isMesh && node.material) {{
                        const materials = Array.isArray(node.material) ? node.material : [node.material];
                        materials.forEach(mat => {{
                            if (mat.uuid === uuid) {{
                                mat.name = newName;
                                console.log('Updated material name to:', newName);
                            }}
                        }});
                    }}
                }});
            }}
        }}

        window.highlightMaterial = function(uuid) {{
            // If clicking the same material, deselect it
            if (selectedMaterial === uuid) {{
                resetMaterialHighlights();
                selectedMaterial = null;
                // Remove selected class from all items
                document.querySelectorAll('.material-item').forEach(item => {{
                    item.classList.remove('selected');
                }});
                return;
            }}

            // Reset previous highlights
            resetMaterialHighlights();
            selectedMaterial = uuid;

            // Update UI to show selected material
            document.querySelectorAll('.material-item').forEach(item => {{
                if (item.getAttribute('data-uuid') === uuid) {{
                    item.classList.add('selected');
                }} else {{
                    item.classList.remove('selected');
                }}
            }});

            // Highlight the material in the 3D model
            if (model) {{
                model.traverse(function(node) {{
                    if (node.isMesh && node.material) {{
                        const materials = Array.isArray(node.material) ? node.material : [node.material];
                        materials.forEach(mat => {{
                            if (mat.uuid === uuid) {{
                                // Highlight this material with emissive glow
                                if (!mat.emissive) {{
                                    mat.emissive = new THREE.Color(0xffff00);
                                }} else {{
                                    mat.emissive.setHex(0xffff00);
                                }}
                                mat.emissiveIntensity = 0.5;
                                mat.needsUpdate = true;
                                console.log('Highlighted material:', mat.name || 'Unnamed');
                            }}
                        }});
                    }}
                }});
            }}
        }}

        function resetMaterialHighlights() {{
            if (model) {{
                model.traverse(function(node) {{
                    if (node.isMesh && node.material) {{
                        const materials = Array.isArray(node.material) ? node.material : [node.material];
                        materials.forEach(mat => {{
                            const originalState = originalMaterialStates.get(mat.uuid);
                            if (originalState) {{
                                if (mat.emissive) {{
                                    mat.emissive.copy(originalState.emissive);
                                }}
                                mat.emissiveIntensity = originalState.emissiveIntensity;
                                mat.needsUpdate = true;
                            }}
                        }});
                    }}
                }});
            }}
        }}

        window.toggleColorPicker = function(uuid) {{
            // Close all other color pickers
            document.querySelectorAll('.color-picker').forEach(picker => {{
                picker.classList.remove('show');
            }});
            
            // Toggle current color picker
            const picker = document.getElementById(`color-picker-${{uuid}}`);
            picker.classList.toggle('show');
        }}

        window.updateMaterialColor = function(uuid, colorValue) {{
            const material = materialsMap.get(uuid);
            if (material) {{
                // Update the material color in real-time
                if (!material.color) {{
                    material.color = new THREE.Color();
                }}
                material.color.setHex(colorValue.replace('#', '0x'));
                material.needsUpdate = true;
                
                // Update the color swatch
                const colorSwatch = document.querySelector(`[data-uuid="${{uuid}}"] .material-color`);
                if (colorSwatch) {{
                    colorSwatch.style.backgroundColor = colorValue;
                }}
                
                // Mark as modified
                modifiedMaterials.add(uuid);
                hasUnsavedChanges = true;
                const materialItem = document.querySelector(`[data-uuid="${{uuid}}"]`);
                materialItem.classList.add('modified');
                
                // Show export button if there are modifications
                updateExportButton();
                
                console.log('Updated material color to:', colorValue);
            }}
        }}

        window.saveMaterialChanges = function(uuid) {{
            const material = materialsMap.get(uuid);
            if (material) {{
                // Update the original state to reflect saved changes
                const originalState = originalMaterialStates.get(uuid);
                if (originalState) {{
                    originalState.color.copy(material.color);
                    originalState.name = material.name;
                }}
                
                // Remove from modified set but keep hasUnsavedChanges true
                modifiedMaterials.delete(uuid);
                const materialItem = document.querySelector(`[data-uuid="${{uuid}}"]`);
                materialItem.classList.remove('modified');
                
                // Keep export button visible since we have saved changes
                updateExportButton();
                
                // Close color picker
                const picker = document.getElementById(`color-picker-${{uuid}}`);
                picker.classList.remove('show');
                
                // Show save confirmation
                showSaveNotification();
                
                console.log('Saved material changes for:', material.name);
            }}
        }}

        function showSaveNotification() {{
            // Create notification element
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #28a745;
                color: white;
                padding: 12px 20px;
                border-radius: 6px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                z-index: 1000;
                font-size: 14px;
                max-width: 300px;
                animation: slideIn 0.3s ease-out;
            `;
            
            notification.innerHTML = `
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span>✅</span>
                    <div>
                        <div style="font-weight: bold;">Material Saved!</div>
                        <div style="font-size: 12px; opacity: 0.9;">Click "Export Modified GLB" to download the updated file</div>
                    </div>
                </div>
            `;
            
            // Add animation styles
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideIn {{
                    from {{ transform: translateX(100%); opacity: 0; }}
                    to {{ transform: translateX(0); opacity: 1; }}
                }}
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(notification);
            
            // Auto-remove after 4 seconds
            setTimeout(() => {{
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {{
                    if (notification.parentNode) {{
                        notification.parentNode.removeChild(notification);
                    }}
                }}, 300);
            }}, 4000);
        }}

        window.resetMaterialColor = function(uuid) {{
            const material = materialsMap.get(uuid);
            const originalState = originalMaterialStates.get(uuid);
            
            if (material && originalState) {{
                // Reset material color
                if (material.color) {{
                    material.color.copy(originalState.color);
                }}
                material.needsUpdate = true;
                
                // Reset color swatch
                const colorSwatch = document.querySelector(`[data-uuid="${{uuid}}"] .material-color`);
                const colorInput = document.querySelector(`#color-picker-${{uuid}} .color-input`);
                if (colorSwatch && colorInput) {{
                    const hexColor = '#' + originalState.color.getHexString();
                    colorSwatch.style.backgroundColor = hexColor;
                    colorInput.value = hexColor;
                }}
                
                // Remove from modified set
                modifiedMaterials.delete(uuid);
                const materialItem = document.querySelector(`[data-uuid="${{uuid}}"]`);
                materialItem.classList.remove('modified');
                
                // If no more modified materials, check if we should hide export button
                if (modifiedMaterials.size === 0 && !hasUnsavedChanges) {{
                    updateExportButton();
                }}
                
                console.log('Reset material color for:', material.name);
            }}
        }}

        function updateExportButton() {{
            const exportBtn = document.getElementById('export-btn');
            const saveInfo = document.getElementById('save-info');
            
            if (modifiedMaterials.size > 0 || hasUnsavedChanges) {{
                exportBtn.style.display = 'inline-block';
                if (modifiedMaterials.size > 0) {{
                    exportBtn.textContent = `💾 Export Modified GLB (${{modifiedMaterials.size}} unsaved changes)`;
                }} else {{
                    exportBtn.textContent = `💾 Export Modified GLB (saved changes)`;
                }}
                saveInfo.style.display = 'block';
            }} else {{
                exportBtn.style.display = 'none';
                saveInfo.style.display = 'none';
            }}
        }}

        window.exportModifiedGLB = function() {{
            if (!model) {{
                alert('No model loaded to export');
                return;
            }}

            // Show loading indicator
            const exportBtn = document.getElementById('export-btn');
            const originalText = exportBtn.textContent;
            exportBtn.textContent = '⏳ Exporting...';
            exportBtn.disabled = true;

            try {{
                // Create a clone of the scene with the modified model
                const exportScene = new THREE.Scene();
                const clonedModel = model.clone();
                exportScene.add(clonedModel);
                
                // Add lights for proper export
                const ambientLight = new THREE.AmbientLight(0xffffff, 0.7);
                exportScene.add(ambientLight);
                
                const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
                directionalLight.position.set(1, 1, 1).normalize();
                exportScene.add(directionalLight);

                // Export to GLB
                const exporter = new GLTFExporter();
                exporter.parse(exportScene, function(gltf) {{
                    try {{
                        // Convert to GLB format
                        const glbData = new Uint8Array(gltf);
                        
                        // Create download link
                        const blob = new Blob([glbData], {{ type: 'application/octet-stream' }});
                        const url = URL.createObjectURL(blob);
                        
                        // Generate filename with timestamp
                        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                        const currentFileName = selectedFileIndex >= 0 && glbFiles[selectedFileIndex] 
                            ? glbFiles[selectedFileIndex].name.replace('.glb', '') 
                            : baseFilename;
                        const filename = `${{currentFileName}}_modified_${{timestamp}}.glb`;
                        
                        // Create download link and trigger download
                        const link = document.createElement('a');
                        link.href = url;
                        link.download = filename;
                        link.style.display = 'none';
                        document.body.appendChild(link);
                        link.click();
                        document.body.removeChild(link);
                        URL.revokeObjectURL(url);
                        
                        console.log('Exported modified GLB:', filename);
                        console.log('File size:', glbData.length, 'bytes');
                        
                        // Show success notification
                        showExportSuccessNotification(filename, glbData.length);
                        
                    }} catch (downloadError) {{
                        console.error('Download failed:', downloadError);
                        alert('Download failed: ' + downloadError.message);
                    }} finally {{
                        // Reset button
                        exportBtn.textContent = originalText;
                        exportBtn.disabled = false;
                    }}
                }}, function(error) {{
                    console.error('Export parsing failed:', error);
                    console.log('Trying fallback export method...');
                    
                    // Fallback: Try to export as JSON and convert
                    try {{
                        const fallbackExporter = new GLTFExporter();
                        fallbackExporter.parse(exportScene, function(gltfJson) {{
                            try {{
                                // Convert JSON to string and create download
                                const jsonString = JSON.stringify(gltfJson, null, 2);
                                const blob = new Blob([jsonString], {{ type: 'application/json' }});
                                const url = URL.createObjectURL(blob);
                                
                                const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
                                const currentFileName = selectedFileIndex >= 0 && glbFiles[selectedFileIndex] 
                                    ? glbFiles[selectedFileIndex].name.replace('.glb', '') 
                                    : baseFilename;
                                const filename = `${{currentFileName}}_modified_${{timestamp}}.gltf`;
                                
                                const link = document.createElement('a');
                                link.href = url;
                                link.download = filename;
                                link.style.display = 'none';
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                URL.revokeObjectURL(url);
                                
                                console.log('Exported as GLTF (fallback):', filename);
                                showExportSuccessNotification(filename, jsonString.length);
                                
                            }} catch (fallbackError) {{
                                console.error('Fallback export failed:', fallbackError);
                                alert('Export failed. Please check browser console for details.');
                            }} finally {{
                                exportBtn.textContent = originalText;
                                exportBtn.disabled = false;
                            }}
                        }}, function(fallbackError) {{
                            console.error('Fallback export parsing failed:', fallbackError);
                            alert('Export failed: ' + fallbackError.message);
                            exportBtn.textContent = originalText;
                            exportBtn.disabled = false;
                        }}, {{ 
                            binary: false
                        }});
                    }} catch (fallbackError) {{
                        console.error('Fallback export failed:', fallbackError);
                        alert('Export failed: ' + fallbackError.message);
                        exportBtn.textContent = originalText;
                        exportBtn.disabled = false;
                    }}
                }}, {{ 
                    binary: true,
                    includeCustomExtensions: true
                }});
                
            }} catch (error) {{
                console.error('Export failed:', error);
                alert('Export failed: ' + error.message);
                exportBtn.textContent = originalText;
                exportBtn.disabled = false;
            }}
        }}

            function showExportSuccessNotification(filename, fileSize) {{
                // Create success notification
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: #28a745;
                    color: white;
                    padding: 15px 20px;
                    border-radius: 6px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                    font-size: 14px;
                    max-width: 350px;
                    animation: slideIn 0.3s ease-out;
                `;
                
                const fileSizeKB = Math.round(fileSize / 1024);
                
                notification.innerHTML = `
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>✅</span>
                        <div>
                            <div style="font-weight: bold;">GLB Exported Successfully!</div>
                            <div style="font-size: 12px; opacity: 0.9;">File: ${{filename}}</div>
                            <div style="font-size: 12px; opacity: 0.9;">Size: ${{fileSizeKB}} KB</div>
                        </div>
                    </div>
                `;
                
                document.body.appendChild(notification);
                
                // Auto-remove after 5 seconds
                setTimeout(() => {{
                    notification.style.animation = 'slideIn 0.3s ease-out reverse';
                    setTimeout(() => {{
                        if (notification.parentNode) {{
                            notification.parentNode.removeChild(notification);
                        }}
                    }}, 300);
                }}, 5000);
            }}

            // File Browser Functions
            function setupFileBrowser() {{
                document.getElementById('open-folder-btn').addEventListener('click', openFolderDialog);
                document.getElementById('open-file-btn').addEventListener('click', openFileDialog);
            }}

            window.openFolderDialog = function() {{
                // Remove any existing file inputs
                const existingInputs = document.querySelectorAll('input[type="file"]');
                existingInputs.forEach(input => input.remove());
                
                // Create a file input for folder selection
                const input = document.createElement('input');
                input.type = 'file';
                input.webkitdirectory = true;
                input.multiple = true;
                input.accept = '.glb';
                input.style.display = 'none';
                document.body.appendChild(input);
                
                input.onchange = function(e) {{
                    const files = Array.from(e.target.files);
                    scanGLBFiles(files);
                    // Clean up the input element
                    if (input.parentNode) {{
                        input.parentNode.removeChild(input);
                    }}
                }};
                
                input.click();
            }}

            window.openFileDialog = function() {{
                // Remove any existing file inputs
                const existingInputs = document.querySelectorAll('input[type="file"]');
                existingInputs.forEach(input => input.remove());
                
                // Create a file input for single file selection
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = '.glb';
                input.multiple = true;
                input.style.display = 'none';
                document.body.appendChild(input);
                
                input.onchange = function(e) {{
                    if (e.target.files.length > 0) {{
                        const files = Array.from(e.target.files);
                        scanGLBFiles(files);
                    }}
                    // Clean up the input element
                    if (input.parentNode) {{
                        input.parentNode.removeChild(input);
                    }}
                }};
                
                input.click();
            }}

            function scanGLBFiles(files) {{
                console.log('Scanning files:', files.length, 'total files');
                console.log('File names:', files.map(f => f.name));
                
                glbFiles = files.filter(file => file.name.toLowerCase().endsWith('.glb'));
                console.log('Filtered GLB files:', glbFiles.length);
                console.log('GLB file names:', glbFiles.map(f => f.name));
                
                if (glbFiles.length === 0) {{
                    showNotification('No GLB files found in the selected location', 'warning');
                    return;
                }}
                
                populateFileList();
                showNotification(`Found ${{glbFiles.length}} GLB file(s)`, 'success');
            }}

            function populateFileList() {{
                const fileList = document.getElementById('file-list');
                
                if (glbFiles.length === 0) {{
                    fileList.innerHTML = '<p style="color: #999; font-size: 12px; text-align: center; padding: 20px;">No GLB files found</p>';
                    return;
                }}
                
                let html = '';
                glbFiles.forEach((file, index) => {{
                    const relativePath = file.webkitRelativePath || file.name;
                    const pathParts = relativePath.split('/');
                    const fileName = pathParts[pathParts.length - 1];
                    const folderPath = pathParts.slice(0, -1).join('/');
                    
                    html += `
                        <div class="file-item" data-index="${{index}}" onclick="selectFile(${{index}})">
                            <div class="file-icon">📦</div>
                            <div>
                                <div class="file-name">${{fileName}}</div>
                                ${{folderPath ? `<div class="file-path">${{folderPath}}</div>` : ''}}
                            </div>
                        </div>
                    `;
                }});
                
                fileList.innerHTML = html;
            }}

            window.selectFile = function(index) {{
                console.log('Selecting file at index:', index);
                
                // Update UI selection
                document.querySelectorAll('.file-item').forEach(item => {{
                    item.classList.remove('selected');
                }});
                const selectedItem = document.querySelector(`[data-index="${{index}}"]`);
                if (selectedItem) {{
                    selectedItem.classList.add('selected');
                    console.log('UI updated for file selection');
                }} else {{
                    console.error('Could not find file item with index:', index);
                }}
                
                selectedFileIndex = index;
                console.log('Selected file index set to:', selectedFileIndex);
                loadSelectedFile();
            }}

            async function loadSelectedFile() {{
                if (selectedFileIndex < 0 || selectedFileIndex >= glbFiles.length) {{
                    console.error('Invalid file index:', selectedFileIndex);
                    return;
                }}
                
                const file = glbFiles[selectedFileIndex];
                console.log('Loading file:', file.name, 'Size:', file.size, 'bytes');
                
                try {{
                    // Show loading state
                    document.getElementById('loading').style.display = 'flex';
                    document.getElementById('loading').innerHTML = `
                        <div class="spinner"></div>
                        <p>Loading ${{file.name}}...</p>
                    `;
                    
                    // Read file as ArrayBuffer
                    console.log('Reading file as ArrayBuffer...');
                    const arrayBuffer = await file.arrayBuffer();
                    console.log('File read successfully, size:', arrayBuffer.byteLength, 'bytes');
                    
                    // Clear current model
                    if (model) {{
                        console.log('Removing current model from scene');
                        scene.remove(model);
                        model = null;
                    }}
                    
                    // Load new model
                    console.log('Parsing GLB data...');
                    const loader = new GLTFLoader();
                    loader.parse(arrayBuffer, '', function(gltf) {{
                        console.log('GLB parsed successfully:', gltf);
                        
                        model = gltf.scene;
                        
                        // Enable shadows
                        model.traverse(function(node) {{
                            if (node.isMesh) {{
                                node.castShadow = true;
                                node.receiveShadow = true;
                            }}
                        }});
                        
                        scene.add(model);
                        console.log('Model added to scene');
                        
                        // Update camera to fit new model
                        const box = new THREE.Box3().setFromObject(model);
                        const center = box.getCenter(new THREE.Vector3());
                        const size = box.getSize(new THREE.Vector3());
                        
                        console.log('Model bounds:', box, 'Center:', center, 'Size:', size);
                        
                        const maxDim = Math.max(size.x, size.y, size.z);
                        const fov = camera.fov * (Math.PI / 180);
                        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
                        cameraZ *= 1.5;
                        
                        camera.position.set(center.x, center.y, center.z + cameraZ);
                        controls.target.set(center.x, center.y, center.z);
                        controls.update();
                        
                        console.log('Camera positioned at:', camera.position, 'Target:', controls.target);
                        
                        // Update materials panel
                        populateMaterialsPanel(gltf);
                        
                        // Update info panel
                        document.getElementById('info').innerHTML = `
                            <h1>📦 ${{file.name}}</h1>
                            <p>🎨 Drag to rotate • Scroll to zoom • Right-click to pan</p>
                        `;
                        
                        // Hide loading
                        document.getElementById('loading').style.display = 'none';
                        
                        // Reset material states
                        resetMaterialHighlights();
                        selectedMaterial = null;
                        modifiedMaterials.clear();
                        hasUnsavedChanges = false;
                        updateExportButton();
                        
                        showNotification(`Loaded: ${{file.name}}`, 'success');
                        console.log('File loaded successfully!');
                        
                    }}, function(error) {{
                        console.error('Error loading model:', error);
                        document.getElementById('loading').innerHTML = 
                            '<p style="color: red;">Error loading model: ' + error.message + '</p>';
                        showNotification('Error loading model: ' + error.message, 'error');
                    }});
                    
                }} catch (error) {{
                    console.error('Error reading file:', error);
                    showNotification('Error reading file: ' + error.message, 'error');
                    document.getElementById('loading').style.display = 'none';
                }}
            }}

            function showNotification(message, type = 'info') {{
                const colors = {{
                    success: '#28a745',
                    error: '#dc3545',
                    warning: '#ffc107',
                    info: '#17a2b8'
                }};
                
                const notification = document.createElement('div');
                notification.style.cssText = `
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: ${{colors[type]}};
                    color: white;
                    padding: 12px 20px;
                    border-radius: 6px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    z-index: 1000;
                    font-size: 14px;
                    max-width: 300px;
                    animation: slideIn 0.3s ease-out;
                `;
                
                notification.textContent = message;
                document.body.appendChild(notification);
                
                // Auto-remove after 3 seconds
                setTimeout(() => {{
                    notification.style.animation = 'slideIn 0.3s ease-out reverse';
                    setTimeout(() => {{
                        if (notification.parentNode) {{
                            notification.parentNode.removeChild(notification);
                        }}
                    }}, 300);
                }}, 3000);
            }}
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"✓ Generated preview: {output_html.name}")
    return output_html

