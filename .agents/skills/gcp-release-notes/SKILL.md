---
name: gcp-release-notes
description: Shows the latest release note items per user topic from Google Cloud release notes in BigQuery.
---

# Skill: GCP Release Notes

This skill queries the BigQuery public dataset for Google Cloud release notes, filters them by user-defined topics/products/keywords, types, or date, and outputs them in a highly readable, structured Markdown table format.

## How to use

Use the provided script to search and retrieve GCP release notes:

```bash
python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --topic "YOUR_TOPIC" [options]
```

**What it does:**

- Connects to `bigquery-public-data.google_cloud_release_notes.release_notes` via the local authenticated `bq` CLI tool.
- Performs a fast, case-insensitive keyword match against both product names and release descriptions.
- Parses HTML tags (paragraphs, links, lists, bolding, etc.) into neat Markdown.
- Adapts paragraphs and lists using `<br>` tag spacing to ensure cells render cleanly inside a single row of a Markdown table.
- Supports listing all existing product names or release types to browse before searching.
- Supports exporting results to a local Markdown or JSON file.

## CLI Parameters

- `--topic <topic>`: (String) The search keyword or exact product name (e.g., `GKE`, `Vertex AI`, `session affinity`).
- `--type <type>`: (String) Filter by specific release note type (e.g., `FEATURE`, `FIX`, `DEPRECATION`, `BREAKING_CHANGE`).
- `--start-date <date>`: (String, default `2024-01-01`) Start date of release notes in `YYYY-MM-DD` format.
- `--limit <limit>`: (Int, default `10`) Maximum number of results to return (clamped up to 1000).
- `--output <table|json>`: (String, default `table`) Standard output format in the console.
- `--save-artifact <file_path>`: (String) Saves the formatted results to a local file. Creates parent directories automatically if they do not exist.
- `--list-products`: (Flag) Queries and lists all available products in alphabetical order (uses local cache if fresh).
- `--list-types`: (Flag) Queries and lists all available release types.
- `--ai-explain`: (Flag) Enables dynamic Gemini-powered solutions-architect impact analysis for each release note as an extra column.

## Output Format Examples

### Standard Search Result

Running:

```bash
python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --topic "session affinity" --limit 1
```

Yields:

## Google Cloud Release Notes: Search Results

- **Topic/Keyword**: "session affinity"
- **Release Type Filter**: ALL
- **Since**: 2024-01-01
- **Results Limit**: 1
- **Generated At**: 2026-05-04 10:43 AM

| Published At | Product Name         | Type    | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| :----------- | :------------------- | :------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2024-10-29   | Cloud Load Balancing | FEATURE | All the Application Load Balancers, except the classic Application Load Balancer, now support stateful cookie-based session affinity. When you use stateful cookie-based affinity, the load balancer includes an HTTP cookie in the `Set-Cookie` header in response to the initial HTTP request. With stateful session affinity, customers can preserve stickiness to the selected backend. <br> For details, see [Stateful cookie-based session affinity](https://docs.cloud.google.com/load-balancing/docs/backend-service#stateful-session-affinity). <br> This capability is in **General Availability**. |

### AI Explanation Search Result

Running:

```bash
python3 .agents/skills/gcp-release-notes/scripts/get_release_notes.py --topic "Cloud NGFW" --limit 1 --ai-explain
```

Yields:

## Google Cloud Release Notes: Search Results

- **Topic/Keyword**: "Cloud NGFW"
- **Release Type Filter**: ALL
- **Since**: 2024-01-01
- **Results Limit**: 1
- **Generated At**: 2026-05-04 10:54 AM

| Published At | Product Name | Type    | Description                                                                                                                                                                                                                                                                                                                                                                          | AI Architect Impact                                                                                                                                                                                     |
| :----------- | :----------- | :------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2026-03-24   | Cloud NGFW   | FEATURE | You can use the URL filtering service to filter your workload traffic by using <br> domain and Server Name Indication (SNI) information available in the egress <br> HTTP(S) messages. For more information, see <br> [URL filtering service overview](https://docs.cloud.google.com/firewall/docs/about-url-filtering). This <br> feature is available in **General Availability**. | Architects can now enforce granular egress security by filtering outbound traffic via domain and SNI, preventing data exfiltration and ensuring compliance without the overhead of full TLS decryption. |
