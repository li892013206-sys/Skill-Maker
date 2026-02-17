#!/usr/bin/env python3
"""Skill Maker - 初始化标准 Skill Package 目录结构"""

import argparse
import json
import os


MANIFEST_TEMPLATE = {
    "name": "",
    "version": "0.1.0",
    "author": "",
    "description": "",
    "industry": "finance",
    "tags": [],
    "tools": [],
    "knowledge": [],
}

SKILL_MD_TEMPLATE = """# {name}

## 角色定义
<!-- 描述该 Skill 扮演的专家角色 -->

## 核心能力
<!-- 列出该 Skill 的关键能力 -->

## 决策链
<!-- 描述专家的推理和决策流程 -->
1.
2.
3.

## 约束条件
<!-- 定义该 Skill 的边界和限制 -->
-

## 输出规范
<!-- 定义输出的格式和质量要求 -->
"""

TOOL_TEMPLATE = '''"""
Tool: {tool_name}
Skill: {skill_name}
"""


def run(**kwargs):
    """工具入口函数"""
    raise NotImplementedError("请实现该工具的具体逻辑")
'''


def create_skill(base_dir: str, name: str, author: str, industry: str):
    """创建标准 Skill Package 目录结构"""
    skill_dir = os.path.join(base_dir, name)

    if os.path.exists(skill_dir):
        print(f"错误: 目录 '{skill_dir}' 已存在")
        return False

    # 创建目录
    os.makedirs(os.path.join(skill_dir, "tools"))
    os.makedirs(os.path.join(skill_dir, "knowledge"))

    # 写入 manifest.json
    manifest = {**MANIFEST_TEMPLATE, "name": name, "author": author, "industry": industry}
    with open(os.path.join(skill_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 写入 SKILL.md
    with open(os.path.join(skill_dir, "SKILL.md"), "w", encoding="utf-8") as f:
        f.write(SKILL_MD_TEMPLATE.format(name=name))

    # 写入工具占位文件
    with open(os.path.join(skill_dir, "tools", "__init__.py"), "w") as f:
        pass
    with open(os.path.join(skill_dir, "tools", "example_tool.py"), "w", encoding="utf-8") as f:
        f.write(TOOL_TEMPLATE.format(tool_name="example_tool", skill_name=name))

    # knowledge 目录放一个 README
    with open(os.path.join(skill_dir, "knowledge", "README.md"), "w", encoding="utf-8") as f:
        f.write("# Knowledge\n\n将该 Skill 专用的参考文档放在此目录下（PDF、Excel、CSV 等）。\n")

    print(f"Skill '{name}' 创建成功: {skill_dir}")
    print(f"  ├── manifest.json")
    print(f"  ├── SKILL.md")
    print(f"  ├── tools/")
    print(f"  │   ├── __init__.py")
    print(f"  │   └── example_tool.py")
    print(f"  └── knowledge/")
    print(f"      └── README.md")
    return True


def main():
    parser = argparse.ArgumentParser(description="Skill Maker - 创建标准 Skill Package")
    parser.add_argument("name", help="Skill 名称（英文，用作目录名）")
    parser.add_argument("--author", default="anonymous", help="作者名称")
    parser.add_argument("--industry", default="finance", help="行业分类 (默认: finance)")
    parser.add_argument("--output", default="./skills", help="输出根目录 (默认: ./skills)")
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    create_skill(args.output, args.name, args.author, args.industry)


if __name__ == "__main__":
    main()
