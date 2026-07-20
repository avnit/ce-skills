#!/usr/bin/env python3
"""Parsing and command extraction utilities for codelab validation markdown files."""

import hashlib
import re

# Fenced-block languages whose content is executed as shell commands. Output/data
# languages (text, output, yaml, json, hcl, log, ...) and narrative between blocks
# are never collected. NOTE: 'console' is kept executable to preserve prior behavior;
# whether terminal-session blocks should run is a separate decision (see #77).
_EXECUTABLE_FENCE_LANGS = {"", "bash", "sh", "shell", "console"}
_FENCE_LINE_RE = re.compile(r"^[ \t]*```[ \t]*([^\s`]*)")


def _filter_hermetic_commands(commands: list[str]) -> list[str]:
    clean = []
    for cmd in commands:
        if "while true" in cmd.lower():
            continue
        if "gcloud compute ssh" in cmd.lower() and "--command" not in cmd.lower():
            continue
        clean.append(cmd)
    return clean


def _extract_command_blocks(body: str) -> list[str]:
    """Extract executable fenced code blocks via proper open/close fence pairing.

    A line-based state machine: fences alternate open/close, so the text *between* a
    non-executable block (e.g. a ```text output block) and the next block is never
    captured. This fixes the findall-regex flaw (#77) where a closing fence followed
    by narrative and an opening fence matched as one spurious block — executing the
    narrative as bash and dropping the real command.
    """
    blocks: list[str] = []
    in_block = False
    lang = ""
    buf: list[str] = []
    for raw in body.splitlines():
        line = raw.rstrip("\r")
        is_fence = _FENCE_LINE_RE.match(line)
        if not in_block:
            if is_fence:
                in_block = True
                lang = is_fence.group(1).lower()
                buf = []
            # a non-fence line outside a block is narrative -> ignored
        elif is_fence:
            # any fence line closes the current block
            if lang in _EXECUTABLE_FENCE_LANGS:
                block = "\n".join(buf).strip()
                if block:
                    blocks.append(block)
            in_block = False
            lang = ""
            buf = []
        else:
            buf.append(line)
    return blocks


def normalize_command(cmd: str) -> str:
    lines = []
    for line in cmd.splitlines():
        line_s = line.strip()
        if not line_s or line_s.startswith("#"):
            continue
        if " #" in line_s:
            line_s = line_s.split(" #", 1)[0].strip()
        words = line_s.split()
        lines.append(" ".join(words))
    return "\n".join(lines)


def get_cmd_hash(cmd: str) -> str:
    return hashlib.sha256(normalize_command(cmd).encode("utf-8")).hexdigest()
