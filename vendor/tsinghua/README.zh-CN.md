# 清华大学毕业论文格式检查 Skill

[English](./README.md)

这是一个面向 **清华大学研究生学位论文格式审查** 的可复用 Codex skill 与 Python 工作流。

本仓库将“规则脚本检查”和“二阶段人工复核流程”打包到一起。它适用于仅靠文本抽取还不够的场景：有些规则可以通过 DOCX/PDF 结构自动判断，而另一些规则仍需要结合 **PDF 可视化检查** 与 **人工或子代理判断** 才能稳妥完成。

## 项目功能

整个流程分为三层：

1. **自动脚本检查**
   从 DOCX 和 PDF 中抽取证据，执行已实现规则，并生成 Markdown 报告和结构化 JSON 结果。
2. **脚本 + SOP 复核**
   先利用脚本生成预填证据，再由审查者或子代理结合渲染后的 PDF 对版式敏感规则做确认。
3. **纯 SOP 复核**
   处理脚本无法稳定判定的规则，例如中英文摘要内容对应关系。

实际使用中，这个项目适合：

- 答辩前格式预检查
- 导师或学生自查
- 最终 PDF 提交前的结构化质量核查
- 生成带位置依据的论文回复或修改说明

## 主要特性

- 同时使用 **DOCX 文本**、**DOCX XML 元数据**、**PDF 文本** 和 **PDF 可视化版式** 作为并行证据来源。
- 代码中已实现 **48 条自动规则**。
- 将剩余 **8 条规则** 组织为二阶段人工复核流程。
- 生成带定位信息的问题结果，包含：
  - DOCX 段落编号
  - PDF 页码
  - 段落前导文本，方便人工定位
- 支持使用 **Codex 子代理** 并行执行 SOP 复核。
- 在人工结果写回后，自动生成合并后的总报告。

## 仓库结构

- `SKILL.md`
  Codex skill 入口文件。
- `agents/openai.yaml`
  skill 的 UI 元数据。
- `scripts/`
  工作流启动脚本。
- `references/`
  工作流说明、所需文件说明和规则映射。
- `guide_checker/`
  核心检查器实现。
- `tsinghua_p0_p1_rules.json`
  当前使用的规则注册表。

## 环境要求

- Python 3.10+
- `lxml`
- `PyMuPDF`

安装依赖：

```bash
pip install -e .
```

## 快速开始

直接运行完整流程：

```bash
python -X utf8 -m guide_checker.cli.run_full_review \
  --docx /path/to/thesis.docx \
  --pdf /path/to/thesis.pdf
```

也可以使用封装脚本：

```bash
python scripts/start_review.py \
  --docx /path/to/thesis.docx \
  --pdf /path/to/thesis.pdf
```

Windows PowerShell 用法：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_review.ps1 `
  -Docx "D:\path\to\thesis.docx" `
  -Pdf "D:\path\to\thesis.pdf"
```

如果仓库根目录下只有 1 个 DOCX 和 1 个 PDF，检查器也可以尝试自动发现；如果候选文件不止一个，建议显式传参。

## 输出文件

完整流程会把结果写入 `guide_checker/output/`。

核心输出包括：

- `report.md`
- `analysis.json`
- `manual_review_inventory.json`
- `manual_review_results.template.json`
- `manual_review_results.json`
- `script_sop_checklist.md`
- `pure_sop_checklist.md`
- `full_review_report.md`

这些文件的用途分别是：

- `report.md`
  仅包含自动脚本检查结果。
- `manual_review_inventory.json`
  当前运行中二阶段规则分组的权威清单。
- `manual_review_results.json`
  用于填写人工复核结论的结果文件。
- `full_review_report.md`
  自动检查与人工复核合并后的总报告。

## 审查流程

推荐顺序如下：

1. 运行 `run_full_review`。
2. 阅读 `script_sop_checklist.md` 和 `pure_sop_checklist.md`。
3. 用子代理结合 PDF 可视化检查完成剩余规则复核。
4. 将结论写回 `manual_review_results.json`。
5. 再次运行 `run_full_review`，刷新 `full_review_report.md`。

当前二阶段规则分组如下：

- **PDF 可视化复核**
  `REFSEC-02`、`FIG-03`、`TAB-01`
- **术语与摘要形式复核**
  `G-06`、`WR-04`
- **结构与写作复核**
  `WR-05`、`WR-07`
- **中英文摘要对应复核**
  `ABS-07`

## 在 Codex 中使用

可以在 Codex 中这样调用这个 skill：

```text
Use $tsinghua-thesis-format-checker-skill to run the thesis review workflow and refresh the report.
```

建议的 Codex 执行模式是：

- 先运行自动脚本分析
- 生成二阶段复核清单
- 启动子代理执行 PDF 可视化与 SOP 复核
- 将结论写回 `manual_review_results.json`
- 重新生成总报告

## 哪些可自动化，哪些不能

本仓库并不是“一次运行即可完全自动化”的工具。

自动规则比较适合处理：

- 文档结构
- 标题与样式
- 页码模式
- 参考文献结构线索
- 单位、公式、脚注和表内文字样式

仍需要人工或子代理复核的内容包括：

- 图是否紧跟首次引用
- 表是否真正满足三线表要求
- 单条参考文献是否在 PDF 中明显跨页
- 新缩写是否解释得足够清楚
- 中英文摘要是否语义对应

这种“自动 + 人工确认”的混合设计是刻意保留的，因为在论文审查场景里，错误的自动确定性往往比明确要求人工确认更危险。

## 隐私与数据处理

本仓库的设计目标是 **在不携带真实论文文件的前提下开源**。

请不要提交：

- 真实论文 DOCX
- 最终论文 PDF
- 自动生成的审查输出
- 截图
- 个人信息
- 答辩委员名单、个人简历或未公开学术成果

仓库自带的 `.gitignore` 已屏蔽常见本地产物，但每次推送前仍建议手动做一次隐私检查。

## 适用范围与限制

- 当前规则注册表面向 **清华大学研究生学位论文格式要求**。
- 部分规则默认遵循对应写作指南，不一定能直接泛化到其他学校。
- 对于版式敏感规则，仍需要 PDF 可视化复核。
- 仓库未附带公开示例论文文件，因为为保护隐私刻意不包含真实样本。

## 安装后的命令行入口

安装完成后，可使用以下 CLI 入口：

- `tsinghua-thesis-check`
- `tsinghua-thesis-full-review`

示例：

```bash
tsinghua-thesis-check --docx /path/to/thesis.docx --pdf /path/to/thesis.pdf
tsinghua-thesis-full-review --docx /path/to/thesis.docx --pdf /path/to/thesis.pdf
```

## 许可证

本项目使用 MIT License 开源，详见 [LICENSE](LICENSE)。
