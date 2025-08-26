import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu

# ======================
# 🎨 Page Configuration
# ======================
st.set_page_config(
    page_title="CodeLeaf AI",
    page_icon="🌿",
    layout="centered"
)

# ======================
# 🎨 Custom CSS Styling
# ======================
st.markdown("""
    <style>
        .main {
            background-color: #0f1116;
            color: #e0e0e0;
        }
        .title {
            font-size: 2.5rem;
            font-weight: bold;
            color: #4ade80;
            text-align: center;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.2rem;
            color: #9ca3af;
            text-align: center;
            margin-bottom: 30px;
        }
        .stTextArea textarea {
            border-radius: 12px;
            border: 1px solid #4ade80;
            padding: 12px;
            font-size: 1rem;
            background-color: #181a1f;
            color: #e0e0e0;
        }
        .stButton>button {
            background: linear-gradient(to right, #4ade80, #22c55e);
            color: white;
            border-radius: 10px;
            padding: 10px 20px;
            font-size: 1rem;
            font-weight: bold;
            transition: 0.3s;
            border: none;
        }
        .stButton>button:hover {
            background: linear-gradient(to right, #22c55e, #16a34a);
            transform: scale(1.05);
        }
        .output-card {
            background-color: #1e2128;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
        }
        .optimization-card {
            background-color: #1e2121;
            padding: 20px;
            border-radius: 12px;
            margin-top: 20px;
            box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.3);
            border: 1px solid #6b7280;
        }
        footer {
            text-align: center;
            margin-top: 50px;
            font-size: 0.9rem;
            color: #6b7280;
        }
        footer a {
            color: #4ade80;
            text-decoration: none;
        }
        footer a:hover {
            text-decoration: underline;
        }
    </style>
""", unsafe_allow_html=True)

# ======================
# Session State Initialization
# ======================
if "history" not in st.session_state:
    st.session_state.history = []

# ======================
# 🌿 Logo + Titles
# ======================
st.image("https://placehold.co/180x180/0f1116/4ade80?text=CodeLeaf%20AI", width=180)
st.markdown('<div class="title">🌿 CodeLeaf AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">A Green Leap Forward – Generate Smarter Code</div>', unsafe_allow_html=True)

# ======================
# ⚡ Menu for Navigation
# ======================
selected_option = option_menu(
    menu_title=None,
    options=["Code Generation", "Code Optimization", "Dashboard"],
    icons=["code-slash", "arrow-repeat", "clipboard-data"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#111827", "border-radius": "10px"},
        "icon": {"color": "#4ade80", "font-size": "18px"},
        "nav-link": {"font-size": "14px", "color": "#e0e0e0", "text-align": "center", "margin":"0px", "--hover-color": "#1f2937"},
        "nav-link-selected": {"background-color": "#22c55e"},
    }
)

# ======================
# 🚀 View: Code Generation
# ======================
if selected_option == "Code Generation":
    # Input area for code generation prompt
    prompt = st.text_area("💡 Describe the code you want:", height=150, placeholder="e.g., Python calculator, sorting algorithm...")

    # Button to trigger code generation
    if st.button("⚡ Generate Code", key="generate_code"):
        if prompt.strip():
            with st.spinner("🌱 Growing your code..."):
                try:
                    # Call the Flask backend's codegen endpoint
                    r = requests.post("http://127.0.0.1:5000/codegen", json={"prompt": prompt})
                    r.raise_for_status()
                    data = r.json()

                    # Display the generated code and CO2 data
                    st.markdown('<div class="output-card">', unsafe_allow_html=True)
                    st.subheader("📝 Generated Code")
                    st.code(data["code"], language="python")
                    # Correctly use the 'total_co2_kg' key from the backend
                    st.success(f"🌍 Estimated Total CO₂: {data['total_co2_kg']:.6f} kg")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Save the event to session history, including the new CO2 metrics
                    st.session_state.history.insert(0, {
                        "type": "generation",
                        "prompt": prompt,
                        "code": data["code"],
                        "llm_co2_kg": data["llm_co2_kg"],
                        "execution_co2_kg": data["execution_co2_kg"],
                        "timestamp": datetime.now()
                    })
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to the backend server. Please make sure it is running.")
                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")
        else:
            st.warning("⚠️ Please enter a prompt before generating.")

