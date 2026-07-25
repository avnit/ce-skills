#!/usr/bin/env python3
"""
HTML Report Generator Module.
Generates zero-indentation HTML tables wrapped in Markdown containers.
CRITICAL RULE - ZERO INDENTATION: Every single HTML line starts at column 0.
"""

from typing import Dict, Any, List


class HTMLReportGenerator:
    """Generates styled Markdown and HTML cost audit reports with strict zero indentation."""

    @staticmethod
    def generate(
        project_id: str,
        resources: List[Dict[str, Any]],
        total_cost: float,
        cache_status: str,
        lookup_ms: float,
        catalog_source: str,
    ) -> str:
        """Constructs report string guaranteeing 0 spaces leading whitespace for all HTML tags."""
        lines = [
            "# Deployed Sandbox Pricing Audit Report",
            "",
            f"- **Target GCP Project**: `{project_id}`",
            f"- **Pricing Catalog Source**: `{catalog_source}` (Cache: {cache_status}, Latency: {lookup_ms:.2f}ms)",
            f"- **Hourly Running Cost**: `${total_cost:.4f}`",
            "",
            "## Active Billable Resources",
            "",
            "<div style=\"max-width: 1000px; margin: 0 auto; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #ffffff; border-radius: 12px; border: 1px solid #e8eaed; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);\">",
            '<table style="width: 100%; border-collapse: collapse; margin: 0; font-size: 13px;">',
            "<thead>",
            '<tr style="background-color: #f8f9fa; border-bottom: 2px solid #e8eaed; text-align: left; color: #3c4043;">',
            '<th style="padding: 12px 16px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Resource Name</th>',
            '<th style="padding: 12px 16px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Resource Type</th>',
            '<th style="padding: 12px 16px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Status</th>',
            '<th style="padding: 12px 16px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Current Configuration</th>',
            '<th style="padding: 12px 16px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Location</th>',
            '<th style="padding: 12px 16px; font-weight: 600; text-transform: uppercase; font-size: 11px; letter-spacing: 0.5px;">Hourly Cost</th>',
            "</tr>",
            "</thead>",
            "<tbody>",
        ]

        for r in resources:
            status_bg = (
                "#e6f4ea"
                if r["status"] in ("RUNNING", "RUNNABLE", "PROVISIONED")
                else "#f1f3f4"
            )
            status_color = (
                "#137333"
                if r["status"] in ("RUNNING", "RUNNABLE", "PROVISIONED")
                else "#5f6368"
            )
            lines.extend(
                [
                    '<tr style="border-bottom: 1px solid #e8eaed; background-color: #ffffff;">',
                    f'<td style="padding: 14px 16px; font-weight: 600; color: #3c4043;">`{r["name"]}`</td>',
                    f'<td style="padding: 14px 16px; color: #5f6368;">{r["type"]}</td>',
                    f'<td style="padding: 14px 16px;"><span style="background: {status_bg}; color: {status_color}; padding: 4px 10px; border-radius: 12px; font-weight: 600; font-size: 11px;">{r["status"]}</span></td>',
                    f'<td style="padding: 14px 16px; color: #5f6368;">{r["config"]}</td>',
                    f'<td style="padding: 14px 16px; color: #5f6368;">{r["location"]}</td>',
                    f'<td style="padding: 14px 16px; font-weight: 600; color: #1a73e8;">${r["hourly_cost"]:.4f}</td>',
                    "</tr>",
                ]
            )

        lines.extend(
            [
                "</tbody>",
                "</table>",
                "</div>",
                "",
                f"**Total Deployed Sandbox Cost**: `${total_cost:.4f} / hour`",
                "",
                "## Audit Warnings & Disclaimers",
                "",
                "> [!NOTE]",
                "> This audit represents exact deterministic hourly configuration charges currently running in your project based on active topologies and Billing Catalog metrics. Volume-based usage (network egress, query scans) is excluded.",
            ]
        )

        return "\n".join(lines)
