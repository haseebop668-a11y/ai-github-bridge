import streamlit as st
import io
from utils import parse_chat_logs, commit_to_github

st.set_page_config(page_title="AI-to-GitHub Bridge", layout="wide", page_icon="🚀")

def init_session_state():
    """Initialize enterprise state tracking for deferred execution."""
    defaults = {
        "pat": "", "pat_locked": False,
        "repo_name": "ai-bridge-output", "repo_visibility": "Private", "repo_description": "Files extracted via AI-to-GitHub Bridge",
        "raw_text": "", "raw_file_bytes": None, "uploaded_file_name": None,
        "last_result": None, "trigger_retry": False
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session_state()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("🔐 GitHub PAT")
    if st.session_state.pat_locked:
        st.success("Token Locked & Active")
        if st.button("🔓 Unlock / Change Token"):
            st.session_state.pat_locked = False
            st.rerun()
    else:
        pat_input = st.text_input("Enter GitHub PAT", type="password", value=st.session_state.pat)
        if st.button("🔒 Lock Token"):
            if pat_input:
                st.session_state.pat = pat_input
                st.session_state.pat_locked = True
                st.rerun()
            else:
                st.error("Please enter a valid PAT.")
                
    st.divider()
    st.subheader("📦 Repository Settings")
    st.session_state.repo_name = st.text_input("Repository Name", st.session_state.repo_name)
    st.session_state.repo_visibility = st.radio("Visibility", ["Private", "Public"], index=0 if st.session_state.repo_visibility == "Private" else 1)
    st.session_state.repo_description = st.text_area("Description", st.session_state.repo_description)

# --- Main Input Area ---
st.header("📥 Input Context")
input_mode = st.radio("Input Method", ["Paste Text", "Upload Log File"], horizontal=True)

if input_mode == "Paste Text":
    text_content = st.text_area("Paste your AI chat logs here:", height=400, value=st.session_state.raw_text)
    st.session_state.raw_text = text_content
    st.session_state.raw_file_bytes = None # Clear file state if text mode selected
else:
    uploaded_file = st.file_uploader("Upload massive log file (.txt, .md, .log)", type=["txt", "md", "log"])
    if uploaded_file is not None:
        if st.session_state.uploaded_file_name != uploaded_file.name:
            st.session_state.raw_file_bytes = uploaded_file.getvalue()
            st.session_state.uploaded_file_name = uploaded_file.name
        st.info(f"Loaded: {uploaded_file.name} ({len(st.session_state.raw_file_bytes)} bytes)")
    st.session_state.raw_text = "" # Clear text state if file mode selected

st.divider()

# --- Execution Flow Control (Push-Only Pattern) ---
push_clicked = st.button("🚀 Extract and Push to GitHub", type="primary", use_container_width=True)

# Handle Retry Trigger from Execution History
if st.session_state.trigger_retry:
    push_clicked = True
    st.session_state.trigger_retry = False

if push_clicked:
    # 1. Strict Validation Gate
    if not st.session_state.pat_locked:
        st.error("❌ Process Aborted: Please lock your GitHub PAT in the sidebar first.")
    elif not st.session_state.repo_name.strip():
        st.error("❌ Process Aborted: Repository name cannot be empty.")
    elif not st.session_state.raw_text.strip() and st.session_state.raw_file_bytes is None:
        st.warning("⚠️ No input provided. Please paste text or upload a file.")
    else:
        # 2. Action-Triggered Logic
        with st.status("Processing AI Context...", expanded=True) as status:
            st.write("⚙️ Initializing streaming parser...")
            
            try:
                # High-Throughput Stream Routing
                if st.session_state.raw_text.strip():
                    lines_iter = io.StringIO(st.session_state.raw_text)
                else:
                    lines_iter = io.TextIOWrapper(io.BytesIO(st.session_state.raw_file_bytes), encoding='utf-8')
                    
                st.write("⚡ Parsing files (streaming mode)...")
                extracted_files = parse_chat_logs(lines_iter)
                total_files = len(extracted_files)
                
                if total_files == 0:
                    st.warning("⚠️ No valid code blocks found in the input context.")
                    status.update(state="error", label="Parsing Complete - No Files Found")
                else:
                    st.write(f"✅ Parsing complete! Extracted {total_files} files.")
                    st.write("🚀 Connecting to GitHub and building Git Tree...")
                    
                    success, result_url, error_details = commit_to_github(
                        st.session_state.pat, 
                        st.session_state.repo_name, 
                        st.session_state.repo_visibility == "Private", 
                        st.session_state.repo_description, 
                        extracted_files
                    )
                    
                    if success:
                        st.write("🎉 Successfully pushed to GitHub!")
                        st.markdown(f"[🔗 View Repository]({result_url})")
                        status.update(label="Push Complete!", state="complete", expanded=False)
                        st.session_state.last_result = {"success": True, "url": result_url}
                        st.balloons()
                    else:
                        st.error(f"❌ GitHub Push Failed: {result_url}")
                        st.code(error_details, language="text")
                        status.update(label="Push Failed", state="error", expanded=True)
                        st.session_state.last_result = {"success": False, "error": result_url, "details": error_details}
                        
            except Exception as e:
                st.error(f"❌ Unexpected pipeline failure: {str(e)}")
                status.update(state="error", label="Pipeline Failure")
                st.session_state.last_result = {"success": False, "error": "Pipeline Failure", "details": str(e)}

# --- Execution History & Retry Dashboard ---
if st.session_state.last_result:
    st.divider()
    st.subheader("📊 Execution History")
    if st.session_state.last_result["success"]:
        st.success(f"Last Push Successful: [View Repository]({st.session_state.last_result['url']})")
    else:
        st.error(f"Last Push Failed: {st.session_state.last_result['error']}")
        if st.button("🔄 Retry Last Push"):
            st.session_state.trigger_retry = True
            st.rerun()

# Memory Management Utility
if st.session_state.raw_file_bytes or st.session_state.raw_text:
    if st.sidebar.button("🗑️ Clear Input Data (Free Memory)"):
        st.session_state.raw_text = ""
        st.session_state.raw_file_bytes = None
        st.session_state.uploaded_file_name = None
        st.rerun()
