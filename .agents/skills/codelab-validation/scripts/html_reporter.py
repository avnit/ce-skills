#!/usr/bin/env python3
"""
HTML Reporter module for Codelab Validation Engine.
Decouples UI formatting and zero-indentation HTML board generation from core execution logic.
"""

import datetime
from typing import List, Dict, Any

HTML_SKELETON_TOP = """<div style="max-width: 900px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
<div style="padding: 20px 24px; background: #ffffff; border-bottom: 1px solid #e8eaed; border-left: 6px solid #1a73e8;">
<h1 style="margin: 0 0 8px 0; font-size: 22px; color: #1a73e8; font-weight: 600;">Codelab Unified Stateful Validation Board</h1>
<div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #5f6368;">"""

HTML_SKELETON_MID = """</div>
</div>
<div style="padding: 20px 24px; border-bottom: 1px solid #e8eaed;">
<div style="font-size: 14px; font-weight: 600; margin: 0 0 8px 0; color: #3c4043; text-transform: uppercase; letter-spacing: 0.5px;">Objective</div>
<p style="margin: 0; font-size: 14px; color: #5f6368; line-height: 1.5;">
Validate the codelab step-by-step using stateful verification, ensuring correctness, command cache hits, and persistent subshell execution.
</p>
</div>
<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">
<thead>
<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">
<th style="padding: 12px 24px; font-weight: 600; width: 100px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>
<th style="padding: 12px 12px 12px 0; font-weight: 600; width: 240px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Execution Step</th>
<th style="padding: 12px 24px 12px 0; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Details & Outputs</th>
</tr>
</thead>
<tbody>"""

HTML_SKELETON_BOT = """</tbody>
</table>
</div>"""

BADGE_MAP = {
    "PENDING": '<span style="background: #f1f3f4; color: #5f6368; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">PENDING</span>',
    "RUNNING": '<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">RUNNING</span>',
    "DONE": '<span style="background: #e6f4ea; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">DONE</span>',
    "FAILED": '<span style="background: #fce8e6; color: #c53929; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">FAILED</span>',
    "BLOCKED": '<span style="background: #ffebee; color: #c53929; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">BLOCKED</span>',
    "IN PROGRESS": '<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">IN PROGRESS</span>',
    "COMPLETED": '<span style="background: #e6f4ea; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">COMPLETED</span>',
    "SKIPPED/NO-OP": '<span style="background: #f1f3f4; color: #5f6368; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">SKIPPED/NO-OP</span>'
}

class HTMLReporter:
    """Handles generating zero-indentation HTML task tracking reports."""
    
    @staticmethod
    def generate_board(project_id: str, steps: List[Dict[str, Any]], overall_status: str = "IN PROGRESS", repo_root: str = "") -> str:
        """Compiles the complete HTML string representing the current validation state."""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        lines = [
            HTML_SKELETON_TOP,
            f'<div style="display: flex; align-items: center; gap: 6px;"><strong>Overall Status:</strong> {BADGE_MAP.get(overall_status, BADGE_MAP["PENDING"])}</div>',
            f'<div><strong>Project ID:</strong> {project_id}</div>',
            f'<div><strong>Last Updated:</strong> {timestamp}</div>',
            HTML_SKELETON_MID
        ]

        for step in steps:
            status = step.get("status", "PENDING")
            badge = BADGE_MAP.get(status, BADGE_MAP["PENDING"])
            row_style = 'border-bottom: 1px solid #e8eaed; background-color: #fafbfc;'
            if status == "RUNNING":
                row_style = 'border-bottom: 2px solid #1a73e8; background-color: #ffffff;'

            details = step.get("instructions", "")
            if step.get("has_gui"):
                details = '<span style="background: #fff3e0; color: #e65100; padding: 3px 8px; border-radius: 12px; font-size: 10px; font-weight: 600; letter-spacing: 0.5px; display: inline-block; margin-bottom: 6px;">🖥️ GUI / MANUAL ACTION</span><br>' + details
            if step.get("commands"):
                cmd_text = step["commands"][0]
                if repo_root:
                    prefix_to_strip = f'export PATH="{repo_root}/bin:$HOME/.local/bin:$PATH"'
                    if cmd_text.startswith(prefix_to_strip):
                        cmd_text = cmd_text[len(prefix_to_strip):].lstrip()
                cmd_preview = cmd_text[:100] + "..." if len(cmd_text) > 100 else cmd_text
                details += f'<br><code style="font-family: monospace; font-size: 11px; color: #202124; background: #f1f3f4; padding: 2px 4px; border-radius: 4px;">{cmd_preview}</code>'

            lines.append(f'<tr style="{row_style}">')
            lines.append(f'<td style="padding: 14px 24px; vertical-align: top;">{badge}</td>')
            lines.append(f'<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: {"#1a73e8" if status == "RUNNING" else "#3c4043"};">Step {step["num"]}: {step["title"]}</td>')
            lines.append(f'<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">{details}')
            
            if step.get("error"):
                safe_err = step["error"].replace("<", "&lt;").replace(">", "&gt;")
                lines.append(f'<pre style="font-family: ui-monospace, monospace; font-size: 11px; background: #f1f3f4; padding: 8px 12px; border-radius: 6px; color: #202124; margin: 8px 0 0 0; white-space: pre-wrap; word-break: break-all;">{safe_err}</pre>')
            lines.append('</td></tr>')

        lines.append(HTML_SKELETON_BOT)
        return "\n".join(line.strip() for line in lines)
