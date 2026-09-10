#!/usr/bin/env python3
"""What this repository has to agree with itself about.

Three implementations of one API, a JSON schema, and three example manifests,
all kept in step by hand until now. The editor's own repository has learned the
same lesson three times in one week: a list written twice drifts, and the half
that drifts is the half nobody reads.

Run with no arguments from anywhere; paths are resolved against this file.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
problems: list[str] = []


def fail(message: str) -> None:
    problems.append(message)


def names_in_lua(path: Path) -> set[str]:
    """Every `M.x` the module defines, as a function or as a field."""
    source = path.read_text(encoding="utf-8")
    return {
        m.group(1)
        for m in re.finditer(r"^(?:function )?M\.([A-Za-z_]\w*)\s*[=(]", source, re.M)
    }


def names_in_js(path: Path) -> set[str]:
    """Every key of the exported object literal.

    Read as text rather than by requiring the module: it refers to `storage`,
    `t` and `require`, which the editor injects and node does not have.
    """
    source = path.read_text(encoding="utf-8")
    start = source.index("module.exports = {")
    return {
        m.group(1)
        for m in re.finditer(r"^  ([A-Za-z_]\w*):", source[start:], re.M)
    }


def check_sdk_parity() -> None:
    lua = names_in_lua(ROOT / "packages/lua/lib/marktext-plus.lua")
    js = names_in_js(ROOT / "packages/js/lib/marktext-plus.js")

    # A pattern that stops matching returns an empty set, and two empty sets
    # agree with each other perfectly. Say so instead.
    for label, found in (("lua", lua), ("js", js)):
        if len(found) < 8:
            fail(f"{label} 只读出 {len(found)} 个名字（{sorted(found)}），"
                 f"八成是写法变了而这个脚本没跟上")

    only_lua = sorted(lua - js)
    only_js = sorted(js - lua)
    if only_lua:
        fail(f"只有 lua 有：{only_lua}——插件作者换个语言就用不了")
    if only_js:
        fail(f"只有 js 有：{only_js}——插件作者换个语言就用不了")


def check_schema() -> None:
    schema_path = ROOT / "schema/manifest.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        fail("没有 jsonschema，manifest 只能靠眼看")
        return

    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:  # noqa: BLE001 - reported, not handled
        fail(f"schema 自己不合法：{error}")
        return

    validator = Draft202012Validator(schema)
    manifests = sorted(ROOT.glob("packages/*/manifest.json"))
    if not manifests:
        fail("一个示例 manifest 都没找到，路径变了")
    for manifest in manifests:
        document = json.loads(manifest.read_text(encoding="utf-8"))
        for error in validator.iter_errors(document):
            where = "/".join(str(p) for p in error.path) or "(顶层)"
            fail(f"{manifest.relative_to(ROOT)} 不符合自家 schema：{where} — {error.message}")



def check_documented_paths() -> None:
    """Paths the READMEs point at have to be paths this repository has.

    A release commit once rewrote the README and its eleven translations from
    an older copy, putting back a directory name that had been changed and a
    tool that had been deleted — and shipped that way, so the first thing a
    new plugin author did was open a directory that was not there.
    """
    directories = {
        entry.name
        for entry in ROOT.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    }
    # A path is anything with a slash inside backticks, a fenced block, or a
    # link target. The first segment is what gets checked: a name that is not
    # a directory here is either a typo or a leftover.
    reference = re.compile(r"(?<![\w./-])([A-Za-z][\w-]*)/([\w./-]*)")

    docs = [ROOT / "README.md", *sorted((ROOT / "docs/i18n").glob("*.md"))]
    for doc in docs:
        if not doc.exists():
            fail(f"{doc.relative_to(ROOT)} 不在了")
            continue
        seen: set[str] = set()
        for match in reference.finditer(doc.read_text(encoding="utf-8")):
            head, rest = match.group(1), match.group(2)
            # Only names that look like they mean a directory in here: either
            # one that exists, or one this repository has had before.
            if head not in directories and head not in {"examples", "tool", "tools"}:
                continue
            whole = f"{head}/{rest}".rstrip("/.,)")
            if whole in seen:
                continue
            seen.add(whole)
            if not (ROOT / whole).exists():
                fail(f"{doc.relative_to(ROOT)} 指向不存在的 {whole}")


def check_every_export_is_documented() -> None:
    """Every name a plugin author can call says what it does, right above it.

    `nothing` lost its comment when `ui` was added between it and `replace`:
    the line stayed where it was, so `--- Do nothing.` ended up on top of the
    interface-drawing docs and the function that did nothing said nothing. In
    both languages, because they were edited together.

    Nobody reads this module top to bottom; it is read one function at a time,
    in an editor's hover. A comment one function out is worse than none — it
    describes the wrong thing with the same authority.
    """
    lua = (ROOT / "packages/lua/lib/marktext-plus.lua").read_text(encoding="utf-8")
    lines = lua.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(?:function )?M\.([A-Za-z_]\w*)\s*[=(]", line)
        if not m:
            continue
        above = lines[i - 1].strip() if i > 0 else ""
        if not above.startswith("---"):
            fail(f"lua 的 M.{m.group(1)} 上面没有紧挨着的文档注释")

    js = (ROOT / "packages/js/lib/marktext-plus.js").read_text(encoding="utf-8")
    start = js.index("module.exports = {")
    lines = js[start:].splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^  ([A-Za-z_]\w*):", line)
        if not m:
            continue
        above = lines[i - 1].strip() if i > 0 else ""
        # Either the end of a block comment, or a one-line `/** ... */`.
        if not (above.endswith("*/")):
            fail(f"js 的 {m.group(1)} 上面没有紧挨着的文档注释")


def main() -> int:
    check_sdk_parity()
    check_every_export_is_documented()
    check_schema()
    check_documented_paths()
    if problems:
        print("检查没通过：")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("三份实现、schema 与示例 manifest 一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
