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


def main() -> int:
    check_sdk_parity()
    check_schema()
    if problems:
        print("检查没通过：")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    print("三份实现、schema 与示例 manifest 一致。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
