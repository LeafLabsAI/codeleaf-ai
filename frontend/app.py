import streamlit as st
import requests

st.set_page_config(page_title="CodeLeaf AI", page_icon="🌱", layout="centered")
st.image("assets/logo/CodeLeaf.png", width=180)
st.title("CodeLeaf AI — A Green Leap Forward")

prompt = st.text_area("Describe the code you want:", height=150)

if st.button("Generate"):
    with st.spinner("Thinking green…"):
        r = requests.post("http://127.0.0.1:5000/codegen", json={"prompt": prompt})
        data = r.json()
        st.subheader("Generated code")
        st.code(data["code"], language="python")
        st.success(f"Estimated CO₂: {data['co2_kg']:.6f} kg")
