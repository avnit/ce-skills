---
trigger: always_on
description: Enforces the creation and continuous updates of a consistent, beautifully formatted HTML table task tracking file saved as an unindented .md artifact to guarantee native visual previews.
---

# Task Tracking and Reporting Standard

Whenever the user prompts you to perform work, you **MUST** create a task tracking file for the run and display it to the user. This file serves as the single source of truth for the execution state, providing transparency, structured progress tracking, and a consistent user experience time after time.

## Requirements

1. **Format**: The task file must be written using a **styled HTML `<table>`** embedded inside a markdown container to provide rigid column alignment and scannability.
2. **Filename**: Save the file as **`task.md`** (e.g., `<appDataDir>/brain/<conversation-id>/task.md`). Using the `.md` extension ensures that when the user clicks the link in the chat, their environment automatically opens it in a rendered visual preview tab.
3. **CRITICAL RULE - ZERO INDENTATION**: You **MUST NOT** indent any HTML tags. Keep every single line completely flush left (0 spaces of leading whitespace). Markdown specifications interpret lines indented by 4+ spaces as preformatted code blocks, which breaks table rendering.
4. **Continuous Updates**: Keep the file updated as you execute each step. Dynamically change step statuses (e.g., from `PENDING` to `RUNNING` to `DONE` or `ERROR`) and update timestamps accordingly.

## Consistent Unindented Table Template

Use the following standardized inline-CSS table template. Ensure all placeholders are populated dynamically:

<!-- prettier-ignore -->
```html
<div style="max-width: 900px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
<div style="padding: 20px 24px; background: #ffffff; border-bottom: 1px solid #e8eaed; border-left: 6px solid #1a73e8;">
<h1 style="margin: 0 0 8px 0; font-size: 22px; color: #1a73e8; font-weight: 600;">[Task Title / Overview]</h1>
<div style="display: flex; flex-wrap: wrap; gap: 16px; font-size: 13px; color: #5f6368;">
<div style="display: flex; align-items: center; gap: 6px;">
<strong>Overall Status:</strong>
<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px;">IN PROGRESS</span>
</div>
<div><strong>Started:</strong> [YYYY-MM-DD HH:MM:SS]</div>
<div><strong>Last Updated:</strong> [YYYY-MM-DD HH:MM:SS]</div>
<div><strong>GCP Project ID:</strong> [PROJECT_ID / NONE]</div>
<div><strong>Test Status:</strong> <a href="file:///<appDataDir>/brain/<conversation-id>/test_status.md">[test_status.md]</a></div>
</div>
</div>
<div style="padding: 20px 24px; border-bottom: 1px solid #e8eaed;">
<div style="font-size: 14px; font-weight: 600; margin: 0 0 8px 0; color: #3c4043; text-transform: uppercase; letter-spacing: 0.5px;">Objective</div>
<p style="margin: 0; font-size: 14px; color: #5f6368; line-height: 1.5;">[Detailed description of the user request and expected final outcome.]</p>
</div>
<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">
<thead>
<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">
<th style="padding: 12px 24px; font-weight: 600; width: 100px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>
<th style="padding: 12px 12px 12px 0; font-weight: 600; width: 240px; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Execution Step</th>
<th style="padding: 12px 24px 12px 0; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Details & Outputs</th>
</tr>
</thead>
<tbody>
<!-- Example Completed Step -->
<tr style="border-bottom: 1px solid #e8eaed; background-color: #fafbfc;">
<td style="padding: 14px 24px; vertical-align: top;">
<span style="background: #e6f4ea; color: #137333; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">DONE</span>
</td>
<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">Step 1: [Step Name]</td>
<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">
[Description of what was executed]
<pre style="font-family: ui-monospace, monospace; font-size: 11px; background: #f1f3f4; padding: 8px 12px; border-radius: 6px; color: #202124; margin: 8px 0 0 0; white-space: pre-wrap; word-break: break-all;">[Optional output block]</pre>
</td>
</tr>
<!-- Example Running Step -->
<tr style="border-bottom: 2px solid #1a73e8; background-color: #ffffff;">
<td style="padding: 14px 24px; vertical-align: top;">
<span style="background: #e8f0fe; color: #1a73e8; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">RUNNING</span>
</td>
<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #1a73e8;">Step 2: [Step Name]</td>
<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">[Current action description]</td>
</tr>
<!-- Example Pending Step -->
<tr style="border-bottom: 1px solid #e8eaed; background-color: #fafbfc;">
<td style="padding: 14px 24px; vertical-align: top;">
<span style="background: #f1f3f4; color: #5f6368; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px; letter-spacing: 0.5px; display: inline-block;">PENDING</span>
</td>
<td style="padding: 14px 12px 14px 0; vertical-align: top; font-weight: 600; color: #3c4043;">Step 3: [Step Name]</td>
<td style="padding: 14px 24px 14px 0; vertical-align: top; color: #5f6368;">[Planned next action]</td>
</tr>
</tbody>
</table>
</div>
```
