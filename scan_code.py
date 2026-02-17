#!/usr/bin/env python3
"""Skill Maker - 代码扫描器：扫描 Python 代码，检测可提取的业务逻辑，自动重构到 Skill Package"""

import argparse
import json
import os
import sys

from anthropic import Anthropic

ANALYSIS_SYSTEM_PROMPT = """你是一个资深的代码分析专家。你的任务是分析 Python 源代码，检测其中包含的"复杂业务计算逻辑"或"重复金融评估流程"。

这些逻辑通常具有以下特征：
- 包含多步骤的数值计算或评估流程
- 涉及行业特定的阈值判断、评分模型、风险评估
- 包含可复用的业务规则或决策逻辑
- 函数内部有较复杂的条件分支或数据转换

请分析用户提供的代码，返回 JSON 格式的分析结果。

输出格式要求（用标记包裹）：
---ANALYSIS_START---
{
  "found": true/false,
  "functions": [
    {
      "name": "函数名",
      "reason": "为什么这个函数适合提取为 Skill 工具",
      "line_start": 起始行号,
      "line_end": 结束行号,
      "code": "函数完整源代码"
    }
  ]
}
---ANALYSIS_END---

如果没有检测到适合提取的函数，返回 {"found": false, "functions": []}。"""

REFACTOR_SYSTEM_PROMPT = """你是一个代码重构专家。你的任务是将一个 Python 函数重构为标准的 Skill 工具格式。

标准工具格式要求：
1. 模块顶部有 docstring，说明工具名称和所属 Skill
2. 有一个 run(**kwargs) 入口函数
3. run() 函数内从 kwargs 中提取参数并执行业务逻辑
4. 保留原始的业务逻辑，但适配为工具调用格式
5. 返回结果应为可序列化的 dict

同时，你需要生成一段 SKILL.md 的调用说明，描述该工具的用途和参数。

输出格式要求：
- 工具代码用 ---TOOL_CODE_START--- 和 ---TOOL_CODE_END--- 包裹
- SKILL.md 调用说明用 ---SKILL_DOC_START--- 和 ---SKILL_DOC_END--- 包裹

示例：
---TOOL_CODE_START---
\"\"\"
Tool: calculate_risk_score
Skill: financial-report-analyzer
\"\"\"


def run(**kwargs):
    \"\"\"计算风险评分\"\"\"
    revenue = kwargs.get("revenue", 0)
    # ... 业务逻辑 ...
    return {"risk_score": score}
---TOOL_CODE_END---

---SKILL_DOC_START---
- **calculate_risk_score**: 根据财务数据计算风险评分。参数：revenue（营收）、debt（负债）。
---SKILL_DOC_END---
"""


def parse_between(text: str, start_marker: str, end_marker: str) -> str | None:
    """提取两个标记之间的内容"""
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1:
        return None
    return text[start + len(start_marker):end]


def validate_inputs(file_path: str, skill_dir: str):
    """校验输入文件和 skill 目录"""
    if not os.path.isfile(file_path):
        print(f"错误: 文件 '{file_path}' 不存在")
        sys.exit(1)
    if not file_path.endswith(".py"):
        print(f"错误: '{file_path}' 不是 Python 文件")
        sys.exit(1)
    if not os.path.isdir(skill_dir):
        print(f"错误: 目录 '{skill_dir}' 不存在")
        sys.exit(1)
    for fname in ("manifest.json", "SKILL.md"):
        if not os.path.isfile(os.path.join(skill_dir, fname)):
            print(f"错误: '{skill_dir}' 中缺少 {fname}")
            sys.exit(1)


def analyze_code(client: Anthropic, code: str) -> dict:
    """发送代码给 Claude 分析，返回检测结果"""
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"请分析以下 Python 代码：\n\n```python\n{code}\n```"}],
    )
    result_text = response.content[0].text
    json_str = parse_between(result_text, "---ANALYSIS_START---", "---ANALYSIS_END---")
    if not json_str:
        print("警告: 无法解析 Claude 的分析结果")
        return {"found": False, "functions": []}
    return json.loads(json_str.strip())


