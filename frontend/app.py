import streamlit as st

st.title("🌱 CodeLeaf AI – A Green Leap Forward")
st.write("Welcome to the MVP dashboard.")

prompt = st.text_area("Enter a coding request (e.g., 'Write a Python function for Fibonacci'):")

if st.button("Generate"):
    st.info("⚡ Backend integration will be added on Day 2–3")
