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

_CONTROL_FLOW_KEYWORDS = {
    "if", "then", "elif", "else", "fi",
    "for", "while", "until", "do", "done",
    "case", "esac", "function", "{", "}", "(", ")"
}

_STATE_MUTATING_CMDS = {
    "export", "cd", "source", ".", "alias", "unset",
    "pushd", "popd", "declare", "readonly", "eval"
}

_BARE_ASSIGN_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")


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


def classify_block(block: str) -> tuple[str, list[str]]:
    """Classifies a shell code block into an execution tier and returns its logical executable units.

    Tiers:
      - "flat": simple sequential logical lines. Units are individual logical lines.
      - "compound_pure": complex/compound structure without state-mutating commands. Unit is [whole block].
      - "compound_stateful": complex/compound structure with state-mutating commands. Unit is [whole block].

    Note: A backslash '\\' followed by trailing whitespace is stripped and treated as an intended
    line continuation matching author intent. Operator continuations ('&&', '||', '|') at line end
    are also joined into logical lines without requiring backslashes.
    """
    raw_block = block.strip()
    if not raw_block:
        return "flat", []

    # 1. Join backslash line continuations and operator continuations (&&, ||, |) into logical lines
    lines = block.splitlines()
    logical_lines = []
    current = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if line.endswith("\\"):
            content = line[:-1].strip() if current else line[:-1].rstrip()
            if content:
                current.append(content)
        elif line.endswith("&&") or line.endswith("||") or line.endswith("|"):
            content = line.strip() if current else line.rstrip()
            if content:
                current.append(content)
        else:
            content = line.strip() if current else line
            if content:
                current.append(content)
            logical_lines.append(" ".join(current).strip())
            current = []

    if current:
        logical_lines.append(" ".join(current).strip())

    # Filter out blank lines and comment-only lines
    non_comment_lines = []
    for ll in logical_lines:
        if ll and not ll.startswith("#"):
            non_comment_lines.append(ll)

    if not non_comment_lines:
        return "flat", []

    is_compound = False

    # 2. Check for Heredocs (<< or <<-)
    if re.search(r"<<-?\s*", block):
        is_compound = True

    # 3. Check for control-flow keywords at statement start
    if not is_compound:
        for line in non_comment_lines:
            sub_cmds = re.split(r";|&&|\|\||\|", line)
            for sub in sub_cmds:
                words = sub.strip().split()
                if words and words[0] in _CONTROL_FLOW_KEYWORDS:
                    is_compound = True
                    break
            if is_compound:
                break

    # 4. Check for trailing & (and not &&)
    if not is_compound:
        for line in non_comment_lines:
            if re.search(r"(?<!&)&\s*$", line):
                is_compound = True
                break

    # 5. Check for unbalanced quotes or parens
    if not is_compound:
        sq_count = block.count("'")
        dq_count = len(re.findall(r'(?<!\\)"', block))
        paren_open = block.count("(")
        paren_close = block.count(")")

        if sq_count % 2 != 0 or dq_count % 2 != 0 or paren_open != paren_close:
            is_compound = True

    if not is_compound:
        for line in non_comment_lines:
            sq = line.count("'")
            dq = len(re.findall(r'(?<!\\)"', line))
            if sq % 2 != 0 or dq % 2 != 0:
                is_compound = True
                break

    if is_compound:
        # Check if compound block contains state-mutating commands or variable assignments
        has_state_mutation = False
        for line in non_comment_lines:
            sub_cmds = re.split(r";|&&|\|\||\|", line)
            for sub in sub_cmds:
                words = sub.strip().split()
                if words:
                    cmd_name = words[0]
                    if cmd_name in _STATE_MUTATING_CMDS or _BARE_ASSIGN_RE.match(cmd_name):
                        has_state_mutation = True
                        break
            if has_state_mutation:
                break

        if has_state_mutation:
            return "compound_stateful", [raw_block]
        else:
            return "compound_pure", [raw_block]

    return "flat", non_comment_lines
