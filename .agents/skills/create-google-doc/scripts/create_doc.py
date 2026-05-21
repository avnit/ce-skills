#!/usr/bin/env python3
import argparse
import base64
import io
import os
import re
import subprocess
import sys
import time

def run_command(cmd_args, retries=3, backoff=2):
    """Runs a system command safely without shell, with dynamic exponential backoff retries for remote SSH/SCP calls."""
    is_remote = len(cmd_args) > 0 and cmd_args[0] in ["ssh", "scp"]
    
    for attempt in range(retries):
        try:
            result = subprocess.run(
                cmd_args,
                shell=False,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            if is_remote and result.returncode == 255:
                raise subprocess.SubprocessError(f"SSH/SCP connection failure (code 255): {result.stderr.strip()}")
                
            return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            if is_remote and attempt < retries - 1:
                sleep_time = backoff * (2 ** attempt)
                print(f"⚠️ Network Bridge Warning: Remote execution attempt {attempt+1} failed: {e}. Retrying in {sleep_time}s...", file=sys.stderr)
                time.sleep(sleep_time)
            else:
                return False, "", str(e)

def load_gcp_config():
    """Recursively searches parent directories for gcp_config.txt and parses configuration key-values."""
    config = {}
    curr_dir = os.getcwd()
    for _ in range(5):
        path = os.path.join(curr_dir, "gcp_config.txt")
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and '=' in line and not line.startswith('#'):
                            k, v = line.split('=', 1)
                            config[k.strip()] = v.strip()
                return config
            except Exception as e:
                pass
        parent = os.path.dirname(curr_dir)
        if parent == curr_dir:
            break
        curr_dir = parent
    return config

def convert_markdown_to_styled_html(markdown_text, title):
    """Converts Codelab markdown into beautifully inline-styled HTML optimized for Google Drive Doc conversion."""
    # Base layout wrapping style
    html_parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>",
        title,
        "</title></head><body style=\"font-family: Arial, sans-serif; color: #202124; line-height: 1.6; font-size: 11pt;\">"
    ]
    
    # 1. Extract Metadata block
    meta_match = re.match(r"^---\n([\s\S]*?)\n---", markdown_text)
    if meta_match:
        meta_text = meta_match.group(1)
        markdown_text = markdown_text[meta_match.end():].strip()
        
        # Build metadata grid table
        html_parts.append("<table style=\"width: 100%; border-collapse: collapse; margin-bottom: 24px; background-color: #f8f9fa; border: 1px solid #e8eaed;\"><tbody>")
        for line in meta_text.split("\n"):
            if ":" in line:
                k, v = line.split(":", 1)
                html_parts.append(f"<tr style=\"border-bottom: 1px solid #e8eaed;\"><td style=\"padding: 8px 12px; font-weight: bold; width: 120px; color: #5f6368;\">{k.strip()}</td><td style=\"padding: 8px 12px; color: #202124;\">{v.strip()}</td></tr>")
        html_parts.append("</tbody></table><hr style=\"border: 0; border-top: 1px solid #e8eaed; margin-bottom: 24px;\">")
        
    # 2. Protect Code blocks
    code_blocks = []
    def save_code(m):
        lang = m.group(1).strip() if m.group(1) else ""
        content = m.group(2).strip()
        code_blocks.append((lang, content))
        return f"\n\n%%%CODE_BLOCK_{len(code_blocks)-1}%%%\n\n"
    markdown_text = re.sub(r"```([a-zA-Z0-9_+-]*)\n([\s\S]*?)```", save_code, markdown_text)
    
    # 3. Protect Callout Asides
    asides = []
    def save_aside(m):
        atype = m.group(1).strip().lower()
        content = m.group(2).strip()
        # remove inner quotes
        content = re.sub(r"(^|\n)\s*>\s*", r"\1", content).strip()
        asides.append((atype, content))
        return f"\n\n%%%ASIDE_{len(asides)-1}%%%\n\n"
    markdown_text = re.sub(r"(?:^|\n)>\s*aside\s+(positive|negative)([\s\S]*?)(?=\n\n|\n$)", save_aside, markdown_text, flags=re.IGNORECASE)
    
    # 4. Normalize Spacing
    markdown_text = re.sub(r"^(#{1,6}\s.*)$", r"\n\n\1\n\n", markdown_text, flags=re.MULTILINE)
    markdown_text = re.sub(r"^(Duration:\s.*)$", r"\n\n\1\n\n", markdown_text, flags=re.MULTILINE|re.IGNORECASE)
    
    # Helper to parse inline markdown elements
    def parse_inline(text):
        # Bold
        text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
        # Inline Code
        text = re.sub(r"`([^`]+)`", r"<code style=\"font-family: 'Courier New', Courier, monospace; background-color: #f8f9fa; padding: 2px 4px; border-radius: 3px; font-size: 10pt;\">\1</code>", text)
        # Markdown Links
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href=\"\2\" style=\"color: #1a73e8; text-decoration: none;\">\1</a>", text)
        return text

    # 5. Process remaining blocks
    blocks = re.split(r"\n\n+", markdown_text)
    is_first_step = True
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
            
        if block.startswith("%%%CODE_BLOCK_"):
            idx_match = re.search(r"\d+", block)
            if idx_match:
                idx = int(idx_match.group(0))
                lang, content = code_blocks[idx]
                # Escape HTML tags in code content safely
                content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                html_parts.append(f"<table style=\"width: 100%; border-collapse: collapse; margin: 16px 0; background-color: #f8f9fa; border: 1px solid #e8eaed; border-radius: 6px;\"><tbody><tr><td style=\"padding: 12px;\"><pre style=\"font-family: 'Courier New', Courier, monospace; font-size: 10pt; margin: 0; white-space: pre-wrap; word-break: break-all; color: #202124;\">{content}</pre></td></tr></tbody></table>")
            continue
            
        if block.startswith("%%%ASIDE_"):
            idx_match = re.search(r"\d+", block)
            if idx_match:
                idx = int(idx_match.group(0))
                atype, content = asides[idx]
                content = parse_inline(content.replace("\n", "<br>"))
                bg_color = "#e6f4ea" if atype == "positive" else "#fce8e6"
                border_color = "#137333" if atype == "positive" else "#c5221f"
                html_parts.append(f"<table style=\"width: 100%; border-collapse: collapse; margin: 16px 0; background-color: {bg_color}; border-left: 4px solid {border_color};\"><tbody><tr><td style=\"padding: 12px; color: #202124;\">{content}</td></tr></tbody></table>")
            continue
            
        # Title
        if block.startswith("# "):
            t_text = parse_inline(block[2:].strip())
            html_parts.append(f"<h1 style=\"font-size: 24pt; color: #1a73e8; margin-bottom: 12px; font-weight: normal;\">{t_text}</h1>")
            continue
            
        # Step Headings (## )
        if block.startswith("## "):
            s_text = parse_inline(block[3:].strip())
            pb_style = "page-break-before: always; " if not is_first_step else ""
            is_first_step = False
            html_parts.append(f"<h2 style=\"{pb_style}font-size: 16pt; color: #202124; border-bottom: 1px solid #e8eaed; padding-bottom: 6px; margin-top: 24px; margin-bottom: 12px;\">{s_text}</h2>")
            continue
            
        # Sub headings (###, ####)
        if block.startswith("### "):
            h3_text = parse_inline(block[4:].strip())
            html_parts.append(f"<h3 style=\"font-size: 13pt; color: #202124; margin-top: 16px; margin-bottom: 8px;\">{h3_text}</h3>")
            continue
            
        if block.startswith("#### "):
            h4_text = parse_inline(block[5:].strip())
            html_parts.append(f"<h4 style=\"font-size: 11pt; color: #5f6368; margin-top: 12px; margin-bottom: 6px;\">{h4_text}</h4>")
            continue
            
        # Duration
        if block.lower().startswith("duration:"):
            d_text = parse_inline(block.strip())
            html_parts.append(f"<p style=\"font-style: italic; color: #5f6368; margin-bottom: 16px;\">{d_text}</p>")
            continue
            
        # Lists and plain text blocks
        lines = block.split("\n")
        current_list_type = None
        list_items = []
        
        def flush_list():
            if list_items:
                tag = "ul" if current_list_type == "bullet" else "ol"
                items_str = "".join(f"<li style=\"margin-bottom: 4px;\">{item}</li>" for item in list_items)
                html_parts.append(f"<{tag} style=\"margin-top: 8px; margin-bottom: 12px; padding-left: 24px;\">{items_str}</{tag}>")
                list_items.clear()
                
        for line in lines:
            line_s = line.strip()
            if not line_s:
                continue
            b_match = re.match(r"^[\*\-]\s+(.*)", line_s)
            n_match = re.match(r"^\d+\.\s+(.*)", line_s)
            
            if b_match:
                if current_list_type == "number":
                    flush_list()
                current_list_type = "bullet"
                list_items.append(parse_inline(b_match.group(1)))
            elif n_match:
                if current_list_type == "bullet":
                    flush_list()
                current_list_type = "number"
                list_items.append(parse_inline(n_match.group(1)))
            else:
                # If inside list, append to last item or treat as standalone paragraph
                if list_items:
                    list_items[-1] += " " + parse_inline(line_s)
                else:
                    html_parts.append(f"<p style=\"margin-bottom: 12px;\">{parse_inline(line_s)}</p>")
        flush_list()
        
    html_parts.append("</body></html>")
    return "".join(html_parts)

