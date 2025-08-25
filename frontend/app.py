import streamlit as st
import requests

# ======================
# 🎨 Page Configuration
# ======================
st.set_page_config(
    page_title="CodeLeaf AI",
    page_icon="🌱",
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
# 🌿 Logo + Titles
# ======================
st.image("assets/logo/CodeLeaf.png", width=180)
st.markdown('<div class="title">🌿 CodeLeaf AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">A Green Leap Forward – Generate Smarter Code</div>', unsafe_allow_html=True)

# ======================
# ✨ Input Box
# ======================
prompt = st.text_area("💡 Describe the code you want:", height=150, placeholder="e.g., Python calculator, sorting algorithm...")

# ======================
# ⚡ Button + Output
# ======================
if st.button("⚡ Generate Code"):
    if prompt.strip():
        with st.spinner("🌱 Growing your code..."):
            try:
                r = requests.post("http://127.0.0.1:5000/codegen", json={"prompt": prompt})
                data = r.json()

                st.markdown('<div class="output-card">', unsafe_allow_html=True)
                st.subheader("📝 Generated Code")
                st.code(data["code"], language="python")
                st.success(f"🌍 Estimated CO₂: {data['co2_kg']:.6f} kg")
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Backend error: {e}")
    else:
        st.warning("⚠️ Please enter a prompt before generating.")

# ======================
# ❤️ Footer
# ======================
st.markdown(
    "<footer>Made with ❤️ by LeafLabsAI • <a href='https://github.com/LeafLabsAI/codeleaf-ai'>GitHub</a></footer>",
    unsafe_allow_html=True
)
