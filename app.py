import streamlit as st
import io
from utils import (parse_strict_logs, extract_zip, check_ollama_status, 
                   analyze_code, generate_readme, generate_commit_message, commit_to_github)

st.set_page_config(page_title="AI-to-GitHub Bridge", layout="wide", page_icon="🚀")

# Premium CSS Styling
st.markdown("""
<style>
    .main-header { font-size: 3rem; font-weight: 900; background: linear-gradient(90deg, #00C9FF 0%, #92FE9D 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 0; letter-spacing: -1px; }
    .sub-header { font-size: 1.2rem; color: #6c757d; margin-bottom: 2.5rem; font-weight: 400; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: 600; height: 3.2rem; transition: all 0.3s ease; border: 1px solid #e0e0e0; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; padding: 10px 24px; background-color: #f8f9fa; border-radius: 8px 8px 0 0; }
</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
defaults = {"step": 1, "files": {}, "bugs": {}, "readme": "", "commit_msg": "", "pat": "", "pat_locked": False}
for k, v in defaults.items():
    if k not in st.session_state: st.session_state[k] = v

# --- Dialog for Bug Fixes ---
@st.dialog("🛠️ Fix Suggestion", width="large")
def fix_dialog(file_path, bug_idx):
    bug = st.session_state.bugs[file_path][bug_idx]
    st.error(f"**Detected Bug:**\n{bug['bug']}")
    st.divider()
    st.success("**Proposed Fix (Full Code):**")
    ext = file_path.split('.')[-1] if '.' in file_path else "text"
    st.code(bug['corrected_code'], language=ext)
    
    c1, c2 = st.columns(2)
    if c1.button("✅ Confirm & Apply", use_container_width=True):
        st.session_state.files[file_path] = bug['corrected_code']
        st.session_state.bugs[file_path].pop(bug_idx)
        if not st.session_state.bugs[file_path]: del st.session_state.bugs[file_path]
        st.rerun()
    if c2.button("❌ Ignore", use_container_width=True):
        st.session_state.bugs[file_path].pop(bug_idx)
        if not st.session_state.bugs[file_path]: del st.session_state.bugs[file_path]
        st.rerun()

# --- Sidebar Configuration ---
with st.sidebar:
    st.header("⚙️ Configuration")
    if st.session_state.pat_locked:
        st.success("🔒 Token Secured")
        if st.button("🔓 Unlock Token"): st.session_state.pat_locked = False; st.rerun()
    else:
        pat = st.text_input("GitHub PAT", type="password", value=st.session_state.pat)
        if st.button("🔒 Lock Token"):
            if pat: st.session_state.pat = pat; st.session_state.pat_locked = True; st.rerun()
                
    st.divider()
    repo_name = st.text_input("Repository Name", "ai-bridge-prod")
    is_private = st.toggle("Private Repository", True)
    desc = st.text_area("Description", "Autonomous AI Code Pipeline")
    
    st.divider()
    st.header("🧠 Local LLM (Ollama)")
    ollama_ok = check_ollama_status()
    if ollama_ok: st.success("Llama 3 Connected")
    else: st.error("Ollama Offline"); st.caption("Start Ollama locally to enable Auto-Fix.")
        
    st.divider()
    if st.button("🗑️ Clear Context & Reset", type="primary", use_container_width=True):
        for key in ["step", "files", "bugs", "readme", "commit_msg"]:
            if key in st.session_state: del st.session_state[key]
        st.rerun()

# --- Main Execution Flow ---
st.markdown('<p class="main-header">AI-to-GitHub Bridge</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Enterprise-Grade Code Transport & Autonomous Optimization Pipeline</p>', unsafe_allow_html=True)

if st.session_state.step == 1:
    st.subheader("1️⃣ Ingest Context")
    tab1, tab2, tab3 = st.tabs(["📝 Raw Text", "📄 Log File", "🗜️ Zip Archive"])
    
    with tab1: text_input = st.text_area("Paste AI Chat Logs (Strict Format: `# Filename: path`)", height=400)
    with tab2: file_input = st.file_uploader("Upload .txt/.md logs", type=["txt", "md", "log"])
    with tab3: zip_input = st.file_uploader("Upload Codebase .zip", type=["zip"])
        
    if st.button("⚙️ Parse & Analyze", type="primary", use_container_width=True):
        with st.spinner("Parsing context and extracting files..."):
            files = {}
            if text_input: files = parse_strict_logs(io.StringIO(text_input))
            elif file_input: files = parse_strict_logs(io.TextIOWrapper(file_input, encoding='utf-8'))
            elif zip_input: files = extract_zip(zip_input.getvalue())
                
            if not files: st.error("No valid files found. Ensure strict formatting or valid zip.")
            else:
                st.session_state.files = files
                if ollama_ok:
                    st.info("🧠 Llama 3 is analyzing codebase for bugs...")
                    bugs = {}
                    prog = st.progress(0)
                    for idx, (path, content) in enumerate(files.items()):
                        res = analyze_code(path, content)
                        if res: bugs[path] = res
                        prog.progress((idx + 1) / len(files))
                    st.session_state.bugs = bugs
                    st.info("📝 Generating README & Commit Message...")
                    st.session_state.readme = generate_readme(files)
                    st.session_state.commit_msg = generate_commit_message(files)
                st.session_state.step = 2; st.rerun()

elif st.session_state.step == 2:
    st.subheader("2️⃣ Review & Optimize")
    if st.session_state.bugs:
        st.warning(f"⚠️ Llama 3 detected potential issues in {len(st.session_state.bugs)} file(s).")
        for path, bugs_list in st.session_state.bugs.items():
            for idx, bug in enumerate(bugs_list):
                with st.container():
                    st.markdown(f"**File:** `{path}` | **Issue:** {bug['bug']}")
                    if st.button(f"Review Fix for {path}", key=f"btn_{path}_{idx}"):
                        fix_dialog(path, idx)
        st.divider()
        
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 📄 Auto-Generated README")
        st.session_state.readme = st.text_area("Edit README.md", st.session_state.readme, height=300)
    with c2:
        st.markdown("#### 💬 Commit Message")
        st.session_state.commit_msg = st.text_area("Edit Commit Message", st.session_state.commit_msg, height=300)
        
    with st.expander("📂 Inspect Extracted Files (Read-Only)"):
        for path, content in st.session_state.files.items():
            st.markdown(f"**`{path}`**")
            ext = path.split('.')[-1] if '.' in path else "text"
            st.code(content, language=ext)
            
    c3, c4 = st.columns(2)
    if c3.button("⬅️ Back to Ingest", use_container_width=True): st.session_state.step = 1; st.rerun()
    if c4.button("🚀 Proceed to Push", type="primary", use_container_width=True):
        if not st.session_state.pat_locked: st.error("Lock your PAT in the sidebar first!")
        else: st.session_state.step = 3; st.rerun()

elif st.session_state.step == 3:
    st.subheader("3️⃣ Execute GitHub Push")
    st.markdown(f"**Target:** `{repo_name}` ({'Private' if is_private else 'Public'})")
    
    if st.button("🔥 COMMIT & PUSH TO GITHUB", type="primary", use_container_width=True):
        with st.status("Executing Git Data API...", expanded=True) as status:
            st.write("Building Git Tree & Blobs...")
            success, url, err = commit_to_github(
                st.session_state.pat, repo_name, is_private, desc, 
                st.session_state.files, st.session_state.commit_msg, st.session_state.readme
            )
            if success:
                st.write("🎉 Push Successful!")
                st.markdown(f"[🔗 Open Repository]({url})")
                status.update(state="complete", expanded=False)
                st.balloons()
                st.session_state.step = 1; st.session_state.files = {}; st.rerun()
            else:
                st.error(f"Push Failed: {url}")
                st.code(err)
                status.update(state="error")
