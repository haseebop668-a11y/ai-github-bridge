import io
import zipfile
import requests
import re
import logging
import base64
from typing import Iterator, Tuple

logger = logging.getLogger(__name__)

# --- 1. Memory-Safe Stream Chunking Engine ---
def stream_zip_files_safely(uploaded_file) -> Iterator[Tuple[str, str]]:
    """Reads large archives file-by-file from the stream without loading the entire zip into RAM."""
    try:
        with zipfile.ZipFile(uploaded_file, "r") as z:
            for info in z.infolist():
                if info.is_dir() or info.file_size > 50 * 1024 * 1024: # 50MB Safe Ceiling
                    continue
                if info.filename.endswith(('.py', '.cpp', '.h', '.rs', '.go', '.java', '.js', '.sh', '.json', '.yaml', '.html', '.css')):
                    with z.open(info.filename) as f:
                        content = f.read().decode("utf-8", errors="ignore")
                        yield info.filename, content
    except Exception as e:
        logger.error(f"Zip streaming failure: {str(e)}")

# --- 2. OpenRouter API Orchestrator (Zero-Cost Optimized) ---
def call_openrouter(prompt: str, api_token: str, model: str = "qwen/qwen-2.5-coder-7b-instruct:free") -> Tuple[bool, str]:
    # Header injection اور ملٹی ٹیننٹ اسپیس میں ڈیٹا کی حفاظت کے لیے سینیٹائزیشن لازمی ہے
    clean_token = api_token.strip()
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {clean_token}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://enterprise.ai.bridge",
    }
    data = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=90)
        
        if response.status_code == 200:
            return True, response.json()["choices"][0]["message"]["content"]
        elif response.status_code == 429:
            return False, "OpenRouter Rate Limit (429): Free cluster is heavily congested. Please retry in a few seconds."
        elif response.status_code == 503:
            return False, "Service Unavailable (503): OpenRouter free tier node is temporarily overloaded."
        
        return False, f"API Gate Error {response.status_code}: {response.text}"
    except requests.exceptions.Timeout:
        return False, "Gateway Timeout: OpenRouter cluster took too long to compile the refactor pipeline."
    except Exception as e:
        return False, f"Network Infrastructure Failure: {str(e)}"

# --- 3. Polyglot Code Block Extractor (Defensive Layer) ---
def extract_code_blocks(text: str) -> Iterator[Tuple[str, str]]:
    # پائلٹ ٹیسٹنگ کے دوران فارمیٹس کی لچک برقرار رکھنے کے لیے ریموٹ وائٹ اسپیس میچنگ
    pattern = r"```(\w*)[ \t]*\r?\n(.*?)```"
    for match in re.finditer(pattern, text, re.DOTALL):
        lang, code = match.groups()
        if code.strip(): 
            yield lang if lang else "text", code.strip()

# --- 4. Enterprise GitHub Deployment Pipeline (Race-Condition Free) ---
def commit_to_github(pat: str, repo_name: str, branch: str, file_path: str, content: str, commit_msg: str) -> Tuple[bool, str]:
    clean_pat = pat.strip()
    headers = {"Authorization": f"token {clean_pat}", "Accept": "application/vnd.github.v3+json"}
    base_url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
    
    # الپٹیمسٹک لاکنگ انشور کرنے کے لیے SHA فیچنگ لک اپ
    try:
        get_res = requests.get(base_url, headers=headers, params={"ref": branch}, timeout=15)
        sha = get_res.json().get("sha") if get_res.status_code == 200 else None
    except Exception:
        sha = None # اگر فائل نئی ہے تو بغیر SHA کے آگے بڑھے گا
    
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
    payload = {
        "message": commit_msg,
        "content": encoded_content,
        "branch": branch
    }
    if sha:
        payload["sha"] = sha
        
    try:
        put_res = requests.put(base_url, headers=headers, json=payload, timeout=20)
        
        if put_res.status_code in [200, 201]:
            return True, put_res.json()["content"]["html_url"]
        elif put_res.status_code == 409:
            return False, "Git State Conflict (409): Stale SHA sequence detected. Someone else updated this branch simultaneously. Please retry."
        
        # کریش سے بچنے کے لیے جے سن سیف ہینڈلنگ
        try:
            err_details = put_res.json().get("message", "Deployment Failed")
        except Exception:
            err_details = f"HTTP Error {put_res.status_code}: {put_res.text}"
        return False, err_details
        
    except Exception as e:
        return False, f"Secure Pipeline Refused Commit Link: {str(e)}"
        
