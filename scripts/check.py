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


def _action_names(text: str) -> list[str]:
    """The action each row of the actions table is about, in order.

    The name, not the whole cell. The cell holds a metavariable or two —
    `<node>`, and the ellipses standing in for a string — and those are
    translated on purpose, being English words rather than code. The key in
    front of the `=` is the thing a plugin actually types.
    """
    names = []
    for line in text.splitlines():
        if not line.startswith("| `{ "):
            continue
        m = re.match(r"^\| `\{ (\w+)", line)
        if m:
            names.append(m.group(1))
    return names


def check_action_tables_agree() -> None:
    """Every translation lists the same actions as the English README.

    Eleven translations carry this table, and nothing compared them. An
    eleventh action added to the English one would leave the other eleven at
    ten — and an author reading in their own language would never learn the
    action exists. The editor's repository has had exactly this guard for its
    own README since a capability row went missing in translation.
    """
    english = _action_names((ROOT / "README.md").read_text(encoding="utf-8"))
    if len(english) < 5:
        fail(f"英文 README 只读出 {len(english)} 个动作，取法要跟着改")
        return

    for path in sorted((ROOT / "docs/i18n").glob("README_*.md")):
        theirs = _action_names(path.read_text(encoding="utf-8"))
        if theirs != english:
            missing = [n for n in english if n not in theirs]
            extra = [n for n in theirs if n not in english]
            fail(
                f"{path.relative_to(ROOT)} 的动作表与英文对不上"
                f"（{len(theirs)} 行 vs {len(english)} 行）"
                + (f"，少了 {missing}" if missing else "")
                + (f"，多了 {extra}" if extra else "")
            )


def check_example_says_how_much_it_shows() -> None:
    """The examples say how many of the API they use, and mean it.

    They used to open with "Every capability the editor offers is used once",
    which was not true of either: seven of the twelve, with `pane` — the grid
    the editor actually lays results out in, and the one the shipped plugin
    lives in — among the five missing. An example is the first thing an author
    copies, so a claim on top of it is read as a map of the API.
    """
    lua_lib = (ROOT / "packages/lua/lib/marktext-plus.lua").read_text(encoding="utf-8")
    exported = {
        m.group(1)
        for m in re.finditer(r"^(?:function )?M\.([A-Za-z_]\w*)\s*[=(]", lua_lib, re.M)
    }

    for path, call in (
        (ROOT / "packages/lua/plugin.lua", "sdk."),
        (ROOT / "packages/js/plugin.js", "sdk."),
    ):
        text = path.read_text(encoding="utf-8")
        used = {name for name in exported if re.search(r"sdk\." + name + r"\b", text)}

        claim = re.search(r"uses (\d+) of the (\d+)", text)
        if claim is None:
            fail(f"{path.relative_to(ROOT)} 开头没说它用了几个 API"
                 f"（写成「uses N of the M」，N={len(used)} M={len(exported)}）")
            continue
        said_used, said_all = int(claim.group(1)), int(claim.group(2))
        if said_used != len(used) or said_all != len(exported):
            fail(
                f"{path.relative_to(ROOT)} 说用了 {said_used}/{said_all}，"
                f"实际 {len(used)}/{len(exported)}；没用到的是 "
                f"{sorted(exported - used)}"
            )


def check_ui_nodes_agree() -> None:
    """The node kinds the API module names are the ones the README describes.

    Four kinds — select, checkbox, markdown, image — were added to the editor
    and written into the README's table, and the one-line list inside both API
    modules stayed at seven. That list is what an author sees in a hover, which
    is where the question "what can I put in a tree?" is actually asked.

    The README's table is the reference; the editor's repository is what holds
    *that* to what the editor draws. This only asks the two halves of this
    repository to agree.
    """
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    table = re.search(
        r"^\| `text` \|.*?(?=\n\n)", readme, re.S | re.M
    )
    if table is None:
        fail("README 里找不到界面节点那张表，取法要跟着改")
        return
    documented = set()
    for row in table.group(0).splitlines():
        for name in re.findall(r"`(\w+)`", row.split("|")[1]):
            documented.add(name)
    if len(documented) < 5:
        fail(f"节点表只读出 {sorted(documented)}，取法要跟着改")
        return

    for path, marker in (
        (ROOT / "packages/lua/lib/marktext-plus.lua", "Nodes are plain tables"),
        (ROOT / "packages/js/lib/marktext-plus.js", "Nodes are plain objects"),
    ):
        text = path.read_text(encoding="utf-8")
        at = text.find(marker)
        if at < 0:
            fail(f"{path.relative_to(ROOT)} 里找不到节点清单那句话")
            continue
        # The sentence runs to the full stop that ends the list.
        # The window covers the sentence and the two that follow it; nothing
        # else in there is written in backticks today, and a word that starts
        # being written that way shows up as `多了` rather than being ignored.
        listed = set(re.findall(r"`(\w+)`", text[at:at + 400]))
        missing = documented - listed
        extra = listed - documented
        if missing or extra:
            fail(
                f"{path.relative_to(ROOT)} 的节点清单与 README 对不上"
                + (f"，少了 {sorted(missing)}" if missing else "")
                + (f"，多了 {sorted(extra)}" if extra else "")
            )


def main() -> int:
    check_sdk_parity()
    check_every_export_is_documented()
    check_action_tables_agree()
    check_ui_nodes_agree()
    check_example_says_how_much_it_shows()
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
