#!/usr/bin/env python3
"""Skill Maker - Skill 编译器：读取 SKILL.md 和 tools/ 代码，生成 Anthropic Tool Use 规范的 tools_schema.json"""

import argparse
import ast
import json
import os
import sys

from anthropic import Anthropic

SCHEMA_SYSTEM_PROMPT = """你是一个 API Schema 生成专家。你的任务是根据 SKILL.md 文档和工具代码信息，生成符合 Anthropic Tool Use 规范的 JSON Schema。

每个工具的 schema 格式如下：
{
  "name": "工具名称",
  "description": "工具描述（结合 SKILL.md 上下文和代码 docstring）",
  "input_schema": {
    "type": "object",
    "properties": {
      "参数名": {
        "type": "参数类型",
        "description": "参数描述"
      }
    },
    "required": ["必填参数列表"]
  }
}

请根据提供的信息，为每个工具生成准确的 schema。从 run() 函数的 kwargs 用法和 docstring 中推断参数。

输出格式要求（用标记包裹）：
---SCHEMA_START---
[
  { ... },
  { ... }
]
---SCHEMA_END---
"""


def parse_between(text: str, start_marker: str, end_marker: str) -> str | None:
    """提取两个标记之间的内容"""
    start = text.find(start_marker)
    end = text.find(end_marker)
    if start == -1 or end == -1:
        return None
    return text[start + len(start_marker):end]


def validate_skill_dir(skill_dir: str):
    """校验目录结构（manifest.json、SKILL.md、tools/）"""
    if not os.path.isdir(skill_dir):
        print(f"错误: 目录 '{skill_dir}' 不存在")
        sys.exit(1)
    for fname in ("manifest.json", "SKILL.md"):
        if not os.path.isfile(os.path.join(skill_dir, fname)):
            print(f"错误: '{skill_dir}' 中缺少 {fname}")
            sys.exit(1)
    tools_dir = os.path.join(skill_dir, "tools")
    if not os.path.isdir(tools_dir):
        print(f"错误: '{skill_dir}' 中缺少 tools/ 目录")
        sys.exit(1)


def read_skill_md(skill_dir: str) -> str:
    """读取 SKILL.md 内容"""
    path = os.path.join(skill_dir, "SKILL.md")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def scan_tools(skill_dir: str) -> list[dict]:
    """遍历 tools/ 下所有 .py，用 ast 模块提取工具信息"""
    tools_dir = os.path.join(skill_dir, "tools")
    tools = []

    for filename in sorted(os.listdir(tools_dir)):
        if not filename.endswith(".py") or filename == "__init__.py":
            continue

        filepath = os.path.join(tools_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        tool_name = filename[:-3]  # 去掉 .py
        tool_info = {"name": tool_name, "module_docstring": None, "run_docstring": None, "code": source}

        try:
            tree = ast.parse(source)
        except SyntaxError:
            print(f"警告: {filepath} 存在语法错误，跳过")
            continue

        # 提取模块 docstring
        tool_info["module_docstring"] = ast.get_docstring(tree)

        # 提取 run() 函数 docstring
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "run":
                tool_info["run_docstring"] = ast.get_docstring(node)
                break

        tools.append(tool_info)

    return tools


def generate_tool_schema(client: Anthropic, skill_md: str, tools: list[dict]) -> list[dict]:
    """将 SKILL.md + 工具信息发送给 Claude，生成 Anthropic Tool Use schema"""
    tools_description = ""
    for tool in tools:
        tools_description += f"\n### 工具: {tool['name']}\n"
        if tool["module_docstring"]:
            tools_description += f"模块说明: {tool['module_docstring']}\n"
        if tool["run_docstring"]:
            tools_description += f"run() 说明: {tool['run_docstring']}\n"
        tools_description += f"完整代码:\n```python\n{tool['code']}\n```\n"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4096,
        system=SCHEMA_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"以下是 SKILL.md 内容：\n\n{skill_md}\n\n"
                f"以下是工具信息：\n{tools_description}"
            ),
        }],
    )
    result_text = response.content[0].text
    json_str = parse_between(result_text, "---SCHEMA_START---", "---SCHEMA_END---")
    if not json_str:
        print("警告: 无法解析 Claude 的 schema 输出")
        return []
    return json.loads(json_str.strip())


def write_schema_file(skill_dir: str, schema: list[dict]):
    """写入 tools_schema.json"""
    path = os.path.join(skill_dir, "tools_schema.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=2)
    print(f"已生成: {path}")


def update_manifest_tools(skill_dir: str, tools: list[dict]):
    """同步 manifest.json 的 tools 列表"""
    path = os.path.join(skill_dir, "manifest.json")
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    manifest["tools"] = [t["name"] for t in tools]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"已更新: {path}")


def main():
    parser = argparse.ArgumentParser(description="Skill Maker - Skill 编译器")
    parser.add_argument("--skill-dir", required=True, help="Skill 目录路径")
    args = parser.parse_args()

    skill_dir = os.path.abspath(args.skill_dir)
    validate_skill_dir(skill_dir)

    skill_md = read_skill_md(skill_dir)
    tools = scan_tools(skill_dir)

    if not tools:
        print("tools/ 目录下没有找到工具文件（已排除 __init__.py）。")
        return

    print(f"发现 {len(tools)} 个工具: {', '.join(t['name'] for t in tools)}")
    print("正在生成 Tool Use Schema...")

    client = Anthropic()
    schema = generate_tool_schema(client, skill_md, tools)

    if not schema:
        print("Schema 生成失败。")
        return

    write_schema_file(skill_dir, schema)
    update_manifest_tools(skill_dir, tools)
    print("\n编译完成！")


if __name__ == "__main__":
    main()
