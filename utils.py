import re
import base64
import logging
from typing import Dict, Iterator, Tuple, Optional
from github import Github, UnknownObjectException, InputGitTreeElement, GithubException

# Enterprise-grade logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Extensible Language Mapping. 
# Fallback to the raw tag if not explicitly mapped to ensure zero hardcoded constraints.
LANG_MAP = {
    'python': 'py', 'javascript': 'js', 'typescript': 'ts', 'cpp': 'cpp', 'c++': 'cpp',
    'c': 'c', 'java': 'java', 'dart': 'dart', 'ruby': 'rb', 'rust': 'rs', 'go': 'go',
    'html': 'html', 'css': 'css', 'json': 'json', 'yaml': 'yaml', 'yml': 'yaml', 'markdown': 'md',
    'bash': 'sh', 'shell': 'sh', 'php': 'php', 'swift': 'swift', 'kotlin': 'kt', 'sql': 'sql',
    'xml': 'xml', 'csv': 'csv', 'toml': 'toml', 'ini': 'ini', 'dockerfile': 'dockerfile'
}

def parse_chat_logs(lines_iter: Iterator[str]) -> Dict[str, str]:
    """
    Stateless processor that parses a stream of lines and extracts code blocks.
    Optimized for high-throughput processing of large contexts (100k+ lines) via generators.
    
    Args:
        lines_iter: An iterator yielding string lines (e.g., from io.StringIO or io.TextIOWrapper).
        
    Returns:
        A dictionary mapping file paths to their extracted string content.
    """
    extracted_files = {}
    pending_file = None
    current_content = []
    in_block = False
    file_counter = 0
    
    # Pre-compile regex for O(1) matching speed per line
    file_header_re = re.compile(r'^File:\s*(.+)$', re.IGNORECASE)
    md_fence_re = re.compile(r'^```([^\s]+)?(?:\s+(.+))?$')
    
    for line in lines_iter:
        line = line.rstrip('\n\r')
        
        if in_block:
            if line.strip() == '```':
                if pending_file:
                    extracted_files[pending_file] = "".join(current_content).rstrip('\n')
                pending_file = None
                current_content = []
                in_block = False
            else:
                current_content.append(line + '\n')
        else:
            match_a = file_header_re.match(line.strip())
            if match_a:
                pending_file = match_a.group(1).strip()
                continue
                
            match_b = md_fence_re.match(line.strip())
            if match_b:
                lang = match_b.group(1)
                filename = match_b.group(2)
                
                if pending_file:
                    current_file = pending_file
                    pending_file = None
                elif filename:
                    filename = filename.strip()
                    if '.' not in filename:
                        ext = LANG_MAP.get(lang.lower() if lang else 'txt', lang.lower() if lang else 'txt')
                        current_file = f"{filename}.{ext}"
                    else:
                        current_file = filename
                else:
                    file_counter += 1
                    ext = LANG_MAP.get(lang.lower() if lang else 'txt', lang.lower() if lang else 'txt')
                    current_file = f"file_{file_counter}.{ext}"
                    
                in_block = True
                current_content = []
                
    # Edge case: Unclosed block at EOF
    if in_block and pending_file:
        extracted_files[pending_file] = "".join(current_content).rstrip('\n')
        
    return extracted_files

def commit_to_github(
    pat: str, 
    repo_name: str, 
    is_private: bool, 
    description: str, 
    files_dict: Dict[str, str]
) -> Tuple[bool, str, Optional[str]]:
    """
    Pushes extracted files to GitHub using the Git Data API for atomic commits.
    
    Returns:
        Tuple of (success: bool, repo_url_or_error_title: str, error_details: Optional[str])
    """
    try:
        g = Github(pat)
        user = g.get_user()
        _ = user.login # Force network evaluation to catch auth errors early
        
        try:
            repo = user.get_repo(repo_name)
        except UnknownObjectException:
            repo = user.create_repo(repo_name, private=is_private, description=description)
            
        default_branch = repo.default_branch
        
        # Get Base Tree
        try:
            ref = repo.get_git_ref(f"heads/{default_branch}")
            sha = ref.object.sha
            commit = repo.get_git_commit(sha)
            base_tree = commit.tree
            parents = [commit]
        except GithubException as e:
            # 409 Conflict or 404 Not Found indicates an empty repository
            if e.status in (404, 409):
                base_tree = None
                parents = []
            else:
                raise e
                
        if not files_dict:
            return True, repo.html_url, None

        # Build Tree Elements
        tree_elements = []
        for path, content in files_dict.items():
            content_bytes = content.encode('utf-8')
            b64_content = base64.b64encode(content_bytes).decode('ascii')
            blob = repo.create_git_blob(b64_content, "base64")
            tree_elements.append(InputGitTreeElement(path, "100644", "blob", sha=blob.sha))
            
        new_tree = repo.create_git_tree(tree_elements, base_tree)
        new_commit = repo.create_git_commit("Commit via AI-to-GitHub Bridge", new_tree, parents)
        
        if parents:
            ref.edit(new_commit.sha)
        else:
            repo.create_git_ref(f"refs/heads/{default_branch}", new_commit.sha)
            
        return True, repo.html_url, None

    except GithubException as e:
        logger.error(f"GitHub API Exception: {e}")
        error_msg = e.data.get('message', str(e)) if hasattr(e, 'data') and e.data else str(e)
        return False, "GitHub API Error", error_msg
    except Exception as e:
        logger.error(f"Unexpected Pipeline Error: {e}")
        return False, "Unexpected Pipeline Error", str(e)
