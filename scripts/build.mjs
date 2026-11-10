#!/usr/bin/env node
/**
 * 打包脚本: 把语言包组装成可安装/可发布的目录 dist/。
 * 语言包是纯资源扩展, 没有编译步骤, 只需把 package.json 与 localization/
 * 原样复制到 dist/ (Muxy 加载时优先读 dist/package.json)。
 *
 *   node scripts/build.mjs
 */
import { cpSync, mkdirSync, rmSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const dist = join(root, "dist");

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });

for (const entry of ["package.json", "localization", "icon.svg", "README.md"]) {
  try {
    cpSync(join(root, entry), join(dist, entry), { recursive: true });
    console.log("copied", entry);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
}

console.log("built dist/ — 用 Muxy 的 Settings → Extensions → Unpacked 加载, 或 muxy extension load dist/");
