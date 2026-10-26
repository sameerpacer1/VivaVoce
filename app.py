"""
VivaVoce — Emergency AI Mock Interview & Viva Crash-Prep Simulator
A production-ready, single-file Streamlit application powered by the modern Google Gemini API (`google-genai` SDK).
"""

import streamlit as st
import os
import io
import time
import base64
import re
import socket
from datetime import datetime

# Optimize network socket resolution on Windows to avoid IPv6 timeouts
try:
    _orig_getaddrinfo = socket.getaddrinfo
    def _ipv4_getaddrinfo(*args, **kwargs):
        res = _orig_getaddrinfo(*args, **kwargs)
        ipv4_res = [r for r in res if r[0] == socket.AF_INET]
        return ipv4_res if ipv4_res else res
    socket.getaddrinfo = _ipv4_getaddrinfo
except Exception:
    pass

# Import modern Google Gemini SDK
try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# ==========================================
# 1. PAGE SETUP & METADATA
# ==========================================
st.set_page_config(
    page_title="VivaVoce — Emergency Viva & Mock Interview Simulator",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-Stress / Production Styling
st.markdown("""
<style>
    /* Dark cockpit theme enhancements */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Emergency Header Card */
    .emergency-banner {
        background: linear-gradient(135deg, rgba(218, 54, 51, 0.15) 0%, rgba(248, 81, 73, 0.05) 100%);
        border: 1px solid rgba(248, 81, 73, 0.4);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 25px;
        position: relative;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    
    .emergency-badge {
        display: inline-block;
        background: #da3633;
        color: #ffffff;
        font-weight: 700;
        font-size: 0.75rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        padding: 4px 10px;
        border-radius: 999px;
        margin-bottom: 12px;
        box-shadow: 0 0 10px rgba(218, 54, 51, 0.6);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.04); opacity: 0.85; }
        100% { transform: scale(1); opacity: 1; }
    }
    
    .hud-stat-box {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .hud-stat-num {
        font-size: 1.5rem;
        font-weight: 800;
        color: #58a6ff;
    }
    .hud-stat-label {
        font-size: 0.75rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Chat Bubble Enhancements */
    .interviewer-bubble {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #da3633;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }
    
    .candidate-bubble {
        background: #0e2030;
        border: 1px solid #1f4263;
        border-left: 4px solid #238636;
        border-radius: 10px;
        padding: 18px;
        margin-bottom: 16px;
    }
    
    .critique-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px dashed #4b5563;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 14px;
    }
    
    .score-pill {
        display: inline-block;
        font-weight: 800;
        padding: 2px 10px;
        border-radius: 6px;
        font-size: 0.9rem;
    }
    .score-high { background: #238636; color: white; }
    .score-mid { background: #d29922; color: black; }
    .score-low { background: #da3633; color: white; }
    
    .question-callout {
        background: rgba(88, 166, 255, 0.08);
        border: 1px solid rgba(88, 166, 255, 0.3);
        border-radius: 8px;
        padding: 16px;
        font-size: 1.1rem;
        font-weight: 600;
        color: #f0f6fc;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. SESSION STATE MANAGEMENT
# ==========================================
if "session_active" not in st.session_state:
    st.session_state.session_active = False

if "messages" not in st.session_state:
    # List of message dicts:
    # {
    #   "role": "interviewer" | "student",
    #   "content": str,
    #   "critique": str | None,
    #   "score": int | float | None,
    #   "audio_bytes": bytes | None,
    #   "audio_mime": str | None,
    #   "timestamp": str,
    #   "question_text": str | None
    # }
    st.session_state.messages = []

if "simulation_goal" not in st.session_state:
    st.session_state.simulation_goal = ""

if "target_topics" not in st.session_state:
    st.session_state.target_topics = ""

if "viva_mode" not in st.session_state:
    st.session_state.viva_mode = "🚨 Emergency Crash Mode"

if "interviewer_persona" not in st.session_state:
    st.session_state.interviewer_persona = "🔥 Ruthless FAANG Bar Raiser"

if "question_counter" not in st.session_state:
    st.session_state.question_counter = 0

if "scores_history" not in st.session_state:
    st.session_state.scores_history = []

if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = ""

if "session_start_time" not in st.session_state:
    st.session_state.session_start_time = None

if "show_scorecard" not in st.session_state:
    st.session_state.show_scorecard = False

if "final_scorecard_text" not in st.session_state:
    st.session_state.final_scorecard_text = ""

if "last_processed_audio_hash" not in st.session_state:
    st.session_state.last_processed_audio_hash = None


# ==========================================
# 3. SIDEBAR CONTROLS & API KEY INPUT
# ==========================================
with st.sidebar:
    st.markdown("### 🎙️ VivaVoce")
    st.caption("Emergency AI Mock Interview & Viva Simulator")
    st.markdown("---")
    
    # 3.1 Secure Gemini API Key Field
    st.markdown("#### 🔑 Gemini API Credentials")
    
    # Auto-load from st.secrets, os.environ, or .env
    configured_key = ""
    try:
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            configured_key = str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
        
    if not configured_key:
        configured_key = os.environ.get("GEMINI_API_KEY", "").strip()
        
    if not configured_key and os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as env_f:
                for line in env_f:
                    if line.startswith("GEMINI_API_KEY="):
                        configured_key = line.strip().split("=", 1)[1].strip('"').strip("'")
                        break
        except Exception:
            pass

    default_key = st.session_state.get("gemini_api_key", configured_key)
    
    api_key_input = st.text_input(
        "Enter Google Gemini API Key:",
        value=default_key,
        type="password",
        placeholder="AIzaSy...",
        help="Securely enter your Google Gemini API Key. Your key remains in browser session memory and is never stored on a server."
    )
    
    if api_key_input:
        st.session_state.gemini_api_key = api_key_input.strip()
        st.success("🟢 API Key configured for session", icon="✅")
    else:
        st.warning("⚠️ Gemini API Key required to run simulations.", icon="⚠️")
        st.markdown(
            """
            <small>Don't have an API key? Get one instantly from 
            <a href="https://aistudio.google.com/apikey" target="_blank" style="color: #58a6ff;">Google AI Studio</a>.
            </small>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")
    
    # 3.2 Training Mode Selector
    st.markdown("#### ⚙️ Training Mode")
    mode_selection = st.radio(
        "Select your preparation intensity:",
        [
            "🚨 Emergency Crash Mode",
            "⚡ Advanced Mastery Mode",
            "🌱 Beginner / Foundation Mode"
        ],
        index=0,
        help="Emergency: Rapid fire, zero fluff, immediate pressure. Mastery: Architecture & edge-case grilling. Foundation: Paced guidance."
    )
    st.session_state.viva_mode = mode_selection
    
    # Mode Descriptions
    if mode_selection == "🚨 Emergency Crash Mode":
        st.info("⏱️ **Crash Mode Active:** Skips all warmups. Immediate high-pressure grilling on high-yield topics based on your urgent deadline.")
    elif mode_selection == "⚡ Advanced Mastery Mode":
        st.info("🧠 **Mastery Mode Active:** Focuses on distributed architectures, trade-offs, internal mechanics, concurrency, and failure scenarios.")
    else:
        st.info("🌱 **Foundation Mode Active:** Patient, step-by-step paced interrogation with structured conceptual explanations.")

    st.markdown("---")
    
    # 3.3 Advanced Interview Settings (Expander)
    with st.expander("🛠️ Advanced Settings", expanded=False):
        model_choice = st.selectbox(
            "Gemini Model:",
            ["gemini-3.5-flash", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"],
            index=0,
            help="gemini-3.5-flash is ultra-fast, stable, and highly responsive for multimodal audio viva simulations."
        )
        st.session_state.model_choice = model_choice
        
        interviewer_persona = st.selectbox(
            "Interviewer Persona:",
            [
                "🔥 Ruthless FAANG Bar Raiser",
                "🎓 Strict University Viva Examiner",
                "💼 Senior Staff Infrastructure Architect",
                "🤝 Constructive Senior Engineering Lead"
            ],
            index=0
        )
        st.session_state.interviewer_persona = interviewer_persona

    # 3.4 Live Simulation Telemetry (If active)
    if st.session_state.session_active:
        st.markdown("---")
        st.markdown("#### 📊 Live Session Telemetry")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Questions", f"{st.session_state.question_counter}")
        with col2:
            if st.session_state.scores_history:
                avg_score = sum(st.session_state.scores_history) / len(st.session_state.scores_history)
                st.metric("Avg Score", f"{avg_score:.1f}/10")
            else:
                st.metric("Avg Score", "—")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Debrief / Scorecard Generator Button
        if st.button("📋 Generate Final Scorecard & Debrief", use_container_width=True, type="secondary"):
            st.session_state.show_scorecard = True
            st.rerun()
            
        # Reset Session Button
        if st.button("🛑 Reset / Exit Simulation", use_container_width=True):
            st.session_state.session_active = False
            st.session_state.messages = []
            st.session_state.question_counter = 0
            st.session_state.scores_history = []
            st.session_state.show_scorecard = False
            st.session_state.final_scorecard_text = ""
            st.session_state.session_start_time = None
            st.rerun()


# ==========================================
# 4. HELPER FUNCTIONS & GEMINI CLIENT
# ==========================================
def get_gemini_client():
    """Initializes and returns the modern Google GenAI Client."""
    api_key = st.session_state.get("gemini_api_key", "").strip()
    if not api_key:
        return None
    if not GENAI_AVAILABLE:
        st.error("The `google-genai` SDK is not installed in the environment. Please run `pip install google-genai`.")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize Gemini Client: {e}")
        return None


def build_system_prompt(goal, topics, mode, persona):
    """Generates a dynamic, high-pressure system prompt based on user deadline and mode."""
    mode_rules = {
        "🚨 Emergency Crash Mode": """
- URGENCY LEVEL: CRITICAL. Candidate has an impending exam/interview in hours or tomorrow.
- SKIP all small talk, introductions, and warm-up questions.
- Immediately simulate the most demanding, high-yield interview questions they are guaranteed to face.
- If their answer lacks technical rigor, be blunt, accurate, and point out the exact blindspot.
- Keep evaluations tight, brutal, and memorable so they don't make the mistake in the real viva.
""",
        "⚡ Advanced Mastery Mode": """
- FOCUS: Deep architectural reasoning, edge-cases, race conditions, internal runtime behaviors, and trade-offs.
- Interrogate their choices: 'Why not Paxos?', 'What happens during a network partition?', 'How does the OS handle thrashing here?'.
- Demand exact terminology (e.g. CAS operations, cache invalidation protocols, memory barriers).
""",
        "🌱 Beginner / Foundation Mode": """
- FOCUS: Clear core mental models, fundamentals, and structured explanations.
- Patient and constructive tone, but firm on technical accuracy.
- Break down complex mechanisms into intuitive first-principles if the candidate struggles.
"""
    }

    prompt = f"""You are the lead AI Interviewer in 'VivaVoce - Emergency AI Mock Interview & Viva Simulator'.

INTERVIEW TARGET:
Candidate Goal / Deadline: "{goal}"
Target Topics: "{topics if topics else 'Core topics for the stated target'}"
Mode: {mode}
Persona: {persona}

MODE DIRECTIVES:
{mode_rules.get(mode, "")}

CRITICAL RESPONSE FORMAT RULES:
For every response after the candidate answers, you MUST format your answer with these EXACT markdown headers:

### 📝 Viva Evaluation & Score
- **Score:** [Give an exact score between 1 and 10, e.g. 7.5/10]
- **Key Strengths:** [1-2 concise bullet points on what they got right]
- **Fatal Blindspots / Missing Nuances:** [Exact technical details, corner cases, or keywords an examiner/interviewer expects that candidate missed]
- **Spoken Delivery & Clarity:** [Feedback on candidate's conciseness, verbal delivery, or confidence]

---

### ❓ Question [N]: [Topic Title]
[State the next probing viva question clearly, directly, and aggressively. No pleasantries. Grill them on the next critical topic.]

If this is the initial kickoff of the interview (Question 1), set the stage in 2 high-intensity sentences, then directly issue Question 1 under the header:
### ❓ Question 1: [Topic Title]
"""
    return prompt


def parse_score_from_response(text):
    """Extracts score from markdown text like **Score:** 7.5/10."""
    try:
        match = re.search(r"Score:\*?\*?\s*\[?(\d+(?:\.\d+)?)\s*/\s*10\]?", text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    except Exception:
        pass
    return None


def execute_gemini_turn(client, model_name, system_instruction, history_messages, spoken_audio=None, written_text=None):
    """Executes a multimodal or text turn using Google Gemini API (`google-genai`)."""
    contents = []
    
    # 1. Populate previous history
    for msg in history_messages:
        if msg["role"] == "interviewer":
            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
        elif msg["role"] == "student":
            text_repr = msg.get("content", "")
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"Candidate's Answer:\n{text_repr}")]
                )
            )
            
    # 2. Add current candidate answer
    new_parts = []
    if spoken_audio is not None:
        # Multimodal audio input
        audio_bytes, audio_mime = spoken_audio
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=audio_mime or "audio/wav"
        )
        new_parts.append(audio_part)
        new_parts.append(
            types.Part.from_text(
                text="[Candidate Spoken Audio Response]\nPlease listen to my verbal answer, transcribe it accurately in your evaluation, critique my technical accuracy and tone, score it out of 10, and provide the next tough viva question."
            )
        )
    elif written_text:
        new_parts.append(
            types.Part.from_text(
                text=f"[Candidate Written Response]\n{written_text}\n\nPlease evaluate my response, score it out of 10, and provide the next tough viva question."
            )
        )
        
    contents.append(types.Content(role="user", parts=new_parts))
    
