import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from ui.utils import find_df_by_keyword

def render_anatomy_3d(dark_mode: bool, normalized_data: dict) -> None:
    st.markdown("## 🧬 3D Biometric Hologram")
    st.markdown("A premium, real-time spatial projection of physiological data using advanced WebGL post-processing.")
    
    DEMO_AVATARS = {
        "Healthy Baseline": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb",
        "Michael (Homeless / Family Separation)": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb",
        "Elena (Trauma Survivor)": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb",
        "Rebecca (Birth Trauma / PTSD)": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb",
        "Margaret (Elder Abuse / Neglect)": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb",
        "Robert (Elder Neglect)": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb",
        "Jordan (NDIS Exploitation)": "https://raw.githubusercontent.com/mrdoob/three.js/master/examples/models/gltf/Soldier.glb"
    }

    col1, col2 = st.columns([2, 2])
    with col1:
        st.info("💡 **Holographic Atlas Controls:** Toggle systems via the glass panel. Left-click and drag to rotate. Click glowing nodes to inspect real-time biometrics and trigger the deep-dive camera zoom.")
        x_ray_mode = st.checkbox("🔍 Enable Deep X-Ray Mode", value=False)
    with col2:
        sim_persona = st.selectbox(
            "Persona Simulation",
            list(DEMO_AVATARS.keys())
        )
        custom_avatar_url = st.text_input("🔗 Custom Avatar GLB URL (Optional)", placeholder="https://models.readyplayer.me/YOUR_ID.glb", value="")
        avatar_url = custom_avatar_url if custom_avatar_url.strip() != "" else DEMO_AVATARS[sim_persona]

    timeline_week = st.select_slider(
        "⏳ Hologram Timeline Scrubber",
        options=["Week 1 (Crisis)", "Week 2 (Stabilisation)", "Week 3 (Recovery)", "Week 4 (Baseline)"],
        value="Week 1 (Crisis)"
    )

    is_sanctuary = st.session_state.get("sanctuary_mode", False)

    # Default Biometrics & Maslow Scores (1-100)
    # [Physiological, Safety, Belonging, Esteem, Self-Actualization]
    maslow_scores = [95, 90, 85, 80, 75]
    avg_hr = 70
    sleep_eff = 85
    stress_score = 40
    trauma_target = "none"

    if sim_persona == "Margaret (Elder Abuse / Neglect)":
        maslow_scores = [40, 20, 60, 50, 40]
        avg_hr = 95
        sleep_eff = 45
        stress_score = 88
        trauma_target = "systemic_frailty"
    elif sim_persona == "Rebecca (Birth Trauma / PTSD)":
        maslow_scores = [85, 40, 70, 60, 50]
        avg_hr = 105
        sleep_eff = 55
        stress_score = 92
        trauma_target = "pelvic_trauma"
    elif sim_persona == "Jordan (NDIS Exploitation)":
        maslow_scores = [70, 30, 40, 40, 30]
        avg_hr = 88
        sleep_eff = 60
        stress_score = 85
        trauma_target = "financial_stress"
    elif sim_persona == "Michael (Homeless / Family Separation)":
        maslow_scores = [20, 10, 20, 30, 10]
        avg_hr = 90
        sleep_eff = 30
        stress_score = 95
        trauma_target = "exposure"
    elif sim_persona == "Elena (Trauma Survivor)":
        maslow_scores = [60, 30, 50, 40, 40]
        avg_hr = 100
        sleep_eff = 40
        stress_score = 90
        trauma_target = "hypervigilance"
    elif sim_persona == "Robert (Elder Neglect)":
        maslow_scores = [35, 25, 40, 30, 20]
        avg_hr = 110
        sleep_eff = 35
        stress_score = 85
        trauma_target = "systemic_frailty"

    # Apply Timeline Modifiers (Heal/Degrade based on scrubber)
    if "Week 2" in timeline_week and sim_persona != "Healthy Baseline":
        maslow_scores = [min(100, s + 10) for s in maslow_scores]
        avg_hr = max(75, avg_hr - 5)
        sleep_eff = min(100, sleep_eff + 10)
        stress_score = max(45, stress_score - 10)
    elif "Week 3" in timeline_week and sim_persona != "Healthy Baseline":
        maslow_scores = [min(100, s + 20) for s in maslow_scores]
        avg_hr = max(72, avg_hr - 15)
        sleep_eff = min(100, sleep_eff + 20)
        stress_score = max(42, stress_score - 30)
        # Week 3 removes severe trauma visual modifiers
        trauma_target = "none"
    elif "Week 4" in timeline_week and sim_persona != "Healthy Baseline":
        maslow_scores = [90, 85, 80, 75, 70]
        avg_hr = 70
        sleep_eff = 85
        stress_score = 40
        trauma_target = "none"

    bio_context = {
        "heartRate": avg_hr,
        "sleepEfficiency": sleep_eff,
        "stress": stress_score,
        "maslow": maslow_scores,
        "darkMode": dark_mode,
        "persona": sim_persona,
        "trauma": trauma_target,
        "avatarUrl": avatar_url,
        "xRay": x_ray_mode,
        "isSanctuary": is_sanctuary
    }
    
    bio_json_safe = json.dumps(bio_context).replace("<", "\\u003c")
    
    # Generate HTML Payload with Three.js, EffectComposer, CSS2DRenderer, UnrealBloom, GLTFLoader, and GSAP
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
            
            #sanctuary-banner {{
                position: absolute;
                bottom: 24px;
                left: 24px;
                padding: 10px 20px;
                font-size: 11px;
                font-weight: 700;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                border: 1px solid #10b981;
                background: rgba(16, 185, 129, 0.1);
                color: #10b981;
                border-radius: 8px;
                display: none;
                z-index: 10;
                box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
            }}

            #btn-reset-cam {{
                position: absolute;
                bottom: 24px;
                right: 24px;
                padding: 10px 20px;
                background: rgba(0, 240, 255, 0.1);
                border: 1px solid #00f0ff;
                color: #00f0ff;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                z-index: 10;
                transition: all 0.3s ease;
                display: none;
            }}
            #btn-reset-cam:hover {{ background: rgba(0, 240, 255, 0.3); box-shadow: 0 0 15px rgba(0, 240, 255, 0.4); }}
            
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
        <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
        
        <!-- Post-Processing -->
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/EffectComposer.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/RenderPass.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/ShaderPass.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/CopyShader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/LuminosityHighPassShader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/UnrealBloomPass.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/shaders/FilmShader.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/postprocessing/FilmPass.js"></script>
    </head>
    <body>
        <div id="canvas-container">
            <div id="loading-overlay">Initializing Hologram Avatar...</div>
            <!-- UI Sidebar -->
            <div id="layer-controls" class="glass-panel">
                <div class="panel-title">Holographic Layers</div>
                
                <label class="toggle-row">Maslow Rings <div class="switch"><input type="checkbox" id="t-maslow" checked><span class="slider"></span></div></label>
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
            
            <!-- Sanctuary Banner -->
            <div id="sanctuary-banner" class="glass-panel">🔒 Sanctuary Mode Active: E2E Encrypted</div>
            
            <!-- Reset Camera -->
            <button id="btn-reset-cam" class="glass-panel">Reset View</button>
        </div>

        <script>
            const bioData = {bio_json_safe};
            const isDark = bioData.darkMode;
            
            if (bioData.persona !== "Healthy Baseline") {{
                const b = document.getElementById("condition-banner");
                b.innerText = "SIMULATING: " + bioData.persona;
                b.classList.add("condition-active");
            }}
            
            if (bioData.isSanctuary) {{
                document.getElementById("sanctuary-banner").style.display = "block";
            }}
            
            const container = document.getElementById('canvas-container');
            const scene = new THREE.Scene();
            
            const defaultCameraPos = new THREE.Vector3(0, 1.5, 10);
            const defaultControlsTarget = new THREE.Vector3(0, 0.5, 0);

            const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
            camera.position.copy(defaultCameraPos);

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
            controls.target.copy(defaultControlsTarget);
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
            bloomPass.strength = isDark ? 1.0 : 0.6; // Reduced to prevent blow-out
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
            const matBone = new THREE.MeshStandardMaterial({{ color: 0x00ffff, emissive: 0x00aaff, emissiveIntensity: 1.5, transparent: true, opacity: 0.8, wireframe: true }});
            const matMuscle = new THREE.MeshStandardMaterial({{ color: 0xff0033, emissive: 0x880022, emissiveIntensity: 0.5, wireframe: true, transparent: true, opacity: 0.15 }});
            const matHeart = new THREE.MeshStandardMaterial({{ color: 0x880000, emissive: 0xff0000, emissiveIntensity: 3.0, transparent: true, opacity: 0.95 }});
            const matBrain = new THREE.MeshStandardMaterial({{ color: 0x4400ff, emissive: 0x8800ff, emissiveIntensity: 2.5, transparent: true, opacity: 0.9 }});
            const matDigestive = new THREE.MeshStandardMaterial({{ color: 0x00ff00, emissive: 0x22cc22, emissiveIntensity: 1.0, transparent: true, opacity: 0.5, wireframe: true }});
            const matLungs = new THREE.MeshStandardMaterial({{ color: 0x00aaff, emissive: 0x0088ff, emissiveIntensity: 1.2, transparent: true, opacity: 0.4 }});
            const matEndocrine = new THREE.MeshStandardMaterial({{ color: 0xff00ff, emissive: 0xcc00ff, emissiveIntensity: 2.5, transparent: true, opacity: 0.8 }});
            const matLymph = new THREE.MeshStandardMaterial({{ color: 0x00ff88, emissive: 0x00ff88, emissiveIntensity: 1.5, wireframe: true, transparent: true, opacity: 0.3 }});
            const matUro = new THREE.MeshStandardMaterial({{ color: 0xffff00, emissive: 0xaaaa00, emissiveIntensity: 1.5, transparent: true, opacity: 0.7 }});
            
            // ==========================================
            // HOLOGRAPHIC SHADER (GLSL)
            // ==========================================
            const holographicVertexShader = `
                varying vec3 vNormal;
                varying vec3 vViewPosition;
                varying vec2 vUv;

                uniform float uTime;
                uniform float uGlitchIntensity;

                void main() {{
                  vNormal = normalize(normalMatrix * normal);
                  vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                  vViewPosition = -mvPosition.xyz;
                  vUv = uv;

                  vec3 pos = position;
                  // Very subtle breathing / holographic flicker
                  pos += normal * sin(uTime * 6.0) * 0.0015 * uGlitchIntensity;

                  gl_Position = projectionMatrix * mvPosition;
                }}
            `;

            const holographicFragmentShader = `
                varying vec3 vNormal;
                varying vec3 vViewPosition;
                varying vec2 vUv;

                uniform float uTime;
                uniform float uOpacity;
                uniform vec3 uBaseColor;
                uniform vec3 uStressColor;
                uniform float uStressLevel;
                uniform float uWellbeingScore;
                uniform float uRimPower;

                void main() {{
                  vec3 normal = normalize(vNormal);
                  vec3 viewDir = normalize(vViewPosition);

                  // Strong Fresnel rim (edge glow) - this is what makes it feel holographic
                  float fresnel = pow(1.0 - dot(viewDir, normal), uRimPower);

                  // Animated subtle scanlines
                  float scan = sin(vUv.y * 180.0 - uTime * 12.0) * 0.04 + 0.96;

                  // Base color with stress tint
                  vec3 color = mix(uBaseColor, uStressColor, uStressLevel * 0.75);

                  // Inner glow based on wellbeing
                  float innerGlow = uWellbeingScore * 1.4 + 0.6;

                  vec3 finalColor = color * (fresnel * 2.2 + innerGlow);
                  finalColor *= scan;

                  float alpha = uOpacity * (0.55 + fresnel * 0.9);

                  gl_FragColor = vec4(finalColor, alpha);
                }}
            `;

            const stressLevel = bioData.stress / 100.0;
            // Calculate a wellbeing score (average of maslow)
            const wellbeing = bioData.maslow.reduce((a, b) => a + b, 0) / (bioData.maslow.length * 100.0);
            
            let baseColor = new THREE.Color(0x00f0ff);
            let stressColor = new THREE.Color(0xff1e56);
            let glitchInt = 1.0;

            const matSkinHolo = new THREE.ShaderMaterial({{
                vertexShader: holographicVertexShader,
                fragmentShader: holographicFragmentShader,
                uniforms: {{
                    uTime: {{ value: 0.0 }},
                    uOpacity: {{ value: bioData.xRay ? 0.03 : 0.25 }},
                    uBaseColor: {{ value: baseColor }},
                    uStressColor: {{ value: stressColor }},
                    uStressLevel: {{ value: stressLevel }},
                    uWellbeingScore: {{ value: wellbeing }},
                    uRimPower: {{ value: 2.0 }},
                    uGlitchIntensity: {{ value: glitchInt }}
                }},
                transparent: true,
                wireframe: false,
                blending: THREE.NormalBlending,
                side: THREE.FrontSide,
                depthWrite: false
            }});
            
            // Particles Material
            const particleColor = bioData.stress > 70 ? 0xff0033 : (bioData.sleepEfficiency < 60 ? 0xffaa00 : 0x00ff88);
            const matParticles = new THREE.PointsMaterial({{ color: particleColor, size: 0.05, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending }});

            // Condition Overrides
            if (bioData.trauma === "systemic_frailty") {{
                matHeart.emissive.setHex(0xff5500);
                matSkinHolo.uniforms.uBaseColor.value.setHex(0xffaa00);
                matSkinHolo.uniforms.uGlitchIntensity.value = 2.0;
                matBrain.emissiveIntensity = 0.5; // Dimmed cognition
            }} else if (bioData.trauma === "pelvic_trauma") {{
                matSkinHolo.uniforms.uBaseColor.value.setHex(0xff1e56);
                matSkinHolo.uniforms.uGlitchIntensity.value = 4.0;
                matBrain.emissive.setHex(0xff8800); // Hypervigilance
                matBrain.emissiveIntensity = 3.0;
                filmPass.uniforms.nIntensity.value = 1.0; 
            }} else if (bioData.trauma === "financial_stress") {{
                matEndocrine.emissive.setHex(0xff0000); // Adrenal fatigue
                matSkinHolo.uniforms.uGlitchIntensity.value = 2.5;
                matEndocrine.emissiveIntensity = 5.0;
                matHeart.emissiveIntensity = 4.0;
                filmPass.uniforms.nIntensity.value = 1.5; 
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

            // MASLOW RINGS
            const sysMaslow = createLayer('maslow');
            const maslowLabels = ["Physiological", "Safety", "Belonging", "Esteem", "Self-Actualization"];
            const maslowColors = [0xff1e56, 0xffaa00, 0xffff00, 0x00ff88, 0x00f0ff];
            const rings = [];
            
            // Vertical placement mapping: Waist, Chest, Shoulders, Head, Halo
            const heights = [0.2, 1.2, 2.2, 3.2, 4.2];
            const radii = [1.2, 1.4, 1.6, 1.0, 0.8]; 
            
            for(let i=0; i<5; i++) {{
                const score = bioData.maslow[i];
                const ringColor = score < 50 ? 0xff0000 : maslowColors[i];
                const ringOpac = score < 50 ? 0.3 : 1.0;
                const ringEmisInt = score < 50 ? 1.0 : 3.0; // High emissive for neon tube
                
                const rMat = new THREE.MeshStandardMaterial({{
                    color: ringColor,
                    emissive: ringColor,
                    emissiveIntensity: ringEmisInt,
                    transparent: true,
                    opacity: ringOpac,
                    wireframe: score < 50
                }});
                
                const rGeo = new THREE.TorusGeometry(radii[i], 0.04, 16, 100);
                const ring = new THREE.Mesh(rGeo, rMat);
                ring.rotation.x = Math.PI / 2;
                ring.position.y = heights[i];
                
                ring.userData = {{ 
                    name: `Maslow: ${{maslowLabels[i]}}`, 
                    desc: score < 50 ? "Critical Deficit Detected" : "Need Satisfied", 
                    metric: `Score: ${{score}}/100` 
                }};
                
                sysMaslow.add(ring);
                rings.push({{ mesh: ring, speed: (i+1)*0.2, dir: i%2===0?1:-1 }});
            }}

            // PARTICLES (Stress/Trauma Clouds)
            const pGeo = new THREE.BufferGeometry();
            const pCount = 800; // Dense cloud
            const pPositions = new Float32Array(pCount * 3);
            const pVelocities = []; 
            
            for(let i=0; i<pCount*3; i+=3) {{
                // Cluster around chest (y=1.5) and head (y=3.2)
                const isHead = Math.random() > 0.5;
                const r = Math.random() * (isHead ? 0.8 : 1.5);
                const theta = Math.random() * Math.PI * 2;
                const baseY = isHead ? 3.2 : 1.5;
                const y = baseY + (Math.random() * 1.5 - 0.75);
                
                pPositions[i] = r * Math.cos(theta);
                pPositions[i+1] = y;
                pPositions[i+2] = r * Math.sin(theta);
                
                // Upward drift velocity (faster for trauma/stress)
                const drift = bioData.stress > 70 ? 0.02 + Math.random()*0.03 : 0.005 + Math.random()*0.01;
                pVelocities.push({{ y: drift, r: r, theta: theta, speed: 0.2 + Math.random()*0.5 }});
            }}
            pGeo.setAttribute('position', new THREE.BufferAttribute(pPositions, 3));
            const particleSystem = new THREE.Points(pGeo, matParticles);
            particleSystem.userData = {{ velocities: pVelocities, pCount: pCount }};
            sysMaslow.add(particleSystem);


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

            // MUSCULAR
            const sysMuscular = createLayer('muscular');
            // Optional: attach a dummy mesh if desired, but just defining the layer prevents the crash
            
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
            pancreas.userData = {{ name: "Pancreas", desc: "Insulin Regulation.", metric: "Nominal" }};
            sysEndo.add(pancreas);
            const adrenalL = new THREE.Mesh(new THREE.IcosahedronGeometry(0.08, 0), matEndocrine);
            adrenalL.position.set(-0.35, -0.1, -0.15);
            adrenalL.userData = {{ name: "Adrenals", desc: "Cortisol production.", metric: bioData.stress>70?"Cortisol Spike!":"Normal" }};
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
            lungL.userData = {{ name: "Left Lung", desc: "Gas exchange.", metric: "SpO2 99%" }};
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

            // TRAUMA OVERLAYS
            if (bioData.trauma === "pelvic_trauma") {{
                const pelvicGlow = new THREE.Mesh(new THREE.SphereGeometry(0.4, 16, 16), new THREE.MeshStandardMaterial({{color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 5.0, transparent:true, opacity:0.8}}));
                pelvicGlow.position.set(0, -0.5, 0.2);
                pelvicGlow.scale.set(1.5, 0.8, 1);
                pelvicGlow.userData = {{ name: "Pelvic Floor", desc: "Severe trauma detected (Birth Complications).", metric: "Chronic Pain" }};
                sysSkel.add(pelvicGlow);
            }}

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
                
                // Scale depending on the model
                if (avatarUrl.includes("readyplayer.me")) {{
                    avatarModel.scale.set(3, 3, 3);
                    avatarModel.position.y = 0.5; // Align with skeleton
                }} else {{
                    avatarModel.scale.set(2.2, 2.2, 2.2);
                    avatarModel.position.y = 0;
                }}
                
                // Trauma Morphs
                if (bioData.trauma === "systemic_frailty") {{
                    avatarModel.scale.x *= 0.85; // Emaciated / Frail
                    avatarModel.scale.z *= 0.85;
                    avatarModel.rotation.x = 0.25; // Severe Slouch
                }} else if (bioData.trauma === "financial_stress") {{
                    avatarModel.rotation.x = 0.15; // Tense/Slouch
                }}

                avatarModel.traverse((child) => {{
                    if (child.isMesh) {{
                        child.material = matSkinHolo;
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
                'maslow', 'skeletal', 'muscular', 'cardio', 'digestive', 'endocrine', 
                'nervous', 'respiratory', 'immune', 'urinary', 'skin', 'sensory'
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
            // ORBITING HUD PANELS (Concept Art)
            // ==========================================
            function createHudPanel(title, value, metric) {{
                const div = document.createElement('div');
                div.className = 'spatial-label';
                div.style.padding = '8px 12px';
                div.style.background = 'rgba(0, 15, 25, 0.75)';
                div.style.border = '1px solid rgba(0, 240, 255, 0.4)';
                div.style.backdropFilter = 'blur(4px)';
                div.style.pointerEvents = 'none';
                div.innerHTML = `<div style="font-size:10px; color:#00f0ff; letter-spacing:1px">${{title}}</div>
                                 <div style="font-size:24px; font-weight:700; color:#fff">${{value}}</div>
                                 <div style="font-size:9px; color:#94a3b8; text-transform:uppercase">${{metric}}</div>`;
                const obj = new THREE.CSS2DObject(div);
                scene.add(obj);
                return obj;
            }}
            
            const hudStress = createHudPanel("STRESS", bioData.stress, bioData.stress > 70 ? "CRITICAL" : "NOMINAL");
            const hudSleep = createHudPanel("SLEEP", bioData.sleepEfficiency + "%", "RECOVERY RATE");
            const hudWellness = createHudPanel("WELLNESS", Math.round(wellbeing * 100) + "%", "MASLOW INDEX");

            // ==========================================
            // RAYCASTING & CAMERA ANIMATION (GSAP)
            // ==========================================
            const raycaster = new THREE.Raycaster();
            const mouse = new THREE.Vector2();
            let hoveredMesh = null;
            let originalEmissiveInt = 0;
            
            const btnResetCam = document.getElementById('btn-reset-cam');
            
            btnResetCam.addEventListener('click', () => {{
                // Animate camera back to default
                gsap.to(camera.position, {{
                    x: defaultCameraPos.x,
                    y: defaultCameraPos.y,
                    z: defaultCameraPos.z,
                    duration: 1.5,
                    ease: "power3.inOut"
                }});
                gsap.to(controls.target, {{
                    x: defaultControlsTarget.x,
                    y: defaultControlsTarget.y,
                    z: defaultControlsTarget.z,
                    duration: 1.5,
                    ease: "power3.inOut"
                }});
                btnResetCam.style.display = "none";
            }});

            container.addEventListener('pointermove', (event) => {{
                const rect = container.getBoundingClientRect();
                mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
                mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
                
                raycaster.setFromCamera(mouse, camera);
                const interactables = [];
                atlasGroup.traverse((child) => {{
                    if (child.isMesh && child.visible && child.parent && child.parent.visible && child.userData && child.userData.name) interactables.push(child);
                }});

                const intersects = raycaster.intersectObjects(interactables, false);
                
                if (intersects.length > 0) {{
                    const object = intersects[0].object;
                    if (hoveredMesh !== object) {{
                        if (hoveredMesh && hoveredMesh.material) {{
                            hoveredMesh.material.emissiveIntensity = originalEmissiveInt; // Restore old
                        }}
                        hoveredMesh = object;
                        if (object.material) {{
                            originalEmissiveInt = object.material.emissiveIntensity || 0;
                            object.material.emissiveIntensity = originalEmissiveInt * 2.0 + 1.0; // Highlight
                        }}
                        container.style.cursor = 'pointer';
                    }}
                }} else {{
                    if (hoveredMesh) {{
                        if(hoveredMesh.material) hoveredMesh.material.emissiveIntensity = originalEmissiveInt;
                        hoveredMesh = null;
                        container.style.cursor = 'default';
                    }}
                }}
            }});
            
            container.addEventListener('click', () => {{
                raycaster.setFromCamera(mouse, camera);
                // Intersect only meshes in the atlasGroup
                const interactables = [];
                atlasGroup.traverse((child) => {{
                    if (child.isMesh && child.visible && child.parent && child.parent.visible) interactables.push(child);
                }});

                const intersects = raycaster.intersectObjects(interactables, false);
                
                if (hoveredMesh && hoveredMesh.material) {{
                    hoveredMesh.material.emissiveIntensity = originalEmissiveInt;
                }}
                labelDiv.classList.remove('visible');

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
                        
                        // GSAP CAMERA ZOOM TO TARGET
                        // Calculate a position slightly offset from the organ
                        const offsetPos = new THREE.Vector3(worldPos.x + 1.5, worldPos.y, worldPos.z + 2.0);
                        
                        gsap.to(camera.position, {{
                            x: offsetPos.x,
                            y: offsetPos.y,
                            z: offsetPos.z,
                            duration: 1.5,
                            ease: "power3.inOut"
                        }});
                        
                        gsap.to(controls.target, {{
                            x: worldPos.x,
                            y: worldPos.y - 0.5,
                            z: worldPos.z,
                            duration: 1.5,
                            ease: "power3.inOut"
                        }});
                        
                        btnResetCam.style.display = "block";
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
                
                // Update Shader Uniforms
                matSkinHolo.uniforms.uTime.value = time;
                
                if (avatarMixer) avatarMixer.update(delta * 2);
                
                // Cardiovascular Pulse
                if (layers['cardio'].visible) {{
                    const pulseRate = bioData.heartRate / 60;
                    const pulse = (Math.sin(time * Math.PI * 2 * pulseRate) + 1) / 2;
                    heart.scale.setScalar(1 + pulse * 0.2);
                    heart.material.emissiveIntensity = 2.0 + (pulse * 3.0);
                }}
                
                // Respiratory Breathing
                if (layers['respiratory'].visible) {{
                    const breathRate = bioData.trauma !== "none" ? 1.5 : 1;
                    const breath = (Math.sin(time * breathRate) + 1) / 2;
                    lungL.scale.setScalar(0.9 + breath * 0.15);
                    lungL.scale.y = 2.0;
                    lungR.scale.setScalar(0.9 + breath * 0.15);
                    lungR.scale.y = 2.0;
                }}
                
                // Nervous Jitter (Stress)
                if (layers['nervous'].visible && bioData.stress > 70) {{
                    brain.position.x = (Math.random() - 0.5) * 0.05;
                }}

                // Maslow Rings Rotation
                if (layers['maslow'].visible) {{
                    rings.forEach(r => {{
                        r.mesh.rotation.z += (delta * r.speed * r.dir);
                    }});
                    
                    // Particle Animation (Drift upwards and reset)
                    const positions = particleSystem.geometry.attributes.position.array;
                    const vels = particleSystem.userData.velocities;
                    const pCnt = particleSystem.userData.pCount;
                    for(let i=0; i<pCnt; i++) {{
                        positions[i*3 + 1] += vels[i].y * delta * 60; // Drift up
                        
                        // Slowly spiral
                        vels[i].theta += delta * vels[i].speed;
                        positions[i*3] = vels[i].r * Math.cos(vels[i].theta);
                        positions[i*3 + 2] = vels[i].r * Math.sin(vels[i].theta);
                        
                        if (positions[i*3 + 1] > 4.8) {{ // Reset if too high
                            positions[i*3 + 1] = Math.random() > 0.5 ? 1.0 : 2.5; // Reset to chest or neck
                        }}
                    }}
                    particleSystem.geometry.attributes.position.needsUpdate = true;
                }}
                
                // Orbiting HUD Panels
                const hudY = 3.5;
                const hudR = 1.8;
                hudStress.position.set(Math.cos(time * 0.3) * hudR, hudY, Math.sin(time * 0.3) * hudR);
                hudSleep.position.set(Math.cos(time * 0.3 + 2.09) * hudR, hudY + 0.2 * Math.sin(time), Math.sin(time * 0.3 + 2.09) * hudR);
                hudWellness.position.set(Math.cos(time * 0.3 + 4.18) * hudR, hudY + 0.2 * Math.cos(time), Math.sin(time * 0.3 + 4.18) * hudR);

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
