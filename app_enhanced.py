
import json
import re
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
from faq_engine import FAQEngine, normalize_text

# Ollama is optional: CampusAssist should still run if it is not installed.
try:
    from ollama_service import ask_ollama
except ImportError:
    ask_ollama = None


# ---------------------------------------------------------
# PAGE SETUP
# ---------------------------------------------------------

st.set_page_config(
    page_title="CampusAssist | Student Support",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

CATEGORIES = {
    "Attendance": ("▦", "Understand requirements and absence guidance."),
    "Fees & Payments": ("▣", "Find fee schedules and payment guidance."),
    "Library Services": ("◫", "Explore borrowing, renewals and resources."),
    "Placements": ("▱", "Prepare for opportunities and applications."),
    "Academic Support": ("✎", "Find study advice and teaching support."),
    "Campus Services": ("⌖", "Navigate facilities and everyday help."),
    "Examinations": ("✧", "Find exam and results information."),
}

SUGGESTIONS = [
    "What are the attendance requirements?",
    "When is my next fee deadline?",
    "Can I renew a library book online?",
    "What are the placement eligibility rules?",
    "How do I contact academic support?",
    "How can I check my exam results?",
]


# ---------------------------------------------------------
# FAQ ENGINE
# ---------------------------------------------------------

@st.cache_resource
def load_engine():
    return FAQEngine()


try:
    engine = load_engine()
except Exception as exc:
    st.error(
        "CampusAssist couldn't load faqs.json. "
        "Check that the file exists and contains valid JSON."
    )
    st.code(str(exc))
    st.stop()


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

defaults = {
    "messages": [],
    "conversations": [],
    "dark_mode": False,
    "active_category": "All services",
    "pending_question": "",
    "last_topic": "",
    "message_feedback": {},
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------------------------------------------------
# CHAT RESPONSE LOGIC
# ---------------------------------------------------------

def personal_record_response(question):
    """Never pretend the demo has access to private student records."""
    q = normalize_text(question)

    marks_terms = [
        "mark", "marks", "grade", "grades", "result",
        "results", "score", "percentage", "cgpa", "sgpa",
        "gpa", "academic record", "report card",
    ]

    record_terms = [
        "my", "mine", "personal", "own", "i got",
        "i scored", "i have", "my attendance",
        "my fees", "my balance", "my account",
    ]

    marks_how_to = any(term in q for term in [
        "check my marks", "check marks", "view my marks", "see my marks",
        "check my result", "check results", "view results", "my grades",
        "how can i check", "how do i check",
    ]) and any(term in q for term in marks_terms)

    if marks_how_to or (any(term in q for term in marks_terms) and (
        any(term in q for term in record_terms)
        or q.startswith("what about")
        or q.startswith("how about")
    )):
        return (
            "I can help you understand your marks, but I can't "
            "access your personal academic records in this demo. "
            "You can check your institution's official results "
            "portal. If you share your marks here, I can help "
            "calculate your percentage or explain the grading "
            "calculation."
        )

    if any(term in q for term in [
        "my attendance", "my attendance percentage",
        "my attendance record",
    ]):
        return (
            "I can't see your personal attendance record yet. "
            "Please check your official student portal. If you "
            "share your attended classes and total classes, I can "
            "calculate the percentage for you."
        )

    if any(term in q for term in [
        "my fee", "my fees", "my fee balance",
        "my payment status", "did i pay",
    ]):
        return (
            "I can't access your personal payment records. Please "
            "check your official college fee portal or contact "
            "the accounts office to confirm your balance."
        )

    if any(term in q for term in [
        "my library account", "my borrowed books",
        "books i borrowed",
    ]):
        return (
            "Your library account isn't connected to this demo, "
            "so I can't see which books you borrowed. Check your "
            "library portal or ask the librarian for your current "
            "loan details."
        )

    return None


def get_response(question):
    """Route the question before attempting FAQ matching."""
    q = normalize_text(question)
    # Common informal spellings seen in student chat.
    typo_map = {
        "mrks": "marks", "markss": "marks", "makrs": "marks",
        "libary": "library", "librry": "library",
        "attendence": "attendance", "attandance": "attendance",
        "placemnt": "placement", "fee's": "fees",
        "exm": "exam", "timetablee": "timetable",
    }
    for wrong, right in typo_map.items():
        q = re.sub(rf"\b{re.escape(wrong)}\b", right, q)

    if not q:
        return (
            "Type a question about student services and I'll "
            "help you find the right information."
        ), "CampusAssist"

    # Personal data must be handled before general FAQ matching.
    corrected_question = q
    personal_answer = personal_record_response(corrected_question)
    if personal_answer:
        return personal_answer, "Personal records notice"

    if re.fullmatch(
        r"(hi|hii+|hello+|hey+|good morning|good afternoon|good evening|"
        r"hi there|hello there)",
        q,
    ):
        return (
            "Hello! 👋 I'm CampusAssist. You can ask me about "
            "attendance, fees, library services, placements, "
            "examinations, or academic support. What do you need?"
        ), "Conversation"

    if any(phrase in q for phrase in [
        "who are you", "what are you", "your name",
    ]):
        return (
            "I'm CampusAssist, a student-support chatbot prototype. "
            "I answer questions from a local FAQ knowledge base. "
            "Personal college records aren't connected yet."
        ), "About CampusAssist"

    if any(phrase in q for phrase in [
        "thank you", "thanks", "thank u", "thx",
    ]):
        return (
            "You're welcome! 🌿 Is there anything else about "
            "student services I can help you with?"
        ), "Conversation"

    if any(phrase in q for phrase in [
        "what about my marks", "how about my marks",
        "what about marks", "and my marks",
        "what about my result", "how about my result",
    ]):
        return (
            "I can help with your marks, but I can't access your "
            "personal results in this demo. Are you trying to "
            "check your results, calculate your percentage, or "
            "understand your grades?"
        ), "Personal records notice"

    if q in {
        "can you help me",
        "can you help",
        "help me",
        "i need help",
        "what can you do",
    }:
        return (
            "Of course! I can help with attendance rules, fee "
            "payments, library services, placements, examinations, "
            "and academic support. Choose a suggested question "
            "or tell me what you need."
        ), "Getting started"

    # Handle direct requests about service categories.
    category_questions = {
        "attendance": (
            "Attendance",
            "Attendance requirements and absence guidance can vary by institution. "
            "Check your student handbook or official portal for the required "
            "attendance percentage and the procedure for explaining absences."
        ),
        "fees": (
            "Fees & Payments",
            "For fee schedules, payment deadlines, receipts, and late-payment rules, "
            "check your institution's official fee portal or contact the accounts "
            "office. This demo does not know your personal balance or deadline."
        ),
        "library": (
            "Library Services",
            "The library can help with borrowing, renewals, returns, and study "
            "resources. Check your institution's library portal or ask a librarian "
            "about loan periods and renewal rules."
        ),
        "placements": (
            "Placements",
            "Check your placement cell's announcements, eligibility criteria, "
            "application deadlines, and recruitment drives. Keep your resume updated "
            "and practise aptitude, technical, and interview questions."
        ),
        "academic support": (
            "Academic Support",
            "For academic support, contact your faculty advisor, course instructor, "
            "department office, or tutoring centre if available. Include your course "
            "name and explain the topic you need help with."
        ),
        "campus services": (
            "Campus Services",
            "For campus facilities, check your college directory or student portal "
            "for office locations, contact details, facility timings, and student "
            "support services."
        ),
        "examinations": (
            "Examinations",
            "For examination schedules, hall tickets, results, and grading rules, "
            "check your institution's official exam portal or contact the examination "
            "office. This demo cannot access your personal results."
        ),
    }

    # Normalize ampersands and punctuation so "fees & payments" and
    # "fees and payments" are treated alike.
    category_text = q.replace("&", " and ")
    category_text = re.sub(r"[^a-z0-9\s]", " ", category_text)
    category_text = re.sub(r"\s+", " ", category_text).strip()

    direct_prefixes = (
        "tell me about ", "information about ", "tell me about the ",
        "show me ", "open ", "help with ", "help me with ",
    )
    topic = category_text
    for prefix in direct_prefixes:
        if topic.startswith(prefix):
            topic = topic[len(prefix):].strip()
            break

    aliases = [
        (("fees and payments", "fees payments", "fee and payment", "fee payment", "fees", "fee"), "fees"),
        (("placement", "placements"), "placements"),
        (("library", "library services"), "library"),
        (("attendance",), "attendance"),
        (("academic support", "study support"), "academic support"),
        (("campus services", "campus facility", "campus facilities"), "campus services"),
        (("examination", "examinations", "exam", "exams"), "examinations"),
    ]

    # Understand natural category requests such as "can I know about library?"
    # and "tell me about fees & payments" without hijacking detailed questions.
    request_starters = (
        "tell me about ", "information about ", "about ", "show me ",
        "open ", "help with ", "help me with ", "can i know about ",
        "can you tell me about ", "i want to know about ",
        "what about ", "explain ",
    )
    topic = category_text
    for prefix in request_starters:
        if topic.startswith(prefix):
            topic = topic[len(prefix):].strip()
            break

    # Remove polite filler and trailing punctuation from the topic.
    topic = re.sub(r"^(the|your)\s+", "", topic).strip()
    topic = re.sub(r"\bplease\b", "", topic).strip()
    topic = re.sub(r"\s+", " ", topic).strip()

    for phrases, key in aliases:
        if topic in phrases or any(
            topic == phrase + " services" for phrase in phrases
        ):
            category, answer = category_questions[key]
            return answer, category

    result = engine.search(question)

    if result:
        category = result.get("category", "Student services")
        answer = str(result["answer"])
        return answer, category

    # General-purpose AI is used only after the local FAQ has no match.
    # Do not ask it to guess institution-specific rules or student records.
    college_specific_phrases = (
        "my attendance", "attendance percentage", "minimum attendance",
        "attendance requirement", "attendance shortage", "attendance rule",
        "my fee", "my fees", "fee deadline", "fees deadline", "payment deadline",
        "late fee", "fee balance", "fee receipt", "my library account",
        "books i borrowed", "book i borrowed", "renew my book", "my placement eligibility",
        "placement eligibility", "placement deadline", "placement drive date",
        "exam schedule", "exam date", "exam timetable", "hall ticket",
        "my result", "my marks", "my grade", "my cgpa", "my sgpa",
        "semester result", "results date", "result date", "college deadline",
        "college policy", "college rule", "college fee", "college fees",
        "hostel fee", "hostel rules", "scholarship deadline", "student portal",
        "academic calendar", "office timing", "office hours",
    )
    is_college_specific = any(phrase in q for phrase in college_specific_phrases)

    if not is_college_specific and ask_ollama is not None:
        try:
            ai_answer = ask_ollama(question)
        except Exception:
            # A local model failure should never crash the Streamlit interface.
            ai_answer = None
        if ai_answer:
            return ai_answer, "Local AI · Qwen3 (Ollama)"

    return (
        "I want to help, but I couldn't find a trustworthy match in "
        "the information available to this demo. Could you rephrase "
        "the question or tell me which area it belongs to: attendance, "
        "fees, library, placements, exams, or academic support? "
        "For how-to questions about marks, I can guide you to your "
        "official results portal; I cannot fetch private college records."
    ), "Needs clarification"


def start_new_conversation():
    if st.session_state.messages:
        st.session_state.conversations.insert(
            0, st.session_state.messages.copy()
        )
        st.session_state.conversations = (
            st.session_state.conversations[:8]
        )

    st.session_state.messages = []
    st.session_state.last_topic = ""
    st.session_state.pending_question = ""


def submit_question(question):
    question = str(question or "").strip()
    if not question:
        return

    answer, source = get_response(question)

    st.session_state.messages.append({
        "role": "user",
        "content": question,
        "time": datetime.now().strftime("%I:%M %p"),
    })

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer,
        "source": source,
        "time": datetime.now().strftime("%I:%M %p"),
    })

    st.session_state.pending_question = ""


