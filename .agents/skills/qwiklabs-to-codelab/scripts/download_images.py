#!/usr/bin/env python3
import os
import re
import sys
import hashlib
import urllib.request
import urllib.parse

def download_image(url, target_dir):
    # Generate a unique, deterministic filename based on MD5 hash of URL to avoid conflicts
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    
    # Try to determine extension from path or default to .png
    parsed_url = urllib.parse.urlparse(url)
    path_ext = os.path.splitext(parsed_url.path)[1]
    ext = path_ext if path_ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'] else '.png'
    
    filename = f"image_{url_hash}{ext}"
    target_path = os.path.join(target_dir, filename)
    
    if os.path.exists(target_path):
        # Already downloaded
        return f"img/{filename}"
        
    print(f"Downloading remote asset: {url} -> {target_path} ...")
    try:
        # Set browser-like user agent to prevent blocks on CDNs
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            # Check content type headers to refine extension if needed
            content_type = response.headers.get('Content-Type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'gif' in content_type:
                ext = '.gif'
            elif 'svg' in content_type:
                ext = '.svg'
            elif 'webp' in content_type:
                ext = '.webp'
                
            # Re-evaluate filename with verified extension
            filename = f"image_{url_hash}{ext}"
            target_path = os.path.join(target_dir, filename)
            
            with open(target_path, 'wb') as f:
                f.write(response.read())
                
        print(f"Successfully localized to: img/{filename}")
        return f"img/{filename}"
    except Exception as e:
        print(f"Warning: Failed to download {url}: {e}")
        return None

def localize_assets(filepath):
    if not os.path.exists(filepath):
        print(f"Error: File not found at {filepath}")
        sys.exit(1)
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Create img directory adjacent to file
    file_dir = os.path.dirname(os.path.abspath(filepath))
    img_dir = os.path.join(file_dir, "img")
    os.makedirs(img_dir, exist_ok=True)
    
    # Match standard markdown images: ![alt](url)
    md_img_pattern = re.compile(r'(!\[.*?\])\((https?://.*?)\)')
    # Match HTML images: <img src="url" ...>
    html_img_pattern = re.compile(r'(<img[^>]+src=["\'])(https?://[^"\']*)(["\'])')
    
    modified = False
    
    # Handle Markdown Images
    md_matches = md_img_pattern.findall(content)
    for alt_block, url in md_matches:
        # Skip already local files
        if url.startswith('img/') or url.startswith('./img/'):
            continue
            
        local_path = download_image(url, img_dir)
        if local_path:
            # Escape special characters in alt_block and url for regex replacement
            target = f"{alt_block}({url})"
            replacement = f"{alt_block}({local_path})"
            content = content.replace(target, replacement)
            modified = True
            
    # Handle HTML Images
    html_matches = html_img_pattern.findall(content)
    for prefix, url, suffix in html_matches:
        if url.startswith('img/') or url.startswith('./img/'):
            continue
            
        local_path = download_image(url, img_dir)
        if local_path:
            target = f"{prefix}{url}{suffix}"
            replacement = f"{prefix}{local_path}{suffix}"
            content = content.replace(target, replacement)
            modified = True
            
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Successfully updated all image references inside: {filepath}")
    else:
        print("No remote image assets found or updated.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: download_images.py <codelab_markdown_filepath>")
        sys.exit(1)
        
    localize_assets(sys.argv[1])
