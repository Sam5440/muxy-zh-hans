#!/usr/bin/env python3
"""校验 muxy-zh-hans 语言包, 规则对齐 Muxy 2.x 的加载器
(crates/muxy-app-core/src/localization.rs + catalog.rs):

  1. package.json 的 muxy.localizations 字段合法, language 与 .lproj 目录名一致
  2. bundle 必须有 Info.plist 且不得含 CFBundleExecutable
  3. Localizable.strings 可解析 (old-style plist 语法)
  4. 每条译文只能读取原文传入的参数: 占位符的类型与位置必须被原文覆盖
     (%@ / %lld / %1$@ / %%), 不允许多读或类型不符
  5. 与英文目录 (en.lproj/Localizable.strings) 对比:
     缺失键 / 多余键 / 未翻译键统计

退出码: 0=通过 (可以有未翻译), 1=有错误.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EN_CATALOG = os.path.join(ROOT, "..", "muxy", "crates", "muxy-app", "localization",
                          "en.lproj", "Localizable.strings")

MAX_BYTES = 4 * 1024 * 1024


def parse_strings(text, source="<strings>"):
    """解析 old-style .strings: "key" = "value"; 支持 \\n \\t \\" \\\\ \\uXXXX 等转义。"""
    entries = {}
    i, n = 0, len(text)
    def skip_ws_comments(i):
        while i < n:
            while i < n and text[i] in " \t\r\n":
                i += 1
            if i < n and text.startswith("//", i):
                j = text.find("\n", i)
                i = n if j < 0 else j + 1
                continue
            if i < n and text.startswith("/*", i):
                j = text.find("*/", i + 2)
                if j < 0:
                    raise ValueError(f"{source}: 未闭合的块注释 @ {i}")
                i = j + 2
                continue
            return i
        return i
    def parse_string(i):
        quote = text[i]
        assert quote in "\"'", (source, i)
        i += 1
        out = []
        while i < n:
            c = text[i]
            if c == "\\":
                e = text[i + 1]
                mapping = {"n": "\n", "t": "\t", "r": "\r", '"': '"',
                           "'": "'", "\\": "\\", "0": "\0"}
                if e in mapping:
                    out.append(mapping[e]); i += 2
                elif e == "u":
                    out.append(chr(int(text[i + 2:i + 6], 16))); i += 6
                elif e == "U":
                    out.append(chr(int(text[i + 2:i + 10], 16))); i += 10
                else:
                    raise ValueError(f"{source}: 未知转义 \\{e} @ {i}")
            elif c == quote:
                return "".join(out), i + 1
            else:
                out.append(c); i += 1
        raise ValueError(f"{source}: 字符串未闭合 @ {i}")
    while True:
        i = skip_ws_comments(i)
        if i >= n:
            break
        key, i = parse_string(i)
        i = skip_ws_comments(i)
        if i < n and text[i] == "=":
            i += 1
            i = skip_ws_comments(i)
            value, i = parse_string(i)
            i = skip_ws_comments(i)
            if i >= n or text[i] != ";":
                raise ValueError(f"{source}: 缺少 ';' @ {i}")
            i += 1
            entries[key] = value
        else:
            raise ValueError(f"{source}: 缺少 '=' @ {i}")
    return entries


SPEC_RE = re.compile(r"%(?:%|(\d+)\$)?(@|d|u|x|X|o|f|e|g|a|lld|llu|llx|llX|llo|ld|lu|lx|lX|lo|lf|zd|zu|zx|zx|ld)")


def kind_of(spec):
    if spec == "@":
        return "string"
    if spec.endswith("d") or spec.endswith("u") or spec.endswith("x") or spec.endswith("X") \
            or spec.endswith("o"):
        return "int"
    return "float"


