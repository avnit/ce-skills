
def generate_html_table(title, objective, overall_status, steps):
    """
    Generates a completely unindented HTML status table as mandated by tasks.md.
    All lines are flush left to guarantee flawless markdown parser evaluation.
    """
    status_colors = {
        "DONE": ("#e6f4ea", "#137333"),
        "RUNNING": ("#e8f0fe", "#1a73e8"),
        "BLOCKED": ("#ffebee", "#c53929"),
        "PENDING": ("#f1f3f4", "#5f6368"),
        "FAILED": ("#fce8e6", "#c53929"),
        "IN PROGRESS": ("#e8f0fe", "#1a73e8"),
        "COMPLETED": ("#e6f4ea", "#137333"),
    }
    
    # Header and overall details
    lines = [
        '<div style="max-width: 900px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">',
        '<div style="padding: 20px 24px; background: #ffffff; border-bottom: 1px solid #e8eaed; border-left: 6px solid #1a73e8;">',
        f'<h1 style="margin: 0 0 8px 0; font-size: 22px; color: #1a73e8; font-weight: 600;">{title}</h1>',
        '<div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #5f6368;">',
        '<div style="display: flex; align-items: center; gap: 6px;">',
        '<strong>Overall Status:</strong>',
        f'<span style="background: {status_colors[overall_status][0]}; color: {status_colors[overall_status][1]}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px;">{overall_status}</span>',
        '</div>',
        '<div><strong>Started:</strong> 2026-05-18 19:40:00</div>',
        '<div><strong>Last Updated:</strong> 2026-05-18 19:40:00</div>',
        '</div>',
        '</div>',
        '<div style="padding: 20px 24px; border-bottom: 1px solid #e8eaed;">',
        '<div style="font-size: 14px; font-weight: 600; margin: 0 0 8px 0; color: #3c4043; text-transform: uppercase; letter-spacing: 0.5px;">Objective</div>',
        f'<p style="margin: 0; font-size: 14px; color: #5f6368; line-height: 1.5;">{objective}</p>',
        '</div>',
        '<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">',
        '<thead>',
        '<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">',
        '<th style="padding: 12px 24px; font-weight: 600; width: 100px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>',
        '<th style="padding: 12px 12px 12px 0; font-weight: 600; width: 240px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Execution Step</th>',
        '<th style="padding: 12px 24px 12px 0; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Details & Outputs</th>',
        '</tr>',
        '</thead>',
        '<tbody>'
    ]
    
    # Step rows
    for step in steps:
        status = step["status"]
        bg, fg = status_colors[status]
        border_style = "border-bottom: 2px solid #1a73e8;" if status == "RUNNING" else "border-bottom: 1px solid #e8eaed;"
        row_bg = "background-color: #ffffff;" if status == "RUNNING" else "background-color: #fafbfc;"
        
        lines.extend([
            f'<tr style="{border_style} {row_bg}">',
            '<td style="padding: 14px 24px; vertical-align: top;">',
            f'<span style="background: {bg}; color: {fg}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">{status}</span>',
            '</td>',
            f'<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: {"#1a73e8" if status == "RUNNING" else "#3c4043"};">',
            f'Step {step["num"]}: {step["title"]}',
            '</td>',
            '<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">',
            step["details"]
        ])
        
        if step.get("error"):
            lines.extend([
                '<pre style="font-family: ui-monospace, monospace; font-size: 11px; background: #f1f3f4; padding: 8px 12px; border-radius: 6px; color: #202124; margin: 8px 0 0 0; white-space: pre-wrap; word-break: break-all;">',
                step["error"].replace("<", "&lt;").replace(">", "&gt;"),
                '</pre>'
            ])
            
        lines.extend([
            '</td>',
            '</tr>'
        ])
        
    lines.extend([
        '</tbody>',
        '</table>',
        '</div>'
    ])
    
    # Enforce completely flush left (0 leading spaces on every line)
    return "\n".join(line.strip() for line in lines)

def lint_html(content):
    """
    Lints the HTML content to ensure there is absolutely zero leading spaces.
    """
    lines = content.split("\n")
    for idx, line in enumerate(lines):
        if line.startswith(" ") or line.startswith("\t"):
            print(f"LINT ERROR: Leading whitespace found on line {idx + 1}: {repr(line)}")
            return False
    return True

# ---------------------------------------------------------
# Simulation Execution
# ---------------------------------------------------------

if __name__ == "__main__":
    print("Starting System B Visual Status Simulation Dry-Run...")
    
    steps = [
        {"num": 1, "title": "Enable Google Cloud APIs", "status": "PENDING", "details": "Enable Compute and container APIs."},
        {"num": 2, "title": "Provision Custom VPC", "status": "PENDING", "details": "Create VPC and secure proxy subnets."},
        {"num": 3, "title": "Verify End-to-End Connectivity", "status": "PENDING", "details": "Run curl checks and verify routing policies."}
    ]
    
    # Transition 1: Step 1 is RUNNING
    steps[0]["status"] = "RUNNING"
    steps[0]["details"] = "Running api enablement commands..."
    html1 = generate_html_table("CE-Scale Codelab Validation Run", "Validate the Secure Proxy topology.", "IN PROGRESS", steps)
    assert lint_html(html1), "Transition 1 Lint Failed!"
    
    # Transition 2: Step 1 is DONE, Step 2 is RUNNING
    steps[0]["status"] = "DONE"
    steps[0]["details"] = "Successfully enabled compute.googleapis.com and container.googleapis.com."
    steps[1]["status"] = "RUNNING"
    steps[1]["details"] = "Executing gcloud network creation command..."
    html2 = generate_html_table("CE-Scale Codelab Validation Run", "Validate the Secure Proxy topology.", "IN PROGRESS", steps)
    assert lint_html(html2), "Transition 2 Lint Failed!"
    
    # Transition 3: Step 2 becomes BLOCKED
    steps[1]["status"] = "BLOCKED"
    steps[1]["details"] = "VPC creation blocked by quota restrictions."
    steps[1]["error"] = "ERROR: (gcloud.compute.networks.create) Quota 'NETWORKS' exceeded. Limit: 5 in region us-central1."
    html3 = generate_html_table("CE-Scale Codelab Validation Run", "Validate the Secure Proxy topology.", "IN PROGRESS", steps)
    assert lint_html(html3), "Transition 3 Lint Failed!"
    
    # Transition 4: Step 2 becomes DONE, Step 3 becomes RUNNING
    steps[1]["status"] = "DONE"
    steps[1]["details"] = "Subnets and VPC provisioned successfully after manual quota increase."
    if "error" in steps[1]:
        del steps[1]["error"]
    steps[2]["status"] = "RUNNING"
    steps[2]["details"] = "Sending connectivity probe packets from client pod..."
    html4 = generate_html_table("CE-Scale Codelab Validation Run", "Validate the Secure Proxy topology.", "IN PROGRESS", steps)
    assert lint_html(html4), "Transition 4 Lint Failed!"
    
    # Transition 5: Step 3 FAILED, Overall FAILED
    steps[2]["status"] = "FAILED"
    steps[2]["details"] = "Connectivity probe failed."
    steps[2]["error"] = "curl: (7) Failed to connect to 10.0.0.1 port 80: Connection timed out after 30000 milliseconds."
    html5 = generate_html_table("CE-Scale Codelab Validation Run", "Validate the Secure Proxy topology.", "FAILED", steps)
    assert lint_html(html5), "Transition 5 Lint Failed!"
    
    print("Simulation Succeeded!")
