<p align="center">
  <img src="assets/Code.png" alt="CodeLeaf AI Logo" width="300"/>
</p>

<p align="center"><i>"🌿 A Green Leap Forward — Smarter, Greener Code"</i></p>

---

## 📌 About
**CodeLeaf AI** is an eco-conscious coding assistant that helps developers measure and reduce the **carbon footprint of their software**.  
Built by students, for students and professionals, it combines **AI-powered code generation, optimization, and sustainability insights** to promote greener development practices.

This is the **MVP (Phase 1)** release — lightweight, cost-effective, and powered entirely by **open-source + free-tier tools**.

---

## ✨ Major Functionalities

1. ⚡ **Eco-Friendly Coding Insights**  
   - Track **energy usage & CO₂ emissions** using CodeCarbon.  
   - Compare “green scores” of different solutions (recursion vs iteration).  
   - Suggest eco-efficient libraries and methods.  

2. 🤖 **AI Code Assistant**  
   - Generate and explain code from natural prompts.  
   - Debug and provide **optimized versions** of inefficient code.  
   - Support multiple languages (Python, JS, Java, C++).  
   - AI-driven best practices for efficiency & readability.  

3. 📊 **Developer Dashboard**  
   - Personalized **Green Report** after each run.  
   - Weekly stats for **energy saved & CO₂ reduced**.  
   - Interactive **charts & visualizations** (Streamlit + Plotly).  

4. 🌍 **Eco-Aware Recommendations**  
   - Integration with APIs like **Electricity Maps** (planned).  
   - Show when running compute-heavy jobs is “greenest” (based on renewable share).  

5. 🧠 **Learning & Community Features** *(upcoming)*  
   - Built-in **green coding tutorials**.  
   - “Did you know?” tips (e.g., vectorized NumPy vs loops).  
   - Share **green badges** on GitHub/LinkedIn.  

---

## 🚀 Development Roadmap

### ✅ Phase 1 – MVP (Current Stage)
- Core eco-tracking with **CodeCarbon**.  
- AI Code Assistant via **Hugging Face Free API**.  
- Flask backend + Streamlit frontend.  
- Localhost + LAN deployment.  
- Branding: logo + slogan + basic landing page.  

### ⚡ Phase 2 – Beta Release
- Add multi-language support (Python + JS at least).  
- Smarter AI agent with LangChain / LlamaIndex for code Q&A.  
- Weekly “Green Reports” with efficiency tips.  
- Gamified **Green Badges** for eco-efficient coding.  
- Carbon-aware job scheduling with **Electricity Maps API**.  

### 🌍 Phase 3 – Full Release
- **AI Pair Programmer** (Copilot but eco-aware).  
- Enterprise dashboards for dev teams.  
- Community + snippet marketplace.  
- Leaderboards for “greenest coders.”  
- Mobile app companion.  
- Monetization (Freemium + Pro tier).  

---

## 🛠️ Tech Stack
- **Frontend:** Streamlit (UI, Dashboard)  
- **Backend:** Flask (Python API)  
- **AI Models:** Hugging Face Inference API (Qwen, CodeT5, StarCoder)  
- **Carbon Tracking:** CodeCarbon  
- **Visualization:** Plotly + Pandas  
- **Version Control:** Git + GitHub  

---

## ⚡ Quick Start

1️⃣ **Clone the Repository**
```bash
git clone https://github.com/<your-username>/codeleaf-ai.git
cd codeleaf-ai
```

2️⃣ **Create Virtual Environment**
```bash
python -m venv venv
# Linux/Mac
source venv/bin/activate
# Windows
venv\Scripts\activate
```

3️⃣ **Install Dependencies**
```bash
pip install -r requirements.txt
```

4️⃣ **Add Hugging Face Token**

1.Create a free account at Hugging Face.
2.Go to Access Tokens → generate a token (Read permissions).
3.Create a .env file:
```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxx
```

5️⃣ **Run the Backend**
```bash
cd backend
python app.py
# Backend available at http://127.0.0.1:5000
```

6️⃣ **Run the Frontend**
```bash
cd frontend
streamlit run app.py
# Localhost: http://localhost:8501
# Network: http://192.168.29.77:8501
```
<p align="center">Made with ❤️ by Leaf Core Labs</p> ```