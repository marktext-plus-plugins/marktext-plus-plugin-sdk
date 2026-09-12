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


def check_commands_are_answered() -> None:
    """Every command an example declares is one its script names.

    An example that does not work teaches the wrong thing more effectively
    than no example at all, and this is the way one stops working without
    anybody noticing: a menu entry is added to the manifest and the script is
    not, so the reader clicks it and the plugin does whatever its last branch
    happens to do. The official plugin had precisely that shape — one of its
    four commands reached the translation branch by not being either of the
    two above it — and nothing in either repository could see it.

    Both directions. A branch for a command the manifest does not declare can
    never run: the editor refuses a command a plugin never declared, so that
    code is dead and says otherwise.
    """
    pattern = re.compile(r'command\s*[=!~]==?\s*"([^"]+)"')
    examples = 0
    for manifest_path in sorted(ROOT.glob("packages/*/manifest.json")):
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        entry = manifest.get("entrypoint")
        if not entry:
            continue
        script = manifest_path.parent / entry
        if not script.exists():
            fail(f"{manifest_path.parent.name} 的 entrypoint {entry} 不存在")
            continue

        declared = {
            item["id"]
            for key in ("menus", "panels", "toolbar", "commands")
            for item in (manifest.get(key) or [])
            if isinstance(item, dict) and item.get("id")
        }
        if not declared:
            continue
        examples += 1

        answered = set(pattern.findall(script.read_text(encoding="utf-8")))
        # A reading that stops matching returns an empty set, and an empty set
        # agrees with nothing rather than with everything — say so.
        if not answered:
            fail(f"{script.relative_to(ROOT)} 里读不出任何命令比较，取法要跟着改")
            continue

        for missing in sorted(declared - answered):
            fail(
                f"{manifest_path.relative_to(ROOT)} 声明了 {missing}，"
                f"而 {script.name} 从不与它比较"
                "——一个什么都不做、或者做错事的菜单项"
            )
        for extra in sorted(answered - declared):
            fail(
                f"{script.relative_to(ROOT)} 处理 {extra}，"
                f"而 manifest 没有声明它——编辑器会先拒绝，那个分支永远不会运行"
            )

    if examples < 2:
        fail(f"只核对了 {examples} 个示例，路径或 manifest 结构变了")

def check_no_bare_return() -> None:
    """No Lua here uses a valueless `return`.

    The editor runs plugin Lua on `lua_dardo`, where a valueless `return`
    inside a nested function is not a return at all: execution carries on to
    the next statement. `if not ok then return end` is how every Lua
    programmer writes a guard, so this is not an exotic corner — and inside
    `while true` the same fault is a loop with no exit, which reaches the
    reader as an editor that has stopped answering.

    The README says all this in its own table. The examples beside it are what
    an author copies, and nothing here compared the two: the check that does
    lives in the editor's repository, and its CI only runs when the editor is
    pushed. An example broken here stayed broken until then.

    Every way Lua lets the statement be written: alone, before `end`, before
    `else`, closed with a semicolon, or followed by a comment.
    """
    bare = re.compile(r'\breturn\s*(end\b|else\b|;|--|$)')
    files = sorted(ROOT.glob("packages/**/*.lua"))
    if not files:
        fail("一个 .lua 都没扫到，路径变了")
        return
    for path in files:
        for number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("--"):
                continue
            if bare.search(line):
                fail(f"{path.relative_to(ROOT)}:{number} 的 return 不会真的返回，"
                     f"改成 return nil：{line.strip()}")


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