def prompt_user_confirmation(analysis: dict) -> list:
    """展示检测结果，让用户确认要提取的函数"""
    if not analysis["found"] or not analysis["functions"]:
        print("\n未检测到适合提取的业务逻辑函数。")
        return []

    print(f"\n检测到 {len(analysis['functions'])} 个潜在的 Professional Skill 函数：\n")
    for i, func in enumerate(analysis["functions"], 1):
        print(f"  {i}. {func['name']} (行 {func['line_start']}-{func['line_end']})")
        print(f"     原因: {func['reason']}\n")

    print("检测到潜在的 Professional Skill，是否将其抽离并封装到我们的 Skill Registry 中？")
    answer = input("确认提取？(y/n): ").strip().lower()
    if answer != "y":
        print("已取消。")
        return []
    return analysis["functions"]


def refactor_to_tool(client: Anthropic, func: dict, skill_name: str) -> tuple[str | None, str | None]:
    """将函数重构为标准工具格式，返回 (tool_code, skill_doc)"""
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=REFACTOR_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"请将以下函数重构为 Skill 工具格式。\n"
                f"所属 Skill: {skill_name}\n"
                f"函数名: {func['name']}\n\n"
                f"```python\n{func['code']}\n```"
            ),
        }],
    )
    result_text = response.content[0].text
    tool_code = parse_between(result_text, "---TOOL_CODE_START---", "---TOOL_CODE_END---")
    skill_doc = parse_between(result_text, "---SKILL_DOC_START---", "---SKILL_DOC_END---")
    return (tool_code.strip() if tool_code else None, skill_doc.strip() if skill_doc else None)


def write_tool_file(skill_dir: str, func_name: str, tool_code: str):
    """将工具代码写入 tools/ 目录"""
    tools_dir = os.path.join(skill_dir, "tools")
    os.makedirs(tools_dir, exist_ok=True)
    path = os.path.join(tools_dir, f"{func_name}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(tool_code + "\n")
    print(f"已生成工具文件: {path}")


def update_skill_md(skill_dir: str, skill_doc: str):
    """将调用说明追加到 SKILL.md 的核心能力 section"""
    path = os.path.join(skill_dir, "SKILL.md")
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    marker = "## 核心能力"
    idx = content.find(marker)
    if idx == -1:
        content += f"\n## 核心能力\n{skill_doc}\n"
    else:
        # 找到下一个 ## 标题或文件末尾
        next_section = content.find("\n## ", idx + len(marker))
        insert_pos = next_section if next_section != -1 else len(content)
        content = content[:insert_pos].rstrip() + "\n" + skill_doc + "\n\n" + content[insert_pos:]

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已更新: {path}")


def update_manifest(skill_dir: str, func_name: str):
    """将工具名加入 manifest.json 的 tools 列表"""
    path = os.path.join(skill_dir, "manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    if func_name not in manifest.get("tools", []):
        manifest.setdefault("tools", []).append(func_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"已更新: {path}")


def main():
    parser = argparse.ArgumentParser(description="Skill Maker - 代码扫描器")
    parser.add_argument("--file", required=True, help="要扫描的 Python 文件路径")
    parser.add_argument("--skill-dir", required=True, help="目标 Skill 目录路径")
    args = parser.parse_args()

    file_path = os.path.abspath(args.file)
    skill_dir = os.path.abspath(args.skill_dir)

    validate_inputs(file_path, skill_dir)

    with open(file_path, "r", encoding="utf-8") as f:
        code = f.read()

    # 读取 skill 名称
    manifest_path = os.path.join(skill_dir, "manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as f:
        skill_name = json.load(f).get("name", "unknown")

    client = Anthropic()

    print(f"正在分析: {file_path}")
    analysis = analyze_code(client, code)

    functions = prompt_user_confirmation(analysis)
    if not functions:
        return

    for func in functions:
        print(f"\n正在重构: {func['name']}...")
        tool_code, skill_doc = refactor_to_tool(client, func, skill_name)

        if not tool_code:
            print(f"警告: 无法重构 {func['name']}，跳过")
            continue

        write_tool_file(skill_dir, func["name"], tool_code)
        if skill_doc:
            update_skill_md(skill_dir, skill_doc)
        update_manifest(skill_dir, func["name"])

    print("\n扫描重构完成！")


if __name__ == "__main__":
    main()
