#!/usr/bin/env python3
"""Check Markdown constructs that Hugo can otherwise render as literal source."""

from __future__ import annotations

import argparse
import dataclasses
import pathlib
import re
import sys


FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}(?![#\s])")


@dataclasses.dataclass(frozen=True)
class Problem:
    line: int
    column: int
    message: str


def markdown_files(entries: list[pathlib.Path]) -> list[pathlib.Path]:
    files: set[pathlib.Path] = set()
    for entry in entries:
        if entry.is_dir():
            files.update(path for path in entry.rglob("*.md") if path.is_file())
        elif entry.is_file() and entry.suffix.lower() == ".md":
            files.add(entry)
    return sorted(files)


def check_text(text: str) -> tuple[list[Problem], list[int]]:
    problems: list[Problem] = []
    insertions: list[int] = []
    lines = text.splitlines(keepends=True)
    offset = 0
    front_matter: str | None = None
    fence: tuple[str, int] | None = None
    inline_ticks: int | None = None
    strong_open: tuple[int, int] | None = None

    for line_number, line in enumerate(lines, 1):
        stripped = line.rstrip("\r\n")

        if line_number == 1 and stripped in {"---", "+++"}:
            front_matter = stripped
            offset += len(line)
            continue
        if front_matter is not None:
            if stripped == front_matter:
                front_matter = None
            offset += len(line)
            continue

        fence_match = FENCE_RE.match(stripped)
        if fence is not None:
            if fence_match:
                marker = fence_match.group(1)
                if marker[0] == fence[0] and len(marker) >= fence[1]:
                    fence = None
            offset += len(line)
            continue
        if fence_match:
            marker = fence_match.group(1)
            fence = (marker[0], len(marker))
            offset += len(line)
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            problems.append(
                Problem(line_number, heading_match.end(), "ATX heading marker needs a space")
            )

        index = 0
        while index < len(stripped):
            char = stripped[index]
            if char == "\\":
                index += 2
                continue
            if char == "`":
                end = index + 1
                while end < len(stripped) and stripped[end] == "`":
                    end += 1
                run = end - index
                if inline_ticks is None:
                    inline_ticks = run
                elif run == inline_ticks:
                    inline_ticks = None
                index = end
                continue
            if inline_ticks is not None:
                index += 1
                continue
            if char != "*":
                index += 1
                continue

            end = index + 1
            while end < len(stripped) and stripped[end] == "*":
                end += 1
            run = end - index
            if run != 2:
                index = end
                continue

            if strong_open is None:
                previous = stripped[index - 1] if index else "\n"
                if previous.isalnum():
                    problems.append(
                        Problem(
                            line_number,
                            index + 1,
                            "strong emphasis needs whitespace before opening **",
                        )
                    )
                    insertions.append(offset + index)
                strong_open = (line_number, index + 1)
            else:
                following = stripped[end] if end < len(stripped) else "\n"
                if following.isalnum():
                    problems.append(
                        Problem(
                            line_number,
                            end + 1,
                            "strong emphasis needs whitespace after closing **",
                        )
                    )
                    insertions.append(offset + end)
                strong_open = None
            index = end

        offset += len(line)

    if front_matter is not None:
        problems.append(Problem(1, 1, "unclosed front matter"))
    if fence is not None:
        problems.append(Problem(len(lines), 1, "unclosed fenced code block"))
    if inline_ticks is not None:
        problems.append(Problem(len(lines), 1, "unclosed inline code span"))
    if strong_open is not None:
        problems.append(Problem(strong_open[0], strong_open[1], "unclosed strong emphasis"))

    return problems, sorted(set(insertions), reverse=True)


def apply_insertions(text: str, insertions: list[int]) -> str:
    for position in insertions:
        text = text[:position] + " " + text[position:]
    return text


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fix", action="store_true", help="insert missing emphasis whitespace")
    parser.add_argument("paths", nargs="+", type=pathlib.Path)
    args = parser.parse_args()

    paths = markdown_files(args.paths)
    failures: list[tuple[pathlib.Path, Problem]] = []
    fixed = 0
    for path in paths:
        text = path.read_text(encoding="utf-8")
        problems, insertions = check_text(text)
        if args.fix and insertions:
            path.write_text(apply_insertions(text, insertions), encoding="utf-8")
            fixed += len(insertions)
            problems, _ = check_text(path.read_text(encoding="utf-8"))
        failures.extend((path, problem) for problem in problems)

    if failures:
        for path, problem in failures:
            print(
                f"{path}:{problem.line}:{problem.column}: {problem.message}",
                file=sys.stderr,
            )
        print(f"markdown check failed: {len(failures)} problem(s)", file=sys.stderr)
        return 1

    action = f"; fixed {fixed}" if args.fix else ""
    print(f"markdown check passed: {len(paths)} files{action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