def signature(fmt):
    """返回 {位置: 类型}; 位置从 1 开始, 非定位的按出现顺序; %% 忽略。
    返回 None 表示格式串本身有歧义 (同一位置两种类型)。"""
    sig = {}
    order = 0
    for m in SPEC_RE.finditer(fmt):
        if m.group(0) == "%%":
            continue
        spec = m.group(2)
        if m.group(1):
            pos = int(m.group(1))
        else:
            order += 1
            pos = order
        k = kind_of(spec)
        if sig.get(pos, k) != k:
            return None
        sig[pos] = k
    return sig


def check_placeholder(key, value):
    """对齐 catalog.rs: 译文的签名必须被原文签名覆盖 (子集, 类型一致)。"""
    ks, vs = signature(key), signature(value)
    if ks is None or vs is None:
        return "原文或译文的格式串无法解析"
    for pos, kind in vs.items():
        if ks.get(pos) != kind:
            return f"译文占位符 %{pos} 类型 {kind} 不在原文签名 {ks} 中"
    return None


def main():
    errors, warnings = [], []

    # --- package.json ---
    with open(os.path.join(ROOT, "package.json"), encoding="utf-8") as f:
        pkg = json.load(f)
    muxy = pkg.get("muxy") or {}
    localizations = muxy.get("localizations") or []
    if not localizations:
        errors.append("package.json 缺少 muxy.localizations")
    if pkg.get("name") != "muxy-zh-hans":
        errors.append("package name 必须是 muxy-zh-hans (安装时目录名必须一致)")

    # --- 每个本地化条目 ---
    for loc in localizations:
        language, bundle_rel = loc["language"], loc["bundle"]
        bundle = os.path.join(ROOT, bundle_rel)
        if not os.path.isdir(bundle):
            errors.append(f"bundle 目录不存在: {bundle_rel}")
            continue
        info = os.path.join(bundle, "Info.plist")
        if not os.path.isfile(info):
            errors.append(f"{bundle_rel}: 缺少 Info.plist")
        else:
            content = open(info, encoding="utf-8").read()
            if "CFBundleExecutable" in content:
                errors.append(f"{bundle_rel}: Info.plist 不得包含 CFBundleExecutable")
        lproj = os.path.join(bundle, f"{language}.lproj")
        if not os.path.isdir(lproj):
            errors.append(f"缺少 {language}.lproj 目录")
            continue
        for name in sorted(os.listdir(lproj)):
            path = os.path.join(lproj, name)
            size = os.path.getsize(path)
            if size > MAX_BYTES:
                errors.append(f"{name} 超过 4 MiB 上限")

        strings_path = os.path.join(lproj, "Localizable.strings")
        if not os.path.isfile(strings_path):
            errors.append(f"缺少 Localizable.strings")
            continue

        zh = parse_strings(open(strings_path, encoding="utf-8").read(), strings_path)

        # --- 占位符校验 ---
        for k, v in zh.items():
            problem = check_placeholder(k, v)
            if problem:
                errors.append(f"占位符错误: {k!r} → {v!r}: {problem}")

        # --- 与英文目录对比 ---
        en = {}
        if os.path.isfile(EN_CATALOG):
            en = parse_strings(open(EN_CATALOG, encoding="utf-8").read(), EN_CATALOG)
            missing = [k for k in en if k not in zh]
            extra = [k for k in zh if k not in en]
            untranslated = [k for k in zh if k in en and zh[k] == en[k]
                            and re.search(r"[A-Za-z]{2,}", k)]
            if missing:
                warnings.append(f"缺少翻译 {len(missing)} 条 (将回落英文), 例如: {missing[:5]}")
            if extra:
                errors.append(f"存在英文目录中没有的键 {len(extra)} 条, 例如: {extra[:5]}")
            print(f"英文目录: {len(en)} 条 | 已翻译: {len(zh) - len(untranslated)} 条 | "
                  f"未翻译: {len(untranslated)} 条")
            if untranslated:
                warnings.append(f"未翻译键示例: {untranslated[:5]}")

    for w in warnings:
        print(f"[warn] {w}")
    for e in errors:
        print(f"[error] {e}", file=sys.stderr)
    if errors:
        sys.exit(1)
    print("校验通过 ✓")


if __name__ == "__main__":
    main()
