# app.py
import streamlit as st
import google.generativeai as genai
from PIL import Image
import json
import urllib.parse

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Multimodal Construction Intelligence Platform",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern CSS styling for metrics and pills
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        border-radius: 8px;
        padding: 20px;
        border-left: 5px solid #ff4b4b;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .status-pill {
        display: inline-block;
        padding: 5px 12px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 0.9em;
    }
    .status-High, .status-Critical { background-color: #ff4b4b; color: white; }
    .status-Medium { background-color: #ffa500; color: white; }
    .status-Low, .status-Safe { background-color: #00cc66; color: white; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SIDEBAR: CONFIGURATION & ARCHITECTURE
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ System Config")
    api_key = st.text_input("Google Gemini API Key", type="password", help="Enter your Gemini API key to enable live AI inference.")
    
    if api_key:
        genai.configure(api_key=api_key)
        demo_mode = False
        st.success("API Key authenticated. Live mode active.")
    else:
        demo_mode = True
        st.warning("No API Key provided. Running in Demonstration Mode (Mock Data).")

    st.markdown("---")
    st.markdown("### 🏗️ Architecture Overview")
    st.markdown("""
    - **Vision LLM:** Gemini 1.5 Flash (Multimodal)
    - **Framework:** Streamlit (Python)
    - **Standards:** OSHA & IS 456
    - **Modules:** PPE Audit, Structural Diagnostics, Valuation, Site Advisory
    """)

# -----------------------------------------------------------------------------
# CORE LOGIC & MOCK DATA (FOR DEMO MODE)
# -----------------------------------------------------------------------------
def get_gemini_vision_response(prompt, image, response_schema=None):
    if demo_mode:
        # Mock responses based on the context
        if "PPE" in prompt:
            return json.dumps({
                "safety_score": 65,
                "overall_status": "Warning",
                "ppe_detection": {"helmets": False, "vests": True, "boots": True, "harnesses": False},
                "hazards": [
                    {"issue": "Missing Hard Hat", "severity": "High", "remedy": "Issue immediate stop-work until helmet is donned."},
                    {"issue": "Working at height without harness", "severity": "Critical", "remedy": "Deploy fall protection systems immediately."}
                ]
            })
        else:
            return json.dumps({
                "defect_type": "Structural Shear Crack",
                "estimated_width_mm": 3.5,
                "root_causes": ["Differential settlement", "Excessive load exceeding shear capacity"],
                "engineering_repairs": ["Epoxy injection grouting", "Carbon fiber wrap reinforcement"],
                "urgency": "High"
            })
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        config = genai.GenerationConfig(response_mime_type="application/json")
        response = model.generate_content([prompt, image], generation_config=config)
        return response.text
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return "{}"

# -----------------------------------------------------------------------------
# MAIN DASHBOARD TABS
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "🛡️ Site Safety & PPE", 
    "🔍 Crack Diagnostics", 
    "📊 Planning & Valuation", 
    "⛈️ Daily Site Assistant"
])

# =============================================================================
# TAB 1: SITE SAFETY & PPE AUDIT (EPIC 2)
# =============================================================================
with tab1:
    st.header("Site Safety & PPE Audit")
    st.markdown("Upload construction site photos for OSHA and IS 456 compliance auditing.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        safety_file = st.file_uploader("Upload Site Photo", type=["jpg", "png", "jpeg"], key="safety_upload")
        if safety_file:
            safe_img = Image.open(safety_file)
            st.image(safe_img, caption="Uploaded Site Photo", use_container_width=True)
            analyze_safety = st.button("Run Safety Audit", type="primary")
            
    with col2:
        if safety_file and analyze_safety:
            with st.spinner("Analyzing site imagery against OSHA/IS 456 standards..."):
                safety_prompt = """
                Analyze this construction site photo. Assess PPE compliance (helmets, high-vis vests, steel-toe boots, safety harnesses) 
                based on OSHA and IS 456 standards. Return ONLY a JSON object with this exact schema:
                {
                  "safety_score": integer (0-100),
                  "overall_status": "string (Safe, Warning, Critical)",
                  "ppe_detection": {"helmets": boolean, "vests": boolean, "boots": boolean, "harnesses": boolean},
                  "hazards": [{"issue": "string", "severity": "Low/Medium/High/Critical", "remedy": "string"}]
                }
                """
                result_str = get_gemini_vision_response(safety_prompt, safe_img)
                try:
                    result = json.loads(result_str)
                    
                    # Metrics
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Safety Score", f"{result.get('safety_score', 0)}/100")
                    c2.markdown(f"**Status:** <span class='status-pill status-{result.get('overall_status', 'Safe')}'>{result.get('overall_status', 'N/A')}</span>", unsafe_allow_html=True)
                    
                    # PPE Checklist
                    st.subheader("PPE Compliance Checklist")
                    ppe = result.get('ppe_detection', {})
                    for item, status in ppe.items():
                        icon = "✅" if status else "❌"
                        st.write(f"{icon} {item.capitalize()}")
                    
                    # Hazards Table
                    st.subheader("Identified Hazards & Remedies")
                    hazards = result.get('hazards', [])
                    if hazards:
                        for h in hazards:
                            st.markdown(f"""
                            <div style='background-color:#2a2a2a; padding:10px; border-radius:5px; margin-bottom:10px;'>
                                <strong>Issue:</strong> {h['issue']} <br/>
                                <strong>Severity:</strong> <span class='status-pill status-{h['severity']}'>{h['severity']}</span> <br/>
                                <strong>Remedy:</strong> {h['remedy']}
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.success("No major hazards detected.")
                        
                    st.download_button("Download JSON Report", data=result_str, file_name="safety_audit.json", mime="application/json")
                    
                except json.JSONDecodeError:
                    st.error("Failed to parse AI response. Ensure API key is valid.")

# =============================================================================
# TAB 2: CRACK DIAGNOSTICS & STRUCTURAL INTEGRITY (EPIC 2)
# =============================================================================
with tab2:
    st.header("Crack Diagnostics & Structural Integrity")
    st.markdown("Assess concrete and masonry defects to determine root causes and engineering repairs.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        crack_file = st.file_uploader("Upload Structural Defect Photo", type=["jpg", "png", "jpeg"], key="crack_upload")
        if crack_file:
            crack_img = Image.open(crack_file)
            st.image(crack_img, caption="Surface Photo", use_container_width=True)
            analyze_crack = st.button("Run Structural Diagnostic", type="primary")

    with col2:
        if crack_file and analyze_crack:
            with st.spinner("Classifying defect and calculating intervention parameters..."):
                crack_prompt = """
                Analyze this construction defect photo. Classify the defect type (Hairline, Settlement, Structural Shear, Thermal Expansion, Spalling). 
                Return ONLY a JSON object with this schema:
                {
                  "defect_type": "string",
                  "estimated_width_mm": float,
                  "root_causes": ["string"],
                  "engineering_repairs": ["string"],
                  "urgency": "Low/Medium/High/Critical"
                }
                """
                crack_res_str = get_gemini_vision_response(crack_prompt, crack_img)
                try:
                    c_result = json.loads(crack_res_str)
                    
                    st.markdown(f"### Diagnosis: {c_result.get('defect_type', 'Unknown')}")
                    st.markdown(f"**Estimated Width:** {c_result.get('estimated_width_mm', 0)} mm | **Urgency:** <span class='status-pill status-{c_result.get('urgency', 'Low')}'>{c_result.get('urgency', 'Unknown')}</span>", unsafe_allow_html=True)
                    
                    st.markdown("#### Root Causes")
                    for cause in c_result.get('root_causes', []):
                        st.write(f"- {cause}")
                        
                    st.markdown("#### Engineering Repairs")
                    for repair in c_result.get('engineering_repairs', []):
                        st.write(f"- {repair}")
                        
                except json.JSONDecodeError:
                    st.error("Failed to parse AI diagnostic data.")

# =============================================================================
# TAB 3: PLANNING & REAL ESTATE VALUATION (EPIC 3)
# =============================================================================
with tab3:
    st.header("Planning & Real Estate Valuation")
    
    col_input, col_metrics = st.columns([1, 2])
    
    with col_input:
        struct_type = st.selectbox("Structure Type", ["Residential High-Rise", "Commercial Plaza", "Industrial Warehouse", "Infrastructure (Bridge/Road)"])
        loc_tier = st.selectbox("Location Tier", ["Tier 1 (Metro)", "Tier 2 (Urban)", "Tier 3 (Semi-Urban)"])
        built_up = st.number_input("Built-up Area (Sq.Ft)", min_value=1000, value=15000, step=1000)
        completion = st.slider("Project Completion %", 0, 100, 35)
        
        # Hardcoded realistic baselines for Indian construction
        rates = {"Tier 1 (Metro)": 3500, "Tier 2 (Urban)": 2400, "Tier 3 (Semi-Urban)": 1600}
        rate_per_sqft = rates[loc_tier]
        
    with col_metrics:
        # Calculations
        total_budget_inr = built_up * rate_per_sqft
        capex_incurred = total_budget_inr * (completion / 100)
        market_valuation = capex_incurred * 1.25 if completion > 20 else capex_incurred
        
        steel_req_mt = (built_up * 4.5) / 1000  # Approx 4.5 kg per sqft
        cement_bags = built_up * 0.45          # Approx 0.45 bags per sqft
        
        # Financial Formatting (Lakhs/Crores)
        def format_inr(value):
            if value >= 10000000:
                return f"₹ {value/10000000:.2f} Cr"
            return f"₹ {value/100000:.2f} Lakhs"

        st.markdown("### Financial & Material Metrics")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Est. Budget", format_inr(total_budget_inr))
        m2.metric("CAPEX Incurred", format_inr(capex_incurred))
        m3.metric("Current Asset Valuation", format_inr(market_valuation))
        
        m4, m5, m6 = st.columns(3)
        m4.metric("Steel Req. (MT)", f"{steel_req_mt:.1f}")
        m5.metric("Cement Req. (Bags)", f"{cement_bags:,.0f}")
        m6.metric("Completion", f"{completion}%")
        
        st.progress(completion / 100)
        
        st.markdown("### Conceptual 3D Architectural Rendering")
        prompt_str = f"Hyper-realistic 3D architectural render of a {struct_type} construction project in an Indian {loc_tier} city, modern design, cinematic lighting, 8k resolution"
        encoded_prompt = urllib.parse.quote(prompt_str)
        pollinations_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=400&nologo=true"
        st.image(pollinations_url, caption=f"AI Generated Concept: {struct_type}", use_container_width=True)

# =============================================================================
# TAB 4: DAILY SITE ASSISTANT & WEATHER-AWARE ADVISORY (EPIC 5)
# =============================================================================
with tab4:
    st.header("Daily Site Assistant")
    
    st.subheader("Weather-Aware Protocol Engine")
    weather = st.radio("Current Site Weather Conditions", ["Normal", "High Wind (>40km/h)", "Heavy Rain / Monsoon", "Extreme Heat (>40°C)"], horizontal=True)
    
    if weather == "High Wind (>40km/h)":
        st.error("🚨 **CRITICAL ALERTS:** Suspend all tower crane operations immediately. Secure all loose materials on scaffolding. Halt working at heights.")
    elif weather == "Heavy Rain / Monsoon":
        st.warning("⚠️ **WARNING:** Suspend concrete pouring. Cover freshly poured slabs. Ensure electrical distribution boxes are elevated and tarped. Check excavation trench shoring.")
    elif weather == "Extreme Heat (>40°C)":
        st.warning("⚠️ **WARNING:** Implement wet-curing protocols for concrete to prevent thermal cracking. Mandate 15-minute hydration breaks for laborers every 2 hours.")
    else:
        st.success("✅ Weather normal. Standard operating procedures apply.")
        
    st.markdown("---")
    st.subheader("💬 Site Engineering Chatbot")
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I am your AI Site Engineer. Ask me about concrete mix designs, IS code compliance, structural load paths, or schedule optimization."}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("E.g., What is the curing time for M30 concrete under IS 456?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if demo_mode:
                response = f"[Demo Mode] Regarding your query about '{prompt}': Refer to IS 456 Section 13.5. Curing should continue for at least 7 days for ordinary Portland cement, and 10 days if exposed to dry/hot weather."
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
            else:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    # Construct history
                    history = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-4:]])
                    full_prompt = f"You are an expert Indian civil engineer and construction manager. Answer based on IS codes and modern engineering practices.\n\nHistory:\n{history}\n\nEngineer, please answer: {prompt}"
                    
                    ai_response = model.generate_content(full_prompt)
                    st.markdown(ai_response.text)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response.text})
                except Exception as e:
                    st.error(f"Chatbot Error: {e}")