def check_contribution_points_agree() -> None:
    """The contribution points block, against the schema and against itself.

    The block is what an author copies. It listed five keys and three of them
    were drawn by the editor; `toolbar` and `pages` were read and then never
    looked at again, and nothing in the block said so — the `†` that means "the
    permission is real and there is nothing behind it" lived two sections away,
    in the permissions table, and `pages` has no permission to carry one.

    So three readings, none of which existed:

    * every key in the block is a property the schema has, and every array-of-
      objects property the schema has is either in the block or excused here.
      A field added to one and not the other is what put this repository's
      README ahead of its own schema before.
    * the eleven translations list the same keys in the same order. The action
      table beside this has had that guard since a row went missing in
      translation; the contribution points had not.
    * they carry the same number of `‡` marks. That symbol is what tells an
      author the editor does not run a compiled plugin yet, and a translation
      that loses it costs somebody an evening.
    """
    schema = json.loads((ROOT / "schema/manifest.schema.json").read_text(encoding="utf-8"))
    properties = schema.get("properties") or {}

    # Documented in a section of its own rather than in the block.
    elsewhere = {"settings"}
    from_schema = {
        name
        for name, spec in properties.items()
        if spec.get("type") == "array"
        and (spec.get("items") or {}).get("type") == "object"
    }
    if not from_schema:
        fail("schema 里读不出任何「数组套对象」的字段，取法要跟着改")
        return

    docs = [ROOT / "README.md", *sorted((ROOT / "docs/i18n").glob("README_*.md"))]
    if len(docs) < 12:
        fail(f"只找到 {len(docs)} 份文档，取法要跟着改")
        return

    english_keys: list[str] | None = None
    english_marks: int | None = None
    for path in docs:
        text = path.read_text(encoding="utf-8")
        keys = re.findall(r'^"(\w+)":', text, re.M)
        marks = text.count("‡")
        if not keys:
            fail(f"{path.relative_to(ROOT)} 里读不出贡献点块，取法要跟着改")
            continue

        if english_keys is None:
            english_keys, english_marks = keys, marks
            missing = sorted(from_schema - set(keys) - elsewhere)
            extra = sorted(set(keys) - from_schema)
            if missing:
                fail(
                    f"schema 有这些贡献点而 README 的块里没有：{missing}——"
                    "作者照块抄就不会知道它们存在"
                )
            if extra:
                fail(
                    f"README 的块里有这些而 schema 不认：{extra}——"
                    "照块写出来的 manifest 装不上"
                )
            continue

        if keys != english_keys:
            fail(
                f"{path.relative_to(ROOT)} 的贡献点与英文对不上："
                f"{keys} vs {english_keys}"
            )
        if marks != english_marks:
            fail(
                f"{path.relative_to(ROOT)} 的 ‡ 标记数与英文对不上"
                f"（{marks} vs {english_marks}）——"
                "那个符号是在说编辑器还不会启动编译型插件，丢了要花掉别人一个晚上"
            )


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


def check_dart_package_version() -> None:
    """The Dart package says the version this SDK was released at.

    It had said 0.1.1 since a refactor, through two releases, because nothing
    read it and nothing compared it. An author who takes the package by path
    and looks at what they have would have been told the wrong thing — and a
    version number is the one field whose whole purpose is to be believed.
    """
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    released = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", changelog, re.M)
    if not released:
        fail("CHANGELOG 里读不出任何已发布版本，取法要跟着改")
        return
    newest = released[0]

    pubspec = (ROOT / "packages/dart/pubspec.yaml").read_text(encoding="utf-8")
    m = re.search(r"^version: (\S+)", pubspec, re.M)
    if m is None:
        fail("packages/dart/pubspec.yaml 里找不到 version")
        return
    if m.group(1) != newest:
        fail(
            f"packages/dart 的版本是 {m.group(1)}，而 CHANGELOG 最新发布的是 "
            f"{newest}——发版时这两处要一起改"
        )


def main() -> int:
    check_sdk_parity()
    check_dart_package_version()
    check_every_export_is_documented()
    check_action_tables_agree()
    check_ui_nodes_agree()
    check_example_says_how_much_it_shows()
    check_commands_are_answered()
    check_no_bare_return()
    check_schema()
    check_contribution_points_agree()
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