def call_gemini_with_fallback(client, preferred_model, contents, config=None):
    """Executes a Gemini generation call with automatic fallback if a model is deprecated (404) or experiencing high demand (503)."""
    candidate_chain = [
        preferred_model,
        "gemini-3.5-flash",
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.5-flash-lite",
        "gemini-flash-latest"
    ]
    seen = set()
    models_to_try = []
    for m in candidate_chain:
        if m and m not in seen:
            seen.add(m)
            models_to_try.append(m)

    last_error = None
    for model in models_to_try:
        try:
            kwargs = {"model": model, "contents": contents}
            if config is not None:
                kwargs["config"] = config
            return client.models.generate_content(**kwargs)
        except Exception as err:
            last_error = err
            err_msg = str(err)
            # If model is deprecated (404) or busy (503), gracefully try next model in chain
            if any(code in err_msg for code in ["404", "503", "NOT_FOUND", "UNAVAILABLE"]):
                continue
            raise err
    raise last_error


def execute_gemini_turn(client, model_name, system_instruction, history_messages, spoken_audio=None, written_text=None):
    """Executes a multimodal or text turn using Google Gemini API (`google-genai`)."""
    contents = []
    
    # 1. Populate previous history
    for msg in history_messages:
        if msg["role"] == "interviewer":
            contents.append(
                types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=msg["content"])]
                )
            )
        elif msg["role"] == "student":
            text_repr = msg.get("content", "")
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=f"Candidate's Answer:\n{text_repr}")]
                )
            )
            
    # 2. Add current candidate answer
    new_parts = []
    if spoken_audio is not None:
        # Multimodal audio input
        audio_bytes, audio_mime = spoken_audio
        audio_part = types.Part.from_bytes(
            data=audio_bytes,
            mime_type=audio_mime or "audio/wav"
        )
        new_parts.append(audio_part)
        new_parts.append(
            types.Part.from_text(
                text="[Candidate Spoken Audio Response]\nPlease listen to my verbal answer, transcribe it accurately in your evaluation, critique my technical accuracy and tone, score it out of 10, and provide the next tough viva question."
            )
        )
    elif written_text:
        new_parts.append(
            types.Part.from_text(
                text=f"[Candidate Written Response]\n{written_text}\n\nPlease evaluate my response, score it out of 10, and provide the next tough viva question."
            )
        )
        
    contents.append(types.Content(role="user", parts=new_parts))
    
    # 3. Call Gemini API with automatic model fallback
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=0.7,
        max_output_tokens=2048,
    )
    
    response = call_gemini_with_fallback(
        client=client,
        preferred_model=model_name or "gemini-3.5-flash",
        contents=contents,
        config=config
    )
    return response.text