# ======================
# 📈 View: Code Optimization
# ======================
elif selected_option == "Code Optimization":
    # Input area for unoptimized code
    st.subheader("Unoptimized Code")
    unoptimized_code = st.text_area("Paste your code here:", height=300, key="unoptimized_code_input", placeholder="e.g., inefficient sorting, a large loop...")
    
    # Button to trigger optimization
    if st.button("♻️ Optimize & Compare", key="optimize_code"):
        if unoptimized_code.strip():
            with st.spinner("🌿 Optimizing your code..."):
                try:
                    # Send the code to the backend for dynamic CO2 measurement and optimization
                    payload = {"code": unoptimized_code}
                    r = requests.post("http://127.0.0.1:5000/optimize", json=payload)
                    r.raise_for_status()
                    data = r.json()

                    st.markdown('<div class="optimization-card">', unsafe_allow_html=True)
                    st.subheader("✅ Optimized Code")
                    st.code(data["optimized_code"], language="python")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"Before CO₂: {data['before_co2']:.6f} kg")
                    with col2:
                        st.success(f"After CO₂: {data['after_co2']:.6f} kg")
                    
                    st.markdown(f"**CO₂ Saved:** :green[**{(data['before_co2'] - data['after_co2']):.6f} kg**]")
                    st.markdown('</div>', unsafe_allow_html=True)

                    # Save the event to session history
                    st.session_state.history.insert(0, {
                        "type": "optimization",
                        "unoptimized_code": unoptimized_code,
                        "optimized_code": data["optimized_code"],
                        "co2_before_kg": data["before_co2"],
                        "co2_after_kg": data["after_co2"],
                        "timestamp": datetime.now()
                    })
                except requests.exceptions.ConnectionError:
                    st.error("❌ Could not connect to the backend server. Please make sure it is running.")
                except Exception as e:
                    st.error(f"❌ An error occurred: {e}")
        else:
            st.warning("⚠️ Please paste some code to optimize.")

# ======================
# 📊 View: Dashboard
# ======================
elif selected_option == "Dashboard":
    st.header("📊 Your Green Dashboard")
    
    if st.session_state.history:
        # Create a DataFrame for the chart
        generation_data = [item for item in st.session_state.history if item["type"] == "generation"]
        if generation_data:
            chart_data = [{
                "Timestamp": item["timestamp"].strftime("%H:%M:%S"),
                "Total CO2 Emissions (kg)": item["llm_co2_kg"] + item["execution_co2_kg"]
            } for item in generation_data]
            df = pd.DataFrame(chart_data)
            st.subheader("Last 10 Code Generations by Total CO₂ Footprint")
            st.bar_chart(df.set_index("Timestamp"))
        
        st.subheader("📜 History Log")
        for item in st.session_state.history:
            if item["type"] == "generation":
                st.markdown(f"**Generated Code** at `{item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}`")
                st.markdown(f"**Prompt:** {item['prompt']}")
                st.code(item["code"][:100] + "..." if len(item["code"]) > 100 else item["code"], language="python")
                
                # Display the breakdown of CO2 for generated code
                st.markdown(f"**LLM CO₂:** `{item['llm_co2_kg']:.6f} kg`")
                st.markdown(f"**Code Execution CO₂:** `{item['execution_co2_kg']:.6f} kg`")
                st.markdown(f"**Total CO₂:** `{item['llm_co2_kg'] + item['execution_co2_kg']:.6f} kg`")
                st.markdown("---")
            elif item["type"] == "optimization":
                st.markdown(f"**Code Optimization** at `{item['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}`")
                st.markdown(f"**Before CO₂:** `{item['co2_before_kg']:.6f} kg`")
                st.markdown(f"**After CO₂:** `{item['co2_after_kg']:.6f} kg`")
                st.markdown(f"**CO₂ Saved:** `:green[{(item['co2_before_kg'] - item['co2_after_kg']):.6f} kg]`")
                st.markdown("---")
    else:
        st.info("No history to display yet. Start generating or optimizing some code!")

# ======================
# ❤️ Footer
# ======================
st.markdown(
    "<footer>Made with ❤️ by LeafLabsAI • <a href='https://github.com/LeafLabsAI/codeleaf-ai'>GitHub</a></footer>",
    unsafe_allow_html=True
)
