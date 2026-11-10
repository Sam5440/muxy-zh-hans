# muxy-zh-hans · Muxy 简体中文语言包

Muxy 2.x 桌面端的**简体中文语言包**，以官方扩展（语言包）机制实现，无需修改 Muxy 本体。

A Simplified Chinese language pack for the Muxy 2.x desktop app, built with the
official extension (localization) mechanism — no Muxy modifications required.

## 功能 / Features

- 覆盖 Muxy 全部 **2352 条**界面字符串（界面、设置、菜单、Git/源代码管理、扩展、浏览器等）
- 按官方机制自动回落：极少数品牌名（App Store、Google Play 等）保留英文原文
- 占位符（`%@`、`%lld`、定位参数）与英文原文严格对齐，通过加载器校验
- 自带校验脚本，规则对齐 `muxy-app/muxy` 的 `localization.rs` + `catalog.rs`

## 安装 / Install

### 方式一：从源码加载（Unpacked）

```bash
git clone https://github.com/sam5440/muxy-zh-hans.git
# 然后在 Muxy 中: Settings → Extensions → Load Unpacked… 选择本目录
```

或使用 Muxy CLI：

```bash
muxy extension load muxy-zh-hans
muxy extension enable muxy-zh-hans
```

### 方式二：使用安装后的包

```bash
node scripts/build.mjs   # 生成 dist/
muxy extension load muxy-zh-hans/dist
muxy extension enable muxy-zh-hans
```

### 启用中文

在 **Settings → Appearance → App language** 中选择 **简体中文**。

## 开发 / Development

```bash
python3 scripts/validate.py          # 校验占位符/键完整性 (需要旁侧有 muxy 源码检出)
python3 scripts/apply.py status      # 查看翻译进度
python3 scripts/apply.py build       # 从 translations.json 生成 Localizable.strings
node scripts/build.mjs               # 组装 dist/
```

翻译存储在 `scripts/translations.json`（键 = 英文原文）。生成时未翻译的键回落英文，
因此 `Localizable.strings` 始终是完整、可加载的。

## 目录结构 / Layout

```
package.json                 Muxy 扩展清单 (muxy.localizations)
localization/
  SimplifiedChinese.bundle/
    Info.plist               资源包清单 (无 CFBundleExecutable)
    zh-Hans.lproj/
      Localizable.strings    2352 条翻译
scripts/
  validate.py                对齐 Muxy 加载器规则的校验器
  apply.py                   翻译批处理工具
  translations.json          翻译源数据
  build.mjs                  dist/ 组装脚本
```

## 许可 / License

MIT。Muxy 是 [muxy-app/muxy](https://github.com/muxy-app/muxy) 的产品，
本语言包是独立的社区翻译扩展，与 Muxy 官方无关。
