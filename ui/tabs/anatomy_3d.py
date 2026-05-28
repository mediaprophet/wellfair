import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from ui.utils import find_df_by_keyword

def render_anatomy_3d(dark_mode: bool, normalized_data: dict) -> None:
    st.markdown("## 🧬 3D Biometric Hologram")
    st.markdown("A revolutionary, real-time spatial projection of physiological data.")

    # 1. Extract Biometric Averages
    avg_hr = 70
    sleep_eff = 85
    stress_score = 40
    
    hr_df = find_df_by_keyword(normalized_data, "heart_rate")
    if hr_df is not None and not hr_df.empty and "heart_rate" in hr_df.columns:
        avg_hr = int(hr_df["heart_rate"].mean())
        
    sleep_df = find_df_by_keyword(normalized_data, "sleep")
    if sleep_df is not None and not sleep_df.empty and "efficiency" in sleep_df.columns:
        sleep_eff = int(sleep_df["efficiency"].mean())
        
    stress_df = find_df_by_keyword(normalized_data, "stress")
    if stress_df is not None and not stress_df.empty and "score" in stress_df.columns:
        stress_score = int(stress_df["score"].mean())

    # Build the context object for the Three.js Engine
    bio_context = {
        "heartRate": avg_hr,
        "sleepEfficiency": sleep_eff,
        "stress": stress_score,
        "darkMode": dark_mode
    }
    
    # Generate HTML Payload with Three.js, OrbitControls, and Advanced UI
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; font-family: 'Outfit', sans-serif; user-select: none; }}
            #canvas-container {{ width: 100%; height: 600px; position: relative; }}
            
            /* Premium Glassmorphism UI */
            .glass-panel {{
                position: absolute;
                background: { "rgba(10, 5, 15, 0.75)" if dark_mode else "rgba(255, 255, 255, 0.85)" };
                border: 1px solid { "rgba(255, 30, 86, 0.2)" if dark_mode else "rgba(15, 23, 42, 0.1)" };
                color: { "#f1f5f9" if dark_mode else "#0f172a" };
                backdrop-filter: blur(16px);
                border-radius: 12px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                transition: all 0.3s ease;
            }}
            
            /* Layer Controls Sidebar */
            #layer-controls {{
                top: 20px;
                left: 20px;
                width: 220px;
                padding: 16px;
                z-index: 10;
            }}
            .panel-title {{
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.15em;
                color: { "#ff1e56" if dark_mode else "#0d9488" };
                font-weight: 800;
                margin-bottom: 16px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
                padding-bottom: 8px;
            }}
            
            /* Toggle Switches */
            .toggle-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                font-size: 13px;
                font-weight: 500;
                cursor: pointer;
            }}
            .toggle-row:hover {{ color: { "#ffb3c6" if dark_mode else "#3b82f6" }; }}
            .switch {{
                position: relative;
                display: inline-block;
                width: 34px;
                height: 18px;
            }}
            .switch input {{ opacity: 0; width: 0; height: 0; }}
            .slider {{
                position: absolute;
                cursor: pointer;
                top: 0; left: 0; right: 0; bottom: 0;
                background-color: rgba(255,255,255,0.1);
                transition: .4s;
                border-radius: 34px;
                border: 1px solid rgba(255,255,255,0.2);
            }}
            .slider:before {{
                position: absolute;
                content: "";
                height: 12px;
                width: 12px;
                left: 2px;
                bottom: 2px;
                background-color: #94a3b8;
                transition: .4s;
                border-radius: 50%;
            }}
            input:checked + .slider {{ background-color: { "#ff1e56" if dark_mode else "#10b981" }; border-color: transparent; }}
            input:checked + .slider:before {{ transform: translateX(16px); background-color: #fff; }}

            /* Interactive Tooltip (Raycaster) */
            #info-tooltip {{
                display: none;
                pointer-events: none;
                z-index: 20;
                padding: 16px;
                min-width: 180px;
                transform: translate(-50%, -100%);
                margin-top: -15px;
            }}
            #tooltip-title {{
                font-size: 14px;
                font-weight: 800;
                color: { "#00f0ff" if dark_mode else "#3b82f6" };
                margin-bottom: 4px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            #tooltip-desc {{
                font-size: 12px;
                color: #94a3b8;
            }}
            #tooltip-metric {{
                margin-top: 8px;
                font-size: 20px;
                font-weight: 700;
                color: { "#ffb3c6" if dark_mode else "#0f172a" };
            }}

            .instruction {{
                position: absolute;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                font-size: 11px;
                color: #94a3b8;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                background: rgba(0,0,0,0.5);
                padding: 6px 12px;
                border-radius: 20px;
                pointer-events: none;
            }}
        </style>
        
        <!-- Three.js and OrbitControls -->
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <!-- UI Sidebar -->
            <div id="layer-controls" class="glass-panel">
                <div class="panel-title">Anatomy 3D Atlas</div>
                
                <label class="toggle-row">
                    Skeletal System
                    <div class="switch">
                        <input type="checkbox" id="toggle-skeletal" checked>
                        <span class="slider"></span>
                    </div>
                </label>
                
                <label class="toggle-row">
                    Cardiovascular
                    <div class="switch">
                        <input type="checkbox" id="toggle-cardio" checked>
                        <span class="slider"></span>
                    </div>
                </label>
                
                <label class="toggle-row">
                    Nervous System
                    <div class="switch">
                        <input type="checkbox" id="toggle-nervous" checked>
                        <span class="slider"></span>
                    </div>
                </label>
            </div>

            <!-- Dynamic Tooltip -->
            <div id="info-tooltip" class="glass-panel">
                <div id="tooltip-title">Organ</div>
                <div id="tooltip-desc">Description</div>
                <div id="tooltip-metric">--</div>
            </div>

            <div class="instruction">Left Click: Inspect | Drag: Rotate | Scroll: Zoom</div>
        </div>

        <script>
            const bioData = {json.dumps(bio_context).replace("<", "\\u003c")};
            const isDark = bioData.darkMode;
            
            // Core Setup
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 1, 8);

            const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            container.appendChild(renderer.domElement);

            // OrbitControls (Like Anatomy 3D Atlas)
            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.set(0, 0, 0);
            controls.minDistance = 3;
            controls.maxDistance = 15;

            // Lighting (Studio Setup for X-Ray / Glass aesthetic)
            const ambient = new THREE.AmbientLight(0xffffff, isDark ? 0.4 : 0.7);
            scene.add(ambient);
            
            const dirLight = new THREE.DirectionalLight(isDark ? 0x00f0ff : 0xffffff, 0.8);
            dirLight.position.set(5, 5, 5);
            scene.add(dirLight);
            
            const backLight = new THREE.DirectionalLight(isDark ? 0xff1e56 : 0x0d9488, 0.5);
            backLight.position.set(-5, 5, -5);
            scene.add(backLight);

            // ==========================================
            // ANATOMY ATLAS SYSTEM GENERATION
            // ==========================================
            
            const atlasGroup = new THREE.Group();
            
            // Materials
            const matBone = new THREE.MeshPhysicalMaterial({{
                color: isDark ? 0xaaaaaa : 0xffffff,
                transparent: true,
                opacity: 0.3,
                roughness: 0.2,
                metalness: 0.1,
                clearcoat: 1.0,
                side: THREE.DoubleSide
            }});
            
            const matHeart = new THREE.MeshPhysicalMaterial({{
                color: 0xff1e56,
                emissive: bioData.heartRate > 90 ? 0xff0000 : 0x550011,
                transparent: true,
                opacity: 0.85,
                roughness: 0.1,
                transmission: 0.5
            }});
            
            const matBrain = new THREE.MeshPhysicalMaterial({{
                color: 0x00f0ff,
                emissive: bioData.sleepEfficiency < 75 ? 0xffaa00 : 0x002255,
                transparent: true,
                opacity: 0.7,
                roughness: 0.4
            }});
            
            // 1. SKELETAL SYSTEM
            const skeletalLayer = new THREE.Group();
            skeletalLayer.name = "SkeletalSystem";
            
            // Skull
            const skullGeo = new THREE.SphereGeometry(0.6, 32, 32);
            const skull = new THREE.Mesh(skullGeo, matBone);
            skull.position.y = 2.5;
            skull.scale.set(1, 1.2, 1);
            skull.userData = {{ name: "Cranium", desc: "Protects the brain.", metric: "Structural Intact" }};
            skeletalLayer.add(skull);
            
            // Spine
            for(let i=0; i<12; i++) {{
                const vert = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.15, 16), matBone);
                vert.position.set(0, 1.5 - (i * 0.25), -0.2);
                vert.userData = {{ name: "Vertebrae", desc: "Spinal column.", metric: "Cervical/Thoracic" }};
                skeletalLayer.add(vert);
            }}
            
            // Ribcage (Instanced Torus)
            for(let i=0; i<8; i++) {{
                const rib = new THREE.Mesh(new THREE.TorusGeometry(0.6 + (Math.sin(i/8 * Math.PI)*0.2), 0.05, 8, 32, Math.PI), matBone);
                rib.position.set(0, 1.2 - (i * 0.2), -0.2);
                rib.rotation.x = -Math.PI / 2 + 0.2;
                rib.userData = {{ name: "Ribcage", desc: "Thoracic cavity protection.", metric: "Respiration Normal" }};
                skeletalLayer.add(rib);
            }}
            
            // 2. CARDIOVASCULAR SYSTEM
            const cardioLayer = new THREE.Group();
            cardioLayer.name = "CardioSystem";
            
            const heart = new THREE.Mesh(new THREE.SphereGeometry(0.3, 32, 32), matHeart);
            heart.position.set(-0.2, 0.8, 0.2);
            heart.userData = {{ name: "Heart (Myocardium)", desc: "Central circulatory pump.", metric: bioData.heartRate + " BPM" }};
            cardioLayer.add(heart);
            
            // Aorta (Tube)
            class CustomSinCurve extends THREE.Curve {{
                constructor(scale = 1) {{ super(); this.scale = scale; }}
                getPoint(t, optionalTarget = new THREE.Vector3()) {{
                    const tx = Math.sin(t * Math.PI) * 0.2;
                    const ty = t * -1.5;
                    const tz = Math.cos(t * Math.PI) * 0.1;
                    return optionalTarget.set(tx, ty, tz).multiplyScalar(this.scale);
                }}
            }}
            const aortaGeo = new THREE.TubeGeometry(new CustomSinCurve(1), 20, 0.05, 8, false);
            const aorta = new THREE.Mesh(aortaGeo, matHeart);
            aorta.position.set(-0.2, 0.9, 0.2);
            aorta.userData = {{ name: "Aorta", desc: "Main systemic artery.", metric: "Pressure Nom" }};
            cardioLayer.add(aorta);
            
            // 3. NERVOUS SYSTEM
            const nervousLayer = new THREE.Group();
            nervousLayer.name = "NervousSystem";
            
            const brain = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 32), matBrain);
            brain.position.set(0, 2.5, 0);
            brain.scale.set(0.9, 1.0, 0.9);
            brain.userData = {{ name: "Brain (Cerebrum)", desc: "Central Nervous System.", metric: bioData.sleepEfficiency + "% Recovery" }};
            nervousLayer.add(brain);
            
            const spinalCord = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 3, 16), matBrain);
            spinalCord.position.set(0, 0.5, -0.2);
            spinalCord.userData = {{ name: "Spinal Cord", desc: "Main neural pathway.", metric: "Conductivity Nom" }};
            nervousLayer.add(spinalCord);

            // Add layers to main group
            atlasGroup.add(skeletalLayer);
            atlasGroup.add(cardioLayer);
            atlasGroup.add(nervousLayer);
            atlasGroup.position.y = -0.5;
            scene.add(atlasGroup);

            // ==========================================
            // UI LAYER TOGGLES
            // ==========================================
            document.getElementById('toggle-skeletal').addEventListener('change', (e) => {{ skeletalLayer.visible = e.target.checked; }});
            document.getElementById('toggle-cardio').addEventListener('change', (e) => {{ cardioLayer.visible = e.target.checked; }});
            document.getElementById('toggle-nervous').addEventListener('change', (e) => {{ nervousLayer.visible = e.target.checked; }});

            // ==========================================
            // RAYCASTING (Click to Inspect)
            // ==========================================
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            const tooltip = document.getElementById('info-tooltip');
            let hoveredMesh = null;
            let originalEmissive = new THREE.Color(0x000000);

            container.addEventListener('pointermove', (event) => {{
                const rect = container.getBoundingClientRect();
                mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                
                // Position tooltip to follow mouse (if visible)
                if(tooltip.style.display === 'block') {{
                    tooltip.style.left = (event.clientX - rect.left) + 'px';
                    tooltip.style.top = (event.clientY - rect.top) + 'px';
                }}
            }});
            
            container.addEventListener('click', () => {{
                raycaster.setFromCamera(mouse, camera);
                const intersects = raycaster.intersectObjects(atlasGroup.children, true);
                
                // Reset previous hover
                if (hoveredMesh) {{
                    hoveredMesh.material.emissive = originalEmissive;
                    hoveredMesh = null;
                    tooltip.style.display = 'none';
                }}

                if (intersects.length > 0) {{
                    const object = intersects[0].object;
                    if (object.userData && object.userData.name) {{
                        hoveredMesh = object;
                        originalEmissive = object.material.emissive.clone();
                        object.material.emissive.setHex(0xffffff); // Highlight
                        
                        // Update UI
                        document.getElementById('tooltip-title').innerText = object.userData.name;
                        document.getElementById('tooltip-desc').innerText = object.userData.desc;
                        document.getElementById('tooltip-metric').innerText = object.userData.metric;
                        tooltip.style.display = 'block';
                    }}
                }}
            }});

            // ==========================================
            // ANIMATION LOOP
            // ==========================================
            let time = 0;
            function animate() {{
                requestAnimationFrame(animate);
                controls.update(); // Required for damping
                
                // Biological Animations
                time += 0.016;
                
                // Heartbeat pulse
                if (cardioLayer.visible) {{
                    const pulseRate = bioData.heartRate / 60;
                    const pulse = (Math.sin(time * Math.PI * 2 * pulseRate) + 1) / 2;
                    heart.scale.setScalar(1 + pulse * 0.15);
                }}
                
                // Brain activity
                if (nervousLayer.visible) {{
                    if (bioData.sleepEfficiency < 75) {{
                        brain.position.x = (Math.random() - 0.5) * 0.02;
                    }} else {{
                        const brainPulse = (Math.sin(time * 1.5) + 1) / 2;
                        brain.scale.setScalar(0.9 + brainPulse * 0.05);
                    }}
                }}

                renderer.render(scene, camera);
            }}
            animate();

            // Handle Resize
            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """
    
    # Render component
    components.html(html_code, height=620)
    
    st.info("💡 **Atlas Controls:** Use the glass panel to toggle anatomical layers. Left-click and drag to rotate the model in 3D space. Scroll to zoom. Click on specific organs or bones (Raycasting) to reveal real-time biometric metrics linked to that system.")
