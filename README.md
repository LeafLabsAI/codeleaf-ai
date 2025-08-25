<p align="center">
  <img src="assets/logo/CodeLeaf.png" alt="CodeLeaf AI Logo" width="200"/>
</p>

<p align="center"><i>"A Green Leap Forward — Smart, Simple, Student-Friendly"</i></p>

---

## 📌 About
CodeLeaf AI is a **cost-effective AI assistant** built by students, for students.  
It can **read documents, analyze spreadsheets, and answer general/mathematical queries** using free & open-source AI models.  

This is the **MVP (Phase 1)** version — lightweight, runs locally, and integrates Hugging Face free APIs.  

---

## ✨ Features (Phase 1 MVP)
✅ Smart **Document Reader** (PDF, TXT, DOCX)  
✅ **Spreadsheet Analyzer** (CSV, XLSX)  
✅ **Math & General QnA**  
✅ **Streamlit Frontend** for interaction  
✅ **Hugging Face API** for AI power (free tier)  

---

## 🛠️ Tech Stack
- **Frontend:** Streamlit  
- **Backend:** Python  
- **AI Models:** Hugging Face Free Inference API  
- **Version Control:** Git + GitHub  

---

## 🚀 Quick Start (Step by Step)

### Step 1 Clone the Repository
```bash
git clone https://github.com/<your-username>/codeleaf-ai.git
cd codeleaf-ai
```
### 2 Create Virtual Environment
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows PowerShell)

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Get Hugging Face Token
```bash
Create free account → Hugging Face

Go to → Access Tokens

Create a token with Read permissions.

Copy it (looks like hf_xxxxxxxxxxx).
```
### 5. Add Environment Variables
```bash
Create a .env file in the root:

HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxx


⚠️ Don’t push .env to GitHub (already in .gitignore).
```
### 6. Run Streamlit App
```bash
streamlit run app.py

```
🚀 Roadmap

 Phase 1 – MVP (Docs + Spreadsheets + Hugging Face API)

 Phase 2 – Add vector DB (FAISS / ChromaDB) for local document search

 Phase 3 – Deploy free on Streamlit Cloud / Hugging Face Spaces

 Phase 4 – Add advanced agents (LangChain, local models)

🤝 Contributing

Since this is a student project, any feedback, ideas, or contributions are welcome.
Feel free to fork and open PRs.

