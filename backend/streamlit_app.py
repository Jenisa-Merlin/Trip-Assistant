import streamlit as st
import requests
import uuid
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional

# -----------------------
# Config
# -----------------------
DEFAULT_BACKEND = "http://127.0.0.1:8000/query"

# We'll try two likely DB locations (project root and backend/DB)
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parent.parent  # Trip-Assistant/
CANDIDATE_DB_PATHS = [
    PROJECT_ROOT / "airline.db",
    THIS_FILE.parent / "DB" / "airline.db",
    THIS_FILE.parent / "airline.db",
]

DB_PATH = next((p for p in CANDIDATE_DB_PATHS if p.exists()), CANDIDATE_DB_PATHS[0])

# -----------------------
# Styling (polished)
# -----------------------
st.set_page_config(page_title="Trip Assistant", layout="wide", page_icon="✈️")
APP_CSS = """
<style>
:root{
    --bg:#0b0f14;
    --panel:#0f1720;
    --muted:#94a3b8;
    --accent:#0b5cff;
    --card:#0b1220;
    --bubble-user:linear-gradient(135deg,#0b5cff,#1e90ff);
    --bubble-assistant:linear-gradient(135deg,#0f1720,#0b1220);
}
body { background: var(--bg); color: #e6eefb; }
.stApp > header { display: none; } /* hide top bar for a cleaner demo */
.chat-card { background: var(--card); border-radius: 12px; padding: 18px; box-shadow: 0 8px 30px rgba(2,6,23,0.6); }
.sidebar .sidebar-content { background: linear-gradient(180deg,#0b0f14,#07101a); padding: 16px; border-radius: 8px; }
.bubble-user { background: var(--bubble-user); color: white; padding:12px 16px; border-radius:14px; display:inline-block; max-width:80%; }
.bubble-assistant { background: linear-gradient(180deg,#0b1220,#0f1726); color:#e6eefb; padding:12px 16px; border-radius:14px; display:inline-block; max-width:80%; border:1px solid rgba(255,255,255,0.03); }
.small-muted { color: var(--muted); font-size:13px; }
.header-brand { font-weight:700; color:var(--accent); font-size:20px; margin-bottom:6px; }
.footer-note { color: var(--muted); font-size:13px; margin-top:10px; }

/* --- NEW: Improved Button Styles --- */

/* Style all default 'quick action' buttons */
.stButton > button {
    background: transparent;
    color: #e6eefb;
    border-radius: 8px;
    padding: 8px 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.2s ease;
    width: 100%; /* Make them fill their column */
}
.stButton > button:hover {
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(11, 92, 255, 0.1);
}
.stButton > button:active {
    background: rgba(11, 92, 255, 0.15);
}

/* Style the primary 'Send' button in the form */
.stForm .stButton > button {
    background: var(--accent);
    color: white;
    border: 1px solid var(--accent);
}
.stForm .stButton > button:hover {
    background: #0a4ecb; /* A bit darker */
    border-color: #0a4ecb;
    color: white;
}

/* Style sidebar buttons (Load table, Clear, Reset) */
.sidebar .stButton > button {
    background-color: var(--panel);
    border-color: rgba(255, 255, 255, 0.1);
}
.sidebar .stButton > button:hover {
    background-color: var(--panel);
    border-color: var(--accent);
    color: var(--accent);
}

/* --- NEW: Fix for text input visibility --- */
.stTextInput label {
    color: #e6eefb !important; /* Make label visible */
    padding-bottom: 6px; /* Add some space below label */
}
.stTextInput input {
    background: var(--panel); /* Use the panel color for bg */
    color: #e6eefb; /* Bright text for typing */
    border: 1px solid rgba(255, 255, 255, 0.1); /* Subtle border */
    border-radius: 8px; /* Match button radius */
}
.stTextInput input::placeholder {
    color: var(--muted); /* Use the muted color */
    opacity: 1; /* Ensure it's not faded out */
}

</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

# -----------------------
# Helpers
# -----------------------
def build_backend_url() -> str:
    return st.session_state.get("backend_url", DEFAULT_BACKEND)

def backend_query(payload: dict) -> dict:
    url = build_backend_url()
    try:
        resp = requests.post(url, json=payload, timeout=12)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"Backend request failed: {e}"}

def ensure_session_state():
    # Must create keys BEFORE any widget with same key is instantiated
    if "messages" not in st.session_state:
        # **FIX (Feature):** Added 'data' key to support tables
        st.session_state["messages"] = [
            {
                "role": "assistant",
                "text": "Hey there! I'm your Trip Assistant. I can help with flight info, bookings, cancellations, and more. Just let me know what you need!",
                "data": None,
            }
        ]
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())
    if "input_text" not in st.session_state:
        st.session_state["input_text"] = ""
    if "pending_command" not in st.session_state:
        st.session_state["pending_command"] = None
    if "backend_url" not in st.session_state:
        st.session_state["backend_url"] = DEFAULT_BACKEND

# **FIX (Feature):** Added 'data' parameter to store DataFrames
def append_message(role: str, text: str, data: Optional[pd.DataFrame] = None):
    st.session_state.messages.append({"role": role, "text": text, "data": data})

def clear_chat():
    st.session_state["messages"] = []
    # **FIX 1:** Replaced 'experimental_rerun'
    st.rerun()

def read_table(table_name: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    # Basic protection against SQL injection
    if not table_name.isalnum():
        return pd.DataFrame()
    try:
        con = sqlite3.connect(str(DB_PATH))
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", con)
        return df
    except Exception:
        return pd.DataFrame()
    finally:
        try:
            con.close()
        except Exception:
            pass

# Initialize session state safely
ensure_session_state()

# If a quick action was clicked previously (pending_command), set input_text and clear pending
if st.session_state.pending_command:
    st.session_state.input_text = st.session_state.pending_command
    st.session_state.pending_command = None
    # We do *not* rerun here - the form will pick up the input_text now

# -----------------------
# Sidebar (Admin)
# -----------------------
with st.sidebar:
    st.markdown("<div class='sidebar-card'>", unsafe_allow_html=True)
    st.markdown("<div class='header-brand'>✈️ Trip Assistant</div>", unsafe_allow_html=True)
    st.markdown("<div class='small-muted'>Your Airline AI ChatBot</div>", unsafe_allow_html=True)
    st.markdown("---")
    # Backend URL input (bind to session_state)
    # st.text_input("Backend URL", key="backend_url")
    # st.markdown("**Quick user selection**")
    # st.selectbox("Customer (user_id)", options=["None", "1", "2", "3", "4", "5"], key="selected_user")

    # --- NEW: Session controls moved from side panel to sidebar ---
    # st.markdown("---")
    # st.markdown("<h4 style='margin:0 0 10px 0'>Session</h4>", unsafe_allow_html=True)
    # st.caption("User ID (session):")
    # st.code(st.session_state.user_id)

    # Use columns for buttons
    # s_col1, s_col2 = st.columns(2)
    # with s_col1:
    if st.button("Clear chat", use_container_width=True):
        clear_chat()
    # with s_col2:
    #     if st.button("Reset user", use_container_width=True):
    #         st.session_state.user_id = str(uuid.uuid4())
    #         st.success("New user_id generated.")
    #         st.rerun() # Added rerun for immediate UI update
    # --- End of moved block ---

    # st.markdown("---")
    # # st.markdown("**Database inspector**")
    # if DB_PATH.exists():
    #     # st.success(f"DB found: {DB_PATH}")
    #     tbl = st.selectbox("Table to view", ["flights", "customers", "bookings", "policies", "seats"], key="inspect_table")
    #     if st.button("Load table", use_container_width=True): # Added width
    #         df = read_table(st.session_state.inspect_table)
    #         if df.empty:
    #             st.warning("Table empty or could not be read.")
    #         else:
    #             st.dataframe(df)
    # else:
    #     st.error(f"airline.db not found. Looked at these paths:\n" + "\n".join(str(p) for p in CANDIDATE_DB_PATHS))
    st.markdown("</div>", unsafe_allow_html=True)

# -----------------------
# Main layout
# --- REMOVED: col_main, col_side = st.columns([3, 1]) ---
# --- REMOVED: with col_main: (and un-indented contents) ---
# -----------------------
st.markdown("<div class='chat-card'>", unsafe_allow_html=True)
st.markdown("<div style='display:flex; gap:14px; align-items:center;'><div class='header-brand'>✈️ Trip Assistant</div></div>", unsafe_allow_html=True)
st.write("")

# --- NEW: Chat window with fixed height and scroll ---
chat_container = st.container(height=550)
with chat_container:
    for m in st.session_state.messages:
        if m["role"] == "user":
            st.markdown(f"<div style='display:flex; justify-content:flex-end; margin-bottom:10px'><div class='bubble-user'>{m['text']}</div></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='display:flex; justify-content:flex-start; margin-bottom:10px'><div class='bubble-assistant'>{m['text']}</div></div>", unsafe_allow_html=True)
            # **FIX (Feature):** Render dataframe if it exists in the message
            if m.get("data") is not None:
                st.dataframe(m["data"], use_container_width=True)

st.markdown("---")

# Input form (we already ensured input_text exists in session_state before creating widget)
# **FIX 2:** Changed 'clear_on_submit' to True to fix the StreamlitAPIException
with st.form(key="chat_form", clear_on_submit=True):
    user_text = st.text_input("Enter your message", key="input_text", placeholder="e.g. What is the status of flight AI202?")
    submit = st.form_submit_button("Send")

# Quick action buttons: instead of mutating input_text directly after widget creation,
# we set pending_command and then rerun, so the code above will copy pending_command into input_text
btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
with btn_col1:
    # --- NEW: Added use_container_width=True ---
    if st.button("Check status", use_container_width=True):
        st.session_state.pending_command = "What is the status of flight AI202?"
        # **FIX 1:** Replaced 'experimental_rerun'
        st.rerun()
with btn_col2:
    # --- NEW: Added use_container_width=True ---
    if st.button("Book a flight", use_container_width=True):
        st.session_state.pending_command = "I want to book a flight"
        # **FIX 1:** Replaced 'experimental_rerun'
        st.rerun()
with btn_col3:
    # --- NEW: Added use_container_width=True ---
    if st.button("Cancel a ticket", use_container_width=True):
        st.session_state.pending_command = "I want to cancel my flight ticket"
        # **FIX 1:** Replaced 'experimental_rerun'
        st.rerun()
with btn_col4:
    # --- NEW: Added use_container_width=True ---
    if st.button("Policies", use_container_width=True):
        st.session_state.pending_command = "What is the baggage policy?"
        # **FIX 1:** Replaced 'experimental_rerun'
        st.rerun()

# Handle submission
if submit:
    text = (st.session_state.get("input_text") or "").strip()
    if not text:
        st.warning("Please enter a message.")

    # **FIX (Feature):** Handle '/view' command locally
    elif text.startswith("/view "):
        table_name = text.split(" ", 1)[-1].strip()
        append_message("user", text)  # Add user's command to chat
        if not table_name:
            append_message("assistant", "Please specify a table name. e.g., `/view customers`")
        else:
            df = read_table(table_name)
            if df.empty:
                append_message("assistant", f"Table `{table_name}` is empty or does not exist.")
            else:
                append_message("assistant", f"Displaying table: `{table_name}`", data=df)
        # Rerun to show new messages (form clear_on_submit handles input)
        st.rerun()

    else:
        # choose selected user or existing session user_id
        sel = st.session_state.get("selected_user")
        if sel and sel != "None":
            st.session_state.user_id = str(sel)
        ensure_session_state()
        append_message("user", text)

        payload = {"query": text, "user_id": st.session_state.user_id}
        with st.spinner("Contacting backend..."):
            resp = backend_query(payload)
        if resp.get("error"):
            append_message("assistant", f"Error: {resp['error']}")
        else:
            assistant_text = resp.get("response") or str(resp)
            # if backend returns a new user_id, update it
            if resp.get("user_id"):
                st.session_state.user_id = resp["user_id"]
            append_message("assistant", assistant_text)

        # **FIX 2:** Removed 'st.session_state["input_text"] = ""'
        # (Handled by clear_on_submit=True in st.form)

        # **FIX 1:** Replaced 'experimental_rerun'
        # rerun to show updated chat immediately
        st.rerun()

# st.markdown("<div class='footer-note'>Tip: keep the same user_id to continue a multi-turn conversation. Use the sidebar to emulate customers.</div>", unsafe_allow_html=True)
# st.markdown("</div>", unsafe_allow_html=True)

# --- REMOVED: Entire 'with col_side:' block ---
# The session controls and shortcuts formerly here have been
# moved to the sidebar or removed for a cleaner UI.