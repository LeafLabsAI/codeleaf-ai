🌿 CodeLeaf AI
<p align="center"> <img src="assets/logo/CodeLeaf.png" alt="CodeLeaf AI Logo" width="300"/> </p> <p align="center"><i>"A Green Leap Forward — Smart, Simple, Student-Friendly"</i></p>
📌 About

CodeLeaf AI is a student-driven AI platform that helps developers write smarter, more efficient, and eco-friendly code.
It provides real-time carbon footprint insights, AI-powered code generation, and code optimization to promote greener programming practices.

This is the MVP (Phase 1) release, built with free and open-source tools to remain cost-effective and accessible for students and researchers.

✨ Features

✅ Eco-Friendly Coding Insights → Estimate CO₂ emissions with CodeCarbon
.

✅ AI Code Assistant → Generate, explain, and analyze code via Hugging Face APIs.

✅ Code Optimizer → Paste unoptimized code and get optimized, greener alternatives with side-by-side CO₂ savings.

✅ Interactive Dashboard → Track history, CO₂ savings, and efficiency progress with visual charts.

✅ Streamlit Frontend + Flask Backend → Clean, responsive UI with efficient backend APIs.

🛠️ Tech Stack

Frontend: Streamlit

Backend: Flask (Python)

AI Models: Hugging Face Inference API

Sustainability Tracking: CodeCarbon v3.0.4

Visualization: Plotly + Pandas

Version Control: Git + GitHub

🚀 Quick Start
1️⃣ Clone the Repository
git clone https://github.com/<your-username>/codeleaf-ai.git
cd codeleaf-ai

2️⃣ Create Virtual Environment
python -m venv venv
source venv/bin/activate    # (Linux/Mac)
venv\Scripts\activate       # (Windows PowerShell)

3️⃣ Install Dependencies
pip install -r requirements.txt

4️⃣ Hugging Face Token Setup

Create a free account → Hugging Face

Go to → Access Tokens → Generate token with Read permissions

Copy it (looks like hf_xxxxxxxxxxx)

5️⃣ Add Environment Variables

Create a .env file in the project root:

HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxx

6️⃣ Run Applications

Backend (Flask API):

python backend/app.py


Frontend (Streamlit):

streamlit run app.py


Local URL → http://localhost:8501
Network URL → http://192.168.29.77:8501
Backend API → http://127.0.0.1:5000

🤝 Contributing

Since this is a student-led project, any feedback, ideas, or contributions are highly welcome.
Feel free to fork, experiment, and submit PRs to make CodeLeaf AI greener and smarter.