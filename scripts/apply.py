#!/usr/bin/env python3
"""翻译批处理工具:

  python3 scripts/apply.py add batch-01.json     # 合并一批翻译 (JSON: {英文原文: 中文})
  python3 scripts/apply.py build                 # 重新生成 Localizable.strings
  python3 scripts/apply.py status                # 查看进度

工作存储: scripts/translations.json (键 = 英文原文, 值 = 中文或 null)
生成时, null 或缺失的键回落为英文原文 (Muxy 的官方回落机制), 文件始终完整。
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "scripts", "translations.json")
EN = os.path.join(ROOT, "..", "muxy", "crates", "muxy-app", "localization", "en.lproj",
                  "Localizable.strings")
OUT = os.path.join(ROOT, "localization", "SimplifiedChinese.bundle", "zh-Hans.lproj",
                   "Localizable.strings")


def parse_strings(text):
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from validate import parse_strings
    return parse_strings(text, EN)


def load_en():
    return parse_strings(open(EN, encoding="utf-8").read())


def load_store():
    if os.path.isfile(STORE):
        return json.load(open(STORE, encoding="utf-8"))
    return {}


def save_store(store):
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=0, sort_keys=True)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    en = load_en()
    store = load_store()

    if cmd == "add":
        batch = json.load(open(sys.argv[2], encoding="utf-8"))
        bad = [k for k in batch if k not in en]
        if bad:
            print(f"[error] 批次里有 {len(bad)} 个键不在英文目录中:", file=sys.stderr)
            for k in bad[:10]:
                print("  ", repr(k), file=sys.stderr)
            sys.exit(1)
        store.update(batch)
        save_store(store)
        print(f"已合并 {len(batch)} 条, 存量 {sum(1 for v in store.values() if v)} 条")
    elif cmd == "build":
        lines = ["/* Muxy 简体中文语言包 — muxy-zh-hans",
                 "   键为 Muxy 英文原文, 未翻译的条目回落英文。 */", ""]
        for key in en:
            value = store.get(key)
            if not value:
                value = key
            lines.append(f"{json.dumps(key, ensure_ascii=False)} = "
                         f"{json.dumps(value, ensure_ascii=False)};")
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        done = sum(1 for k in en if store.get(k))
        print(f"已生成 {OUT}: {len(en)} 条, 其中翻译 {done} 条 ({done * 100 // len(en)}%)")
    elif cmd == "status":
        done = sum(1 for k in en if store.get(k))
        print(f"英文 {len(en)} 条 | 已翻译 {done} 条 | 剩余 {len(en) - done} 条")
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main()
