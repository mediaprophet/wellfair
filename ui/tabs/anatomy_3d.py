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
    
    # Generate HTML Payload
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; font-family: 'Outfit', sans-serif; }}
            #canvas-container {{ width: 100%; height: 600px; position: relative; }}
            .overlay-card {{
                position: absolute;
                background: { "rgba(15, 23, 42, 0.7)" if dark_mode else "rgba(255, 255, 255, 0.8)" };
                border: 1px solid { "rgba(255, 255, 255, 0.15)" if dark_mode else "rgba(15, 23, 42, 0.1)" };
                color: { "#f1f5f9" if dark_mode else "#0f172a" };
                padding: 12px 16px;
                border-radius: 12px;
                backdrop-filter: blur(12px);
                pointer-events: none;
                transition: opacity 0.3s;
                opacity: 0;
                transform: translate(-50%, -50%);
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            }}
            .metric-title {{ font-size: 11px; text-transform: uppercase; letter-spacing: 0.1em; color: #94a3b8; font-weight: 600; margin-bottom: 4px; }}
            .metric-value {{ font-size: 24px; font-weight: 800; }}
            .pulse-red {{ color: #ff1e56; text-shadow: 0 0 10px rgba(255,30,86,0.5); }}
            .pulse-blue {{ color: #00f0ff; text-shadow: 0 0 10px rgba(0,240,255,0.5); }}
            .pulse-amber {{ color: #ffaa00; text-shadow: 0 0 10px rgba(255,170,0,0.5); }}
            #heart-card {{ top: 40%; left: 35%; }}
            #brain-card {{ top: 20%; left: 65%; }}
            #nervous-card {{ top: 60%; left: 65%; }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <div id="heart-card" class="overlay-card">
                <div class="metric-title">Cardiac System</div>
                <div class="metric-value" id="heart-val">-- BPM</div>
            </div>
            <div id="brain-card" class="overlay-card">
                <div class="metric-title">Cognitive Recovery</div>
                <div class="metric-value" id="brain-val">-- %</div>
            </div>
            <div id="nervous-card" class="overlay-card">
                <div class="metric-title">Nervous System</div>
                <div class="metric-value" id="stress-val">-- Score</div>
            </div>
        </div>

        <script>
            const bioData = {json.dumps(bio_context)};
            
            // UI Updates
            setTimeout(() => {{
                document.getElementById('heart-card').style.opacity = 1;
                document.getElementById('brain-card').style.opacity = 1;
                document.getElementById('nervous-card').style.opacity = 1;
                
                const hrEl = document.getElementById('heart-val');
                hrEl.innerText = bioData.heartRate + " BPM";
                if(bioData.heartRate > 90) hrEl.className = "metric-value pulse-red";
                else hrEl.className = "metric-value pulse-blue";
                
                const brEl = document.getElementById('brain-val');
                brEl.innerText = bioData.sleepEfficiency + "%";
                if(bioData.sleepEfficiency < 75) brEl.className = "metric-value pulse-amber";
                else brEl.className = "metric-value pulse-blue";
                
                const stEl = document.getElementById('stress-val');
                stEl.innerText = bioData.stress;
                if(bioData.stress > 60) stEl.className = "metric-value pulse-amber";
                else stEl.className = "metric-value pulse-blue";
            }}, 1000);

            // Three.js Scene Setup
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            // Transparent background
            
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.z = 10;
            camera.position.y = 0;

            const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            container.appendChild(renderer.domElement);

            // Abstract Hologram Humanoid Construction
            const humanGroup = new THREE.Group();
            
            // Base Hologram Material
            const wireMaterial = new THREE.MeshBasicMaterial({{ 
                color: bioData.darkMode ? 0x00f0ff : 0x0d9488, 
                wireframe: true, 
                transparent: true, 
                opacity: 0.15 
            }});
            
            const solidMaterial = new THREE.MeshPhongMaterial({{
                color: bioData.darkMode ? 0x0088ff : 0x14b8a6,
                transparent: true,
                opacity: 0.1,
                shininess: 100,
                blending: THREE.AdditiveBlending
            }});

            function createPart(geo, y, scale=1) {{
                const mesh1 = new THREE.Mesh(geo, wireMaterial);
                const mesh2 = new THREE.Mesh(geo, solidMaterial);
                mesh1.scale.set(scale, scale, scale);
                mesh2.scale.set(scale*0.98, scale*0.98, scale*0.98);
                const group = new THREE.Group();
                group.add(mesh1);
                group.add(mesh2);
                group.position.y = y;
                return group;
            }}

            // Head
            const head = createPart(new THREE.SphereGeometry(0.5, 16, 16), 2.5);
            humanGroup.add(head);

            // Torso
            const torso = createPart(new THREE.CylinderGeometry(0.8, 0.6, 2.5, 16, 8), 0.5);
            humanGroup.add(torso);
            
            // Arms
            const armGeo = new THREE.CylinderGeometry(0.2, 0.15, 2.2, 8, 4);
            const lArm = createPart(armGeo, 0.5); lArm.position.x = -1.2;
            const rArm = createPart(armGeo, 0.5); rArm.position.x = 1.2;
            humanGroup.add(lArm);
            humanGroup.add(rArm);
            
            // Legs
            const legGeo = new THREE.CylinderGeometry(0.25, 0.15, 2.5, 8, 4);
            const lLeg = createPart(legGeo, -2.2); lLeg.position.x = -0.4;
            const rLeg = createPart(legGeo, -2.2); rLeg.position.x = 0.4;
            humanGroup.add(lLeg);
            humanGroup.add(rLeg);

            // --- Biometric Anomalies ---
            
            // Heart Node
            const heartGeo = new THREE.SphereGeometry(0.25, 16, 16);
            const heartColor = bioData.heartRate > 90 ? 0xff1e56 : 0x00f0ff;
            const heartMat = new THREE.MeshBasicMaterial({{ color: heartColor, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending }});
            const heartNode = new THREE.Mesh(heartGeo, heartMat);
            heartNode.position.set(-0.2, 1.2, 0.5);
            humanGroup.add(heartNode);
            
            // Brain Node
            const brainGeo = new THREE.SphereGeometry(0.3, 16, 16);
            const brainColor = bioData.sleepEfficiency < 75 ? 0xffaa00 : 0x00f0ff;
            const brainMat = new THREE.MeshBasicMaterial({{ color: brainColor, transparent: true, opacity: 0.6, blending: THREE.AdditiveBlending }});
            const brainNode = new THREE.Mesh(brainGeo, brainMat);
            brainNode.position.set(0, 2.5, 0);
            humanGroup.add(brainNode);

            scene.add(humanGroup);
            humanGroup.position.y = -0.5;

            // Lights
            const ambient = new THREE.AmbientLight(0xffffff, 0.5);
            scene.add(ambient);
            const pointLight = new THREE.PointLight(0xffffff, 1);
            pointLight.position.set(5, 5, 5);
            scene.add(pointLight);

            // Animation Loop
            let time = 0;
            function animate() {{
                requestAnimationFrame(animate);
                
                // Slow rotation
                humanGroup.rotation.y = Math.sin(time * 0.5) * 0.3;
                
                // Heartbeat pulse effect
                const pulseRate = bioData.heartRate / 60; // beats per second
                const pulse = (Math.sin(time * Math.PI * 2 * pulseRate) + 1) / 2; // 0 to 1
                heartNode.scale.setScalar(1 + pulse * 0.4);
                heartNode.material.opacity = 0.4 + pulse * 0.6;
                
                // Brain interference effect (poor sleep = jitter)
                if (bioData.sleepEfficiency < 75) {{
                    brainNode.position.x = (Math.random() - 0.5) * 0.05;
                    brainNode.material.opacity = 0.3 + Math.random() * 0.5;
                }} else {{
                    const brainPulse = (Math.sin(time * 2) + 1) / 2;
                    brainNode.scale.setScalar(1 + brainPulse * 0.1);
                }}

                time += 0.016; // Approx 60fps
                renderer.render(scene, camera);
            }}
            animate();

            // Handle resize
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
    
    st.info("The holographic projection maps real-time biometric anomalies directly to the anatomy. High heart rates cause the cardiac node to pulse rapidly in crimson, while poor sleep efficiency triggers cognitive interference (amber static) in the neural node.")
