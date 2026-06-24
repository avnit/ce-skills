#!/usr/bin/env python3
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from html import unescape

def run_command(cmd_args):
    """Runs a command without a shell and returns success status, stdout, and stderr."""
    try:
        result = subprocess.run(
            cmd_args,
            shell=False,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def validate_date(date_str):
    """Validates that a date string is in YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: '{date_str}'. Must be in YYYY-MM-DD format.")

def html_to_markdown(html, is_table_mode=False):
    """Converts simple HTML tags from Google Cloud release notes to standard Markdown."""
    if not html:
        return ""
    
    # Decode HTML entities
    text = unescape(html)
    text = text.strip()
    
    # Replace <strong>/<b> with **
    text = re.sub(r'</?(strong|b)>', '**', text)
    
    # Replace <em>/<i> with *
    text = re.sub(r'</?(em|i)>', '*', text)
    
    # Replace <code> with `
    text = re.sub(r'</?code>', '`', text)
    
    # Replace links with any attributes: <a href="URL" ...>TEXT</a> -> [TEXT](URL)
    text = re.sub(r'<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', text)
    
    if is_table_mode:
        # In Markdown tables, literal newlines break formatting.
        # We convert list items and paragraph breaks into <br> tags.
        text = re.sub(r'<li>', '* ', text)
        text = re.sub(r'</li>', '', text)
        text = re.sub(r'</?ul>', '', text)
        text = re.sub(r'<p>', '', text)
        text = re.sub(r'</p>', '<br>', text)
        
        # Strip duplicate or trailing breaks
        text = re.sub(r'(<br>\s*)+$', '', text)
        text = re.sub(r'\n+', '<br>', text)
        text = re.sub(r'(<br>)+', ' <br> ', text)
    else:
        # Standard paragraph/list formatting for readable markdown documents
        text = re.sub(r'<li>', '* ', text)
        text = re.sub(r'</li>', '\n', text)
        text = re.sub(r'</?ul>', '', text)
        text = re.sub(r'<p>', '', text)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
    # Escape pipes (|) to protect Markdown table structure
    text = text.replace('|', '\\|')
    
    return text.strip()

def execute_query(query):
    """Executes a query using the bq CLI and handles errors gracefully."""
    cmd_args = ["bq", "query", "--use_legacy_sql=false", "--max_rows=100000", "--format=json", query]
    success, stdout, stderr = run_command(cmd_args)
    
    if not success:
        # Catch common authentication or configuration errors
        if "credentials" in stderr.lower() or "authentication" in stderr.lower() or "access token" in stderr.lower():
            print("❌ Error: Authentication failure. Could not query BigQuery.", file=sys.stderr)
            print("💡 Fix: Please run 'gcloud auth login' or configure application default credentials.", file=sys.stderr)
        else:
            print(f"❌ BigQuery query failed:\n{stderr}", file=sys.stderr)
        sys.exit(1)
        
    try:
        return json.loads(stdout)
    except Exception as e:
        print(f"❌ Error parsing BigQuery JSON response: {e}", file=sys.stderr)
        print(f"Response was:\n{stdout}", file=sys.stderr)
        sys.exit(1)

def list_products():
    """Lists all available products, utilizing a local cache file if it's fresh."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    skill_dir = os.path.dirname(script_dir)
    cache_path = os.path.join(skill_dir, "products.md")
    
    use_cache = False
    cache_products = []
    
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse timestamp: * **Last Updated**: YYYY-MM-DD
            match = re.search(r'\*\*Last Updated\*\*:\s*(\d{4}-\d{2}-\d{2})', content)
            if match:
                last_updated_str = match.group(1)
                last_updated = datetime.strptime(last_updated_str, "%Y-%m-%d")
                age_days = (datetime.now() - last_updated).days
                if age_days < 30:
                    use_cache = True
                    
            if use_cache:
                # Parse product names from markdown table
                for line in content.splitlines():
                    line = line.strip()
                    if line.startswith('|') and 'Product Name' not in line and ':---' not in line:
                        parts = line.split('|')
                        if len(parts) > 1:
                            prod = parts[1].strip()
                            if prod:
                                cache_products.append(prod)
        except Exception as e:
            print(f"⚠️ Warning: Failed to read or parse product cache: {e}", file=sys.stderr)
            use_cache = False
            
    if use_cache and cache_products:
        print("ℹ️ Using cached product list (updated within the last 30 days).")
        print("\n### Available Google Cloud Products")
        print("| Product Name |")
        print("| :--- |")
        for prod in cache_products:
            print(f"| {prod} |")
        return
        
    # Cache missing or stale -> Query BigQuery and update cache
    print("🔍 Fetching all product names from Google Cloud release notes in BigQuery (Cache is stale or missing)...")
    query = """
    SELECT DISTINCT product_name 
    FROM `bigquery-public-data.google_cloud_release_notes.release_notes` 
    WHERE published_at >= '2024-01-01' AND product_name IS NOT NULL
    ORDER BY product_name ASC
    """
    results = execute_query(query)
    
    # Print results
    print("\n### Available Google Cloud Products")
    print("| Product Name |")
    print("| :--- |")
    for row in results:
        print(f"| {row['product_name']} |")
        
    # Write to cache file
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            f.write("# GCP Products Cache\n\n")
            f.write(f"*   **Last Updated**: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write("----\n\n")
            f.write("| Product Name |\n")
            f.write("| :--- |\n")
            for row in results:
                f.write(f"| {row['product_name']} |\n")
        print(f"\n💾 Success! Cached product list to: {cache_path}")
    except Exception as e:
        print(f"⚠️ Warning: Failed to write product cache to {cache_path}: {e}", file=sys.stderr)


def list_types():
    """Lists all available release note types."""
    print("🔍 Fetching release note types...")
    query = """
    SELECT DISTINCT release_note_type 
    FROM `bigquery-public-data.google_cloud_release_notes.release_notes` 
    WHERE published_at >= '2024-01-01' AND release_note_type IS NOT NULL
    ORDER BY release_note_type ASC
    """
    results = execute_query(query)
    
    print("\n### Available Release Note Types")
    print("| Release Note Type |")
    print("| :--- |")
    for row in results:
        print(f"| {row['release_note_type']} |")

def generate_explanation(product_name, release_type, description):
    """Generates a concise AI explanation of why this release item is important/impactful using Gemini."""
    try:
        from google import genai
        client = genai.Client(vertexai=True)
        model_name = "gemini-3-flash-preview"
        
        prompt = f"""
        You are a Google Cloud Principal Solutions Architect. 
        Analyze the following release note for the product "{product_name}" ({release_type}):
        
        Release Description:
        {description}
        
        Provide a single-sentence, highly concise explanation of the architectural impact of this change, why it matters to developers/architects, or what action they should take.
        Be direct, precise, and technical. Do not include introductory phrases like "This change matters because" or "As an architect".
        Keep it under 30 words.
        """
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"⚠️ AI Explanation Unavailable: {e}"

def search_notes(topic, release_type, start_date, limit, output_format, save_path, ai_explain=False):
    """Searches for release notes matching the user parameters."""
    filters = [f"published_at >= '{start_date}'"]
    
    # Build query condition for topic search
    if topic:
        # Match in product name or description
        filters.append(f"(LOWER(product_name) LIKE LOWER('%{topic}%') OR LOWER(description) LIKE LOWER('%{topic}%'))")
        
    if release_type:
        filters.append(f"LOWER(release_note_type) = LOWER('{release_type}')")
        
    filter_clause = " AND ".join(filters)
    
    query = f"""
    SELECT published_at, product_name, release_note_type, description
    FROM `bigquery-public-data.google_cloud_release_notes.release_notes`
    WHERE {filter_clause}
    ORDER BY published_at DESC
    LIMIT {limit}
    """
    
    print(f"🔍 Querying BigQuery for notes matching '{topic or 'ALL'}' (Limit: {limit})...")
    results = execute_query(query)
    
    if not results:
        print(f"\nℹ️ No release notes found matching your criteria since {start_date}.")
        return
        
    is_table = (output_format == 'table')
    
    # Process and clean results
    processed_results = []
    for row in results:
        desc_clean = html_to_markdown(row.get('description', ''), is_table_mode=is_table)
        
        ai_impact = ""
        if ai_explain:
            print(f"🤖 Generating AI Explanation for: {row.get('product_name')} ({row.get('published_at')})...")
            ai_raw = generate_explanation(row.get('product_name'), row.get('release_note_type'), desc_clean)
            ai_impact = html_to_markdown(ai_raw, is_table_mode=is_table)
            
        item = {
            'published_at': row.get('published_at', ''),
            'product_name': row.get('product_name', ''),
            'release_note_type': row.get('release_note_type', ''),
            'description': desc_clean
        }
        if ai_explain:
            item['ai_impact'] = ai_impact
            
        processed_results.append(item)
        
    if output_format == 'json':
        output_str = json.dumps(processed_results, indent=2)
        print(output_str)
    else:
        # Generate Markdown Table
        headers = ["Published At", "Product Name", "Type", "Description"]
        alignments = [":---", ":---", ":---", ":---"]
        if ai_explain:
            headers.append("AI Architect Impact")
            alignments.append(":---")
            
        lines = [
            "## Google Cloud Release Notes: Search Results",
            "",
            f"*   **Topic/Keyword**: \"{topic or 'ALL'}\"",
            f"*   **Release Type Filter**: {release_type or 'ALL'}",
            f"*   **Since**: {start_date}",
            f"*   **Results Limit**: {limit}",
            f"*   **Generated At**: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}",
            "",
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(alignments) + " |"
        ]
        for row in processed_results:
            row_cells = [row['published_at'], row['product_name'], row['release_note_type'], row['description']]
            if ai_explain:
                row_cells.append(row['ai_impact'])
            lines.append("| " + " | ".join(row_cells) + " |")
            
        output_str = "\n".join(lines)
        print(output_str)
        
    if save_path:
        try:
            # Auto-create parent directories if they don't exist
            parent_dir = os.path.dirname(save_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
                
            with open(save_path, 'w', encoding='utf-8') as f:
                if output_format == 'json':
                    json.dump(processed_results, f, indent=2)
                else:
                    f.write(output_str + "\n")
            print(f"\n💾 Success! Saved results to: {save_path}")
        except Exception as e:
            print(f"❌ Error saving results to {save_path}: {e}", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(
        description="Google Cloud Release Notes CLI Search Tool. Queries BigQuery public datasets to find release items by topic.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for GKETopic:
  python3 get_release_notes.py --topic "GKE" --limit 5

  # Search for GKE Features only, since 2025-01-01:
  python3 get_release_notes.py --topic "GKE" --type FEATURE --start-date 2025-01-01

  # List all available products in alphabetical order:
  python3 get_release_notes.py --list-products

  # Save search results as a Markdown table to a file:
  python3 get_release_notes.py --topic "session affinity" --save-artifact "artifacts/session_affinity_notes.md"
"""
    )
    
    parser.add_argument("--topic", help="Topic, keyword, or product name to search for.")
    parser.add_argument("--type", help="Filter by specific release type (e.g., FEATURE, FIX, DEPRECATION).")
    parser.add_argument("--start-date", default="2024-01-01", type=validate_date, help="Start date for search filtering (YYYY-MM-DD). Default is 2024-01-01.")
    parser.add_argument("--limit", default=10, type=int, help="Maximum number of release notes to return (1 to 1000). Default is 10.")
    parser.add_argument("--output", default="table", choices=["table", "json"], help="Console and file output format. 'table' outputs a beautiful Markdown table, 'json' outputs structured JSON.")
    parser.add_argument("--save-artifact", help="Absolute or relative path to write the search results to.")
    parser.add_argument("--list-products", action="store_true", help="Query and list all unique products available in the release notes.")
    parser.add_argument("--list-types", action="store_true", help="Query and list all unique release note types.")
    parser.add_argument("--ai-explain", action="store_true", help="Enables live AI architectural explanations for each release note.")
    
    args = parser.parse_args()
    
    # Clamping limit between 1 and 1000
    if args.limit < 1 or args.limit > 1000:
        args.limit = max(1, min(args.limit, 1000))
        print(f"⚠️ Limit clamped to: {args.limit}")
        
    if args.list_products:
        list_products()
    elif args.list_types:
        list_types()
    elif not args.topic and not args.list_products and not args.list_types:
        parser.print_help()
        sys.exit(0)
    else:
        search_notes(
            topic=args.topic,
            release_type=args.type,
            start_date=args.start_date,
            limit=args.limit,
            output_format=args.output,
            save_path=args.save_artifact,
            ai_explain=args.ai_explain
        )

if __name__ == "__main__":
    main()