# ---------------------------------------------------------
# COLOUR PALETTE — MATCHES YOUR REFERENCE
# ---------------------------------------------------------

if st.session_state.dark_mode:
    bg = "#102E2B"
    sidebar_bg = "#103A36"
    card = "#19413C"
    text = "#F0F5EC"
    muted = "#B7C9C1"
    border = "#315750"
    accent = "#55C5AD"
    mint = "#234B43"
else:
    bg = "#F4F5EF"
    sidebar_bg = "#153D39"
    card = "#FFFEFA"
    text = "#1B3430"
    muted = "#6E7B75"
    border = "#E0E5DC"
    accent = "#0D8879"
    mint = "#E6F3EB"


# ---------------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------------

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

    :root {{
        --page: {bg};
        --sidebar: {sidebar_bg};
        --card: {card};
        --ink: {text};
        --muted: {muted};
        --border: {border};
        --accent: {accent};
        --mint: {mint};
    }}

    html, body, [data-testid="stAppViewContainer"] {{
        background: var(--page);
        color: var(--ink);
        font-family: 'DM Sans', sans-serif;
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stSidebar"] {{
        background: var(--sidebar);
        border-right: 1px solid rgba(255,255,255,.08);
    }}

    [data-testid="stSidebar"] * {{
        color: #EAF5EE;
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        line-height: 1.55;
    }}

    /* Sidebar controls need strong contrast in BOTH themes. */
    [data-testid="stSidebar"] div.stButton > button {{
        background: #204D46 !important;
        color: #F2F7F1 !important;
        border: 1px solid #35665D !important;
        border-radius: 13px !important;
        min-height: 42px;
        text-align: left;
    }}
    [data-testid="stSidebar"] div.stButton > button:hover {{
        background: #2C6258 !important;
        color: #FFFFFF !important;
        border-color: #77CDB8 !important;
    }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"],
    [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"] {{
        background: linear-gradient(135deg, #DDF3E3, #A9E1CF) !important;
        color: #153D39 !important;
        border-color: #A9E1CF !important;
        text-align: center;
    }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover,
    [data-testid="stSidebar"] div.stButton > button[data-testid="stBaseButton-primary"]:hover {{
        background: #B9E9D8 !important;
        color: #103A36 !important;
    }}

    h1, h2, h3 {{
        color: var(--ink);
        font-family: 'Playfair Display', Georgia, serif;
        letter-spacing: -.5px;
    }}

    .brand {{
        display:flex;
        align-items:center;
        gap:12px;
        padding: 8px 0 22px;
        color:#F2FAF2;
        font-size:19px;
        font-weight:700;
    }}

    .brand-icon {{
        width:43px;
        height:43px;
        display:grid;
        place-items:center;
        border-radius:15px;
        color:#143C36;
        background:linear-gradient(145deg,#D9F3DE,#8CD4BE);
        box-shadow:0 7px 18px #071E1B55;
        font-size:23px;
        transform:rotate(-5deg);
    }}

    .eyebrow {{
        color:var(--accent);
        font-size:12px;
        font-weight:700;
        letter-spacing:2.4px;
        text-transform:uppercase;
    }}

    .welcome {{
        background:
          radial-gradient(circle at 10% 20%, #D8F0E3 0, transparent 35%),
          radial-gradient(circle at 95% 5%, #F7EED8 0, transparent 38%),
          linear-gradient(125deg,#E5F4E9,#F8F5E9);
        border:1px solid #E3E9DD;
        border-radius:25px;
        padding:28px;
        color:#1A3B34;
        box-shadow:0 15px 40px #1B47370C;
        margin: 14px 0 25px;
        animation: rise .55s ease both;
    }}

    .welcome h2 {{
        color:#1A3B34;
        font-size:25px;
        margin:0 0 5px;
    }}

    .welcome p {{
        color:#5B6D63;
        font-size:14px;
        margin:0;
    }}

    .welcome-icon {{
        display:grid;
        place-items:center;
        width:68px;
        height:68px;
        border-radius:24px;
        color:white;
        font-size:33px;
        background:linear-gradient(145deg,#57BFA9,#08796F);
        box-shadow:0 12px 25px #147D7040;
        transform:rotate(-7deg);
    }}

    .section-label {{
        font-family:'Playfair Display', Georgia, serif;
        color:var(--ink);
        font-size:21px;
        font-weight:700;
        margin: 20px 0 5px;
    }}

    .section-note {{
        color:var(--muted);
        font-size:13px;
        margin-bottom:13px;
    }}

    .surface {{
        background:var(--card);
        border:1px solid var(--border);
        border-radius:19px;
        padding:18px;
        box-shadow:0 8px 25px #173D3210;
        transition:transform .2s ease, box-shadow .2s ease;
        height:100%;
    }}

    .surface:hover {{
        transform:translateY(-3px);
        box-shadow:0 14px 30px #173D3217;
    }}

    .service-icon {{
        display:grid;
        place-items:center;
        width:39px;
        height:39px;
        background:var(--mint);
        border-radius:13px;
        color:var(--accent);
        font-size:20px;
        margin-bottom:12px;
    }}

    .service-title {{
        font-size:15px;
        font-weight:700;
        color:var(--ink);
        margin-bottom:5px;
    }}

    .service-desc {{
        color:var(--muted);
        font-size:13px;
        line-height:1.5;
        min-height:39px;
    }}

    .status-note {{
        background:var(--mint);
        border-radius:13px;
        padding:12px;
        color:var(--muted);
        font-size:12px;
        line-height:1.5;
        margin-top:14px;
    }}

    .message-user {{
        background:var(--accent);
        color:white;
        border-radius:18px 18px 5px 18px;
        padding:13px 16px;
        margin:10px 0 10px auto;
        max-width:85%;
        width:fit-content;
        line-height:1.6;
        animation:rise .25s ease both;
    }}

    .message-bot {{
        background:var(--card);
        color:var(--ink);
        border:1px solid var(--border);
        border-radius:5px 18px 18px 18px;
        padding:15px 17px;
        margin:10px auto 10px 0;
        max-width:94%;
        line-height:1.65;
        box-shadow:0 5px 18px #173D3208;
        animation:rise .25s ease both;
    }}

    .message-meta {{
        color:var(--muted);
        font-size:11px;
        margin-top:7px;
    }}

    .demo-banner {{
        background:var(--mint);
        border:1px solid var(--border);
        border-radius:13px;
        padding:13px 15px;
        color:var(--muted);
        font-size:12px;
        line-height:1.6;
    }}

    
div.stButton > button {{
    background: var(--card);
    color: var(--ink);
    border: 1px solid var(--border);
    border-radius: 13px;
    transition: all .2s ease;
    font-weight: 600;
}}

div.stButton > button:hover {{
    background: var(--mint);
    color: var(--accent);
    border-color: var(--accent);
    transform: translateY(-2px);
}}

/* Keep the conversation export button readable in both themes. */
div[data-testid="stDownloadButton"] > button {{
    background: var(--card) !important;
    color: var(--ink) !important;
    border: 1px solid var(--border) !important;
    border-radius: 13px !important;
}}

/* Keep the main action teal, never bright red */
div.stButton > button[kind="primary"],
div.stButton > button[data-testid="stBaseButton-primary"] {{
    background: var(--accent);
    color: #FFFFFF;
    border: 1px solid var(--accent);
}}

div.stButton > button[kind="primary"]:hover,
div.stButton > button[data-testid="stBaseButton-primary"]:hover {{
    background: #096F63;
    color: #FFFFFF;
}}


    div[data-testid="stTextArea"] textarea,
    div[data-testid="stTextInput"] input {{
        border-radius:14px;
        background:var(--card);
        color:var(--ink);
        border-color:var(--border);
    }}

    @keyframes rise {{
        from {{ opacity:0; transform:translateY(8px); }}
        to {{ opacity:1; transform:translateY(0); }}
    }}

    @media (max-width: 900px) {{
        .welcome {{ padding:20px; }}
        .welcome h2 {{ font-size:22px; }}
        .message-bot, .message-user {{ max-width:100%; }}
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------

with st.sidebar:
    st.markdown(
        """
        <div class="brand">
          <div class="brand-icon">🎓</div>
          <span>CampusAssist</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "＋  New conversation",
        use_container_width=True,
        type="primary",
    ):
        start_new_conversation()
        st.rerun()

    st.markdown("### EXPLORE SERVICES")

    if st.button("▦  All services", use_container_width=True):
        st.session_state.active_category = "All services"

    for category, (symbol, _) in CATEGORIES.items():
        if st.button(
            f"{symbol}  {category}",
            key=f"nav_{category}",
            use_container_width=True,
        ):
            st.session_state.active_category = category
            st.session_state.pending_question = (
                f"Tell me about {category.lower()}."
            )

    st.divider()
    st.markdown("### CONVERSATION HISTORY")

    if not st.session_state.conversations:
        st.caption("Your recent conversations will appear here.")
    else:
        for index, conversation in enumerate(
            st.session_state.conversations
        ):
            first_question = next(
                (
                    message["content"]
                    for message in conversation
                    if message["role"] == "user"
                ),
                "Previous conversation",
            )
            label = first_question[:28]
            if st.button(
                f"▢  {label}",
                key=f"history_{index}",
                use_container_width=True,
            ):
                st.session_state.messages = conversation.copy()
                st.rerun()

    st.divider()
    st.toggle(
        "Dark mode",
        key="dark_mode",
        help="Switch between cream and deep-teal themes.",
    )
    st.caption("Student support · Demo prototype")


# ---------------------------------------------------------
# MAIN HEADER
# ---------------------------------------------------------

header_left, header_right = st.columns([3, 1])

with header_left:
    st.markdown(
        '<div class="eyebrow">YOUR CAMPUS, MADE SIMPLER</div>',
        unsafe_allow_html=True,
    )
    st.title("How can we help today?")

with header_right:
    st.write("")
    st.write("🌿  **Student**")

st.markdown(
    """
    <div class="welcome">
      <div style="display:flex;align-items:center;gap:18px;">
        <div class="welcome-icon">✧</div>
        <div>
          <h2>Hi, I'm CampusAssist.</h2>
          <p>Ask me anything about student services. I'll help you find a place to start.</p>
        </div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# THREE-COLUMN DASHBOARD
# ---------------------------------------------------------

main_col, gap_col, status_col = st.columns(
    [2.2, 0.08, 0.85],
    gap="small",
)

with main_col:
    st.markdown(
        '<div class="section-label">Suggested questions</div>'
        '<div class="section-note">Tap a question to start a conversation.</div>',
        unsafe_allow_html=True,
    )

    suggestion_cols = st.columns(2)

    for index, suggestion in enumerate(SUGGESTIONS):
        with suggestion_cols[index % 2]:
            if st.button(
                f"{suggestion}  ↗",
                key=f"suggestion_{index}",
                use_container_width=True,
            ):
                st.session_state.pending_question = suggestion

    st.markdown(
        '<div class="section-label">Student services</div>'
        '<div class="section-note">Find the right support for your question.</div>',
        unsafe_allow_html=True,
    )

    service_columns = st.columns(3)

    for index, (category, (symbol, description)) in enumerate(
        CATEGORIES.items()
    ):
        with service_columns[index % 3]:
            st.markdown(
                f"""
                <div class="surface">
                  <div class="service-icon">{symbol}</div>
                  <div class="service-title">{category}</div>
                  <div class="service-desc">{description}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Open ↗",
                key=f"open_{category}",
                use_container_width=True,
            ):
                st.session_state.active_category = category
                st.session_state.pending_question = (
                    f"Tell me about {category.lower()}."
                )
                st.rerun()

    st.markdown(
        '<div class="section-label">Conversation</div>'
        '<div class="section-note">Ask a question and continue the discussion.</div>',
        unsafe_allow_html=True,
    )

    for index, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.markdown(
                f'<div class="message-user">{message["content"]}'
                f'<div class="message-meta" style="color:#E1F5EE;">'
                f'{message.get("time", "")}</div></div>',
                unsafe_allow_html=True,
            )
        else:
            safe_content = (
                message["content"]
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\n", "<br>")
            )
            st.markdown(
                f'<div class="message-bot">'
                f'<strong>✧ CampusAssist</strong><br>{safe_content}'
                f'<div class="message-meta">Topic: '
                f'{message.get("source", "Student services")} · '
                f'{message.get("time", "")}</div></div>',
                unsafe_allow_html=True,
            )
            # Lightweight copy control: this is UI-only and does not touch
            # the FAQ engine or local AI service.
            # Encode the answer so quotes/newlines cannot break the HTML/JavaScript.
            import base64
            copy_text_b64 = base64.b64encode(
                str(message["content"]).encode("utf-8")
            ).decode("ascii")
            components.html(
                f"""<!doctype html>
                <html><body style="margin:0;background:transparent;font-family:sans-serif;">
                <button id="copy-answer" type="button"
                    style="border:1px solid #cbd5d1;border-radius:8px;padding:7px 12px;
                    background:#ffffff;color:#173f39;cursor:pointer;font-size:13px;">
                    Copy answer
                </button>
                <script>
                const encodedAnswer = "{copy_text_b64}";
                const button = document.getElementById("copy-answer");
                button.addEventListener("click", async () => {{
                    const answer = decodeURIComponent(escape(atob(encodedAnswer)));
                    try {{
                        await navigator.clipboard.writeText(answer);
                        button.textContent = "Copied!";
                    }} catch (error) {{
                        button.textContent = "Copy unavailable";
                    }}
                    setTimeout(() => button.textContent = "Copy answer", 1400);
                }});
                </script></body></html>""",
                height=42,
                scrolling=False,
            )
            feedback_key = str(message.get("time", "")) + ":" + str(index)
            feedback_value = st.session_state.message_feedback.get(feedback_key)
            feedback_col1, feedback_col2, feedback_col3 = st.columns([0.18, 0.22, 0.6])
            with feedback_col1:
                if st.button("👍 Helpful", key=f"feedback_yes_{index}",
                              type="secondary", disabled=feedback_value == "helpful"):
                    st.session_state.message_feedback[feedback_key] = "helpful"
                    st.toast("Thanks for your feedback!")
            with feedback_col2:
                if st.button("👎 Not helpful", key=f"feedback_no_{index}",
                              type="secondary", disabled=feedback_value == "not_helpful"):
                    st.session_state.message_feedback[feedback_key] = "not_helpful"
                    st.toast("Thanks — feedback noted for this session.")
            if feedback_value:
                st.caption("Feedback recorded for this session.")

    if not st.session_state.messages:
        st.info(
            "No messages yet. Choose a suggested question above "
            "or ask your own below."
        )

    with st.form("chat_form", clear_on_submit=True):
        user_question = st.text_input(
            "Your question",
            placeholder=(
                "Ask about attendance, fees, library, marks..."
            ),
            label_visibility="collapsed",
        )
        send_clicked = st.form_submit_button(
            "Send message  ➤",
            use_container_width=True,
            type="primary",
        )

    if send_clicked and user_question.strip():
        submit_question(user_question)
        st.rerun()

    if st.session_state.pending_question:
        question = st.session_state.pending_question
        submit_question(question)
        st.rerun()

    if st.session_state.messages:
        export_text = "\n\n".join(
            f"{'You' if item['role'] == 'user' else 'CampusAssist'}: "
            f"{item['content']}"
            for item in st.session_state.messages
        )

        download_col, clear_col = st.columns(2)

        with download_col:
            st.download_button(
                "↓ Export conversation",
                data=export_text,
                file_name="campusassist_conversation.txt",
                mime="text/plain",
                use_container_width=True,
                type="secondary",
            )

        with clear_col:
            if st.button(
                "Clear conversation",
                use_container_width=True,
            ):
                start_new_conversation()
                st.rerun()


with status_col:
    st.markdown(
        '<div class="surface">'
        '<div class="section-label" style="margin-top:0">Quick status</div>'
        '<div class="section-note">Sample information only.</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="surface">
          <div style="display:flex;justify-content:space-between;">
            <span>Attendance</span><strong>86%</strong>
          </div>
          <div style="height:7px;background:#DDE7DF;border-radius:8px;margin:12px 0 20px;">
            <div style="height:7px;width:86%;background:#0D8879;border-radius:8px;"></div>
          </div>
          <div style="display:flex;justify-content:space-between;margin:14px 0;">
            <span>Fees</span><strong>No pending alerts</strong>
          </div>
          <hr style="border-color:#E0E5DC;">
          <div style="display:flex;justify-content:space-between;margin:14px 0;">
            <span>Library</span><strong>2 books due soon</strong>
          </div>
          <hr style="border-color:#E0E5DC;">
          <div style="display:flex;justify-content:space-between;margin:14px 0;">
            <span>Placement profile</span><strong>Complete</strong>
          </div>
          <div class="status-note">
            Demo information. Connect your institution's systems
            to show live records.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown(
        """
        <div class="demo-banner">
          <strong>🌱 Need personal information?</strong><br><br>
          This prototype doesn't connect to student accounts.
          Check your official college portal for real marks,
          attendance, and payment records.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------
# FOOTER
# ---------------------------------------------------------

st.write("")
st.caption(
    "CampusAssist · Student support prototype · "
    "College-service answers use the local FAQ knowledge base; general questions "
    "may use local Qwen3 through Ollama. Personal college systems are not connected."
)
