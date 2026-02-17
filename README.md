# Skill Maker Infra

**Transforming Financial Expertise into Executable AI Agent Skills.**

---

## 🌟 Overview / 项目简介

`Skill Maker Infra` is a framework designed to bridge the gap between domain expertise and AI Agents. It provides a standardized pipeline to extract implicit logic, modularize business code, and compile them into "Professional Skills" that any AI Agent can immediately understand and execute.

`Skill Maker Infra` 是一个旨在弥合领域专家经验与 AI Agent 之间鸿沟的框架。它提供了一套标准化的流程，用于提取隐性逻辑、模块化业务代码，并将其编译为任何 AI Agent 都能立即理解并执行的“专业技能包”。

---

## 🚀 Key Features / 核心功能

*   **Standardized Skill Architecture**: A rigorous structure (`manifest.json`, `SKILL.md`, `tools/`) for consistency.
    *   **标准化技能架构**：提供严格的目录结构，确保技能包的一致性与可维护性。
*   **Expert Interviewer Agent**: A "Knowledge Engineer" that extracts decision chains through interactive dialogue.
    *   **专家访谈 Agent**：通过互动对话提取专家脑中的决策链、风险阈值和业务红线。
*   **Code-to-Skill Suggester**: Automatically identifies and refactors business logic into reusable Skills.
    *   **代码自动识别**：智能扫描现有代码，自动识别并重构业务逻辑为可复用技能。
*   **Skill Compiler**: Generates **Anthropic Tool Use** (JSON Schema) from natural language and Python code.
    *   **Skill 编译器**：自动将自然语言逻辑与 Python 代码转换为符合 Anthropic 规范的工具集。

---

## 📁 Project Structure / 项目结构

```text
.
├── skill_init.py           # Project initializer / 项目初始化工具
├── expert_interviewer.py    # Knowledge extraction agent / 知识提取助手
├── scan_code.py            # Code analysis & refactoring / 代码扫描与重构
├── skill_compiler.py       # Tool Schema generator / 技能编译器
└── skills/                 # Registry of generated skills / 生成的技能库
    └── [skill-name]/
        ├── manifest.json   # Metadata / 元数据
        ├── SKILL.md        # Expert logic & Prompts / 专家逻辑与提示词
        ├── tools/          # Python implementation / Python 工具实现
        └── knowledge/      # Reference docs & templates / 参考文档与模板
