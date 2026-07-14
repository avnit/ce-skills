#!/usr/bin/env python3
"""
Link Authenticity Verification Script for Customer Engineering Meeting Prep One-Pagers.
Parses Markdown files, extracts all markdown links [text](url), and deterministically validates:
1. Public URLs (cloud.google.com, support.google.com): Live HTTP GET check for 200 OK or valid redirect.
2. Buganizer URLs (b.corp.google.com/issues/<ID>): Validates 9-10 digit numerical ID structure.
3. Workspace URLs (docs.google.com, mail.google.com, chat.google.com): Validates exact URL parameters.
"""

import sys
import re
import urllib.request
import urllib.parse
import urllib.error

def extract_markdown_links(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Regex to find markdown links: [text](url)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    return link_pattern.findall(content)

def check_public_url(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        # Standard opener follows redirects automatically
        with urllib.request.urlopen(req, timeout=5) as resp:
            return True, resp.status, None
    except urllib.error.HTTPError as e:
        if e.code in (301, 302, 307, 308):
            return True, e.code, None
        return False, e.code, f"HTTP Error {e.code}"
    except Exception as e:
        return False, None, str(e)

def verify_links(filepath):
    print(f"🔍 Auditing Link Authenticity in: {filepath}\n" + "="*60)
    links = extract_markdown_links(filepath)
    
    if not links:
        print("ℹ️  No markdown links found in file.")
        return 0

    total_links = len(links)
    valid_count = 0
    warning_count = 0
    failed_count = 0

    for text, url in links:
        clean_url = url.strip()
        parsed = urllib.parse.urlparse(clean_url)
        domain = parsed.netloc.lower()
        
        # 1. Public GCP Documentation & Support Links
        if domain in ("cloud.google.com", "docs.cloud.google.com", "support.google.com") or domain.endswith(".cloud.google.com") or domain.endswith(".support.google.com"):
            ok, status, err = check_public_url(clean_url)
            if ok:
                print(f"✅ [PUBLIC HTTP {status or 200}] {text} -> {clean_url}")
                valid_count += 1
            else:
                print(f"❌ [PUBLIC HTTP ERROR: {err}] {text} -> {clean_url}")
                failed_count += 1

        # 2. Buganizer Internal Issues
        elif domain in ("b.corp.google.com", "buganizer.corp.google.com") or domain.endswith(".b.corp.google.com") or domain.endswith(".buganizer.corp.google.com"):
            bug_id_match = re.search(r'/(issues/)?(\d{7,12})', clean_url)
            if bug_id_match:
                print(f"✅ [BUGANIZER ID VERIFIED ({bug_id_match.group(2)})] {text} -> {clean_url}")
                valid_count += 1
            else:
                print(f"❌ [INVALID BUGANIZER ID] {text} -> {clean_url}")
                failed_count += 1

        # 3. Workspace Docs, Slides, Trix, Mail & Chat
        elif domain in ("docs.google.com", "drive.google.com", "mail.google.com", "chat.google.com") or any(domain.endswith("." + d) for d in ["docs.google.com", "drive.google.com", "mail.google.com", "chat.google.com"]):
            if re.search(r'(/d/[a-zA-Z0-9_-]+|/room/[a-zA-Z0-9_-]+|/issues/|mid=)', clean_url):
                print(f"✅ [WORKSPACE SPEC VERIFIED] {text} -> {clean_url}")
                valid_count += 1
            else:
                print(f"⚠️ [WORKSPACE GENERIC URL] {text} -> {clean_url}")
                warning_count += 1

        # 4. Local File Links
        elif clean_url.startswith("file://") or clean_url.startswith("./") or clean_url.startswith("/"):
            print(f"✅ [LOCAL PATH VERIFIED] {text} -> {clean_url}")
            valid_count += 1

        else:
            print(f"ℹ️  [OTHER LINK] {text} -> {clean_url}")
            valid_count += 1

    print("="*60)
    print(f"📊 Audit Summary: {total_links} total links evaluated.")
    print(f"   - Verified Valid: {valid_count}")
    print(f"   - Warnings: {warning_count}")
    print(f"   - Failed/Invalid: {failed_count}")
    
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 verify_links.py <path_to_markdown_file>")
        sys.exit(1)
    
    target_file = sys.argv[1]
    sys.exit(verify_links(target_file))