def create_google_doc_api(src_path, title):
    """Creates a Google Doc natively on a Google Cloudtop workstation."""
    if not os.path.exists(src_path):
        print(f"❌ Error: Source file not found at [{src_path}]", file=sys.stderr)
        return None
        
    try:
        with open(src_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading source file: {e}", file=sys.stderr)
        return None
        
    # Check if running on Cloudtop natively
    is_cloudtop = os.path.exists("/google/bin/releases") or "glinux" in os.uname().release.lower() if hasattr(os, 'uname') else False
    
    if not is_cloudtop:
        print("❌ Error: This skill can only be executed natively on a Google Cloudtop workstation.", file=sys.stderr)
        print("For security and compliance, remote execution via the SSH Bridge has been disabled.", file=sys.stderr)
        return None
        
    config = load_gcp_config()
    folder_id = config.get("folder_id", "")
    
    # Compile structured HTML payload locally
    html_payload = convert_markdown_to_styled_html(content, title)
    
    print("⚡ Environment Detected: Running natively on Cloudtop. Executing Google Drive pre-formatted import flow...")
    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload
        from googleapiclient.errors import HttpError
        import google.auth
        
        # Attempt 1: Native Pre-Formatted Google Drive Import
        try:
            creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/drive'])
            drive_service = build('drive', 'v3', credentials=creds)
            file_metadata = {
                'name': title,
                'mimeType': 'application/vnd.google-apps.document'
            }
            if folder_id:
                file_metadata['parents'] = [folder_id]
                
            media = MediaIoBaseUpload(io.BytesIO(html_payload.encode('utf-8')), mimetype='text/html', resumable=True)
            file_meta = drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            doc_id = file_meta.get('id')
            doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
            print(f"🚀 Success! Pre-formatted Google Doc natively created:\n{doc_url}")
            return doc_url
        except HttpError as e:
            err_str = str(e)
            if "insufficient authentication scopes" in err_str or "SCOPE_NOT_PERMITTED" in err_str or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in err_str or "quota project" in err_str.lower() or "accessnotconfigured" in err_str.lower():
                print("\n⚠️ Local Google Drive API Restricted natively.", file=sys.stderr)
                print("Your active credentials token lacks quota project bindings or native Drive write permissions.", file=sys.stderr)
                print("To authorize native pre-formatted generation locally, configure your client credentials or set a quota project via:", file=sys.stderr)
                print("\n    gcloud auth application-default set-quota-project <PROJECT_ID>\n", file=sys.stderr)
                print("Gracefully cascading to permitted base Google Docs API builder...", file=sys.stderr)
            else:
                print(f"⚠️ HTTP Error on Drive endpoint: {err_str}. Cascading...", file=sys.stderr)
            
        # Attempt 2: Fallback to standard permitted Google Docs API
        creds, _ = google.auth.default(scopes=['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive'])
        docs_service = build('docs', 'v1', credentials=creds)
        doc = docs_service.documents().create(body={'title': title}).execute()
        doc_id = doc.get('documentId')
        if content.strip():
            requests = [{'insertText': {'location': {'index': 1}, 'text': content}}]
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            
        doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
        print(f"🚀 Success! Base Google Doc successfully generated:\n{doc_url}")
        return doc_url
        
    except Exception as api_err:
        print(f"❌ Native execution failed: {api_err}", file=sys.stderr)
        return None

def main():
    parser = argparse.ArgumentParser(description="Secure passwordless Seamless Global Resilient Google Doc Generator via Remote Cloudtop Bridge.")
    parser.add_argument("--src", required=True, help="Path to local markdown or text source file.")
    parser.add_argument("--title", required=True, help="Title of the target Google Doc.")
    args = parser.parse_args()
    
    create_google_doc_api(args.src, args.title)

if __name__ == "__main__":
    main()
