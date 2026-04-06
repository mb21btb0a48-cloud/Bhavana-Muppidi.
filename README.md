# AI Health Dashboard 🧬

A highly professional, multimodal AI Health Education Dashboard designed to provide personalized clinical insights, structural diagnostic tables, and nutritional guidance. 

The dashboard leverages **OpenAI's latest GPT-4o models** and **Streamlit** to intelligently process user health data via manual text entry, medical report document uploads (PDF/DOCX), and physical report image processing (Vision API) to generate strict dietary plans and lifestyle recommendations.

---

## 🚀 Key Features

* **Multimodal Data Ingestion:**
  * ✍️ **Manual Entry**: Type or speak your symptoms/conditions directly.
  * 📄 **Document Upload**: Upload clinical PDF or DOCX lab reports for automated extraction.
  * 📸 **Image / Vision**: Take a picture or upload physical paper lab reports.
* **Secure Authentication Gate**: 
  * 🛡️ **Aadhar Verification**: Structural validation using the Verhoeff checksum algorithm.
  * 📲 **Twilio SMS OTP**: Real-time mobile verification with secure 6-digit codes.
* **Premium Diagnostic Engine:** Operates under a specialized "Gold Medalist MBBS Doctor" AI persona for absolute clinical strictness and accuracy.
* **Automated Data Processing:** Extracts raw diagnostic values mathematically and graphs them into Visual Gauges & Trend trackers (Current vs. Historical comparisons).
* **Targeted Nutritional Plans:** Generates precise daily macronutrient targets, categorized Grocery Lists, and strict lists of foods to consume and clinically avoid.
* **Smart UI Architecture:** Features a premium light "glassmorphic" interface with Lottie animations, built-in TTS (Text-to-Speech) summaries, and exportable formatting.

---

## 🛠️ Technology Stack

* **Frontend:** [Streamlit](https://streamlit.io/) (Python)
* **AI Engine:** [OpenAI API](https://openai.com/) (GPT-4o-mini / Vision)
* **Data Parsing:** `PyPDF2`, `python-docx`
* **Data Modeling:** `Pydantic` (For strict JSON AI output validation)
* **Authentication:** [Twilio API](https://www.twilio.com/) (SMS Gateway)
* **Database (History Tracking):** SQLite (`sqlite3`)

---

## 💻 Local Setup & Installation

### 1. Clone the Repository
Download this repository to your local machine.

### 2. Configure Environment Variable
The application natively searches for your OpenAI API Key securely in the environment. *Do NOT hardcode your key into `app.py`.*

**Mac/Linux:**
```bash
export OPENAI_API_KEY="sk-proj-your-api-key-here"
```
**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-proj-your-api-key-here"
```

### 3. Install Dependencies
It is recommended to run this project in a Python Virtual Environment (`venv`). Ensure you have Python 3.10+ installed.
```bash
pip install -r requirements.txt
```

### 4. Run the Dashboard
```bash
streamlit run app.py
```
The dashboard will launch automatically in your default internet browser at `http://localhost:8501`.

---

## 🐳 Docker Deployment (AWS / Cloud Ready)

This repository includes a production-ready `Dockerfile` specifically designed for cloud deployments (AWS ECS, Render, DigitalOcean).

**1. Build the Docker Image:**
```bash
docker build -t ai-health-dashboard .
```

**2. Run the Container (Passing the API Key securely):**
```bash
docker run -p 8501:8501 -e OPENAI_API_KEY="sk-proj-your-api-key-here" ai-health-dashboard
```

---

## 🔒 Security & Privacy Notice
* **Medical Disclaimer**: This application is built for *educational and informational purposes only*. It is not a clinical replacement for professional medical diagnosis or treatment.
* **Data Handling**: User tracking data is isolated to the local `health_data.db` SQLite file. This file should be added to `.gitignore` and never committed to source control to protect downstream user PII.
