import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from ui.utils import find_df_by_keyword

def render_anatomy_3d(dark_mode: bool, normalized_data: dict) -> None:
    st.markdown("## 🧬 3D Biometric Hologram")
    st.markdown("A revolutionary, real-time spatial projection of physiological data.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 **Atlas Controls:** Use the glass panel to toggle all 13 anatomical systems. Left-click and drag to rotate. Scroll to zoom. Click on organs to inspect.")
    with col2:
        sim_condition = st.selectbox(
            "Simulate Condition",
            ["Healthy", "Metabolic Syndrome", "Chronic Stress", "Acute Infection"]
        )

    # Extract Biometric Averages
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

    # Override biometrics if simulating a condition to demonstrate the systemic effects
    if sim_condition == "Metabolic Syndrome":
        avg_hr = 95
        stress_score = 65
    elif sim_condition == "Chronic Stress":
        sleep_eff = 50
        stress_score = 90
        avg_hr = 88
    elif sim_condition == "Acute Infection":
        avg_hr = 110
        sleep_eff = 40

    bio_context = {
        "heartRate": avg_hr,
        "sleepEfficiency": sleep_eff,
        "stress": stress_score,
        "darkMode": dark_mode,
        "condition": sim_condition
    }
    
    # Generate HTML Payload with Three.js, OrbitControls, and Advanced UI
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; font-family: 'Outfit', sans-serif; user-select: none; }}
            #canvas-container {{ width: 100%; height: 750px; position: relative; }}
            
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
                width: 240px;
                padding: 16px;
                z-index: 10;
                max-height: 700px;
                overflow-y: auto;
            }}
            
            /* Custom Scrollbar */
            #layer-controls::-webkit-scrollbar {{ width: 6px; }}
            #layer-controls::-webkit-scrollbar-track {{ background: transparent; }}
            #layer-controls::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 3px; }}

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
                margin-bottom: 10px;
                font-size: 12px;
                font-weight: 500;
                cursor: pointer;
            }}
            .toggle-row:hover {{ color: { "#ffb3c6" if dark_mode else "#3b82f6" }; }}
            .switch {{
                position: relative;
                display: inline-block;
                width: 30px;
                height: 16px;
            }}
            .switch input {{ opacity: 0; width: 0; height: 0; }}
            .slider {{
                position: absolute;
                cursor: pointer;
                top: 0; left: 0; right: 0; bottom: 0;
                background-color: rgba(150,150,150,0.3);
                transition: .4s;
                border-radius: 34px;
            }}
            .slider:before {{
                position: absolute;
                content: "";
                height: 10px;
                width: 10px;
                left: 3px;
                bottom: 3px;
                background-color: #fff;
                transition: .4s;
                border-radius: 50%;
            }}
            input:checked + .slider {{ background-color: { "#ff1e56" if dark_mode else "#10b981" }; }}
            input:checked + .slider:before {{ transform: translateX(14px); }}

            /* Interactive Tooltip (Raycaster) */
            #info-tooltip {{
                display: none;
                pointer-events: none;
                z-index: 20;
                padding: 16px;
                min-width: 200px;
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
            #tooltip-desc {{ font-size: 12px; color: #94a3b8; line-height: 1.4; }}
            #tooltip-metric {{
                margin-top: 8px;
                font-size: 18px;
                font-weight: 700;
                color: { "#ffb3c6" if dark_mode else "#0f172a" };
            }}
            
            #condition-banner {{
                position: absolute;
                top: 20px;
                right: 20px;
                padding: 12px 20px;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                border-left: 4px solid #ff1e56;
                display: none;
            }}
            .condition-active {{ display: block !important; animation: pulse 2s infinite; }}
            @keyframes pulse {{
                0% {{ box-shadow: 0 0 0 0 rgba(255, 30, 86, 0.4); }}
                70% {{ box-shadow: 0 0 0 15px rgba(255, 30, 86, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(255, 30, 86, 0); }}
            }}
        </style>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <!-- UI Sidebar (13 Systems) -->
            <div id="layer-controls" class="glass-panel">
                <div class="panel-title">13 Anatomical Systems</div>
                
                <label class="toggle-row">Skeletal <div class="switch"><input type="checkbox" id="t-skeletal" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Muscular <div class="switch"><input type="checkbox" id="t-muscular"><span class="slider"></span></div></label>
                <label class="toggle-row">Cardiovascular <div class="switch"><input type="checkbox" id="t-cardio" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Digestive <div class="switch"><input type="checkbox" id="t-digestive" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Endocrine <div class="switch"><input type="checkbox" id="t-endocrine" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Nervous <div class="switch"><input type="checkbox" id="t-nervous" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Respiratory <div class="switch"><input type="checkbox" id="t-respiratory" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Immune/Lymph <div class="switch"><input type="checkbox" id="t-immune" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Urinary <div class="switch"><input type="checkbox" id="t-urinary" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Female Repro <div class="switch"><input type="checkbox" id="t-repro_f"><span class="slider"></span></div></label>
                <label class="toggle-row">Male Repro <div class="switch"><input type="checkbox" id="t-repro_m"><span class="slider"></span></div></label>
                <label class="toggle-row">Integumentary <div class="switch"><input type="checkbox" id="t-skin"><span class="slider"></span></div></label>
                <label class="toggle-row">Sensory <div class="switch"><input type="checkbox" id="t-sensory" checked><span class="slider"></span></div></label>
            </div>

            <!-- Anomaly Banner -->
            <div id="condition-banner" class="glass-panel"></div>

            <!-- Tooltip -->
            <div id="info-tooltip" class="glass-panel">
                <div id="tooltip-title">Organ</div>
                <div id="tooltip-desc">Description</div>
                <div id="tooltip-metric">--</div>
            </div>
        </div>

        <script>
            const bioData = {json.dumps(bio_context).replace("<", "\\u003c")};
            const isDark = bioData.darkMode;
            
            if (bioData.condition !== "Healthy") {{
                const b = document.getElementById("condition-banner");
                b.innerText = "SIMULATING: " + bioData.condition;
                b.classList.add("condition-active");
            }}
            
            // Core Setup
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 1, 9);

            const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            container.appendChild(renderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.set(0, 0, 0);

            const ambient = new THREE.AmbientLight(0xffffff, isDark ? 0.3 : 0.6);
            scene.add(ambient);
            const dirLight = new THREE.DirectionalLight(isDark ? 0x00f0ff : 0xffffff, 0.8);
            dirLight.position.set(5, 5, 5);
            scene.add(dirLight);
            const backLight = new THREE.DirectionalLight(isDark ? 0xff1e56 : 0x0d9488, 0.5);
            backLight.position.set(-5, 5, -5);
            scene.add(backLight);

            // ==========================================
            // 13 ANATOMICAL SYSTEMS GENERATION
            // ==========================================
            const atlasGroup = new THREE.Group();
            const layers = {{}};
            
            // Shared Materials
            const matBone = new THREE.MeshPhysicalMaterial({{ color: isDark?0xaaaaaa:0xffffff, transparent: true, opacity: 0.3, roughness: 0.2 }});
            const matMuscle = new THREE.MeshPhysicalMaterial({{ color: 0x8b0000, transparent: true, opacity: 0.2, roughness: 0.8 }});
            const matHeart = new THREE.MeshPhysicalMaterial({{ color: 0xff1e56, transparent: true, opacity: 0.85 }});
            const matBrain = new THREE.MeshPhysicalMaterial({{ color: 0x00f0ff, transparent: true, opacity: 0.7 }});
            const matDigestive = new THREE.MeshPhysicalMaterial({{ color: 0x84cc16, transparent: true, opacity: 0.5 }});
            const matLungs = new THREE.MeshPhysicalMaterial({{ color: 0x38bdf8, transparent: true, opacity: 0.4 }});
            const matEndocrine = new THREE.MeshPhysicalMaterial({{ color: 0xd946ef, emissive: 0x4a044e, transparent: true, opacity: 0.9 }});
            const matLymph = new THREE.MeshPhysicalMaterial({{ color: 0xa3e635, wireframe: true, transparent: true, opacity: 0.3 }});
            const matUro = new THREE.MeshPhysicalMaterial({{ color: 0xfacc15, transparent: true, opacity: 0.7 }});
            const matSkin = new THREE.MeshPhysicalMaterial({{ color: 0x0ea5e9, transparent: true, opacity: 0.05, depthWrite: false }});
            const matSensory = new THREE.MeshPhysicalMaterial({{ color: 0xffffff, emissive: 0x00f0ff, transparent: true, opacity: 0.8 }});

            // Condition Overrides
            if (bioData.condition === "Metabolic Syndrome") {{
                matEndocrine.emissive.setHex(0xffaa00); // Pancreas distress
                matHeart.emissive.setHex(0x550000); // Hypertension
                matDigestive.color.setHex(0xaaaa00);
            }} else if (bioData.condition === "Chronic Stress") {{
                matBrain.emissive.setHex(0xffaa00);
                matEndocrine.emissive.setHex(0xff1e56); // Adrenals firing
            }} else if (bioData.condition === "Acute Infection") {{
                matLungs.color.setHex(0xff1e56); // Lung inflammation
                matLungs.opacity = 0.7;
                matLymph.opacity = 0.8; // Swollen lymph
                matLymph.color.setHex(0xffaa00);
                matSkin.color.setHex(0xff0000); // Fever
                matSkin.opacity = 0.1;
            }}

            function createLayer(name) {{
                const group = new THREE.Group();
                group.name = name;
                layers[name] = group;
                atlasGroup.add(group);
                return group;
            }}

            // 1. SKELETAL
            const sysSkel = createLayer('skeletal');
            const skull = new THREE.Mesh(new THREE.SphereGeometry(0.6, 32, 32), matBone);
            skull.position.y = 2.5;
            skull.scale.set(1, 1.2, 1);
            skull.userData = {{ name: "Cranium", desc: "Bone structure of the head.", metric: "Density Normal" }};
            sysSkel.add(skull);
            for(let i=0; i<12; i++) {{
                const vert = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.15, 16), matBone);
                vert.position.set(0, 1.5 - (i * 0.25), -0.2);
                sysSkel.add(vert);
            }}
            for(let i=0; i<8; i++) {{
                const rib = new THREE.Mesh(new THREE.TorusGeometry(0.6 + (Math.sin(i/8*Math.PI)*0.2), 0.05, 8, 32, Math.PI), matBone);
                rib.position.set(0, 1.2 - (i * 0.2), -0.2);
                rib.rotation.x = -Math.PI / 2 + 0.2;
                sysSkel.add(rib);
            }}

            // 2. MUSCULAR (Simple Hull)
            const sysMusc = createLayer('muscular');
            const torsoHull = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.7, 2.8, 16), matMuscle);
            torsoHull.position.set(0, 0.5, 0);
            sysMusc.add(torsoHull);
            sysMusc.visible = false;

            // 3. CARDIOVASCULAR
            const sysCardio = createLayer('cardio');
            const heart = new THREE.Mesh(new THREE.SphereGeometry(0.25, 32, 32), matHeart);
            heart.position.set(-0.2, 0.8, 0.2);
            heart.userData = {{ name: "Heart (Myocardium)", desc: "Central pump.", metric: bioData.heartRate + " BPM" }};
            sysCardio.add(heart);
            const aorta = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 2, 8), matHeart);
            aorta.position.set(-0.1, 0, 0.1);
            sysCardio.add(aorta);

            // 4. DIGESTIVE
            const sysDigestive = createLayer('digestive');
            const stomach = new THREE.Mesh(new THREE.SphereGeometry(0.3, 16, 16), matDigestive);
            stomach.scale.set(1.5, 1, 1);
            stomach.position.set(-0.3, -0.2, 0.2);
            stomach.userData = {{ name: "Stomach", desc: "Digests food.", metric: bioData.condition==="Metabolic Syndrome"?"Delayed Emptying":"Normal" }};
            sysDigestive.add(stomach);
            const intestines = new THREE.Mesh(new THREE.TorusKnotGeometry(0.3, 0.1, 64, 8, 2, 3), matDigestive);
            intestines.position.set(0, -1.0, 0.1);
            intestines.userData = {{ name: "Intestines", desc: "Nutrient absorption.", metric: "Motility Active" }};
            sysDigestive.add(intestines);

            // 5. ENDOCRINE
            const sysEndo = createLayer('endocrine');
            const pancreas = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.4, 8), matEndocrine);
            pancreas.rotation.z = Math.PI / 2;
            pancreas.position.set(0, -0.4, 0.1);
            pancreas.userData = {{ name: "Pancreas", desc: "Insulin production.", metric: bioData.condition==="Metabolic Syndrome"?"Insulin Resistance":"Nominal" }};
            sysEndo.add(pancreas);
            const thyroid = new THREE.Mesh(new THREE.SphereGeometry(0.08, 16, 16), matEndocrine);
            thyroid.scale.set(2, 1, 1);
            thyroid.position.set(0, 1.7, 0.2);
            sysEndo.add(thyroid);
            const adrenalL = new THREE.Mesh(new THREE.SphereGeometry(0.06), matEndocrine);
            adrenalL.position.set(-0.3, -0.4, -0.15);
            adrenalL.userData = {{ name: "Adrenal Glands", desc: "Cortisol production.", metric: bioData.condition==="Chronic Stress"?"Cortisol Elevated!":"Normal" }};
            sysEndo.add(adrenalL);

            // 6. NERVOUS
            const sysNervous = createLayer('nervous');
            const brain = new THREE.Mesh(new THREE.SphereGeometry(0.5, 32, 32), matBrain);
            brain.position.set(0, 2.5, 0);
            brain.scale.set(0.9, 1.0, 0.9);
            brain.userData = {{ name: "Brain", desc: "Central Nervous System.", metric: bioData.sleepEfficiency + "% Recovery" }};
            sysNervous.add(brain);
            const spineCord = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 3.5, 8), matBrain);
            spineCord.position.set(0, 0.5, -0.2);
            sysNervous.add(spineCord);

            // 7. RESPIRATORY
            const sysResp = createLayer('respiratory');
            const lungL = new THREE.Mesh(new THREE.SphereGeometry(0.35, 16, 16), matLungs);
            lungL.scale.set(1, 1.8, 1);
            lungL.position.set(-0.4, 0.9, 0);
            lungL.userData = {{ name: "Left Lung", desc: "Gas exchange.", metric: bioData.condition==="Acute Infection"?"SpO2 88% (Low)":"SpO2 99%" }};
            const lungR = lungL.clone();
            lungR.position.set(0.4, 0.9, 0);
            lungR.userData = {{ name: "Right Lung", desc: "Gas exchange.", metric: bioData.condition==="Acute Infection"?"Consolidation Detected":"Clear" }};
            sysResp.add(lungL);
            sysResp.add(lungR);

            // 8. IMMUNE / LYMPH
            const sysImmune = createLayer('immune');
            const lymph = new THREE.Mesh(new THREE.TorusKnotGeometry(0.8, 0.02, 64, 8, 3, 5), matLymph);
            lymph.position.y = 0.5;
            lymph.userData = {{ name: "Lymphatic Network", desc: "Immune defense.", metric: bioData.condition==="Acute Infection"?"High Leukocytes":"Normal" }};
            sysImmune.add(lymph);

            // 9. URINARY
            const sysUro = createLayer('urinary');
            const kidL = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), matUro);
            kidL.scale.set(1, 1.5, 1);
            kidL.position.set(-0.3, -0.6, -0.2);
            kidL.userData = {{ name: "Kidney", desc: "Filters blood.", metric: "GFR Normal" }};
            const kidR = kidL.clone();
            kidR.position.set(0.3, -0.6, -0.2);
            sysUro.add(kidL);
            sysUro.add(kidR);
            const bladder = new THREE.Mesh(new THREE.SphereGeometry(0.15, 16, 16), matUro);
            bladder.position.set(0, -1.6, 0.1);
            sysUro.add(bladder);

            // 10 & 11. REPRODUCTIVE (Abstracted)
            const sysReproF = createLayer('repro_f');
            const uterus = new THREE.Mesh(new THREE.SphereGeometry(0.15), new THREE.MeshPhysicalMaterial({{color: 0xec4899, transparent:true, opacity:0.8}}));
            uterus.position.set(0, -1.4, 0);
            sysReproF.add(uterus);
            sysReproF.visible = false;
            
            const sysReproM = createLayer('repro_m');
            const prostate = new THREE.Mesh(new THREE.SphereGeometry(0.1), new THREE.MeshPhysicalMaterial({{color: 0x3b82f6, transparent:true, opacity:0.8}}));
            prostate.position.set(0, -1.5, 0.15);
            sysReproM.add(prostate);
            sysReproM.visible = false;

            // 12. INTEGUMENTARY (Skin)
            const sysSkin = createLayer('skin');
            const skinHull = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.75, 3.5, 32), matSkin);
            skinHull.position.y = 0.5;
            const headHull = new THREE.Mesh(new THREE.SphereGeometry(0.7, 32, 32), matSkin);
            headHull.position.y = 2.5;
            sysSkin.add(skinHull);
            sysSkin.add(headHull);
            sysSkin.visible = false;

            // 13. SENSORY
            const sysSensory = createLayer('sensory');
            const eyeL = new THREE.Mesh(new THREE.SphereGeometry(0.08), matSensory);
            eyeL.position.set(-0.25, 2.6, 0.5);
            const eyeR = eyeL.clone();
            eyeR.position.set(0.25, 2.6, 0.5);
            sysSensory.add(eyeL);
            sysSensory.add(eyeR);

            atlasGroup.position.y = -0.5;
            scene.add(atlasGroup);

            // ==========================================
            // UI TOGGLES
            // ==========================================
            const toggles = [
                'skeletal', 'muscular', 'cardio', 'digestive', 'endocrine', 
                'nervous', 'respiratory', 'immune', 'urinary', 'repro_f', 
                'repro_m', 'skin', 'sensory'
            ];
            toggles.forEach(id => {{
                const el = document.getElementById('t-' + id);
                if(el) {{
                    el.addEventListener('change', (e) => {{ layers[id].visible = e.target.checked; }});
                }}
            }});

            // ==========================================
            // RAYCASTING
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
                
                if(tooltip.style.display === 'block') {{
                    tooltip.style.left = (event.clientX - rect.left) + 'px';
                    tooltip.style.top = (event.clientY - rect.top) + 'px';
                }}
            }});
            
            container.addEventListener('click', () => {{
                raycaster.setFromCamera(mouse, camera);
                const intersects = raycaster.intersectObjects(atlasGroup.children, true);
                
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
                        
                        document.getElementById('tooltip-title').innerText = object.userData.name;
                        document.getElementById('tooltip-desc').innerText = object.userData.desc;
                        document.getElementById('tooltip-metric').innerText = object.userData.metric;
                        tooltip.style.display = 'block';
                    }}
                }}
            }});

            // ==========================================
            // ANIMATION
            // ==========================================
            let time = 0;
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                time += 0.016;
                
                // Cardiovascular Pulse
                if (layers['cardio'].visible) {{
                    const pulseRate = bioData.heartRate / 60;
                    const pulse = (Math.sin(time * Math.PI * 2 * pulseRate) + 1) / 2;
                    heart.scale.setScalar(1 + pulse * 0.15);
                }}
                
                // Respiratory Breathing
                if (layers['respiratory'].visible) {{
                    const breathRate = bioData.condition === "Acute Infection" ? 3 : 1; // Faster breathing if sick
                    const breath = (Math.sin(time * breathRate) + 1) / 2;
                    lungL.scale.setScalar(0.9 + breath * 0.15);
                    lungL.scale.y = 1.8;
                    lungR.scale.setScalar(0.9 + breath * 0.15);
                    lungR.scale.y = 1.8;
                }}
                
                // Nervous Jitter (Stress)
                if (layers['nervous'].visible && bioData.condition === "Chronic Stress") {{
                    brain.position.x = (Math.random() - 0.5) * 0.03;
                }}

                renderer.render(scene, camera);
            }}
            animate();

            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=770)