# ==========================================
# 5. SCREEN A: THE EMERGENCY LANDING SCREEN
# ==========================================
if not st.session_state.session_active:
    st.markdown("""
    <div class="emergency-banner">
        <div class="emergency-badge">🚨 EMERGENCY VIVA CRASH-PREP PROTOCOL</div>
        <h1 style="color: #ffffff; margin-top: 0; font-size: 2.2rem; font-weight: 800;">
            VivaVoce: Real-Time AI Viva & Technical Hot Seat
        </h1>
        <p style="font-size: 1.1rem; color: #8b949e; max-width: 850px; line-height: 1.5;">
            Got a high-stakes viva or FAANG interview in a few hours? Reading slides won't save you. 
            <strong>Speak your answers out loud</strong> to Google Gemini in real-time. Experience ruthless scrutiny, instant scoring, and high-yield edge-case grilling.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Missing API Key Warning Banner
    if not st.session_state.get("gemini_api_key"):
        st.warning(
            "👉 **Action Required:** Please enter your **Gemini API Key** in the left sidebar to unlock the simulation. "
            "Get a free key from [Google AI Studio](https://aistudio.google.com/apikey).",
            icon="🔑"
        )

    # Preset Quick Buttons
    st.markdown("##### ⚡ Quick Urgency Presets (Click to autofill):")
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        if st.button("🏢 Google/Meta L5 Systems (Tomorrow morning)", use_container_width=True):
            st.session_state.temp_goal = "Tomorrow 9 AM is my Google L5 Distributed Systems & Microservices Interview."
            st.session_state.temp_topics = "Raft Consensus, CAP Theorem, Distributed Caching, Sharding, Concurrency & Deadlocks"
    with col_p2:
        if st.button("💾 OS & Concurrency Viva (In 2 Hours)", use_container_width=True):
            st.session_state.temp_goal = "University Operating Systems final viva in 2 hours with a strict professor."
            st.session_state.temp_topics = "Process Synchronization, Semaphores vs Mutexes, Virtual Memory Page Faults, Thrashing, Inverted Page Tables"
    with col_p3:
        if st.button("🐍 Python Backend & Architecture (Tonight)", use_container_width=True):
            st.session_state.temp_goal = "Senior Backend Engineer viva tonight on Python internals and database optimization."
            st.session_state.temp_topics = "GIL mechanics, asyncio event loop, B-Tree vs LSM trees, Redis caching patterns, DB transaction isolation levels"

    # Emergency Target Input Form
    st.markdown("<br>", unsafe_allow_html=True)
    with st.container():
        user_goal = st.text_area(
            "🎯 What are you preparing for and when is it?",
            value=st.session_state.get("temp_goal", ""),
            placeholder="e.g., 'Tomorrow at 10 AM is my Distributed Systems final viva. The professor grills on consensus algorithms and partition tolerance...'",
            height=90,
            help="Be specific! Mention the company, course, or professor, and the deadline so Gemini tunes the urgency."
        )
        
        user_topics = st.text_input(
            "📌 Specific Topics / Blindspots to Drill (Optional):",
            value=st.session_state.get("temp_topics", ""),
            placeholder="e.g., Raft, Paxos, 2PC, Database Indexes, Cache Invalidation, Deadlocks",
            help="Comma-separated topics you want to ensure are grilled."
        )

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Initialize Simulation Button
    btn_col1, btn_col2, btn_col3 = st.columns([1, 2, 1])
    with btn_col2:
        start_btn = st.button("🚨 INITIALIZE CRASH SIMULATION", type="primary", use_container_width=True)

    if start_btn:
        api_key = st.session_state.get("gemini_api_key", "").strip()
        if not api_key:
            st.error("❌ Cannot start simulation: Missing Gemini API Key. Please provide it in the sidebar field.")
        elif not user_goal.strip():
            st.warning("⚠️ Please provide what you are preparing for and your deadline before initializing.")
        else:
            client = get_gemini_client()
            if client:
                with st.spinner("⚡ Initializing high-stakes simulation environment & synthesizing Question 1..."):
                    try:
                        st.session_state.simulation_goal = user_goal.strip()
                        st.session_state.target_topics = user_topics.strip()
                        st.session_state.session_start_time = datetime.now()
                        st.session_state.question_counter = 1
                        st.session_state.scores_history = []
                        st.session_state.messages = []
                        
                        system_prompt = build_system_prompt(
                            goal=st.session_state.simulation_goal,
                            topics=st.session_state.target_topics,
                            mode=st.session_state.viva_mode,
                            persona=st.session_state.interviewer_persona
                        )
                        st.session_state.system_prompt = system_prompt
                        
                        # Generate the first question
                        model_name = st.session_state.get("model_choice", "gemini-3.5-flash")
                        init_response = call_gemini_with_fallback(
                            client=client,
                            preferred_model=model_name,
                            contents=[
                                types.Content(
                                    role="user",
                                    parts=[types.Part.from_text(
                                        text=f"Candidate has entered the viva room under {st.session_state.viva_mode}. Start immediately with Question 1."
                                    )]
                                )
                            ],
                            config=types.GenerateContentConfig(
                                system_instruction=system_prompt,
                                temperature=0.7
                            )
                        )
                        
                        opening_question = init_response.text
                        st.session_state.messages.append({
                            "role": "interviewer",
                            "content": opening_question,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        
                        st.session_state.session_active = True
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error initializing simulation: {e}")


# ==========================================
# 6. SCREEN B: ACTIVE SIMULATION & VOICE LOOP
# ==========================================
else:
    # 6.1 HUD & Header
    hud_c1, hud_c2, hud_c3, hud_c4 = st.columns([3, 1, 1, 1])
    with hud_c1:
        st.markdown(f"#### 🎙️ Live Viva: **{st.session_state.simulation_goal}**")
        st.caption(f"Mode: **{st.session_state.viva_mode}** | Persona: **{st.session_state.interviewer_persona}**")
    with hud_c2:
        st.markdown(f"""
        <div class="hud-stat-box">
            <div class="hud-stat-num">#{st.session_state.question_counter}</div>
            <div class="hud-stat-label">Question</div>
        </div>
        """, unsafe_allow_html=True)
    with hud_c3:
        if st.session_state.scores_history:
            latest_score = st.session_state.scores_history[-1]
            st.markdown(f"""
            <div class="hud-stat-box">
                <div class="hud-stat-num">{latest_score:.1f}</div>
                <div class="hud-stat-label">Last Score</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="hud-stat-box">
                <div class="hud-stat-num">—</div>
                <div class="hud-stat-label">Last Score</div>
            </div>
            """, unsafe_allow_html=True)
    with hud_c4:
        if st.session_state.session_start_time:
            elapsed_mins = int((datetime.now() - st.session_state.session_start_time).total_seconds() // 60)
            st.markdown(f"""
            <div class="hud-stat-box">
                <div class="hud-stat-num">{elapsed_mins}m</div>
                <div class="hud-stat-label">Duration</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # 6.2 Scorecard Display if Triggered
    if st.session_state.show_scorecard:
        st.markdown("### 📋 Final Viva Readiness Scorecard & Debrief")
        
        if not st.session_state.final_scorecard_text:
            client = get_gemini_client()
            if client:
                with st.spinner("🧠 Gemini is analyzing full interview transcript to synthesize your Emergency Scorecard..."):
                    debrief_prompt = f"""You are the senior examiner. Review the candidate's complete viva transcript and provide an Emergency Debrief:
Transcript History:
{[(m['role'], m.get('content', '')) for m in st.session_state.messages]}

Format your response in sleek, actionable markdown:
## 🏁 Final Viva Readiness Score: [Score out of 100%]
### 🏆 Top 3 Core Strengths Demonstrated:
[Bullet points]

### 🚨 Critical Fatal Flaws & Blindspots (Must fix before viva):
[Exact concepts where candidate struggled or gave vague answers]

### ⚡ Last-Minute Rapid Cheat Sheet (Memorize in the final hours):
[5-7 high-yield definitions, architecture rules, or formulas candidate should glance at before walking in]

### 🎯 Examiner's Verdict:
[Pass / Distinction / At Risk] with a final 2-sentence piece of advice.
"""
                    try:
                        resp = call_gemini_with_fallback(
                            client=client,
                            preferred_model=st.session_state.get("model_choice", "gemini-3.5-flash"),
                            contents=debrief_prompt
                        )
                        st.session_state.final_scorecard_text = resp.text
                    except Exception as e:
                        st.error(f"Failed to generate scorecard: {e}")
                        
        if st.session_state.final_scorecard_text:
            st.markdown(st.session_state.final_scorecard_text)
            
            # Download report button
            st.download_button(
                label="📥 Download Viva Report & Cheat Sheet (.md)",
                data=st.session_state.final_scorecard_text,
                file_name=f"VivaVoce_Debrief_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown"
            )
            
            if st.button("⬅️ Return to Interview Session"):
                st.session_state.show_scorecard = False
                st.rerun()
                
            st.stop()

    # 6.3 Chat Transcript Display
    st.markdown("##### 📜 Live Interview Transcript")
    
    for idx, msg in enumerate(st.session_state.messages):
        role = msg["role"]
        content = msg.get("content", "")
        ts = msg.get("timestamp", "")
        
        if role == "interviewer":
            st.markdown(f"""
            <div class="interviewer-bubble">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #f85149; font-size: 0.95rem;">
                        🤖 AI Interviewer ({st.session_state.interviewer_persona})
                    </span>
                    <span style="color: #8b949e; font-size: 0.8rem;">{ts}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # Display content with markdown rendering
            st.markdown(content)
            st.markdown("</div>", unsafe_allow_html=True)
            
        elif role == "student":
            st.markdown(f"""
            <div class="candidate-bubble">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; color: #56d364; font-size: 0.95rem;">
                        👤 Candidate (You)
                    </span>
                    <span style="color: #8b949e; font-size: 0.8rem;">{ts}</span>
                </div>
            """, unsafe_allow_html=True)
            
            # If audio bytes are attached, render an audio player
            if msg.get("audio_bytes"):
                st.audio(msg["audio_bytes"], format=msg.get("audio_mime", "audio/wav"))
                
            if content:
                st.markdown(content)
            else:
                st.caption("*(Spoken audio response)*")
                
            st.markdown("</div>", unsafe_allow_html=True)

    # 6.4 The Response & Voice Loop Interface
    st.markdown("---")
    st.markdown("#### 🎙️ Your Turn to Answer")
    
    input_tab1, input_tab2 = st.tabs(["🎙️ Native Voice Input (Recommended)", "⌨️ Text Response Fallback"])
    
    spoken_audio_payload = None
    written_text_payload = None
    trigger_submission = False
    
    with input_tab1:
        st.markdown(
            "<small style='color: #8b949e;'>Click the red record button, speak your viva answer directly into your microphone, then click stop to finalize.</small>",
            unsafe_allow_html=True
        )
        # Streamlit's native audio input component
        recorded_audio = st.audio_input(
            label="Record your answer:",
            key=f"audio_input_q_{st.session_state.question_counter}"
        )
        
        if recorded_audio is not None:
            audio_bytes = recorded_audio.getvalue()
            audio_mime = recorded_audio.type or "audio/wav"
            
            # Hash to verify this is a new recording
            audio_hash = hash(audio_bytes)
            
            sub_col1, sub_col2 = st.columns([1, 2])
            with sub_col1:
                if st.button("🚀 Submit Spoken Answer to Interviewer", type="primary", use_container_width=True):
                    spoken_audio_payload = (audio_bytes, audio_mime)
                    trigger_submission = True
            with sub_col2:
                st.caption("💡 Gemini directly analyzes your tone, pace, and technical vocabulary from the audio.")
                
    with input_tab2:
        user_typed_answer = st.text_area(
            "Type your answer if microphone is unavailable:",
            placeholder="Structure your answer clearly with key technical terms...",
            height=120,
            key=f"text_input_q_{st.session_state.question_counter}"
        )
        if st.button("📤 Submit Typed Answer", use_container_width=True):
            if user_typed_answer.strip():
                written_text_payload = user_typed_answer.strip()
                trigger_submission = True
            else:
                st.warning("Please type an answer before submitting.")

    # 6.5 Process Candidate Submission
    if trigger_submission:
        client = get_gemini_client()
        if not client:
            st.error("Gemini API Key missing or client failed to initialize. Please check sidebar.")
        else:
            with st.spinner("⚡ AI Examiner is listening, evaluating technical depth, and preparing the next question..."):
                try:
                    # 1. Record student turn in session
                    if spoken_audio_payload:
                        st.session_state.messages.append({
                            "role": "student",
                            "content": "",
                            "audio_bytes": spoken_audio_payload[0],
                            "audio_mime": spoken_audio_payload[1],
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                    elif written_text_payload:
                        st.session_state.messages.append({
                            "role": "student",
                            "content": written_text_payload,
                            "audio_bytes": None,
                            "timestamp": datetime.now().strftime("%H:%M:%S")
                        })
                        
                    # 2. Call Gemini
                    gemini_response_text = execute_gemini_turn(
                        client=client,
                        model_name=st.session_state.get("model_choice", "gemini-3.5-flash"),
                        system_instruction=st.session_state.system_prompt,
                        history_messages=st.session_state.messages[:-1],
                        spoken_audio=spoken_audio_payload,
                        written_text=written_text_payload
                    )
                    
                    # 3. Parse score if available
                    score = parse_score_from_response(gemini_response_text)
                    if score is not None:
                        st.session_state.scores_history.append(score)
                        
                    # 4. Increment question counter
                    st.session_state.question_counter += 1
                    
                    # 5. Append interviewer turn
                    st.session_state.messages.append({
                        "role": "interviewer",
                        "content": gemini_response_text,
                        "timestamp": datetime.now().strftime("%H:%M:%S")
                    })
                    
                    st.rerun()
                    
                except APIError as api_err:
                    st.error(f"Google Gemini API Error: {api_err.message}")
                except Exception as e:
                    st.error(f"Simulation Error: {e}")

