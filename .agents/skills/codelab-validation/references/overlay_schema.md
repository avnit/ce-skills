# Codelab Validation Overlay Schema

The per-lab overlay file (`labs/validate/<lab_name>/overlay.json`) allows specifying lab-specific transformations without polluting the generic engine policies in `validator.py`.

## Overlay File Location

When validating a lab, `validator.py` checks for `overlay.json` inside the lab's validation directory (`labs/validate/<lab_name>/overlay.json`). If present, rules are executed after generic engine policies (such as interactive login commenting and project ID substitution).

`overlay.json` is preserved across validation runs during run-directory state cleanup.

## When to Use Overlays (Sandbox vs Narrative Doctrine)

Use `overlay.json` ONLY for environment-specific remediations required to execute a lab within a specific validation sandbox environment (such as temporary org-policy overrides, sandbox quota/zone workarounds, or test-environment version constraints).

**Rule**: **SYNTAX errors** belong directly in the published `.lab.md` narrative. **ENVIRONMENT-specific remediations** (e.g., `--no-address`, `--shielded-secure-boot`, or org-policy bypass flags) MUST go into `overlay.json` and MUST NEVER be baked into the published `.lab.md` narrative, as readers' target environments and org policies differ.

## JSON Schema Structure

```json
{
  "description": "Human-readable description of why this overlay is needed for the codelab.",
  "replacements": [
    {
      "find": "Exact string or regex pattern to search for in the codelab content",
      "replace": "Replacement string",
      "regex": false
    }
  ],
  "append_after_match": [
    {
      "match": "String pattern to search for inside bash code blocks",
      "append_lines": [
        "Line 1 to append to the end of matching bash block",
        "Line 2 to append to the end of matching bash block"
      ]
    }
  ]
}
```

### Fields

- `description` _(string, optional)_: Explains the architectural or lab-specific motivation for the overlay.
- `replacements` _(array of objects, optional)_:
  - `find` _(string, required)_: The target string or regular expression pattern.
  - `replace` _(string, required)_: The replacement string.
  - `regex` _(boolean, optional, default: `false`)_: If `true`, `find` is evaluated as a regular expression via `re.sub()`. If `false`, literal string replacement (`str.replace()`) is performed.
- `append_after_match` _(array of objects, optional)_:
  - `match` _(string, required)_: Pattern to look for inside executable ` ```bash ` blocks.
  - `append_lines` _(array of strings, required)_: Lines appended to the end of any bash block containing `match`.

## Realistic Example

```json
{
  "description": "Overlay for Agent Gateway codelab: relaxes Terraform version constraint and injects service creation error bypass.",
  "replacements": [
    {
      "find": "required_version = \">= 1.12.2\"",
      "replace": "required_version = \">= 1.10.0\"",
      "regex": false
    },
    {
      "find": "agent-gateways import agent-gateway --source=agent-gateway.yaml",
      "replace": "agent-gateways export agent-gateway --destination=agent-gateway.yaml",
      "regex": false
    }
  ],
  "append_after_match": [
    {
      "match": "gcloud alpha agent-registry services create",
      "append_lines": [
        "# Bypass idempotent re-creation error",
        "echo \"Service registration complete\""
      ]
    }
  ]
}
```

## Audit & Error Handling

- **Audit**: All applied overlay rules are printed to stdout by `validator.py` and rendered in `validation-report.md` under the `## Applied Overlay Transforms` section.
- **Error Handling**: Malformed JSON or unreadable `overlay.json` files trigger a hard error (`exit 1`) to ensure lab validation fails explicitly and auditably.
