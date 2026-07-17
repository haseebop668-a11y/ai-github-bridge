import streamlit as st
import uuid
import time
from utils import stream_zip_files_safely, call_openrouter, extract_code_blocks, commit_to_github

st.set_page_config(page_title="AI Enterprise Code Bridge", layout="wide", page_icon="⚡")

# --- ClickUp & Native Flutter-Like Micro-Shadow CSS Injection ---
st.markdown("""
<style>
    .stApp { background-color: #F6F7F9; }
    [data-testid="stSidebar"] { background-color: #FFFFFF !important; border-right: 1px solid #E2E8F0; }
    .enterprise-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.8rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        background-color: #7B61FF !important;
        color: white !important;
        border: none !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.01) !important;
        box-shadow: 0 6px 14px rgba(123,97,255,0.25) !important;
        opacity: 0.95;
    }
    .lock-badge {
        background-color: #00C853;
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 6px;
        font-size: 0.85rem;
        font-weight: bold;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. Isolated Session State Management ---
if "credentials_locked" not in st.session_state: st.session_state.credentials_locked = False
if "or_token" not in st.session_state: st.session_state.or_token = ""
if "git_token" not in st.session_state: st.session_state.git_token = ""
if "file_structure_map" not in st.session_state: st.session_state.file_structure_map = ""
if "zipped_code_context" not in st.session_state: st.session_state.zipped_code_context = ""
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "push_target_code" not in st.session_state: st.session_state.push_target_code = None
if "last_api_call_time" not in st.session_state: st.session_state.last_api_call_time = 0.0

# --- SIDEBAR: SECURE INFRASTRUCTURE CRYPT ---
with st.sidebar:
    st.markdown("### 🔐 Secure Token Gateway")
    if st.session_state.credentials_locked:
        st.markdown('<div class="lock-badge">🔒 Infrastructure Authenticated</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("🔓 Rotate / Unlock Credentials", use_container_width=True):
            st.session_state.credentials_locked = False
            st.rerun()
    else:
        st.session_state.or_token = st.text_input("OpenRouter Key", type="password", value=st.session_state.or_token, placeholder="sk-or-...")
        st.session_state.git_token = st.text_input("GitHub PAT Tokens", type="password", value=st.session_state.git_token, placeholder="ghp_...")
        if st.button("🔒 Lock Settings", use_container_width=True):
            if st.session_state.or_token and st.session_state.git_token:
                st.session_state.credentials_locked = True
                st.rerun()
            else:
                st.error("Both Enterprise Tokens Are Mandatory.")

# --- MAIN INDUSTRIAL DASHBOARD ---
st.markdown('<div class="enterprise-card">', unsafe_allow_html=True)
st.title("⚡ Universal Polyglot AI Agent Engine")
st.caption("Standard Target Alignment: Microsoft | Google | Anthropic Red Teaming Protocols")
st.markdown('</div>', unsafe_allow_html=True)

# Module A: Persistent Repository Context
st.markdown('<div class="enterprise-card">', unsafe_allow_html=True)
st.subheader("📁 Global Repository File Structure Map")
st.session_state.file_structure_map = st.text_area(
    "Paste Directory Tree Map Context Here:",
    value=st.session_state.file_structure_map,
    height=140,
    help="This environment map stays completely isolated and never wipes during chat clear actions."
)
st.markdown('</div>', unsafe_allow_html=True)

# Module B: Heavy-Capacity Archive Processing Core (Optimized Context Window)
st.markdown('<div class="enterprise-card">', unsafe_allow_html=True)
st.subheader("📥 Heavy-Capacity Archive Processing Core")
uploaded_file = st.file_uploader("Upload Multi-Language Source Zip:", type=["zip"])

if uploaded_file:
    if st.button("⚙️ Execute Asynchronous Scan Pipeline", use_container_width=True):
        progress_bar = st.progress(0)
        metrics_status = st.empty()
        
        total_files_processed = 0
        temp_context = ""
        
        for filepath, file_data in stream_zip_files_safely(uploaded_file):
            total_files_processed += 1
            metrics_status.markdown(f"**Streaming Chunk:** `{filepath}` | Parsing Structure...")
            progress_bar.progress(min(total_files_processed / 100, 1.0))
            
            # فیکس: لِمٹ کو بڑھا کر 80k کیا گیا ہے تاکہ پورا ریپو ماڈل کے فری کانٹیکسٹ ونڈو میں فٹ ہو سکے
            if len(temp_context) < 80000:
                temp_context += f"\n--- File Path: {filepath} ---\n{file_data[:1500]}\n"
        
        st.session_state.zipped_code_context = temp_context
        st.success(f"Successfully processed and token-mapped {total_files_processed} polyglot files safely into isolated state memory!")
st.markdown('</div>', unsafe_allow_html=True)

# Module C: Polyglot Chat Studio & Execution Core
st.markdown('<div class="enterprise-card">', unsafe_allow_html=True)
st.subheader("💬 Polyglot Chat Studio")

# Render active conversational logs
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            blocks = list(extract_code_blocks(msg["content"]))
            for idx, (lang, code) in enumerate(blocks):
                st.code(code, language=lang)
                if st.button(f"🚀 Initialize GitHub Push for Block #{idx+1}", key=f"trigger_{msg['id']}_{idx}"):
                    st.session_state.push_target_code = {"code": code, "lang": lang}
                    st.rerun()

if st.session_state.push_target_code:
    st.markdown("---")
    with st.form(key="github_deployment_form"):
        st.markdown("### 🚀 GitHub Code Push Deployment Drawer")
        repo = st.text_input("Repository Target (e.g., username/repo_name)")
        branch = st.text_input("Branch Base", "main")
        dest_path = st.text_input("Target Remote File Path", f"src/output.{st.session_state.push_target_code['lang']}")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            submit_push = st.form_submit_button("Confirm & Commit Changes")
        with col_f2:
            cancel_push = st.form_submit_button("Cancel")
            
        if submit_push and repo and dest_path:
            if not st.session_state.git_token:
                st.error("Missing GitHub Access Token in Gateway Panel.")
            else:
                with st.spinner("Executing Secure Direct Commit via Secure API Crypt..."):
                    ok, url_or_err = commit_to_github(
                        st.session_state.git_token, repo, branch, dest_path, 
                        st.session_state.push_target_code["code"], "Automated Commit via Enterprise Polyglot Agent Engine"
                    )
                    if ok:
                        st.success(f"Production Push Complete! View File: [GitHub Source Link]({url_or_err})")
                        st.session_state.push_target_code = None
                    else:
                        st.error(f"Git Pipeline Refused Commit: {url_or_err}")
        if cancel_push:
            st.session_state.push_target_code = None
            st.rerun()

# Command Input Area
user_query = st.text_area("Command Console / Raw Multi-Language Snippet Input:", height=100)

# Execution Control Row
col_run, col_clear = st.columns(2)
with col_run:
    if st.button("🔍 Scan & Refactor Base", use_container_width=True, type="primary"):
        current_time = time.time()
        cooldown_remaining = 5.0 - (current_time - st.session_state.last_api_call_time)
        
        if not st.session_state.credentials_locked:
            st.error("Access Denied: Lock your Vault Credentials first.")
        elif not user_query.strip():
            st.warning("Input console empty.")
        elif cooldown_remaining > 0:
            st.warning(f"⏳ Rate control active. Please wait {cooldown_remaining:.1f}s before scanning again.")
        else:
            full_payload = ""
            if st.session_state.zipped_code_context:
                full_payload += f"Uploaded Global Repository Context:\n{st.session_state.zipped_code_context}\n\n"
            
            full_payload += (
                f"System Environment Map:\n{st.session_state.file_structure_map}\n\n"
                f"Analyze or refactor the following instructions:\n{user_query}"
            )
            
            with st.spinner("Contacting OpenRouter Polyglot Core Cluster..."):
                st.session_state.last_api_call_time = time.time()
                
                ok, ai_text = call_openrouter(full_payload, st.session_state.or_token)
                if ok:
                    unique_id = str(uuid.uuid4())
                    st.session_state.chat_history.append({"role": "user", "content": user_query, "id": f"u_{unique_id}"})
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_text, "id": f"a_{unique_id}"})
                    st.rerun()
                else:
                    st.error(url_or_err if 'url_or_err' in locals() else ai_text)

with col_clear:
    if st.button("🗑️ Clear Conversation Logs Only", use_container_width=True):
        st.session_state.chat_history.clear()
        st.session_state.push_target_code = None
        st.success("Conversation history cleared. Global file structure tree remains cached.")
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)
