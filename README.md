# 🎙️ VivaVoce: Emergency AI Mock Interview & Viva Crash-Prep Simulator

> **"When your viva or technical interview is in a few hours, reading slides won't cut it. You need to speak your answers out loud under relentless simulated pressure."**

---

## ⚡ What is VivaVoce?
**VivaVoce** is a production-ready, single-file Python web application built using **Streamlit** and the modern **Google Gemini API** (`google-genai` SDK). It allows candidates to simulate high-stakes oral examinations, academic vivas, and FAANG-style system design grilling directly in their browser using their **native voice**.

### 🌟 Key Features
1. **Sidebar Credentials & Secure Control Panel:**
   - Password-masked input field for the user's **Google Gemini API Key** (`GEMINI_API_KEY`).
   - Graceful fallback: works out-of-the-box if `GEMINI_API_KEY` is already in the environment, or prompts the user with an actionable setup link.
   - Live Session Telemetry: Question counter, cumulative average score, and elapsed timer.

2. **3 Tailored Training Modes (`st.sidebar.radio`):**
   - **🚨 Emergency Crash Mode:** Zero warmups, immediate high-pressure grilling on high-yield viva topics based on the user's impending deadline.
   - **⚡ Advanced Mastery Mode:** Hardcore system design, architecture, race conditions, internal mechanisms, and edge-case interrogation.
   - **🌱 Beginner / Foundation Mode:** Step-by-step paced conceptual learning with constructive guidance.

3. **High-Impact Emergency Landing Screen:**
   - One-click urgent presets (OS & Concurrency Viva in 2h, Google L5 Systems tomorrow, Python Architecture tonight, etc.).
   - Custom goal & deadline input area: *"What are you preparing for and when is it?"*.
   - Dynamic Gemini system prompt synthesis tailored to your exact subject, examiner persona, and time constraint.

4. **Native Browser Voice & Multimodal Evaluation Loop:**
   - Uses Streamlit's native `st.audio_input` for seamless in-browser microphone recording.
   - Passes raw audio bytes directly to the Gemini model using `types.Part.from_bytes()`.
   - Gemini listens to your verbal explanation, evaluates technical depth, hesitation, and clarity, issues an exact score out of 10, highlights fatal blindspots, and presents the next challenging question.
   - Text fallback input is also provided for quiet environments.

5. **Final Viva Scorecard & Last-Minute Cheat Sheet:**
   - Real-time synthesis of candidate strengths, critical misconceptions to fix before the exam, and a downloadable rapid-reference markdown cheat sheet.

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- A Google Gemini API Key (obtainable for free at [Google AI Studio](https://aistudio.google.com/apikey))

### 2. Installation
```bash
# Clone or navigate to the repository
cd VivaVoce

# Install required dependencies
pip install -r requirements.txt
```

### 3. Running the Application
```bash
streamlit run app.py
```

### 4. Configuration
Enter your Gemini API key in the left sidebar when the app loads, choose your training mode, set your target exam and deadline, and click **🚨 INITIALIZE CRASH SIMULATION**.

