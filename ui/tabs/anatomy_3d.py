import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from ui.utils import find_df_by_keyword

def render_anatomy_3d(dark_mode: bool, normalized_data: dict) -> None:
    st.markdown("## 🧬 3D Biometric Hologram")
    st.markdown("A premium, real-time spatial projection of physiological data using advanced WebGL post-processing.")
    
    col1, col2 = st.columns([2, 2])
    with col1:
        st.info("💡 **Holographic Atlas Controls:** Toggle systems via the glass panel. Left-click and drag to rotate. Scroll to zoom. Click glowing nodes to inspect real-time biometrics.")
    with col2:
        sim_condition = st.selectbox(
            "Simulate Condition",
            ["Healthy", "Metabolic Syndrome", "Chronic Stress", "Acute Infection"]
        )
        avatar_url = st.text_input("🔗 Custom Avatar GLB URL (Optional)", placeholder="https://models.readyplayer.me/YOUR_ID.glb", value="")

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
        "condition": sim_condition,
        "avatarUrl": avatar_url
    }
    
    bio_json_safe = json.dumps(bio_context).replace("<", "\\u003c")
    
    # Generate HTML Payload with Three.js, EffectComposer, CSS2DRenderer, UnrealBloom, and GLTFLoader
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; font-family: 'Outfit', sans-serif; user-select: none; }}
            #canvas-container {{ width: 100%; height: 800px; position: relative; background: radial-gradient(circle at 50% 50%, { "#1a0f2e" if dark_mode else "#e2e8f0" }, { "#05020a" if dark_mode else "#cbd5e1" }); border-radius: 16px; overflow: hidden; box-shadow: inset 0 0 100px rgba(0,0,0,0.5); }}
            
            /* Premium Glassmorphism UI */
            .glass-panel {{
                position: absolute;
                background: { "rgba(10, 5, 20, 0.65)" if dark_mode else "rgba(255, 255, 255, 0.75)" };
                border: 1px solid { "rgba(0, 240, 255, 0.2)" if dark_mode else "rgba(15, 23, 42, 0.1)" };
                color: { "#f8fafc" if dark_mode else "#0f172a" };
                backdrop-filter: blur(24px);
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.4);
                transition: all 0.3s ease;
            }}
            
            /* Layer Controls Sidebar */
            #layer-controls {{
                top: 24px;
                left: 24px;
                width: 250px;
                padding: 20px;
                z-index: 10;
                max-height: 700px;
                overflow-y: auto;
            }}
            
            /* Custom Scrollbar */
            #layer-controls::-webkit-scrollbar {{ width: 4px; }}
            #layer-controls::-webkit-scrollbar-track {{ background: transparent; }}
            #layer-controls::-webkit-scrollbar-thumb {{ background: rgba(0, 240, 255, 0.3); border-radius: 2px; }}

            .panel-title {{
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.2em;
                color: { "#00f0ff" if dark_mode else "#0d9488" };
                font-weight: 800;
                margin-bottom: 20px;
                border-bottom: 1px solid rgba(0,240,255,0.2);
                padding-bottom: 10px;
            }}
            
            /* Toggle Switches */
            .toggle-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                font-size: 12px;
                font-weight: 600;
                cursor: pointer;
                letter-spacing: 0.05em;
            }}
            .toggle-row:hover {{ color: { "#ff1e56" if dark_mode else "#3b82f6" }; text-shadow: 0 0 8px rgba(255, 30, 86, 0.5); }}
            .switch {{
                position: relative;
                display: inline-block;
                width: 32px;
                height: 18px;
            }}
            .switch input {{ opacity: 0; width: 0; height: 0; }}
            .slider {{
                position: absolute;
                cursor: pointer;
                top: 0; left: 0; right: 0; bottom: 0;
                background-color: rgba(100,100,100,0.3);
                transition: .4s;
                border-radius: 34px;
            }}
            .slider:before {{
                position: absolute;
                content: "";
                height: 12px;
                width: 12px;
                left: 3px;
                bottom: 3px;
                background-color: #fff;
                transition: .4s;
                border-radius: 50%;
                box-shadow: 0 0 5px rgba(255,255,255,0.8);
            }}
            input:checked + .slider {{ background-color: { "#00f0ff" if dark_mode else "#10b981" }; box-shadow: 0 0 10px rgba(0,240,255,0.4); }}
            input:checked + .slider:before {{ transform: translateX(14px); }}

            /* CSS2D Floating Label */
            .spatial-label {{
                background: { "rgba(10, 5, 20, 0.85)" if dark_mode else "rgba(255, 255, 255, 0.95)" };
                border: 1px solid { "#ff1e56" if dark_mode else "#3b82f6" };
                backdrop-filter: blur(10px);
                padding: 12px 16px;
                border-radius: 8px;
                color: { "#fff" if dark_mode else "#000" };
                font-size: 12px;
                pointer-events: none;
                opacity: 0;
                transition: opacity 0.3s ease;
                box-shadow: 0 4px 20px rgba(255, 30, 86, 0.3);
                margin-top: -30px;
                min-width: 150px;
            }}
            .spatial-label.visible {{ opacity: 1; }}
            .label-title {{ color: { "#ff1e56" if dark_mode else "#3b82f6" }; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; font-size: 13px; margin-bottom: 4px; }}
            .label-metric {{ font-size: 16px; font-weight: 700; margin-top: 6px; color: { "#00f0ff" if dark_mode else "#10b981" }; text-shadow: 0 0 5px rgba(0,240,255,0.5); }}
            
            /* Connector Line */
            .label-connector {{
                position: absolute;
                bottom: -20px;
                left: 50%;
                width: 1px;
                height: 20px;
                background: { "#ff1e56" if dark_mode else "#3b82f6" };
                box-shadow: 0 0 5px { "#ff1e56" if dark_mode else "#3b82f6" };
            }}

            #condition-banner {{
                position: absolute;
                top: 24px;
                right: 24px;
                padding: 12px 24px;
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.15em;
                text-transform: uppercase;
                border-left: 4px solid #ff1e56;
                display: none;
                z-index: 10;
            }}
            .condition-active {{ display: block !important; animation: pulse-banner 2s infinite; }}
            @keyframes pulse-banner {{
                0% {{ box-shadow: 0 0 0 0 rgba(255, 30, 86, 0.4); }}
                70% {{ box-shadow: 0 0 0 15px rgba(255, 30, 86, 0); }}
                100% {{ box-shadow: 0 0 0 0 rgba(255, 30, 86, 0); }}
            }}
            
            #loading-overlay {{
                position: absolute;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                color: #00f0ff;
                font-weight: bold;
                letter-spacing: 0.1em;
                z-index: 100;
                transition: opacity 0.5s ease;
            }}
        </style>
        
        <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/renderers/CSS2DRenderer.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
        
        <!-- Post-Processing -->
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/EffectComposer.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/RenderPass.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/ShaderPass.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/CopyShader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/LuminosityHighPassShader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/UnrealBloomPass.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/FilmPass.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <div id="loading-overlay">Initializing Hologram Avatar...</div>
            <!-- UI Sidebar -->
            <div id="layer-controls" class="glass-panel">
                <div class="panel-title">Holographic Layers</div>
                
                <label class="toggle-row">Integumentary (Skin) <div class="switch"><input type="checkbox" id="t-skin" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Skeletal <div class="switch"><input type="checkbox" id="t-skeletal" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Muscular <div class="switch"><input type="checkbox" id="t-muscular"><span class="slider"></span></div></label>
                <label class="toggle-row">Cardiovascular <div class="switch"><input type="checkbox" id="t-cardio" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Digestive <div class="switch"><input type="checkbox" id="t-digestive" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Endocrine <div class="switch"><input type="checkbox" id="t-endocrine" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Nervous <div class="switch"><input type="checkbox" id="t-nervous" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Respiratory <div class="switch"><input type="checkbox" id="t-respiratory" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Immune/Lymph <div class="switch"><input type="checkbox" id="t-immune" checked><span class="slider"></span></div></label>
                <label class="toggle-row">Urinary <div class="switch"><input type="checkbox" id="t-urinary"><span class="slider"></span></div></label>
                <label class="toggle-row">Sensory <div class="switch"><input type="checkbox" id="t-sensory" checked><span class="slider"></span></div></label>
            </div>

            <!-- Anomaly Banner -->
            <div id="condition-banner" class="glass-panel"></div>
        </div>

        <script>
            const bioData = {bio_json_safe};
            const isDark = bioData.darkMode;
            
            if (bioData.condition !== "Healthy") {{
                const b = document.getElementById("condition-banner");
                b.innerText = "SIMULATING: " + bioData.condition;
                b.classList.add("condition-active");
            }}
            
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            
            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.set(0, 1, 9);

            const renderer = new THREE.WebGLRenderer({{ alpha: true, antialias: true, powerPreference: "high-performance" }});
            renderer.setSize(container.clientWidth, container.clientHeight);
            renderer.setPixelRatio(window.devicePixelRatio);
            // Enable Tone Mapping for Bloom
            renderer.toneMapping = THREE.ReinhardToneMapping;
            container.appendChild(renderer.domElement);

            // CSS2D Renderer for Floating Labels
            const labelRenderer = new THREE.CSS2DRenderer();
            labelRenderer.setSize(container.clientWidth, container.clientHeight);
            labelRenderer.domElement.style.position = 'absolute';
            labelRenderer.domElement.style.top = '0px';
            labelRenderer.domElement.style.pointerEvents = 'none';
            container.appendChild(labelRenderer.domElement);

            const controls = new THREE.OrbitControls(camera, renderer.domElement);
            controls.enableDamping = true;
            controls.dampingFactor = 0.05;
            controls.target.set(0, 0.5, 0);
            controls.maxDistance = 15;
            controls.minDistance = 2;

            const ambient = new THREE.AmbientLight(0xffffff, isDark ? 0.2 : 0.6);
            scene.add(ambient);
            const dirLight = new THREE.DirectionalLight(0xffffff, 1.5);
            dirLight.position.set(5, 5, 5);
            scene.add(dirLight);

            // POST-PROCESSING: Bloom & Film
            const renderScene = new THREE.RenderPass(scene, camera);
            const bloomPass = new THREE.UnrealBloomPass(new THREE.Vector2(container.clientWidth, container.clientHeight), 1.5, 0.4, 0.85);
            bloomPass.threshold = 0;
            bloomPass.strength = isDark ? 1.8 : 0.8;
            bloomPass.radius = 0.5;

            const filmPass = new THREE.FilmPass(
                0.35,   // noise intensity
                0.025,  // scanline intensity
                648,    // scanline count
                false   // grayscale
            );

            const composer = new THREE.EffectComposer(renderer);
            composer.addPass(renderScene);
            composer.addPass(bloomPass);
            composer.addPass(filmPass);

            // ==========================================
            // HIGH-END SHADER MATERIALS
            // ==========================================
            const matBone = new THREE.MeshStandardMaterial({{ color: 0xcccccc, metalness: 0.8, roughness: 0.2, transparent: true, opacity: 0.3 }});
            const matMuscle = new THREE.MeshStandardMaterial({{ color: 0xff0033, wireframe: true, transparent: true, opacity: 0.15 }});
            const matHeart = new THREE.MeshStandardMaterial({{ color: 0xff0000, emissive: 0xff1e56, emissiveIntensity: 2.0, transparent: true, opacity: 0.9 }});
            const matBrain = new THREE.MeshStandardMaterial({{ color: 0x0088ff, emissive: 0x00f0ff, emissiveIntensity: 1.5, transparent: true, opacity: 0.85 }});
            const matDigestive = new THREE.MeshStandardMaterial({{ color: 0x00ff00, emissive: 0x22cc22, emissiveIntensity: 0.5, transparent: true, opacity: 0.4, wireframe: true }});
            const matLungs = new THREE.MeshStandardMaterial({{ color: 0x00aaff, emissive: 0x0088ff, emissiveIntensity: 0.8, transparent: true, opacity: 0.3 }});
            const matEndocrine = new THREE.MeshStandardMaterial({{ color: 0xff00ff, emissive: 0xcc00ff, emissiveIntensity: 2.0 }});
            const matLymph = new THREE.MeshStandardMaterial({{ color: 0x00ff88, emissive: 0x00ff88, emissiveIntensity: 1.0, wireframe: true, transparent: true, opacity: 0.2 }});
            const matUro = new THREE.MeshStandardMaterial({{ color: 0xffff00, emissive: 0xaaaa00, emissiveIntensity: 1.0, transparent: true, opacity: 0.6 }});
            
            // Holographic Skin Material (For GLB)
            const matSkinHolo = new THREE.MeshStandardMaterial({{ 
                color: 0x00f0ff, 
                emissive: 0x0055ff, 
                emissiveIntensity: 0.2, 
                transparent: true, 
                opacity: 0.15,
                wireframe: true,
                blending: THREE.AdditiveBlending
            }});
            
            // Condition Overrides
            if (bioData.condition === "Metabolic Syndrome") {{
                matEndocrine.emissive.setHex(0xffaa00);
                matEndocrine.emissiveIntensity = 4.0;
                matHeart.emissive.setHex(0xff5500);
                matHeart.emissiveIntensity = 3.0;
                matSkinHolo.color.setHex(0xffaa00);
                matSkinHolo.emissive.setHex(0x553300);
            }} else if (bioData.condition === "Chronic Stress") {{
                matBrain.emissive.setHex(0xff8800);
                matBrain.emissiveIntensity = 4.0;
                matEndocrine.emissive.setHex(0xff0000); 
                matEndocrine.emissiveIntensity = 5.0;
                filmPass.uniforms.nIntensity.value = 1.2; // Lots of static
            }} else if (bioData.condition === "Acute Infection") {{
                matLungs.emissive.setHex(0xff0000);
                matLungs.emissiveIntensity = 3.0;
                matLymph.emissive.setHex(0xffaa00);
                matLymph.emissiveIntensity = 2.0;
                matSkinHolo.color.setHex(0xff1e56);
                matSkinHolo.emissive.setHex(0x550011);
                matSkinHolo.opacity = 0.25;
            }}

            const atlasGroup = new THREE.Group();
            const layers = {{}};
            function createLayer(name) {{
                const group = new THREE.Group();
                group.name = name;
                layers[name] = group;
                atlasGroup.add(group);
                return group;
            }}

            // SKELETAL
            const sysSkel = createLayer('skeletal');
            const skull = new THREE.Mesh(new THREE.SphereGeometry(0.8, 16, 16), matBone);
            skull.position.y = 3.2;
            skull.userData = {{ name: "Cranium", desc: "Osteo structure.", metric: "Density Normal" }};
            sysSkel.add(skull);
            for(let i=0; i<15; i++) {{
                const vert = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.2, 8), matBone);
                vert.position.set(0, 2.0 - (i * 0.22), -0.3);
                sysSkel.add(vert);
            }}
            for(let i=0; i<10; i++) {{
                const rib = new THREE.Mesh(new THREE.TorusGeometry(0.7 + (Math.sin(i/10*Math.PI)*0.3), 0.04, 8, 32, Math.PI), matBone);
                rib.position.set(0, 1.8 - (i * 0.2), -0.3);
                rib.rotation.x = -Math.PI / 2 + 0.1;
                sysSkel.add(rib);
            }}

            // CARDIOVASCULAR
            const sysCardio = createLayer('cardio');
            const heart = new THREE.Mesh(new THREE.IcosahedronGeometry(0.35, 2), matHeart);
            heart.position.set(-0.25, 1.3, 0.3);
            heart.userData = {{ name: "Myocardium", desc: "Central pump.", metric: bioData.heartRate + " BPM" }};
            sysCardio.add(heart);
            const aorta = new THREE.Mesh(new THREE.TorusGeometry(0.2, 0.05, 8, 16, Math.PI), matHeart);
            aorta.position.set(-0.1, 1.6, 0.3);
            sysCardio.add(aorta);

            // DIGESTIVE
            const sysDigestive = createLayer('digestive');
            const stomach = new THREE.Mesh(new THREE.SphereGeometry(0.35, 16, 16), matDigestive);
            stomach.scale.set(1.5, 1, 1);
            stomach.position.set(-0.3, 0.2, 0.3);
            stomach.userData = {{ name: "Stomach", desc: "Gastric process.", metric: "Active" }};
            sysDigestive.add(stomach);
            const intestines = new THREE.Mesh(new THREE.TorusKnotGeometry(0.4, 0.1, 100, 16, 3, 4), matDigestive);
            intestines.position.set(0, -0.6, 0.2);
            sysDigestive.add(intestines);

            // ENDOCRINE
            const sysEndo = createLayer('endocrine');
            const pancreas = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.5, 8), matEndocrine);
            pancreas.rotation.z = Math.PI / 2;
            pancreas.position.set(0, 0.0, 0.2);
            pancreas.userData = {{ name: "Pancreas", desc: "Insulin Regulation.", metric: bioData.condition==="Metabolic Syndrome"?"Insulin Resistant!":"Nominal" }};
            sysEndo.add(pancreas);
            const adrenalL = new THREE.Mesh(new THREE.IcosahedronGeometry(0.08, 0), matEndocrine);
            adrenalL.position.set(-0.35, -0.1, -0.15);
            adrenalL.userData = {{ name: "Adrenals", desc: "Cortisol production.", metric: bioData.condition==="Chronic Stress"?"Cortisol Spike!":"Normal" }};
            sysEndo.add(adrenalL);

            // NERVOUS
            const sysNervous = createLayer('nervous');
            const brain = new THREE.Mesh(new THREE.IcosahedronGeometry(0.65, 3), matBrain);
            brain.position.set(0, 3.2, 0);
            brain.userData = {{ name: "Cerebral Cortex", desc: "Central Nervous System.", metric: bioData.sleepEfficiency + "% Sleep Recovery" }};
            sysNervous.add(brain);
            const spineCord = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 4, 8), matBrain);
            spineCord.position.set(0, 1.0, -0.3);
            sysNervous.add(spineCord);

            // RESPIRATORY
            const sysResp = createLayer('respiratory');
            const lungL = new THREE.Mesh(new THREE.SphereGeometry(0.4, 16, 16), matLungs);
            lungL.scale.set(1, 2.0, 1);
            lungL.position.set(-0.5, 1.4, 0);
            lungL.userData = {{ name: "Left Lung", desc: "Gas exchange.", metric: bioData.condition==="Acute Infection"?"SpO2 88%":"SpO2 99%" }};
            const lungR = lungL.clone();
            lungR.position.set(0.5, 1.4, 0);
            sysResp.add(lungL);
            sysResp.add(lungR);

            // IMMUNE / LYMPH
            const sysImmune = createLayer('immune');
            const lymph = new THREE.Mesh(new THREE.TorusKnotGeometry(1.0, 0.03, 100, 8, 4, 7), matLymph);
            lymph.position.y = 1.0;
            lymph.userData = {{ name: "Lymphatic Nodes", desc: "Immune defense.", metric: "Active" }};
            sysImmune.add(lymph);

            // URINARY
            const sysUro = createLayer('urinary');
            const kidL = new THREE.Mesh(new THREE.SphereGeometry(0.2, 16, 16), matUro);
            kidL.scale.set(1, 1.5, 1);
            kidL.position.set(-0.4, -0.2, -0.2);
            kidL.userData = {{ name: "Kidney", desc: "Filtration.", metric: "GFR Normal" }};
            sysUro.add(kidL);
            sysUro.visible = false;

            // SENSORY
            const sysSensory = createLayer('sensory');
            const eyeL = new THREE.Mesh(new THREE.SphereGeometry(0.1), new THREE.MeshStandardMaterial({{color:0xffffff, emissive:0xffffff, emissiveIntensity:2}}));
            eyeL.position.set(-0.3, 3.3, 0.6);
            sysSensory.add(eyeL);
            const eyeR = eyeL.clone();
            eyeR.position.set(0.3, 3.3, 0.6);
            sysSensory.add(eyeR);

            atlasGroup.position.y = -1.5;
            scene.add(atlasGroup);

            // ==========================================
            // GLB AVATAR (SKIN LAYER)
            // ==========================================
            const sysSkin = createLayer('skin');
            const gltfLoader = new THREE.GLTFLoader();
            // Default generic human avatar from Three.js examples if none provided
            const avatarUrl = bioData.avatarUrl || "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb";
            
            let avatarModel = null;
            let avatarMixer = null;

            gltfLoader.load(avatarUrl, (gltf) => {{
                avatarModel = gltf.scene;
                
                // Scale depending on the model (Soldier is usually scale 1.5 approx to fit our skeleton)
                // We will adjust based on whether it looks like a ready player me or soldier
                if (avatarUrl.includes("readyplayer.me")) {{
                    avatarModel.scale.set(3, 3, 3);
                    avatarModel.position.y = 0.5; // Align with skeleton
                }} else {{
                    avatarModel.scale.set(2.2, 2.2, 2.2);
                    avatarModel.position.y = 0;
                }}
                
                // Apply Data-Driven Morphs
                // If weight/condition implies larger mass, scale X and Z
                if (bioData.condition === "Metabolic Syndrome") {{
                    avatarModel.scale.x *= 1.2;
                    avatarModel.scale.z *= 1.2;
                }}
                // If sleep is poor, simulate slouching (tilting model forward slightly)
                if (bioData.sleepEfficiency < 60) {{
                    avatarModel.rotation.x = 0.15;
                }}

                avatarModel.traverse((child) => {{
                    if (child.isMesh) {{
                        child.material = matSkinHolo;
                        // Keep a reference to original data if needed, or set userData for HUD
                        child.userData = {{ name: "Integumentary System", desc: "Avatar Skin Shell", metric: "Active" }};
                    }}
                }});

                // Play animation if available (Soldier has animations)
                if (gltf.animations && gltf.animations.length > 0) {{
                    avatarMixer = new THREE.AnimationMixer(avatarModel);
                    // Usually the first animation is an Idle/Walk
                    const action = avatarMixer.clipAction(gltf.animations[0]);
                    action.play();
                }}

                sysSkin.add(avatarModel);
                
                // Hide loader
                const overlay = document.getElementById("loading-overlay");
                overlay.style.opacity = "0";
                setTimeout(() => overlay.remove(), 500);

            }}, undefined, (error) => {{
                console.error("Error loading GLB avatar:", error);
                document.getElementById("loading-overlay").innerText = "Failed to load Avatar GLB";
            }});


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
            // CSS2D SPATIAL LABELS
            // ==========================================
            const labelDiv = document.createElement('div');
            labelDiv.className = 'spatial-label';
            labelDiv.innerHTML = `
                <div class="label-title" id="lbl-title">Organ</div>
                <div id="lbl-desc" style="font-size:11px; color:#94a3b8">Desc</div>
                <div class="label-metric" id="lbl-metric">--</div>
                <div class="label-connector"></div>
            `;
            const spatialLabel = new THREE.CSS2DObject(labelDiv);
            spatialLabel.position.set(0, 0, 0);
            scene.add(spatialLabel);

            // ==========================================
            // RAYCASTING
            // ==========================================
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            let hoveredMesh = null;
            let originalEmissiveInt = 0;

            container.addEventListener('pointermove', (event) => {{
                const rect = container.getBoundingClientRect();
                mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
            }});
            
            container.addEventListener('click', () => {{
                raycaster.setFromCamera(mouse, camera);
                // Intersect only meshes in the atlasGroup
                const interactables = [];
                atlasGroup.traverse((child) => {{
                    if (child.isMesh && child.visible && child.parent && child.parent.visible) interactables.push(child);
                }});

                const intersects = raycaster.intersectObjects(interactables, false);
                
                if (hoveredMesh) {{
                    if(hoveredMesh.material) {{
                        hoveredMesh.material.emissiveIntensity = originalEmissiveInt;
                    }}
                    hoveredMesh = null;
                    labelDiv.classList.remove('visible');
                }}

                if (intersects.length > 0) {{
                    const object = intersects[0].object;
                    if (object.userData && object.userData.name) {{
                        hoveredMesh = object;
                        if(object.material) {{
                            originalEmissiveInt = object.material.emissiveIntensity || 0;
                            object.material.emissiveIntensity = 5.0; // Huge bloom burst on click
                        }}
                        
                        document.getElementById('lbl-title').innerText = object.userData.name;
                        document.getElementById('lbl-desc').innerText = object.userData.desc;
                        document.getElementById('lbl-metric').innerText = object.userData.metric;
                        
                        // Attach label to the clicked object's world position
                        const worldPos = new THREE.Vector3();
                        object.getWorldPosition(worldPos);
                        worldPos.y += 0.5; // Offset above the organ
                        spatialLabel.position.copy(worldPos);
                        labelDiv.classList.add('visible');
                    }}
                }}
            }});

            // ==========================================
            // ANIMATION
            // ==========================================
            const clock = new THREE.Clock();
            function animate() {{
                requestAnimationFrame(animate);
                controls.update();
                const time = clock.getElapsedTime();
                const delta = clock.getDelta();
                
                if (avatarMixer) avatarMixer.update(delta * 2); // Slight speed adjustment
                
                // Cardiovascular Pulse
                if (layers['cardio'].visible) {{
                    const pulseRate = bioData.heartRate / 60;
                    const pulse = (Math.sin(time * Math.PI * 2 * pulseRate) + 1) / 2;
                    heart.scale.setScalar(1 + pulse * 0.2);
                    heart.material.emissiveIntensity = 2.0 + (pulse * 3.0);
                }}
                
                // Respiratory Breathing
                if (layers['respiratory'].visible) {{
                    const breathRate = bioData.condition === "Acute Infection" ? 3 : 1;
                    const breath = (Math.sin(time * breathRate) + 1) / 2;
                    lungL.scale.setScalar(0.9 + breath * 0.15);
                    lungL.scale.y = 2.0;
                    lungR.scale.setScalar(0.9 + breath * 0.15);
                    lungR.scale.y = 2.0;
                }}
                
                // Nervous Jitter (Stress)
                if (layers['nervous'].visible && bioData.condition === "Chronic Stress") {{
                    brain.position.x = (Math.random() - 0.5) * 0.05;
                }}

                // Render via Composer for Post-Processing
                composer.render();
                // Render CSS2D on top
                labelRenderer.render(scene, camera);
            }}
            animate();

            window.addEventListener('resize', () => {{
                camera.aspect = container.clientWidth / container.clientHeight;
                camera.updateProjectionMatrix();
                renderer.setSize(container.clientWidth, container.clientHeight);
                labelRenderer.setSize(container.clientWidth, container.clientHeight);
                composer.setSize(container.clientWidth, container.clientHeight);
            }});
        </script>
    </body>
    </html>
    """
    
    components.html(html_code, height=820)
