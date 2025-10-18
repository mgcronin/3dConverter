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
    <div id="materials-panel">
        <h2>🎨 Materials</h2>
        <p style="color: #666; font-size: 11px; margin-bottom: 10px;">💡 Click to highlight on model</p>
        <div id="materials-list">
            <p style="color: #999; font-size: 12px;">Loading materials...</p>
        </div>
    </div>
    <div id="controls">
        <button class="control-btn" onclick="resetCamera()">↺ Reset View</button>
        <button class="control-btn" onclick="toggleWireframe()">◻ Wireframe</button>
        <button class="control-btn" onclick="toggleAnimation()">▶ Play/Pause</button>
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

        let scene, camera, renderer, controls, model, mixer, clock;
        let wireframeMode = false;
        let animationPaused = false;
        let materialsMap = new Map();
        let selectedMaterial = null;
        let originalMaterialStates = new Map();

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

            // Load GLB model
            const loader = new GLTFLoader();
            
            // Decode base64 GLB data
            const glbData = atob('{glb_base64}');
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
                                emissiveIntensity: mat.emissiveIntensity || 0
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
                            <div class="material-color" style="background-color: #${{color}};"></div>
                            <input 
                                type="text" 
                                value="${{material.name || 'Material_' + index}}"
                                data-uuid="${{uuid}}"
                                onchange="updateMaterialName(this)"
                                onclick="event.stopPropagation()"
                                placeholder="Material name">
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
    </script>
</body>
</html>
"""

    # Write HTML file
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"✓ Generated preview: {output_html.name}")
    return output_html

